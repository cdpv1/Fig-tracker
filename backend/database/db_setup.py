from .connection import get_connection

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
                purchase_price REAL,
                purchase_currency TEXT,
                purchase_store TEXT,
                purchase_date TEXT,
                item_condition TEXT,
                box_condition TEXT,
                displayed INTEGER NOT NULL DEFAULT 0,
                display_location TEXT,
                notes TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (mfc_id) REFERENCES figures (mfc_id)
                )
            '''
        )

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mfc_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT NOT NULL,
                item_Condition TEXT,
                availibility TEXT,
                listing_url TEXT,
                
                recorded at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
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