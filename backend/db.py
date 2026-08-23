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
    return conn

# Creates the figures table if it doesn't exist


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

# Inserts a new figure into the figures table


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
            'SELECT * FROM figures WHERE id = ?', (figure_id,)).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def delete_figure(figure_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM figures WHERE id = ?', (figure_id,))
        conn.commit()
        # return cursor.rowcount > 0  # returns the number of rows deleted
    except:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_figure(figure_id, name, scale):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            UPDATE figures SET name = ?, scale = ? WHERE id = ?
            ''', (name, scale, figure_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            return None

        row = conn.execute(
            """
            SELECT id, name, scale
            FROM figures
            WHERE id = ?
            """,
            (figure_id,)
        ).fetchone()

        return dict(row)

    except:
        conn.rollback()
        raise
    finally:
        conn.close()
