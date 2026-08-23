import sqlite3
from pathlib import Path
from backend.services.enums import FigureStatus

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

# Creates the figures table if it doesn't exist

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS figures (
                mfc_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                mfc_url TEXT,
                picture_url TEXT,
                thumbnail_url TEXT,
                category TEXT,
                scale TEXT,
                height_mm INTEGER,
                origin TEXT,
                manufacturer TEXT,
                release_date TEXT,
                barcode TEXT,
                msrp REAL,
                currency TEXT,
                rating REAL
            )
            '''
        )
        
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS collection (
                mfc_id INTEGER PRIMARY KEY,
                status TEXT NOT NULL,
                FOREIGN KEY (mfc_id) REFERENCES figures (mfc_id)
                )
            '''
        )
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()

# Retrieves all figures from the figures table

def get_figures():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        figures = cursor.execute('SELECT * FROM figures').fetchall()
        if not figures:
            return []
        return [dict(figure) for figure in figures]
    finally:
        conn.close()

# Retrieves a figure by its ID from the figures table

def get_figures_by_id(figure_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        row = cursor.execute(
            'SELECT * FROM figures WHERE mfc_id = ?', (figure_id,)).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def delete_figure(figure_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM figures WHERE mfc_id = ?', (figure_id,))
        conn.commit()
        # return cursor.rowcount > 0  # returns the number of rows deleted
    except:
        conn.rollback()
        raise
    finally:
        conn.close()

def upsert_figure(mfc_id, name, mfc_url, picture_url, thumbnail_url, category, scale, height_mm, origin, manufacturer, release_date, barcode, msrp, currency, rating):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            INSERT INTO figures (mfc_id, name, mfc_url, picture_url, thumbnail_url, category, scale, height_mm, origin, manufacturer, release_date, barcode, msrp, currency, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(mfc_id) DO UPDATE SET name=excluded.name, mfc_url=excluded.mfc_url, picture_url=excluded.picture_url, thumbnail_url=excluded.thumbnail_url, category=excluded.category, scale=excluded.scale, height_mm=excluded.height_mm, origin=excluded.origin, manufacturer=excluded.manufacturer, release_date=excluded.release_date, barcode=excluded.barcode, msrp=excluded.msrp, currency=excluded.currency, rating=excluded.rating
            ''', (mfc_id, name, mfc_url, picture_url, thumbnail_url, category, scale, height_mm, origin, manufacturer, release_date, barcode, msrp, currency, rating))
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()
        
def upsert_collection(mfc_id, status: FigureStatus):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            INSERT INTO collection (mfc_id, status) VALUES (?, ?)
            ON CONFLICT(mfc_id) DO UPDATE SET status=excluded.status
            ''', (mfc_id, status.value))
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()
        
def get_collection():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        collection = cursor.execute('SELECT * FROM collection JOIN figures ON collection.mfc_id = figures.mfc_id').fetchall()
        if not collection:
            return []
        return [dict(item) for item in collection]
    finally:
        conn.close()