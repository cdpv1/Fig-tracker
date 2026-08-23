import sqlite3
from pathlib import Path

DATABASE_PATH = Path("data/figures.db")
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    try:
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
    except:
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_figure(id, name, scale):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            INSERT INTO figures (id, name, scale) VALUES (?, ?, ?)
            ''', (id, name, scale))
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()


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

def get_figures_by_id(figure_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        row = cursor.execute('SELECT * FROM figures WHERE id = ?', (figure_id,)).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:    
        conn.close()