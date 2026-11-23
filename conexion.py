import sqlite3
import os
from contextlib import closing
from pathlib import Path
from dotenv import load_dotenv

directorio_proyecto = Path(__file__).resolve().parent
load_dotenv(directorio_proyecto / '.env')

# Ubicación de la base de datos
ruta_db = Path(os.getenv('CESFAM_DB_PATH') or directorio_proyecto / 'chatbot.db').resolve()

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
