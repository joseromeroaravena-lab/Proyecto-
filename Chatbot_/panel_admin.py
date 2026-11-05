import sqlite3
from contextlib import closing

import streamlit as st

from conexion import conectar

st.set_page_config(page_title="Agenda simulada", layout="wide")
st.title("Agenda simulada de citas")
st.caption("Panel administrativo · Prototipo con datos ficticios")

if st.button("Actualizar agenda"):
    pass  # Al pulsar el botón, Streamlit vuelve a ejecutar la consulta.

consulta = """
    SELECT
        a.id,
        p.name,
        pr.name,
        s.name,
        a.appointment_date,
        a.status
    FROM appointments AS a
    JOIN patients AS p ON p.id = a.patient_id
    LEFT JOIN professionals AS pr ON pr.id = a.professional_id
    LEFT JOIN specialties AS s ON s.id = a.specialty_id
    ORDER BY a.appointment_date, a.id
"""

try:
    with closing(conectar()) as conexion:
        citas = conexion.execute(consulta).fetchall()
except sqlite3.Error as error:
    st.error(f"No se pudo consultar la agenda: {error}")
    st.stop()

estados = {
    "scheduled": "Programada",
    "confirmed": "Confirmada",
    "cancelled": "Cancelada",
}

st.metric("Citas registradas", len(citas))

if citas:
    filas = [
        {
            "ID": cita_id,
            "Paciente": paciente,
            "Profesional": profesional or "Sin asignar",
            "Especialidad": especialidad or "Sin asignar",
            "Fecha y hora": fecha,
            "Estado": estados.get(estado, estado or "Sin estado"),
        }
        for cita_id, paciente, profesional, especialidad, fecha, estado in citas
    ]
    st.dataframe(filas, hide_index=True)
else:
    st.info("Todavía no hay citas registradas.")