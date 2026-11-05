import sqlite3
from contextlib import closing
from pathlib import Path

# Ubicación de la base de datos
ruta_db = Path(__file__).resolve().parent / "chatbot.db"

# Conectar con SQLite
def conectar():
    """Se conecta a la base de datos existente creada en DB Browser."""
    conexion = sqlite3.connect(
        ruta_db.as_uri() + "?mode=rw", uri=True, timeout=10
    )
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion

# Consultar las tablas existentes
def main():
    with closing(conectar()) as conexion:
        tablas = conexion.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' ORDER BY name"
        ).fetchall()
    print("Conexión exitosa con SQLite")
    print("Base de datos:", ruta_db)
    print("Tablas encontradas:")
    for tabla in tablas:
        print("-", tabla[0])


if __name__ == "__main__":
    main()
