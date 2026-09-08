from .connection import get_connection
from backend.services.enums import FigureStatus

def upsert_collection_status(mfc_id, status: FigureStatus):
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
        collection = cursor.execute(
            'SELECT c.mfc_id, f.name, f.picture_url, f.manufacturer, f.category, f.scale, f.height_mm, c.status FROM collection c JOIN figures f ON c.mfc_id = f.mfc_id').fetchall()
        if not collection:
            return []
        return [dict(item) for item in collection]
    finally:
        conn.close()


def get_collection_by_id(mfc_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        figure = cursor.execute(
            'SELECT * FROM collection c JOIN figures f ON c.mfc_id = f.mfc_id WHERE c.mfc_id = ?', (
                mfc_id,)
        ).fetchone()
        return figure
    finally:
        conn.close()


def update_collection(mfc_id, updates: dict):
    conn = get_connection()
    cursor = conn.cursor()
    allowed_fields = {
        "status",
        "purchase_price",
        "purchase_currency",
        "purchase_store",
        "purchase_date",
        "item_condition",
        "box_condition",
        "displayed",
        "display_location",
        "notes",
    }
    try:
        set_clauses = []
        values = []
        for field, value in updates.items():
            if field not in allowed_fields:
                raise ValueError(f"Invalid collection field: {field}")
            set_clauses.append(f"{field} = ?")
            values.append(value)
        values.append(mfc_id)
        sql = f"UPDATE collection SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP WHERE mfc_id = ?"
        cursor.execute(sql, values)
        if cursor.rowcount == 0:
            return None  # No rows updated, figure not found
        conn.commit()
        row = cursor.execute(
            'SELECT * FROM collection WHERE mfc_id = ?', (mfc_id,)).fetchone()
        return dict(row)
    except:
        conn.rollback()
        raise
    finally:
        conn.close()
