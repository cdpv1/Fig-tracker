import sqlite3
from pathlib import Path

DATABASE_PATH = Path("data/figures.db")

def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DATABASE_PATH)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS figures (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            scale TEXT
        )
        '''
    )
    conn.commit()
    conn.close()
