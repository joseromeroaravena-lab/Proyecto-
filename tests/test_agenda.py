import sqlite3
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import conexion
from agenda_consultas import consultar_citas, profesionales_agenda
from crear_base import crear_base
from crear_base import ZONA_HORARIA as SANTIAGO


@pytest.fixture
def agenda_db(tmp_path, monkeypatch):
    ruta = tmp_path / "agenda.db"
    crear_base(ruta, datetime(2026, 11, 18, 12, tzinfo=SANTIAGO))
    monkeypatch.setattr(conexion, "ruta_db", ruta)
    monkeypatch.setenv("CESFAM_PANEL_PASSWORD", "solo-pruebas-agenda")
    with closing(sqlite3.connect(ruta)) as db, db:
        db.execute("DELETE FROM appointments")
        db.execute(
            "UPDATE professionals SET name=?,active=1 WHERE id=1", ("Dra. O'Connor",)
        )
        db.execute("UPDATE professionals SET name='Dr. Inactivo',active=0 WHERE id=2")
        db.executemany(
            """INSERT INTO appointments
            (id,patient_id,professional_id,specialty_id,professional,specialty,appointment_date,status)
            VALUES (?,1,?,1,?,'Especialidad histórica',?,?)""",
            [
                (101, 1, "Dra. O'Connor", "2026-11-18 00:00", "scheduled"),
                (102, 1, "Dra. O'Connor", "2026-11-18 23:59:59", "confirmed"),
                (103, 2, "Dr. Inactivo", "2026-11-19 00:00", "cancelled"),
                (104, None, "Dra. Legado", "2026-11-18 12:00", "scheduled"),
            ],
        )
    return ruta


@pytest.mark.parametrize(
    "filtros,esperados",
    [
        ({}, [101, 104, 102, 103]),
        ({"fecha": date(2026, 11, 18)}, [101, 104, 102]),
        ({"fecha": date(2026, 11, 19)}, [103]),
        ({"profesional": "Dra. O'Connor"}, [101, 102]),
        ({"profesional": "Dr. Inactivo"}, [103]),
        ({"profesional": "Dra. Legado"}, [104]),
        ({"estado": "cancelled"}, [103]),
        (
            {
                "fecha": date(2026, 11, 18),
                "profesional": "Dra. O'Connor",
                "estado": "confirmed",
            },
            [102],
        ),
        ({"fecha": date(2026, 11, 18), "profesional": "Dr. Inactivo"}, []),
    ],
)
def test_filters_and_full_day_boundaries(agenda_db, filtros, esperados):
    with closing(sqlite3.connect(agenda_db)) as db:
        assert [fila[0] for fila in consultar_citas(db, **filtros)] == esperados


def test_professional_options_include_historical_and_inactive(agenda_db):
    with closing(sqlite3.connect(agenda_db)) as db:
        assert profesionales_agenda(db) == [
            "Dr. Inactivo",
            "Dra. Legado",
            "Dra. O'Connor",
        ]
        historica = consultar_citas(db, profesional="Dra. Legado")[0]
        assert historica[2] == "Dra. Legado"


def abrir_panel():
    panel = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "panel_admin.py"), default_timeout=20
    )
    panel.session_state["authenticated"] = True
    panel.run()
    assert not panel.exception
    return panel


def ids_agenda(panel):
    for tabla in panel.dataframe:
        if "ID" in tabla.value.columns:
            return tabla.value["ID"].tolist()
    return []


def test_panel_combines_filters_and_clears_only_filter_state(agenda_db):
    panel = abrir_panel()
    assert ids_agenda(panel) == [101, 104, 102, 103]
    assert panel.date_input(key="agenda_fecha").value is None
    panel.date_input(key="agenda_fecha").set_value(date(2026, 11, 18))
    panel.selectbox(key="agenda_profesional").select("Dra. O'Connor")
    panel.selectbox(key="agenda_estado").select("confirmed")
    panel.run()
    assert not panel.exception
    assert ids_agenda(panel) == [102]
    assert panel.metric[0].value == "1"
    assert any("Total de citas registradas: 4." == c.value for c in panel.caption)
    panel.button(key="agenda_limpiar").click().run()
    assert not panel.exception
    assert ids_agenda(panel) == [101, 104, 102, 103]
    assert panel.date_input(key="agenda_fecha").value is None
    assert panel.selectbox(key="agenda_profesional").value == ""
    assert panel.selectbox(key="agenda_estado").value == ""
    assert panel.selectbox(key="agenda_profesional").format_func("") == "Todos"
    assert panel.selectbox(key="agenda_estado").format_func("") == "Todos"
    assert panel.session_state["authenticated"] is True


def test_panel_refresh_keeps_filters_and_reads_new_status(agenda_db):
    panel = abrir_panel()
    panel.selectbox(key="agenda_estado").select("confirmed").run()
    assert ids_agenda(panel) == [102]
    with closing(sqlite3.connect(agenda_db)) as db, db:
        db.execute("UPDATE appointments SET status='confirmed' WHERE id=101")
    panel.button(key="agenda_actualizar").click().run()
    assert not panel.exception
    assert panel.selectbox(key="agenda_estado").value == "confirmed"
    assert ids_agenda(panel) == [101, 102]


def test_panel_distinguishes_no_matches_from_empty_agenda(agenda_db):
    panel = abrir_panel()
    panel.date_input(key="agenda_fecha").set_value(date(2026, 11, 20)).run()
    assert not panel.exception
    assert ids_agenda(panel) == []
    assert any("No hay citas que coincidan" in aviso.value for aviso in panel.info)
    assert panel.metric[0].value == "0"
    with closing(sqlite3.connect(agenda_db)) as db, db:
        db.execute("DELETE FROM appointments")
    panel.button(key="agenda_limpiar").click().run()
    assert not panel.exception
    assert any(
        "Todavía no hay citas registradas." == aviso.value for aviso in panel.info
    )
