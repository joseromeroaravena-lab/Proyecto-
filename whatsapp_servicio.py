import re
import json
from datetime import datetime, timezone

from citas_servicio import cambiar_estado
from tiempos import ahora_utc, instante, SANTIAGO
from whatsapp_botones import resolver_boton


def detalle_recordatorio(cita_id, profesional, especialidad, fecha, botones=False):
    local = instante(fecha, local=True).astimezone(SANTIAGO)
    especialista = f"{profesional} ({especialidad})"
    parametros = [
        especialista,
        local.strftime("%d/%m/%Y"),
        local.strftime("%H:%M"),
        str(cita_id),
    ]
    if botones:
        texto = (
            f"Tienes una cita médica con {especialista}.\n"
            f"Fecha: {parametros[1]}.\nHora: {parametros[2]}.\n\n"
            "Selecciona Confirmar o Cancelar para responder sobre esta cita.\n"
            "Demostración académica con datos ficticios."
        )
        return texto, parametros[:3]
    texto = (
        f"Tienes una cita médica con {especialista} el {parametros[1]} a las {parametros[2]}.\n\n"
        "Responde con una opción:\n1. Confirmar asistencia\n2. Cancelar cita\n\n"
        f"Referencia de tu cita: {cita_id}.\nDemostración académica con datos ficticios."
    )
    return texto, parametros


def normalizar_telefono(valor):
    if not isinstance(valor, str) or not re.fullmatch(r"\+?[1-9][0-9]{7,14}", valor):
        return None
    return valor.lstrip("+")


