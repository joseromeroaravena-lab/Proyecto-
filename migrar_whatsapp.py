"""Migración aditiva y transaccional; no modifica la base al importar."""

import argparse
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from conexion import conectar

SQL = """
CREATE TABLE IF NOT EXISTS whatsapp_inbound (
 id INTEGER PRIMARY KEY, meta_id TEXT NOT NULL UNIQUE,
 patient_id INTEGER REFERENCES patients(id),
 appointment_id INTEGER REFERENCES appointments(id),
 content TEXT NOT NULL, result TEXT NOT NULL,
 received_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS whatsapp_outbox (
 id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patients(id),
 appointment_id INTEGER REFERENCES appointments(id),
 inbound_id INTEGER UNIQUE REFERENCES whatsapp_inbound(id),
 kind TEXT NOT NULL CHECK(kind IN ('reply','72h','24h')),
 message TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
 attempts INTEGER NOT NULL DEFAULT 0, meta_id TEXT UNIQUE,
 created_at TEXT NOT NULL, next_attempt_at TEXT NOT NULL,
 accepted_at TEXT, delivered_at TEXT, read_at TEXT, error_code TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS whatsapp_reminder_unique
 ON whatsapp_outbox(appointment_id, kind) WHERE kind IN ('72h','24h');
CREATE TABLE IF NOT EXISTS whatsapp_status_events (
 meta_id TEXT NOT NULL, status TEXT NOT NULL, occurred_at TEXT NOT NULL,
 error_code TEXT, PRIMARY KEY(meta_id, status, occurred_at)
);
CREATE TABLE IF NOT EXISTS schema_migrations (
 version TEXT PRIMARY KEY, applied_at TEXT NOT NULL
);
"""


def migrar(db):
    # executescript no se usa: haría commit implícito de una transacción abierta.
    for sentencia in SQL.split(";"):
        if sentencia.strip():
            db.execute(sentencia)
    db.execute(
        "INSERT OR IGNORE INTO schema_migrations VALUES ('whatsapp_v1', ?)",
        (datetime.now(timezone.utc).isoformat(),),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-dir", type=Path, default=Path("backups"))
    args = parser.parse_args()
    with closing(conectar()) as db:
        args.backup_dir.mkdir(parents=True, exist_ok=True)
        ruta = args.backup_dir / (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".db"
        )
        with closing(sqlite3.connect(ruta)) as copia:
            db.backup(copia)
        with db:
            db.execute("BEGIN IMMEDIATE")
            migrar(db)
    print(f"Migración aplicada. Respaldo: {ruta}")


if __name__ == "__main__":
    main()
