from tiempos import ahora_utc, instante


def cambiar_estado(db, cita_id, paciente_id, respuesta, ahora=None):
    """La autorización se verifica dentro de la transacción del llamador."""
    ahora = ahora or ahora_utc()
    cita = db.execute(
        """SELECT status, appointment_date FROM appointments
                         WHERE id=? AND patient_id=?""",
        (cita_id, paciente_id),
    ).fetchone()
    if not cita or instante(cita[1], local=True) <= ahora:
        return "unavailable"
    estado = cita[0]
    destino = {"confirmar": "confirmed", "cancelar": "cancelled"}.get(respuesta)
    if destino is None:
        return "invalid"
    if estado == destino:
        return "already_" + destino
    if estado == "cancelled" or estado not in ("scheduled", "confirmed"):
        return "unavailable"
    db.execute("UPDATE appointments SET status=? WHERE id=?", (destino, cita_id))
    return destino
