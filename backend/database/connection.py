import sqlite3
from pathlib import Path

# initialize the database path and create the directory if it doesn't exist
DATABASE_PATH = Path("data/figures.db")
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# returns connection to DB.


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    # allows us to access columns by name instead of index
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn