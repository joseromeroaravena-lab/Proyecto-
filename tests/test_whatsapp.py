import hashlib
import hmac
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

import conexion
from crear_base import crear_base
from migrar_whatsapp import migrar
from recordatorios import generar, despachar, bloqueo_worker
from tiempos import instante, SANTIAGO
from whatsapp_api import crear_app, registrar_estado
from whatsapp_config import Config
from whatsapp_servicio import recibir

NOW = datetime(2026, 11, 15, 12, tzinfo=timezone.utc)


@pytest.fixture
def base(tmp_path, monkeypatch):
    ruta = tmp_path / "demo.db"
    crear_base(ruta, NOW.astimezone(SANTIAGO))
    monkeypatch.setattr(conexion, "ruta_db", ruta)
    with sqlite3.connect(ruta) as db:
        db.execute(
            "UPDATE patients SET phone='+56912345678', consent_whatsapp=1 WHERE id=1"
        )
        db.execute("DELETE FROM appointments")
        db.execute(
            """INSERT INTO appointments
            (id,patient_id,specialty,professional,appointment_date,created_at)
            VALUES (10,1,'Demo','Demo',?,?)""",
            (
                (NOW + timedelta(hours=72))
                .astimezone(SANTIAGO)
                .strftime("%Y-%m-%d %H:%M"),
                (NOW - timedelta(days=2)).isoformat(),
            ),
        )
    return ruta


def mensaje(texto="CONFIRMAR 10", ident="m1", telefono="56912345678"):
    return {"id": ident, "from": telefono, "type": "text", "text": {"body": texto}}


def config():
    return Config(
        version="v99.0",
        phone_id="123",
        token="test",
        secret="secret",
        verify="verify",
        enabled=True,
        test_confirmed=True,
        allowed={"56912345678"},
        template="demo",
        language="es",
    )


def test_numeric_options_and_original_content(base):
    with sqlite3.connect(base) as db:
        assert recibir(db, mensaje("1"), NOW) == "confirmed"
        assert recibir(db, mensaje("1", "n2"), NOW) == "already_confirmed"
        assert recibir(db, mensaje("2", "n3"), NOW) == "cancelled"
        assert recibir(db, mensaje("2 10", "n4"), NOW) == "already_cancelled"
        assert recibir(db, mensaje("3", "n5"), NOW) == "invalid"
        assert db.execute(
            "SELECT content FROM whatsapp_inbound ORDER BY id LIMIT 1"
        ).fetchone() == ("1",)


def test_numeric_multiple_appointments_and_quoted_reply(base):
    with sqlite3.connect(base) as db:
        db.execute("""INSERT INTO appointments
            (id,patient_id,specialty,professional,appointment_date)
            SELECT 11,1,specialty,professional,appointment_date FROM appointments WHERE id=10""")
        assert recibir(db, mensaje("1"), NOW) == "ambiguous"
        generar(db, NOW)
        db.execute("UPDATE whatsapp_outbox SET meta_id='reminder-10' WHERE kind='72h'")
        quoted = mensaje("2", "n2")
        quoted["context"] = {"id": "reminder-10"}
        assert recibir(db, quoted, NOW) == "cancelled"
        assert db.execute("SELECT status FROM appointments WHERE id=11").fetchone() == (
            "scheduled",
        )
        assert recibir(db, mensaje("1 11", "n3"), NOW) == "confirmed"
        quoted["id"] = "n4"
        quoted["context"] = {"id": "unknown"}
        assert recibir(db, quoted, NOW) == "unavailable"


def test_quoted_reply_cannot_target_other_patient(base):
    with sqlite3.connect(base) as db:
        generar(db, NOW)
        db.execute(
            "UPDATE whatsapp_outbox SET meta_id='other-reminder',patient_id=2 WHERE kind='72h'"
        )
        quoted = mensaje("2")
        quoted["context"] = {"id": "other-reminder"}
        assert recibir(db, quoted, NOW) == "unavailable"
        assert db.execute("SELECT status FROM appointments WHERE id=10").fetchone() == (
            "scheduled",
        )


