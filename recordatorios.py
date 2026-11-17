"""Worker independiente: generar recordatorios y despachar mensajes pendientes."""

import argparse
import logging
import time
import sqlite3
from contextlib import closing, contextmanager
from datetime import timedelta

import httpx
import conexion

from conexion import conectar
from tiempos import ahora_utc, instante
from whatsapp_api import reconciliar_estado
from whatsapp_config import Config
from whatsapp_servicio import encolar, normalizar_telefono, detalle_recordatorio


def generar(db, ahora=None):
    ahora = ahora or ahora_utc()
    citas = db.execute("""SELECT a.id, a.patient_id, a.appointment_date, a.created_at,
        a.professional, a.specialty
        FROM appointments a JOIN patients p ON p.id=a.patient_id
        WHERE a.status IN ('scheduled','confirmed') AND p.consent_whatsapp=1""").fetchall()
    for cita_id, paciente_id, fecha, creada, profesional, especialidad in citas:
        fecha_utc = instante(fecha, local=True)
        if fecha_utc <= ahora or not creada:
            continue
        vencidos = [
            (fecha_utc - timedelta(hours=h), h)
            for h in (72, 24)
            if instante(creada) <= fecha_utc - timedelta(hours=h) <= ahora
        ]
        if not vencidos:
            continue
        _, horas = max(vencidos)
        encolar(
            db,
            paciente_id,
            cita_id,
            f"{horas}h",
            detalle_recordatorio(cita_id, profesional, especialidad, fecha)[0],
            ahora,
        )


def construir_payload(db, fila, config, ahora):
    paciente = db.execute(
        "SELECT phone, consent_whatsapp FROM patients WHERE id=?", (fila["patient_id"],)
    ).fetchone()
    telefono = normalizar_telefono(paciente[0]) if paciente else None
    if not paciente or paciente[1] != 1 or telefono not in config.allowed:
        return None, "blocked_recipient"
    payload = {"messaging_product": "whatsapp", "to": telefono}
    if fila["kind"] == "reply":
        recibida = db.execute(
            "SELECT received_at FROM whatsapp_inbound WHERE id=?", (fila["inbound_id"],)
        ).fetchone()
        if not recibida or ahora - instante(recibida[0]) >= timedelta(hours=24):
            return None, "expired_window"
        payload.update(type="text", text={"body": fila["message"]})
    else:
        cita = db.execute(
            "SELECT status, appointment_date, professional, specialty FROM appointments WHERE id=?",
            (fila["appointment_id"],),
        ).fetchone()
        if (
            not cita
            or cita[0] not in ("scheduled", "confirmed")
            or instante(cita[1], local=True) <= ahora
        ):
            return None, "cancelled"
        if fila["kind"] == "72h" and instante(cita[1], local=True) - ahora <= timedelta(
            hours=24
        ):
            return None, "superseded"
        if not config.template:
            return None, "blocked_template"
        _, parametros = detalle_recordatorio(
            fila["appointment_id"], cita[2], cita[3], cita[1]
        )
        payload.update(
            type="template",
            template={
                "name": config.template,
                "language": {"code": config.language},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": valor} for valor in parametros
                        ],
                    }
                ],
            },
        )
    return payload, None


def despachar(config, cliente=None, ahora=None):
    config.validar_envio()
    ahora = ahora or ahora_utc()
    with closing(conectar()) as db:
        db.row_factory = sqlite3.Row
        # Un único worker. Un envío interrumpido es incierto y no se reenvía.
        ids = db.execute(
            "SELECT id FROM whatsapp_outbox WHERE status IN ('pending','retry') AND next_attempt_at<=? ORDER BY id LIMIT 50",
            (ahora.isoformat(),),
        ).fetchall()
        for (identificador,) in ids:
            with db:
                db.execute("BEGIN IMMEDIATE")
                fila = db.execute(
                    "SELECT * FROM whatsapp_outbox WHERE id=? AND status IN ('pending','retry')",
                    (identificador,),
                ).fetchone()
                if not fila:
                    continue
                payload, bloqueo = construir_payload(db, fila, config, ahora)
                if bloqueo:
                    db.execute(
                        "UPDATE whatsapp_outbox SET status=? WHERE id=?",
                        (bloqueo, identificador),
                    )
                    continue
                db.execute(
                    "UPDATE whatsapp_outbox SET status='sending', attempts=attempts+1 WHERE id=?",
                    (identificador,),
                )
            estado, codigo, meta_id = "uncertain", None, None
            try:
                enviar = cliente.post if cliente else httpx.post
                respuesta = enviar(
                    f"https://graph.facebook.com/{config.version}/{config.phone_id}/messages",
                    headers={"Authorization": "Bearer " + config.token},
                    json=payload,
                    timeout=15,
                )
                datos = respuesta.json()
                if 200 <= respuesta.status_code < 300:
                    meta_id = datos["messages"][0]["id"]
                    estado = "accepted"
                else:
                    error = datos.get("error", {})
                    codigo = str(error.get("code", respuesta.status_code))
                    transitorio = (
                        respuesta.status_code == 429
                        or error.get("is_transient") is True
                    )
                    estado = (
                        "retry"
                        if transitorio and fila["attempts"] + 1 < 3
                        else "failed"
                    )
            except (httpx.TransportError, ValueError, KeyError, IndexError, TypeError):
                # No se sabe si Meta aceptó el mensaje. Revisión manual.
                estado = "uncertain"
            with db:
                db.execute(
                    """UPDATE whatsapp_outbox SET status=?, meta_id=?, error_code=?,
                    accepted_at=?, next_attempt_at=? WHERE id=?""",
                    (
                        estado,
                        meta_id,
                        codigo,
                        ahora.isoformat() if meta_id else None,
                        (
                            ahora + timedelta(minutes=2 ** (fila["attempts"] + 1))
                        ).isoformat(),
                        identificador,
                    ),
                )
                if meta_id:
                    reconciliar_estado(db, meta_id)


def ciclo(config):
    with closing(conectar()) as db, db:
        db.execute("BEGIN IMMEDIATE")
        generar(db)
    if config.enabled:
        despachar(config)


@contextmanager
def bloqueo_worker():
    """Candado de SO mediante SQLite separada: no bloquea la agenda."""
    with closing(
        sqlite3.connect(str(conexion.ruta_db) + ".worker.db", timeout=0)
    ) as lock:
        try:
            lock.execute("BEGIN EXCLUSIVE")
        except sqlite3.OperationalError:
            raise RuntimeError("Ya existe un worker activo para esta base.") from None
        try:
            yield
        finally:
            lock.rollback()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    config = Config()
    if config.enabled:
        config.validar_envio()
    with bloqueo_worker():
        with closing(conectar()) as db, db:
            db.execute(
                "UPDATE whatsapp_outbox SET status='uncertain' WHERE status='sending'"
            )
        while True:
            inicio = time.monotonic()
            try:
                ciclo(config)
            except Exception:
                logging.error(
                    "Ciclo fallido; revisar configuración y base local. No se registran credenciales."
                )
                if args.once:
                    raise
            if args.once:
                break
            time.sleep(max(0, 60 - (time.monotonic() - inicio)))


if __name__ == "__main__":
    main()
