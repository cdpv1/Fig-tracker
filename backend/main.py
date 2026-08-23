import sqlite3
from fastapi import FastAPI,HTTPException
from backend.db import create_tables, get_figures_by_id, insert_figure, get_figures
from pydantic import BaseModel

app = FastAPI()
create_tables()

class FigureCreate(BaseModel):
    id: int
    name: str
    scale: str | None = None

@app.get("/api/figures")
def get_figures_endpoint():
    figures = get_figures()
    if not figures:
        raise HTTPException(status_code=404, detail="No figures found.")
    return figures

@app.get("/api/figures/{figure_id}")
def get_figure_by_id_endpoint(figure_id: int):
    figure = get_figures_by_id(figure_id)
    if figure is None:
        raise HTTPException(status_code=404, detail=f"Figure with id {figure_id} not found.")
    return figure

@app.post("/api/figures", status_code=201)
def create_figure_endpoint(figure: FigureCreate):
    try:
        insert_figure(figure.id, figure.name, figure.scale)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail=f"Figure with id {figure.id} already exists.")
    return figure