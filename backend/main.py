from datetime import date
from fastapi import FastAPI, HTTPException, BackgroundTasks
from mfc_api import MFCClient
from backend.database.db_setup import create_tables
from backend.database.collection import get_collection, get_collection_by_id, update_collection
from backend.database.figures import get_figure_by_id, get_figures, delete_figure, upsert_figure
from pydantic import BaseModel
from backend.services.mfc import get_mfc_figure, get_owned_collection_ids
from backend.services.sync import sync_owned_collection, create_sync_job, get_sync_job
from backend.services.enums import FigureStatus
from backend.config import MFC_USERNAME

app = FastAPI()
create_tables()

# Figure models for creating new figures


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


class CollectionUpdate(BaseModel):
    status: FigureStatus | None = None
    purchase_price: float | None = None
    purchase_currency: str | None = None
    purchase_store: str | None = None
    purchase_date: str | None = None
    item_condition: str | None = None
    box_condition: str | None = None
    displayed: bool | None = None
    display_location: str | None = None
    notes: str | None = None

# Get all figures
@app.get("/api/figures", tags=["Figures"])
def get_figures_endpoint():
    figures = get_figures()
    if not figures:
        raise HTTPException(status_code=404, detail="No figures found.")
    return figures

# Get a figure by ID
@app.get("/api/figures/{mfc_id}", tags=["Figures"])
def get_figure_by_id_endpoint(mfc_id: int):
    figure = get_figure_by_id(mfc_id)
    if figure is None:
        raise HTTPException(
            status_code=404, detail=f"Figure with MFC ID {mfc_id} not found.")
    return figure

# Delete a figure by ID
@app.delete("/api/figures/{mfc_id}", status_code=204, tags=["Figures"])
def delete_figure_endpoint(mfc_id: int):
    figure = get_figure_by_id(mfc_id)
    if figure is None:
        raise HTTPException(
            status_code=404, detail=f"Figure with MFC ID {mfc_id} not found.")
    delete_figure(mfc_id)

# Get the collection of figures
@app.get("/api/collection", tags=["Collection"])
def get_collection_endpoint():
    return get_collection()

# Get collection info by MFC ID
@app.get("/api/collection/{mfc_id}", tags=["Collection"])
def get_collection_by_id_endpoint(mfc_id: int):
    figure = get_collection_by_id(mfc_id)
    if figure is None:
        raise HTTPException(
            status_code=404, detail=f"Figure with MFC ID {mfc_id} not found.")
    return figure

# Update collection info by MFC ID
@app.patch("/api/collection/{mfc_id}", tags=["Collection"])
def update_collection_endpoint(mfc_id: int, updates: CollectionUpdate):
    updates = updates.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided.")
    if "status" in updates and updates["status"] is not None:
        updates["status"] = updates["status"].value
    updated_collection = update_collection(mfc_id, updates)
    if updated_collection is None:
        raise HTTPException(
            status_code=404, detail=f"Collection with MFC ID {mfc_id} not found.")
    return updated_collection

# Get a figure from MFC by ID
@app.get("/api/mfc/figure/{mfc_id}", tags=["MFC"])
def get_mfc_figure_endpoint(mfc_id: int):
    try:
        figure = get_mfc_figure(mfc_id)
        if figure is None:
            raise HTTPException(
                status_code=404, detail=f"Figure with MFC ID {mfc_id} not found.")
        return figure
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Import a figure from MFC by ID
@app.post("/api/mfc/figure/{mfc_id}/import", status_code=200, tags=["MFC"])
def import_mfc_figure_endpoint(mfc_id: int):
    try:
        figure = get_mfc_figure(mfc_id)
        if figure is None:
            raise HTTPException(
                status_code=404, detail=f"Figure with MFC ID {mfc_id} not found.")
        # Insert or update the figure in the database
        upsert_figure(**figure)
        return {"message": f"Figure with MFC ID {mfc_id} imported successfully."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get the user's owned collection from MFC
@app.get("/api/mfc/collection", tags=["MFC"])
def get_mfc_collection_endpoint():
    try:
        with MFCClient() as client:
            collection = get_owned_collection_ids(client, MFC_USERNAME)
        if not collection:
            raise HTTPException(
                status_code=404, detail=f"No collection found for user {MFC_USERNAME}.")
        return collection
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Start a background task to sync the user's owned collection from MFC
@app.post("/api/mfc/collection/sync", status_code=200, tags=["MFC"])
def start_collection_sync(background_tasks: BackgroundTasks):
    job_id = create_sync_job(MFC_USERNAME, background_tasks)

    return {"job_id": job_id}

# Get the status of a sync job
@app.get("/api/sync/{job_id}", tags=["MFC"])
def get_sync_status(job_id: str):
    job = get_sync_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Sync job not found",
        )

    return job

@app.get("/api/prices/{mfc_id}", tags=["Prices"])
def get_price_history_endpoint(mfc_id: int):
    from backend.database.prices import get_price_history
    price_history = get_price_history(mfc_id)
    return price_history