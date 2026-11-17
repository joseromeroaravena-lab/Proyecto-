import sqlite3
import os
import hmac
from contextlib import closing
from datetime import datetime

import streamlit as st

from conexion import conectar
from tiempos import SANTIAGO


def registrar_paciente(nombre, telefono):
    with closing(conectar()) as db, db:
        db.execute("""
            INSERT INTO patients (name, phone, consent_whatsapp)
            VALUES (?, ?, 0)
        """, (nombre, telefono))


def registrar_cita(paciente_id, profesional_id, especialidad_id, fecha_hora):
    with closing(conectar()) as db:
        db.execute("PRAGMA foreign_keys = ON")

        with db:
            resultado = db.execute("""
                INSERT INTO appointments (
                    patient_id, professional_id, specialty_id,
                    professional, specialty, appointment_date, status
                )
                SELECT p.id, pr.id, s.id, pr.name, s.name, ?, 'scheduled'
                FROM patients AS p
                CROSS JOIN professionals AS pr
                CROSS JOIN specialties AS s
                WHERE p.id = ?
                  AND pr.id = ? AND pr.active = 1
                  AND s.id = ? AND s.active = 1
                  AND NOT EXISTS (
                      SELECT 1
                      FROM appointments AS a
                      WHERE a.professional_id = pr.id
                        AND a.appointment_date = ?
                        AND a.status IN ('scheduled', 'confirmed')
                  )
            """, (
                fecha_hora, paciente_id, profesional_id,
                especialidad_id, fecha_hora,
            ))
            return resultado.lastrowid if resultado.rowcount == 1 else None


st.set_page_config(page_title="Agenda simulada", layout="wide")
clave = os.getenv('CESFAM_PANEL_PASSWORD', '')
if not clave:
    st.error('Configura CESFAM_PANEL_PASSWORD en .env antes de abrir el panel.')
    st.stop()
if not st.session_state.get('authenticated'):
    with st.form('login'):
        entrada = st.text_input('Contraseña administrativa', type='password')
        ingresar = st.form_submit_button('Ingresar')
    if ingresar and hmac.compare_digest(entrada.encode(), clave.encode()):
        st.session_state['authenticated'] = True
        st.rerun()
    elif ingresar:
        st.error('Contraseña incorrecta.')
    st.stop()
if st.button('Cerrar sesión'):
    st.session_state.clear()
    st.rerun()
st.title("Agenda simulada de citas")
st.caption("Panel administrativo · Prototipo con datos ficticios")

with st.expander("Registrar paciente ficticio"):
    with st.form("form_paciente"):
        nombre = st.text_input("Nombre completo")
        telefono = st.text_input("Teléfono de prueba", placeholder="+56900000001")
        guardar_paciente = st.form_submit_button("Guardar paciente")

    if guardar_paciente:
        nombre = nombre.strip()
        telefono = "".join(telefono.split())

        if not nombre or not telefono:
            st.warning("Completa el nombre y el teléfono de prueba.")
        else:
            try:
                registrar_paciente(nombre, telefono)
                st.success(f"Paciente registrado: {nombre}")
            except sqlite3.IntegrityError:
                st.error("No se pudo guardar el paciente. Revisa si el teléfono ya existe.")
            except sqlite3.Error as error:
                st.error(f"No se pudo guardar el paciente: {error}")

try:
    with closing(conectar()) as db:
        pacientes = dict(db.execute(
            "SELECT id, name FROM patients ORDER BY name, id"
        ).fetchall())
        profesionales = dict(db.execute(
            "SELECT id, name FROM professionals WHERE active = 1 ORDER BY name"
        ).fetchall())
        especialidades = dict(db.execute(
            "SELECT id, name FROM specialties WHERE active = 1 ORDER BY name"
        ).fetchall())
except sqlite3.Error as error:
    st.error(f"No se pudieron cargar los datos de la agenda: {error}")
    st.stop()

with st.expander("Nueva cita"):
    if not (pacientes and profesionales and especialidades):
        st.info("Necesitas un paciente, un profesional y una especialidad para agendar.")
    else:
        with st.form("form_cita"):
            paciente_id = st.selectbox(
                "Paciente", list(pacientes),
                format_func=lambda id_: f"{pacientes[id_]} · ID {id_}",
            )
            profesional_id = st.selectbox(
                "Profesional", list(profesionales),
                format_func=profesionales.get,
            )
            especialidad_id = st.selectbox(
                "Especialidad", list(especialidades),
                format_func=especialidades.get,
            )
            col_fecha, col_hora = st.columns(2)
            fecha = col_fecha.date_input("Fecha")
            hora = col_hora.time_input("Hora")
            guardar_cita = st.form_submit_button("Guardar cita")

        if guardar_cita:
            fecha_cita = datetime.combine(fecha, hora).replace(
                second=0, microsecond=0
            )

            if fecha_cita <= datetime.now(SANTIAGO).replace(tzinfo=None):
                st.warning("Selecciona una fecha y hora futuras.")
            else:
                try:
                    cita_id = registrar_cita(
                        paciente_id, profesional_id, especialidad_id,
                        fecha_cita.strftime("%Y-%m-%d %H:%M"),
                    )
                    if cita_id is None:
                        st.warning("El horario está ocupado o la selección ya no está disponible.")
                    else:
                        st.success(f"Cita ID {cita_id} guardada como Programada.")
                except sqlite3.Error as error:
                    st.error(f"No se pudo guardar la cita: {error}")

st.subheader("Agenda")
st.button("Actualizar agenda")

try:
    with closing(conectar()) as db:
        citas = db.execute("""
            SELECT a.id, p.name, pr.name, s.name, a.appointment_date, a.status
            FROM appointments AS a
            JOIN patients AS p ON p.id = a.patient_id
            LEFT JOIN professionals AS pr ON pr.id = a.professional_id
            LEFT JOIN specialties AS s ON s.id = a.specialty_id
            ORDER BY a.appointment_date, a.id
        """).fetchall()
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

st.subheader('Consentimiento de pruebas')
if pacientes:
    with st.form('consentimiento'):
        seleccionado = st.selectbox('Paciente ficticio', list(pacientes), format_func=pacientes.get)
        consentimiento = st.checkbox('Autoriza recibir mensajes de prueba por WhatsApp')
        guardar = st.form_submit_button('Guardar consentimiento')
    if guardar:
        with closing(conectar()) as db, db:
            db.execute('UPDATE patients SET consent_whatsapp=? WHERE id=?',
                       (int(consentimiento), seleccionado))
        st.success('Consentimiento actualizado. Los envíos requieren además teléfono autorizado en configuración.')

st.subheader('Respuestas y envíos WhatsApp')
try:
    with closing(conectar()) as db:
        for titulo, consulta in (
            ('Respuestas', 'SELECT meta_id, patient_id, appointment_id, content, result, received_at FROM whatsapp_inbound ORDER BY id DESC LIMIT 200'),
            ('Envíos', 'SELECT id, patient_id, appointment_id, kind, status, attempts, created_at, accepted_at, delivered_at, read_at, error_code FROM whatsapp_outbox ORDER BY id DESC LIMIT 200'),
        ):
            cursor = db.execute(consulta)
            columnas = [c[0] for c in cursor.description]
            st.caption(titulo)
            st.dataframe([dict(zip(columnas, fila)) for fila in cursor.fetchall()], hide_index=True)
except sqlite3.OperationalError:
    st.info('Ejecuta migrar_whatsapp.py para habilitar el registro WhatsApp.')
