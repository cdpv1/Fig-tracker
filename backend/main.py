from fastapi import FastAPI
from backend.db import create_tables, insert_figure, get_figures

create_tables()
app = FastAPI()

@app.get("/api/figures")
def get_figures_endpoint():
    return get_figures()