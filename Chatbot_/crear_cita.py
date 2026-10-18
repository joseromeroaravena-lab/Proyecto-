
import sqlite3
from pathlib import Path

# Ubicación de la base de datos
ruta_db = Path(__file__).resolve().parent / "chatbot.db"

conexion = sqlite3.connect(ruta_db)
conexion.execute("PRAGMA foreign_keys = ON")
cursor = conexion.cursor()

# Datos de prueba
patient_id = 1
specialty = "Medicina General"
professional = "Dra. Ana Martínez"
appointment_date = "2026-10-26 10:00"

# Comprobar que el paciente existe
cursor.execute(
    "SELECT name FROM patients WHERE id = ?",
    (patient_id,)
)

paciente = cursor.fetchone()

if paciente is None:
    print("Error: no existe un paciente con ID 1.")
else:
    # Registrar la cita médica
    cursor.execute("""
        INSERT INTO appointments
        (patient_id, specialty, professional,
         appointment_date, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        patient_id,
        specialty,
        professional,
        appointment_date,
        "scheduled"
    ))

    conexion.commit()

    print("=== CITA REGISTRADA ===")
    print("ID de cita:", cursor.lastrowid)
    print("Paciente:", paciente[0])
    print("Especialidad:", specialty)
    print("Profesional:", professional)
    print("Fecha:", appointment_date)
    print("Estado: scheduled")

conexion.close()
