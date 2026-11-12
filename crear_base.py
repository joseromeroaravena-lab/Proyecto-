import argparse
import os
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, time, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo


DIRECTORIO_PROYECTO = Path(__file__).resolve().parent
RUTA_BASE_PREDETERMINADA = DIRECTORIO_PROYECTO / "chatbot.db"
RUTA_ESQUEMA = DIRECTORIO_PROYECTO / "database" / "schema.sql"
RUTA_DATOS_DEMO = DIRECTORIO_PROYECTO / "database" / "seed_demo.sql"
ZONA_HORARIA = ZoneInfo("America/Santiago")

TABLAS_REQUERIDAS = {
    "patients",
    "professionals",
    "specialties",
    "appointments",
    "appointment_responses",
    "outbox",
    "waitlist",
    "offers",
}


def leer_sql(ruta):
    """Lee un archivo SQL versionado usando UTF-8."""
    return ruta.read_text(encoding="utf-8")


def fecha_demo(fecha_base, dias, hora):
    """Calcula una fecha demo relativa y la devuelve en el formato del proyecto."""
    fecha = fecha_base.date() + timedelta(days=dias)
    return datetime.combine(fecha, time(hora), ZONA_HORARIA).strftime(
        "%Y-%m-%d %H:%M"
    )


def insertar_citas_demo(conexion, fecha_base):
    citas = (
        (1, 1, 1, fecha_demo(fecha_base, 2, 10), "scheduled"),
        (2, 2, 2, fecha_demo(fecha_base, 3, 11), "confirmed"),
        (3, 1, 1, fecha_demo(fecha_base, -3, 9), "cancelled"),
    )

    conexion.executemany("""
        INSERT INTO appointments (
            patient_id, professional_id, specialty_id,
            professional, specialty, appointment_date, status
        )
        SELECT ?, pr.id, s.id, pr.name, s.name, ?, ?
        FROM professionals AS pr
        CROSS JOIN specialties AS s
        WHERE pr.id = ? AND s.id = ?
    """, (
        (paciente, fecha, estado, profesional, especialidad)
        for paciente, profesional, especialidad, fecha, estado in citas
    ))


def validar_base(conexion, fecha_base):
    tablas = {
        fila[0]
        for fila in conexion.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
        """)
    }
    faltantes = TABLAS_REQUERIDAS - tablas
    if faltantes:
        nombres = ", ".join(sorted(faltantes))
        raise ValueError(f"Faltan tablas requeridas: {nombres}")

    integridad = conexion.execute("PRAGMA integrity_check").fetchone()[0]
    if integridad != "ok":
        raise ValueError(f"La comprobación de integridad falló: {integridad}")

    claves_invalidas = conexion.execute("PRAGMA foreign_key_check").fetchall()
    if claves_invalidas:
        raise ValueError("La base contiene relaciones de clave foránea inválidas")

    cantidades = {
        tabla: conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        for tabla in ("patients", "professionals", "specialties", "appointments")
    }
    if any(cantidad < 3 for cantidad in cantidades.values()):
        raise ValueError("Los datos mínimos de demostración están incompletos")

    ahora = fecha_base.strftime("%Y-%m-%d %H:%M")
    citas_futuras = conexion.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE appointment_date > ?
          AND status IN ('scheduled', 'confirmed')
    """, (ahora,)).fetchone()[0]
    if citas_futuras < 2:
        raise ValueError("La agenda no contiene las dos citas futuras esperadas")


def crear_base(ruta_db=RUTA_BASE_PREDETERMINADA, fecha_base=None):
    """Crea una base demo completa sin reemplazar un archivo existente."""
    ruta_db = Path(ruta_db).resolve()
    if ruta_db.exists():
        return False

    ruta_db.parent.mkdir(parents=True, exist_ok=True)
    ruta_temporal = ruta_db.with_name(
        f".{ruta_db.name}.{uuid4().hex}.tmp"
    )
    fecha_base = fecha_base or datetime.now(ZONA_HORARIA)

    try:
        with closing(sqlite3.connect(ruta_temporal)) as conexion:
            conexion.execute("PRAGMA foreign_keys = ON")
            try:
                conexion.executescript(
                    "BEGIN IMMEDIATE;\n"
                    + leer_sql(RUTA_ESQUEMA)
                    + "\n"
                    + leer_sql(RUTA_DATOS_DEMO)
                )
                insertar_citas_demo(conexion, fecha_base)
                validar_base(conexion, fecha_base)
            except Exception:
                conexion.rollback()
                raise
            else:
                conexion.commit()

        os.link(ruta_temporal, ruta_db)
    except FileExistsError:
        return False
    finally:
        ruta_temporal.unlink(missing_ok=True)

    return True


def crear_argumentos():
    analizador = argparse.ArgumentParser(
        description="Crea chatbot.db con esquema y datos ficticios de demostración."
    )
    analizador.add_argument(
        "--ruta",
        type=Path,
        default=RUTA_BASE_PREDETERMINADA,
        help="Ruta de salida (por defecto: chatbot.db junto al script).",
    )
    return analizador.parse_args()


def main():
    argumentos = crear_argumentos()
    ruta_db = argumentos.ruta.resolve()

    try:
        creada = crear_base(ruta_db)
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"No se pudo crear la base de datos: {error}", file=sys.stderr)
        return 1

    if not creada:
        print("La base de datos ya existe. No se realizaron cambios:")
        print(ruta_db)
        return 0

    print("Base de datos de demostración creada correctamente:")
    print(ruta_db)
    print("Todos los pacientes y citas incluidos son ficticios.")
    print("Siguiente paso:")
    print(r".\.venv\Scripts\python.exe -m streamlit run panel_admin.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
