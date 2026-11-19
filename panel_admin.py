import sqlite3
from contextlib import closing
from datetime import datetime

import streamlit as st

from conexion import conectar
from agenda_consultas import ESTADOS, consultar_citas, profesionales_agenda


def limpiar_filtros_agenda():
    for campo in ('agenda_fecha', 'agenda_profesional', 'agenda_estado'):
        st.session_state[campo] = None



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

            if fecha_cita <= datetime.now():
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

try:
    with closing(conectar()) as db:
        opciones_profesional = profesionales_agenda(db)
        total_citas = db.execute('SELECT COUNT(*) FROM appointments').fetchone()[0]
except sqlite3.Error as error:
    st.error(f"No se pudo consultar la agenda: {error}")
    st.stop()

st.caption('Combina los filtros para buscar citas. Deja la fecha vacía para ver todos los días.')
col_dia, col_profesional, col_estado = st.columns(3)
with col_dia:
    filtro_fecha = st.date_input(
        'Fecha de atención', value=None, format='DD/MM/YYYY', key='agenda_fecha',
    )
with col_profesional:
    # Si el último registro de un profesional se eliminó, restablecer su selección.
    if st.session_state.get('agenda_profesional') not in [None, *opciones_profesional]:
        st.session_state['agenda_profesional'] = None
    filtro_profesional = st.selectbox(
        'Profesional', [None, *opciones_profesional],
        format_func=lambda valor: 'Todos' if valor is None else valor,
        key='agenda_profesional',
    )
with col_estado:
    filtro_estado = st.selectbox(
        'Estado', [None, *ESTADOS],
        format_func=lambda valor: 'Todos' if valor is None else ESTADOS[valor],
        key='agenda_estado',
    )

col_actualizar, col_limpiar = st.columns(2)
with col_actualizar:
    st.button('Actualizar agenda', key='agenda_actualizar')
with col_limpiar:
    st.button('Limpiar filtros', key='agenda_limpiar', on_click=limpiar_filtros_agenda)

try:
    with closing(conectar()) as db:
        citas = consultar_citas(db, filtro_fecha, filtro_profesional, filtro_estado)
except sqlite3.Error as error:
    st.error(f'No se pudo consultar la agenda: {error}')
    st.stop()

st.metric('Citas encontradas', len(citas))
st.caption(f'Total de citas registradas: {total_citas}.')

if citas:
    filas = [
        {
            "ID": cita_id,
            "Paciente": paciente,
            "Profesional": profesional or "Sin asignar",
            "Especialidad": especialidad or "Sin asignar",
            "Fecha y hora": fecha,
            "Estado": ESTADOS.get(estado, estado or "Sin estado"),
        }
        for cita_id, paciente, profesional, especialidad, fecha, estado in citas
    ]
    st.dataframe(filas, hide_index=True)
elif total_citas:
    st.info('No hay citas que coincidan con los filtros seleccionados.')
else:
    st.info("Todavía no hay citas registradas.")
