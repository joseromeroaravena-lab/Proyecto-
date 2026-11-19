"""Vínculo firmado entre un botón y un recordatorio enviado a un paciente."""

import hashlib
import hmac
import re

ACCIONES = ("confirmar", "cancelar")


def payload_boton(fila, accion, secreto):
    if accion not in ACCIONES or not secreto:
        raise ValueError("El botón requiere una acción válida y secreto configurado.")
    datos = (
        f"cesfam:v1:{fila['id']}:{fila['patient_id']}:{fila['appointment_id']}:{accion}"
    )
    firma = hmac.new(secreto.encode(), datos.encode(), hashlib.sha256).hexdigest()
    return f"cesfam:v1:{fila['id']}:{accion}:{firma}"


def resolver_boton(db, paciente_id, payload, secreto, contexto=None):
    if not isinstance(payload, str) or not secreto:
        return None
    match = re.fullmatch(
        r"cesfam:v1:([1-9][0-9]{0,17}):(confirmar|cancelar):[a-f0-9]{64}", payload
    )
    if not match:
        return None
    identificador, accion = match.groups()
    cursor = db.execute(
        """SELECT id, patient_id, appointment_id, meta_id FROM whatsapp_outbox
           WHERE id=? AND patient_id=? AND kind IN ('72h','24h')
             AND status IN ('accepted','sent','delivered','read')
             AND meta_id IS NOT NULL AND appointment_id IS NOT NULL""",
        (int(identificador), paciente_id),
    )
    valores = cursor.fetchone()
    if not valores:
        return None
    fila = dict(zip((columna[0] for columna in cursor.description), valores))
    if contexto and contexto != fila["meta_id"]:
        return None
    esperado = payload_boton(fila, accion, secreto)
    if not hmac.compare_digest(payload.encode(), esperado.encode()):
        return None
    return accion, fila["appointment_id"]
