from conexion import conectar, ruta_db

print("Iniciando consulta de pacientes...")


print("Base de datos:", ruta_db)

conexion = conectar()
cursor = conexion.cursor()

cursor.execute("SELECT id, name, phone FROM patients")
pacientes = cursor.fetchall()

print("\n=== PACIENTES REGISTRADOS ===")
print("Cantidad de pacientes:", len(pacientes))

for paciente in pacientes:
    print("ID:", paciente[0])
    print("Nombre:", paciente[1])
    print("Teléfono:", paciente[2])
    print("-------------------------")

conexion.close()

print("Consulta finalizada correctamente.")
