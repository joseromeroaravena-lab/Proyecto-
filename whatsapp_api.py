import hashlib
import hmac
import json
from contextlib import closing
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

from conexion import conectar
from whatsapp_config import Config
from whatsapp_servicio import recibir


def registrar_estado(db, estado):
    meta_id = estado["id"]
    status = estado["status"]
    if status not in ("sent", "delivered", "read", "failed"):
        return
    fecha = datetime.fromtimestamp(int(estado["timestamp"]), timezone.utc).isoformat()
    errores = estado.get("errors") or []
    codigo = str(errores[0].get("code", "unknown")) if errores else None
    db.execute(
        """INSERT OR IGNORE INTO whatsapp_status_events
        VALUES (?, ?, ?, ?)""",
        (meta_id, status, fecha, codigo),
    )
    # Los eventos son durables incluso si llegan antes de guardar el ID del envío.
    reconciliar_estado(db, meta_id)


def reconciliar_estado(db, meta_id):
    eventos = db.execute(
        """SELECT status, occurred_at, error_code
        FROM whatsapp_status_events WHERE meta_id=?""",
        (meta_id,),
    ).fetchall()
    por_estado = {e[0]: e for e in eventos}
    for estado in ("read", "delivered", "failed", "sent"):
        if estado in por_estado:
            _, fecha, codigo = por_estado[estado]
            db.execute(
                """UPDATE whatsapp_outbox SET status=?, error_code=?,
                delivered_at=COALESCE(?, delivered_at), read_at=COALESCE(?, read_at)
                WHERE meta_id=?""",
                (
                    estado,
                    codigo,
                    por_estado.get("delivered", (None, None))[1],
                    por_estado.get("read", (None, None))[1],
                    meta_id,
                ),
            )
            break


def crear_app(config=None):
    config = config or Config()
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/webhooks/whatsapp", response_class=PlainTextResponse)
    def verificar(request: Request):
        params = request.query_params
        if (
            config.verify
            and params.get("hub.mode") == "subscribe"
            and hmac.compare_digest(
                params.get("hub.verify_token", "").encode(), config.verify.encode()
            )
            and params.get("hub.challenge")
        ):
            return params["hub.challenge"]
        raise HTTPException(403, "Verificación rechazada")

    @app.post("/webhooks/whatsapp")
    async def webhook(request: Request):
        if not config.secret or not config.phone_id:
            raise HTTPException(503, "Webhook no configurado")
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > 1048576:
                raise HTTPException(413, "Evento demasiado grande")
        firma = (
            "sha256="
            + hmac.new(config.secret.encode(), raw, hashlib.sha256).hexdigest()
        )
        if not hmac.compare_digest(
            firma.encode(), request.headers.get("x-hub-signature-256", "").encode()
        ):
            raise HTTPException(403, "Firma inválida")
        try:
            payload = json.loads(raw)
            if payload.get("object") != "whatsapp_business_account":
                return {"ok": True}
            with closing(conectar()) as db, db:
                db.execute("BEGIN IMMEDIATE")
                for entry in payload.get("entry", []):
                    for cambio in entry.get("changes", []):
                        valor = cambio.get("value", {})
                        if (
                            valor.get("metadata", {}).get("phone_number_id")
                            != config.phone_id
                        ):
                            continue
                        for mensaje in valor.get("messages", []):
                            recibir(db, mensaje)
                        for estado in valor.get("statuses", []):
                            registrar_estado(db, estado)
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            raise HTTPException(400, "Evento inválido") from None
        return {"ok": True}

    return app


app = crear_app()
