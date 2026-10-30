import sqlite3

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from ai import analizar_tarea, ErrorIA
from database import crear_tabla, get_db

app = FastAPI(title="API de Tareas", version="2.0")
crear_tabla()


class TareaEntrada(BaseModel):
    titulo: str = Field(min_length=3, max_length=100)
    descripcion: str | None = Field(default=None, max_length=500)
    completada: bool = False


class Tarea(TareaEntrada):
    id: int
    prioridad: str | None = None
    sugerencia: str | None = None


def fila_a_tarea(fila: sqlite3.Row) -> Tarea:
    return Tarea(
        id=fila["id"],
        titulo=fila["titulo"],
        descripcion=fila["descripcion"],
        completada=bool(fila["completada"]),
        prioridad=fila["prioridad"],
        sugerencia=fila["sugerencia"],
    )


def buscar_fila(db: sqlite3.Connection, tarea_id: int) -> sqlite3.Row:
    fila = db.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,)).fetchone()
    if fila is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return fila


@app.post("/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
def crear_tarea(datos: TareaEntrada, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.execute(
        " INSERT INTO tareas (titulo, descripcion, completada) VALUES (?, ?, ?)",
        (datos.titulo, datos.descripcion, datos.completada),
    )
    db.commit()
    return fila_a_tarea(buscar_fila(db, cursor.lastrowid))


@app.get("/tareas", response_model=list[Tarea])
def listar_tareas(
    completada: bool | None = None, db: sqlite3.Connection = Depends(get_db)
):
    # complete = 1 if completada else 0
    if completada is None:
        filas = db.execute("SELECT * FROM tareas ORDER BY id").fetchall()
    else:
        filas = db.execute(
            "SELECT * FROM tareas WHERE completada = ? ORDER BY id", (completada,)
        ).fetchall()
    return [fila_a_tarea(f) for f in filas]


@app.post("/tareas/{tarea_id}/analizar", response_model=Tarea)
def analizar(tarea_id: int, db: sqlite3.Connection = Depends(get_db)):
    fila = buscar_fila(db, tarea_id)
    try:
        res = analizar_tarea(fila["titulo"], fila["descripcion"])
    except ErrorIA as error:
        raise HTTPException(status_code=503, detail=str(error))
    db.execute(
        "UPDATE tareas SET prioridad =?, sugerencia = ? WHERE id = ?",
        (res.prioridad, res.sugerencia, tarea_id),
    )
    db.commit()
    return fila_a_tarea(buscar_fila(db, tarea_id))
