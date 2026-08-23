import sqlite3
from fastapi import FastAPI,HTTPException
from backend.db import create_tables, get_figures_by_id, insert_figure, get_figures, delete_figure, update_figure, upsert_figure
from pydantic import BaseModel
from backend.services.mfc import get_mfc_figure

app = FastAPI()
create_tables()

#Figure model for creating new figures
class FigureCreate(BaseModel):
    mfc_id: int
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
@app.get("/api/figures/{mfc_id}")
def get_figure_by_id_endpoint(mfc_id: int):
    figure = get_figures_by_id(mfc_id)
    if figure is None:
        raise HTTPException(status_code=404, detail=f"Figure with MFC ID {mfc_id} not found.")
    return figure

# Create a new figure
@app.post("/api/figures", status_code=201)
def create_figure_endpoint(figure: FigureCreate):
    try:
        insert_figure(figure.mfc_id, figure.name, figure.scale)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail=f"Figure with MFC ID {figure.mfc_id} already exists.")
    return figure

# Delete a figure by ID
@app.delete("/api/figures/{mfc_id}", status_code=204)
def delete_figure_endpoint(mfc_id: int):
    figure = get_figures_by_id(mfc_id)
    if figure is None:
        raise HTTPException(status_code=404, detail=f"Figure with MFC ID {mfc_id} not found.")
    delete_figure(mfc_id)

# Update a figure by ID    
@app.put("/api/figures/{mfc_id}", status_code=200)
def update_figure_endpoint(mfc_id: int, figure: FigureUpdate):
    existing_figure = get_figures_by_id(mfc_id)
    # Check if the figure exists before updating
    if existing_figure is None:
        raise HTTPException(status_code=404, detail=f"Figure with MFC ID {mfc_id} not found.")
    
    # Call the update_figure function from db.py
    updated_figure = update_figure(mfc_id, figure.name, figure.scale)
    
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
    
@app.post("/api/mfc/{mfc_id}/import", status_code=200)
def import_mfc_figure_endpoint(mfc_id: int):
    try:
        figure = get_mfc_figure(mfc_id)
        if figure is None:
            raise HTTPException(status_code=404, detail=f"Figure with MFC ID {mfc_id} not found.")
        
        # Insert or update the figure in the database
        upsert_figure(figure["mfc_id"], figure["name"], figure["mfc_url"], figure["picture_url"], figure["thumbnail_url"], figure["category"], figure["scale"], figure["height_mm"], figure["origin"], figure["manufacturer"], figure["release_date"], figure["barcode"], figure["msrp"], figure["currency"], figure["rating"])
        
        return {"message": f"Figure with MFC ID {mfc_id} imported successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))