def test_lifecycle_and_duplicate(base):
    with sqlite3.connect(base) as db:
        assert recibir(db, mensaje(), NOW) == "confirmed"
        assert recibir(db, mensaje(), NOW) == "duplicate"
        assert recibir(db, mensaje(ident="m2"), NOW) == "already_confirmed"
        assert recibir(db, mensaje("CANCELAR 10", "m3"), NOW) == "cancelled"
        assert recibir(db, mensaje("CANCELAR 10", "m4"), NOW) == "already_cancelled"
        assert recibir(db, mensaje("CONFIRMAR 10", "m5"), NOW) == "unavailable"
        assert db.execute("SELECT count(*) FROM whatsapp_inbound").fetchone()[0] == 5
        assert db.execute("SELECT count(*) FROM whatsapp_outbox").fetchone()[0] == 5


def test_ownership_invalid_consent_and_ambiguity(base):
    with sqlite3.connect(base) as db:
        db.execute("UPDATE appointments SET patient_id=2 WHERE id=10")
        assert recibir(db, mensaje(), NOW) == "unavailable"
        assert (
            db.execute("SELECT appointment_id FROM whatsapp_inbound").fetchone()[0]
            is None
        )
        db.execute("UPDATE appointments SET patient_id=1 WHERE id=10")
        db.execute("""INSERT INTO appointments
            (id,patient_id,specialty,professional,appointment_date)
            SELECT 11,1,specialty,professional,appointment_date FROM appointments WHERE id=10""")
        assert recibir(db, mensaje("CONFIRMAR", "m2"), NOW) == "ambiguous"
        assert recibir(db, mensaje("hola", "m3"), NOW) == "invalid"
        db.execute("UPDATE patients SET consent_whatsapp=0 WHERE id=1")
        assert recibir(db, mensaje(ident="m4"), NOW) == "unauthorized"
        assert (
            recibir(db, mensaje(ident="m5", telefono="56999999999"), NOW)
            == "unauthorized"
        )
        assert (
            db.execute(
                "SELECT count(*) FROM appointments WHERE status='scheduled'"
            ).fetchone()[0]
            == 2
        )


def test_past_appointment(base):
    with sqlite3.connect(base) as db:
        assert recibir(db, mensaje(), NOW + timedelta(days=4)) == "unavailable"


def test_reminder_thresholds_and_no_duplicates(base):
    with sqlite3.connect(base) as db:
        generar(db, NOW)
        generar(db, NOW)
        assert db.execute("SELECT kind FROM whatsapp_outbox").fetchall() == [("72h",)]
        generar(db, NOW + timedelta(hours=48))
        generar(db, NOW + timedelta(hours=48))
        assert db.execute("SELECT count(*) FROM whatsapp_outbox").fetchone()[0] == 2


def test_restart_latest_threshold_late_creation_and_cancellation(base):
    with sqlite3.connect(base) as db:
        generar(db, NOW + timedelta(hours=49))
        assert db.execute("SELECT kind FROM whatsapp_outbox").fetchall() == [("24h",)]
        db.execute("DELETE FROM whatsapp_outbox")
        db.execute(
            "UPDATE appointments SET created_at=?",
            ((NOW + timedelta(hours=50)).isoformat(),),
        )
        generar(db, NOW + timedelta(hours=51))
        assert db.execute("SELECT count(*) FROM whatsapp_outbox").fetchone()[0] == 0
        db.execute("UPDATE appointments SET status='cancelled'")
        generar(db, NOW + timedelta(hours=52))
        assert db.execute("SELECT count(*) FROM whatsapp_outbox").fetchone()[0] == 0


def test_webhook_signed_duplicate_wrong_signature(base):
    cliente = TestClient(crear_app(config()))
    assert (
        cliente.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "verify",
                "hub.challenge": "1234",
            },
        ).text
        == "1234"
    )
    assert cliente.get("/webhooks/whatsapp").status_code == 403
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "123"},
                            "messages": [mensaje("CANCELAR 10")],
                        }
                    }
                ]
            }
        ],
    }
    cuerpo = json.dumps(payload).encode()
    assert cliente.post("/webhooks/whatsapp", content=cuerpo).status_code == 403
    firma = "sha256=" + hmac.new(b"secret", cuerpo, hashlib.sha256).hexdigest()
    for _ in range(2):
        assert (
            cliente.post(
                "/webhooks/whatsapp",
                content=cuerpo,
                headers={"x-hub-signature-256": firma},
            ).status_code
            == 200
        )
    with sqlite3.connect(base) as db:
        assert db.execute("SELECT count(*) FROM whatsapp_inbound").fetchone()[0] == 1


