
import sqlite3
from pathlib import Path

print("Iniciando consulta de citas médicas...")

ruta_db = Path(__file__).resolve().parent / "chatbot.db"

conexion = sqlite3.connect(ruta_db)
cursor = conexion.cursor()

# Consultar citas y los nombres de sus pacientes
cursor.execute("""
    SELECT
        a.id,
        p.name,
        a.specialty,
        a.professional,
        a.appointment_date,
        a.status
    FROM appointments AS a
    INNER JOIN patients AS p
        ON a.patient_id = p.id
    ORDER BY a.appointment_date
""")

citas = cursor.fetchall()

print("\n=== CITAS MÉDICAS REGISTRADAS ===")
print("Cantidad de citas:", len(citas))

if citas:
    for cita in citas:
        print("----------------------------")
        print("ID de cita:", cita[0])
        print("Paciente:", cita[1])
        print("Especialidad:", cita[2])
        print("Profesional:", cita[3])
        print("Fecha y hora:", cita[4])
        print("Estado:", cita[5])
else:
    print("Todavía no hay citas médicas registradas.")

conexion.close()

print("\nConsulta finalizada correctamente.")
