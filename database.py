import sqlite3

DB_PATH = "tareas.db"


def crear_tabla():
    """Crea la tabla de tareas si todavia no existe"""
    con = sqlite3.connect(DB_PATH)
    con.execute("""
    CREATE TABLE IF NOT EXISTS tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    completada INTEGER NOT NULL DEFAULT 0,
    prioridad TEXT,
    sugerencia TEXT)
    """)
    con.commit()
    con.close()


def get_db():
    """Dependencia de FASTAPI: abre una conexion por peticion y la cierra al final"""
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()
