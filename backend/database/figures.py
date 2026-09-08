from .connection import get_connection

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


def get_figure_by_id(figure_id):
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

# deletes a figure by its ID from the figures table


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

# inserts or updates a figure in the figures table by ID


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