def test_delivery_out_of_order_and_early_event(base):
    with sqlite3.connect(base) as db:
        recibir(db, mensaje(), NOW)
        for estado in ("read", "delivered", "sent"):
            registrar_estado(
                db,
                {
                    "id": "out1",
                    "status": estado,
                    "timestamp": str(int(NOW.timestamp())),
                },
            )

    def enviar(request):
        return httpx.Response(200, json={"messages": [{"id": "out1"}]})

    with httpx.Client(transport=httpx.MockTransport(enviar)) as cliente:
        despachar(config(), cliente, NOW)
    with sqlite3.connect(base) as db:
        assert db.execute(
            "SELECT status, attempts FROM whatsapp_outbox"
        ).fetchone() == ("read", 1)


@pytest.mark.parametrize(
    "fallo,esperado",
    [("transient", "failed"), ("timeout", "uncertain"), ("permanent", "failed")],
)
def test_failures_and_retry_limit(base, fallo, esperado):
    with sqlite3.connect(base) as db:
        recibir(db, mensaje(), NOW)
    llamadas = []

    def enviar(request):
        llamadas.append(request)
        if fallo == "timeout":
            raise httpx.ReadTimeout("simulado")
        return httpx.Response(
            429 if fallo == "transient" else 400, json={"error": {"code": 4}}
        )

    with httpx.Client(transport=httpx.MockTransport(enviar)) as cliente:
        for minutos in (0, 10, 20, 30):
            despachar(config(), cliente, NOW + timedelta(minutes=minutos))
    assert len(llamadas) == (3 if fallo == "transient" else 1)
    with sqlite3.connect(base) as db:
        assert (
            db.execute("SELECT status FROM whatsapp_outbox").fetchone()[0] == esperado
        )


@pytest.mark.parametrize("bloqueo", ["consent", "cancelled", "allowlist", "template"])
def test_recheck_before_send(base, bloqueo):
    with sqlite3.connect(base) as db:
        generar(db, NOW)
        if bloqueo == "consent":
            db.execute("UPDATE patients SET consent_whatsapp=0 WHERE id=1")
        if bloqueo == "cancelled":
            db.execute("UPDATE appointments SET status='cancelled'")
    ajustes = config()
    if bloqueo == "allowlist":
        ajustes.allowed = {"56900000000"}
    if bloqueo == "template":
        ajustes.template = ""

    def no_enviar(request):
        pytest.fail("No debe llamar a Meta")

    with httpx.Client(transport=httpx.MockTransport(no_enviar)) as cliente:
        despachar(ajustes, cliente, NOW)
    with sqlite3.connect(base) as db:
        assert db.execute("SELECT attempts FROM whatsapp_outbox").fetchone()[0] == 0


def test_budget_guard(base):
    ajustes = config()
    ajustes.test_confirmed = False
    with pytest.raises(ValueError):
        despachar(ajustes, ahora=NOW)


def test_migration_repeat_and_rollback(base):
    with sqlite3.connect(base) as db:
        migrar(db)
        migrar(db)
        assert db.execute("SELECT count(*) FROM schema_migrations").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM appointments").fetchone()[0] == 1
    ruta = base.with_name("rollback.db")
    with closing(sqlite3.connect(ruta)) as db:
        db.execute("BEGIN IMMEDIATE")
        migrar(db)
        db.rollback()
        assert (
            db.execute(
                "SELECT count(*) FROM sqlite_master WHERE name='whatsapp_inbound'"
            ).fetchone()[0]
            == 0
        )


def test_santiago_dst_utc_thresholds():
    # En 2026 el cambio de septiembre adelanta una hora en Chile continental.
    antes = instante("2026-09-05 12:00", local=True)
    despues = instante("2026-09-06 12:00", local=True)
    assert despues - antes == timedelta(hours=23)


