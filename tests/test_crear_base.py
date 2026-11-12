import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

import crear_base


FECHA_BASE = datetime(2026, 11, 12, 12, 0, tzinfo=ZoneInfo("America/Santiago"))


def test_creates_complete_demo_database(tmp_path):
    database_path = tmp_path / "chatbot.db"

    assert crear_base.crear_base(database_path, fecha_base=FECHA_BASE)

    with sqlite3.connect(database_path) as database:
        tables = {
            row[0]
            for row in database.execute("""
                SELECT name FROM sqlite_master WHERE type = 'table'
            """)
        }
        appointments = database.execute("""
            SELECT patient_id, professional_id, specialty_id,
                   appointment_date, status
            FROM appointments
            ORDER BY id
        """).fetchall()

        assert not database.execute("PRAGMA foreign_key_check").fetchall()
        assert database.execute("PRAGMA integrity_check").fetchone() == ("ok",)

    assert crear_base.TABLAS_REQUERIDAS <= tables
    assert appointments == [
        (1, 1, 1, "2026-11-14 10:00", "scheduled"),
        (2, 2, 2, "2026-11-15 11:00", "confirmed"),
        (3, 1, 1, "2026-11-09 09:00", "cancelled"),
    ]


def test_existing_database_is_preserved(tmp_path):
    database_path = tmp_path / "chatbot.db"
    with sqlite3.connect(database_path) as database:
        database.execute("CREATE TABLE marker (value TEXT NOT NULL)")
        database.execute("INSERT INTO marker VALUES ('original')")

    original_content = database_path.read_bytes()

    assert not crear_base.crear_base(database_path, fecha_base=FECHA_BASE)
    assert database_path.read_bytes() == original_content


def test_failed_creation_does_not_leave_partial_database(tmp_path, monkeypatch):
    database_path = tmp_path / "chatbot.db"
    invalid_schema = tmp_path / "invalid_schema.sql"
    invalid_schema.write_text("CREATE TABLE incomplete (", encoding="utf-8")
    monkeypatch.setattr(crear_base, "RUTA_ESQUEMA", invalid_schema)

    try:
        crear_base.crear_base(database_path, fecha_base=FECHA_BASE)
    except sqlite3.Error:
        pass
    else:
        raise AssertionError("Se esperaba un error por el esquema inválido")

    assert not database_path.exists()
    assert not list(tmp_path.glob(".*.tmp"))
