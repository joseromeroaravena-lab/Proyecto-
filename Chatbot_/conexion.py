import sqlite3
from pathlib import Path

# Ubicación de la base de datos
ruta_db = Path(__file__).resolve().parent / "chatbot.db"

# Conectar con SQLite
conexion = sqlite3.connect(ruta_db)

# Consultar las tablas existentes
cursor = conexion.cursor()
cursor.execute(
    "SELECT name FROM sqlite_master "
    "WHERE type='table' ORDER BY name"
)

tablas = cursor.fetchall()

print("Conexión exitosa con SQLite")
print("Tablas encontradas:")

for tabla in tablas:
    print("-", tabla[0])

conexion.close()