def encolar(db, paciente_id, cita_id, tipo, mensaje, ahora, inbound_id=None):
    db.execute(
        """INSERT OR IGNORE INTO whatsapp_outbox
        (patient_id, appointment_id, inbound_id, kind, message, created_at, next_attempt_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            paciente_id,
            cita_id,
            inbound_id,
            tipo,
            mensaje,
            ahora.isoformat(),
            ahora.isoformat(),
        ),
    )


def recibir(db, mensaje, ahora=None, secreto_botones=""):
    ahora = ahora or ahora_utc()
    meta_id = mensaje["id"]
    if db.execute(
        "SELECT 1 FROM whatsapp_inbound WHERE meta_id=?", (meta_id,)
    ).fetchone():
        return "duplicate"
    telefono = normalizar_telefono(mensaje.get("from"))
    pacientes = db.execute(
        "SELECT id, phone, consent_whatsapp FROM patients"
    ).fetchall()
    pacientes = [
        p for p in pacientes if telefono and normalizar_telefono(p[1]) == telefono
    ]
    paciente = pacientes[0] if len(pacientes) == 1 else None
    contenido = mensaje.get("text", {}).get("body", "")
    if mensaje.get("type") == "button":
        contenido = mensaje.get("button", {}).get("text", "")
    if mensaje.get("type") == "interactive":
        contenido = mensaje.get("interactive", {}).get("button_reply", {}).get("id", "")
    contenido = str(contenido)[:4096]
    entrada = contenido
    es_boton = mensaje.get("type") in ("button", "interactive")
    token_boton = None
    if mensaje.get("type") == "button":
        token_boton = mensaje.get("button", {}).get("payload")
    elif mensaje.get("type") == "interactive":
        token_boton = mensaje.get("interactive", {}).get("button_reply", {}).get("id")
    if es_boton:
        contenido = json.dumps(
            {
                "text": entrada,
                "payload": token_boton,
                "context": mensaje.get("context", {}).get("id"),
            },
            ensure_ascii=False,
        )[:4096]
    cita_id = None
    resultado = "unauthorized"
    acuse = None
    if paciente and paciente[2] == 1:
        if es_boton:
            seleccion = resolver_boton(
                db,
                paciente[0],
                token_boton,
                secreto_botones,
                mensaje.get("context", {}).get("id"),
            )
            entrada = f"{seleccion[0]} {seleccion[1]}" if seleccion else ""
        comando = re.fullmatch(
            r"(confirmar|cancelar|1|2)(?:\s+([0-9]+))?", entrada.strip(), re.I
        )
        if not comando:
            resultado = "invalid_button" if es_boton else "invalid"
            acuse = (
                "No pude validar este botón. Usa los botones de un recordatorio vigente."
                if es_boton
                else "Responde 1 para confirmar o 2 para cancelar. "
                "Si tienes varias citas, indica también la referencia: 1 <ID> o 2 <ID>."
            )
        else:
            accion, referencia = comando.groups()
            accion = {"1": "confirmar", "2": "cancelar"}.get(accion, accion.lower())
            if referencia:
                candidata = (
                    db.execute(
                        "SELECT id FROM appointments WHERE id=? AND patient_id=?",
                        (int(referencia), paciente[0]),
                    ).fetchone()
                    if len(referencia) < 19
                    else None
                )
                cita_id = candidata[0] if candidata else None
            elif mensaje.get("context", {}).get("id"):
                # Respuesta citada: vincular solo mensajes enviados a este paciente.
                candidata = db.execute(
                    """SELECT appointment_id FROM whatsapp_outbox
                       WHERE meta_id=? AND patient_id=? AND appointment_id IS NOT NULL""",
                    (mensaje["context"]["id"], paciente[0]),
                ).fetchone()
                cita_id = candidata[0] if candidata else None
            else:
                citas = db.execute(
                    """SELECT id, appointment_date FROM appointments
                    WHERE patient_id=? AND status IN ('scheduled','confirmed')""",
                    (paciente[0],),
                ).fetchall()
                citas = [c for c in citas if instante(c[1], local=True) > ahora]
                if len(citas) == 1:
                    cita_id = citas[0][0]
                elif len(citas) > 1:
                    resultado = "ambiguous"
                    acuse = (
                        "Tienes varias citas. Usa el botón Confirmar o Cancelar del "
                        "recordatorio correspondiente, o responde citando el mensaje "
                        "usando Responder en WhatsApp, o escribe 1 <ID> para confirmar "
                        "o 2 <ID> para cancelar. Referencias: "
                        + ", ".join(str(c[0]) for c in citas)
                    )
            if acuse is None:
                resultado = cambiar_estado(
                    db, cita_id, paciente[0], accion.lower(), ahora
                )
                acuse = {
                    "confirmed": "Tu cita quedó confirmada.",
                    "cancelled": "Tu cita quedó cancelada.",
                    "already_confirmed": "Tu cita ya está confirmada.",
                    "already_cancelled": "Tu cita ya está cancelada.",
                }.get(
                    resultado,
                    "La cita no está disponible para esta acción. Indica un ID válido.",
                )
                if resultado in (
                    "confirmed",
                    "cancelled",
                    "already_confirmed",
                    "already_cancelled",
                ):
                    datos = db.execute(
                        """SELECT professional, specialty, appointment_date
                        FROM appointments WHERE id=? AND patient_id=?""",
                        (cita_id, paciente[0]),
                    ).fetchone()
                    if datos:
                        local = instante(datos[2], local=True).astimezone(SANTIAGO)
                        acuse += f" Atención con {datos[0]} ({datos[1]}), el {local:%d/%m/%Y} a las {local:%H:%M}."
    recibida = ahora
    if mensaje.get("timestamp"):
        recibida = min(
            ahora, datetime.fromtimestamp(int(mensaje["timestamp"]), timezone.utc)
        )
    cursor = db.execute(
        """INSERT INTO whatsapp_inbound
        (meta_id, patient_id, appointment_id, content, result, received_at)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (
            meta_id,
            paciente[0] if paciente else None,
            cita_id,
            contenido,
            resultado,
            recibida.isoformat(),
        ),
    )
    if acuse:
        encolar(db, paciente[0], cita_id, "reply", acuse, ahora, cursor.lastrowid)
    return resultado
