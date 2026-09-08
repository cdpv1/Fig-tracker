from .connection import get_connection

# gets all price history records for a figure by it's id


def get_price_history(mfc_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        price_history = cursor.execute(
            '''
            SELECT * FROM price_history WHERE mfc_id = ? ORDER BY recorded_at DESC
            ''', (mfc_id,)
        ).fetchall()

        return [dict(record) for record in price_history]
    finally:
        conn.close()

# inserts a new price history record for a figure


def add_price_observation(mfc_id, source, price, currency, item_condition=None, availability=None, listing_url=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        record = cursor.execute(
            '''
            INSERT INTO price_history (mfc_id, source, price, currency, item_condition, availability, listing_url) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (mfc_id, source, price, currency, item_condition, availability, listing_url)
        )
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()
