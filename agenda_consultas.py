"""Consultas de agenda; las fechas almacenadas representan hora local de Santiago."""

from datetime import timedelta

ESTADOS = {
    "scheduled": "Programada",
    "confirmed": "Confirmada",
    "cancelled": "Cancelada",
}


def profesionales_agenda(db):
    """Incluye profesionales inactivos y nombres históricos presentes en citas."""
    return [
        fila[0]
        for fila in db.execute("""
            SELECT DISTINCT COALESCE(pr.name, a.professional) AS nombre
            FROM appointments AS a
            LEFT JOIN professionals AS pr ON pr.id = a.professional_id
            WHERE nombre IS NOT NULL AND nombre <> ''
            ORDER BY nombre
        """)
    ]


def consultar_citas(db, fecha=None, profesional=None, estado=None):
    consulta = """
        SELECT a.id, p.name, COALESCE(pr.name, a.professional),
               COALESCE(s.name, a.specialty), a.appointment_date, a.status
        FROM appointments AS a
        JOIN patients AS p ON p.id = a.patient_id
        LEFT JOIN professionals AS pr ON pr.id = a.professional_id
        LEFT JOIN specialties AS s ON s.id = a.specialty_id
    """
    condiciones, parametros = [], []
    if fecha is not None:
        condiciones.extend(["a.appointment_date >= ?", "a.appointment_date < ?"])
        parametros.extend([fecha.isoformat(), (fecha + timedelta(days=1)).isoformat()])
    if profesional is not None:
        condiciones.append("COALESCE(pr.name, a.professional) = ?")
        parametros.append(profesional)
    if estado is not None:
        condiciones.append("a.status = ?")
        parametros.append(estado)
    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)
    consulta += " ORDER BY a.appointment_date, a.id"
    return db.execute(consulta, parametros).fetchall()