def test_single_worker_lock_released(base):
    with bloqueo_worker():
        with pytest.raises(RuntimeError):
            with bloqueo_worker():
                pass
    with bloqueo_worker():
        pass


def test_migration_command_backs_up_existing_database(base, tmp_path, monkeypatch):
    import migrar_whatsapp

    backup_dir = tmp_path / "backups"
    monkeypatch.setattr(
        "sys.argv", ["migrar_whatsapp.py", "--backup-dir", str(backup_dir)]
    )
    migrar_whatsapp.main()
    copias = list(backup_dir.glob("*.db"))
    assert len(copias) == 1
    with sqlite3.connect(copias[0]) as copia:
        assert copia.execute("SELECT id FROM appointments").fetchall() == [(10,)]
        assert copia.execute("PRAGMA integrity_check").fetchone() == ("ok",)


def test_reminder_payload_and_delivery_notification(base):
    with sqlite3.connect(base) as db:
        generar(db, NOW)

    def enviar(request):
        payload = json.loads(request.content)
        assert payload["type"] == "template"
        parametros = payload["template"]["components"][0]["parameters"]
        assert [p["text"] for p in parametros] == [
            "Demo (Demo)",
            "18/11/2026",
            "09:00",
            "10",
        ]
        return httpx.Response(200, json={"messages": [{"id": "out1"}]})

    with httpx.Client(transport=httpx.MockTransport(enviar)) as cliente:
        despachar(config(), cliente, NOW)
    with sqlite3.connect(base) as db:
        assert db.execute("SELECT status FROM whatsapp_outbox").fetchone() == (
            "accepted",
        )
        registrar_estado(
            db,
            {
                "id": "out1",
                "status": "delivered",
                "timestamp": str(int(NOW.timestamp())),
            },
        )
        assert db.execute("SELECT status FROM whatsapp_outbox").fetchone() == (
            "delivered",
        )


def test_expired_reply_does_not_open_new_window(base):
    with sqlite3.connect(base) as db:
        evento = mensaje()
        evento["timestamp"] = str(int((NOW - timedelta(hours=25)).timestamp()))
        recibir(db, evento, NOW)

    def no_enviar(request):
        pytest.fail("Ventana vencida")

    with httpx.Client(transport=httpx.MockTransport(no_enviar)) as cliente:
        despachar(config(), cliente, NOW)
    with sqlite3.connect(base) as db:
        assert db.execute("SELECT status FROM whatsapp_outbox").fetchone() == (
            "expired_window",
        )


def test_pending_72h_is_superseded(base):
    with sqlite3.connect(base) as db:
        generar(db, NOW)

    def no_enviar(request):
        pytest.fail("Recordatorio viejo")

    with httpx.Client(transport=httpx.MockTransport(no_enviar)) as cliente:
        despachar(config(), cliente, NOW + timedelta(hours=49))
    with sqlite3.connect(base) as db:
        assert db.execute("SELECT status FROM whatsapp_outbox").fetchone() == (
            "superseded",
        )


def test_panel_requires_password_and_supports_login(base, monkeypatch):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("CESFAM_PANEL_PASSWORD", "contraseña-de-prueba")
    panel = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "panel_admin.py"), default_timeout=20
    ).run()
    assert not panel.exception
    assert not panel.dataframe
    panel.text_input[0].input("incorrecta")
    panel.button[0].click().run()
    assert panel.error[0].value == "Contraseña incorrecta."
    panel.text_input[0].input("contraseña-de-prueba")
    panel.button[0].click().run()
    assert not panel.exception
    assert panel.session_state["authenticated"] is True
    assert len(panel.dataframe) == 3


def test_panel_without_password_stops(base, monkeypatch):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    monkeypatch.delenv("CESFAM_PANEL_PASSWORD", raising=False)
    panel = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "panel_admin.py"), default_timeout=20
    ).run()
    assert not panel.exception
    assert not panel.dataframe
    assert "CESFAM_PANEL_PASSWORD" in panel.error[0].value
