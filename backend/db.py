import sqlite3
from pathlib import Path

DATABASE_PATH = Path("data/figures.db")
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection():
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


def insert_figure(id, name, scale):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT OR IGNORE INTO figures (id, name, scale) VALUES (?, ?, ?)
        ''', (id, name, scale))
    conn.commit()
    conn.close()


def get_figures():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM figures')
    figures = cursor.fetchall()
    conn.close()
    return figures
