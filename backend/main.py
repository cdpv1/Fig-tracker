import sqlite3
from fastapi import FastAPI,HTTPException
from backend.db import create_tables, get_figures_by_id, insert_figure, get_figures, delete_figure, update_figure
from pydantic import BaseModel
from backend.services.mfc import get_mfc_figure

app = FastAPI()
create_tables()

#Figure model for creating new figures
class FigureCreate(BaseModel):
    id: int
    name: str
    scale: str | None = None
    
class FigureUpdate(BaseModel):
    name: str
    scale: str | None = None
    
# Get all figures
@app.get("/api/figures")
def get_figures_endpoint():
    figures = get_figures()
    if not figures:
        raise HTTPException(status_code=404, detail="No figures found.")
    return figures

# Get a figure by ID
@app.get("/api/figures/{figure_id}")
def get_figure_by_id_endpoint(figure_id: int):
    figure = get_figures_by_id(figure_id)
    if figure is None:
        raise HTTPException(status_code=404, detail=f"Figure with id {figure_id} not found.")
    return figure

# Create a new figure
@app.post("/api/figures", status_code=201)
def create_figure_endpoint(figure: FigureCreate):
    try:
        insert_figure(figure.id, figure.name, figure.scale)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail=f"Figure with id {figure.id} already exists.")
    return figure

# Delete a figure by ID
@app.delete("/api/figures/{figure_id}", status_code=204)
def delete_figure_endpoint(figure_id: int):
    figure = get_figures_by_id(figure_id)
    if figure is None:
        raise HTTPException(status_code=404, detail=f"Figure with id {figure_id} not found.")
    delete_figure(figure_id)
    
# Update a figure by ID    
@app.put("/api/figures/{figure_id}", status_code=200)
def update_figure_endpoint(figure_id: int, figure: FigureUpdate):
    existing_figure = get_figures_by_id(figure_id)
    # Check if the figure exists before updating
    if existing_figure is None:
        raise HTTPException(status_code=404, detail=f"Figure with id {figure_id} not found.")
    
    # Call the update_figure function from db.py
    updated_figure = update_figure(figure_id, figure.name, figure.scale)
    
    return updated_figure

@app.get("/api/mfc/{mfc_id}")
def get_mfc_figure_endpoint(mfc_id: int):
    try:
        figure = get_mfc_figure(mfc_id)
        if figure is None:
            raise HTTPException(status_code=404, detail=f"Figure with MFC ID {mfc_id} not found.")
        return figure
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))