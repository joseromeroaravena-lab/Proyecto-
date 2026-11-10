import sqlite3
from datetime import datetime, timedelta

import conexion
import pytest
from simular_respuesta import registrar_respuesta


@pytest.fixture
def appointment_db(tmp_path, monkeypatch):
    database_path = tmp_path / "test_chatbot.db"
    monkeypatch.setattr(conexion, "ruta_db", database_path)
    appointment_date = (datetime.now() + timedelta(days=1)).strftime(
        "%Y-%m-%d %H:%M"
    )

    with sqlite3.connect(database_path) as database:
        database.executescript("""
            CREATE TABLE patients (id INTEGER PRIMARY KEY);
            CREATE TABLE appointments (
                id INTEGER PRIMARY KEY,
                patient_id INTEGER NOT NULL,
                appointment_date TEXT NOT NULL,
                status TEXT NOT NULL
            );
            INSERT INTO patients (id) VALUES (1), (2);
        """)
        database.execute("""
            INSERT INTO appointments
                (id, patient_id, appointment_date, status)
            VALUES (?, 1, ?, 'scheduled')
        """, (10, appointment_date))

    return database_path


def test_confirmation_updates_appointment_and_records_response(appointment_db):
    assert registrar_respuesta(10, paciente_id=1, respuesta="confirmar")

    with sqlite3.connect(appointment_db) as database:
        appointment = database.execute(
            "SELECT status FROM appointments WHERE id = 10"
        ).fetchone()
        response = database.execute("""
            SELECT appointment_id, response, channel
            FROM appointment_responses
        """).fetchone()

    assert appointment == ("confirmed",)
    assert response == (10, "confirmar", "simulado")


def test_response_for_another_patient_is_rejected(appointment_db):
    assert not registrar_respuesta(10, paciente_id=2, respuesta="cancelar")

    with sqlite3.connect(appointment_db) as database:
        appointment = database.execute(
            "SELECT status FROM appointments WHERE id = 10"
        ).fetchone()
        responses = database.execute(
            "SELECT COUNT(*) FROM appointment_responses"
        ).fetchone()

    assert appointment == ("scheduled",)
    assert responses == (0,)
