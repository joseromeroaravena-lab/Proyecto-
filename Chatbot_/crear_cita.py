from contextlib import closing

from conexion import conectar

# Datos ficticios para la prueba de F1
patient_id = 1
specialty = "Medicina General"
professional = "Dra. Ana Martínez"
appointment_date = "2026-11-12 10:00"

with closing(conectar()) as conexion:
    conexion.execute("PRAGMA foreign_keys = ON")

    with conexion:
        cursor = conexion.execute("""
            INSERT INTO appointments (
                patient_id, specialty, professional, appointment_date,
                status, specialty_id, professional_id
            )
            SELECT p.id, s.name, pr.name, ?, 'scheduled', s.id, pr.id
            FROM patients AS p
            CROSS JOIN specialties AS s
            CROSS JOIN professionals AS pr
            WHERE p.id = ?
              AND s.name = ? AND s.active = 1
              AND pr.name = ? AND pr.active = 1
              AND NOT EXISTS (
                  SELECT 1
                  FROM appointments AS a
                  WHERE a.professional_id = pr.id
                    AND a.appointment_date = ?
                    AND a.status IN ('scheduled', 'confirmed')
              )
        """, (
            appointment_date, patient_id, specialty,
            professional, appointment_date
        ))

    if cursor.rowcount == 1:
        print(f"Cita registrada. ID: {cursor.lastrowid}")
        print(f"Fecha y hora: {appointment_date}")
    else:
        print("No se registró la cita. Revisa los datos y si el horario está ocupado.")
