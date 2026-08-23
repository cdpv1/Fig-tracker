from datetime import date
import sqlite3
from fastapi import FastAPI,HTTPException
from backend.db import create_tables, get_figures_by_id, get_figures, delete_figure, upsert_figure
from pydantic import BaseModel
from backend.services.mfc import get_mfc_figure

app = FastAPI()
create_tables()

#Figure models for creating new figures
class FigureBase(BaseModel):
    name: str
    mfc_url: str | None = None
    picture_url: str | None = None
    thumbnail_url: str | None = None
    category: str | None = None
    scale: str | None = None
    height_mm: int | None = None
    origin: str | None = None
    manufacturer: str | None = None
    release_date: date | None = None
    barcode: str | None = None
    msrp: float | None = None
    currency: str | None = None
    rating: float | None = None


class FigureCreate(FigureBase):
    mfc_id: int


class FigureUpdate(FigureBase):
    pass
    
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

# Delete a figure by ID
@app.delete("/api/figures/{mfc_id}", status_code=204)
def delete_figure_endpoint(mfc_id: int):
    figure = get_figures_by_id(mfc_id)
    if figure is None:
        raise HTTPException(status_code=404, detail=f"Figure with MFC ID {mfc_id} not found.")
    delete_figure(mfc_id)

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
        upsert_figure(**figure)
        return {"message": f"Figure with MFC ID {mfc_id} imported successfully."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))