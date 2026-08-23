from fastapi import FastAPI
from backend.db import create_tables

create_tables()

app = FastAPI()

@app.get("/api/figures")
def get_figures():\
    return [
        {
            "id":1,
            "name":"test figure",
            "scale":1/6
        }
    ]