import sqlite3
from contextlib import closing
from datetime import datetime

from conexion import conectar


def registrar_respuesta(cita_id, paciente_id, respuesta):
    nuevo_estado, estado_1, estado_2 = {
        "confirmar": ("confirmed", "scheduled", "scheduled"),
        "cancelar": ("cancelled", "scheduled", "confirmed"),
    }[respuesta]

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")

    with closing(conectar()) as conexion:
        conexion.execute("PRAGMA foreign_keys = ON")

        with conexion:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS appointment_responses (
                    id INTEGER PRIMARY KEY,
                    appointment_id INTEGER NOT NULL REFERENCES appointments(id),
                    response TEXT NOT NULL
                        CHECK (response IN ('confirmar', 'cancelar')),
                    channel TEXT NOT NULL,
                    received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cambio = conexion.execute("""
                UPDATE appointments
                SET status = ?
                WHERE id = ?
                  AND patient_id = ?
                  AND appointment_date > ?
                  AND status IN (?, ?)
            """, (nuevo_estado, cita_id, paciente_id, ahora, estado_1, estado_2))

            if cambio.rowcount != 1:
                return False

            conexion.execute("""
                INSERT INTO appointment_responses (
                    appointment_id, response, channel
                )
                VALUES (?, ?, 'simulado')
            """, (cita_id, respuesta))

    return True


def main():
    print("=== Chatbot de citas · Prueba local F2 ===")
    print("Sesión simulada del Paciente 1")
    print("1. Confirmar cita")
    print("2. Cancelar cita")

    opciones = {"1": "confirmar", "2": "cancelar"}
    respuesta = opciones.get(input("Selecciona una opción: ").strip())

    if respuesta is None:
        print("Opción inválida. Elige 1 o 2.")
        return

    try:
        cita_id = int(input("Ingresa el ID de la cita: "))
        registrada = registrar_respuesta(cita_id, paciente_id=1, respuesta=respuesta)
    except ValueError:
        print("El ID de la cita debe ser un número entero.")
        return
    except sqlite3.Error as error:
        print(f"Error al guardar la respuesta: {error}")
        return

    if not registrada:
        print("La cita no está disponible para esta acción.")
    elif respuesta == "confirmar":
        print("Tu cita quedó confirmada.")
    else:
        print("Tu cita quedó cancelada.")


if __name__ == "__main__":
    main()