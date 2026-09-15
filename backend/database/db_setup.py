from .connection import get_connection

# Creates tables if they don't exist


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
        figure_columns = {
            row[1] for row in cursor.execute("PRAGMA table_info(figures)")
        }
        if "gallery_urls" not in figure_columns:
            cursor.execute("ALTER TABLE figures ADD COLUMN gallery_urls TEXT")

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
                shop TEXT,
                price REAL NOT NULL,
                currency TEXT NOT NULL,
                item_condition TEXT,
                availability TEXT,
                listing_url TEXT,
                external_product_id TEXT,
                recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (mfc_id) REFERENCES figures (mfc_id)
                )
            '''
        )

        cursor.execute(
            '''
            CREATE INDEX IF NOT EXISTS idx_price_history_mfc_date ON price_history(mfc_id, recorded_at)
            '''
        )

        price_history_columns = {
            row[1] for row in cursor.execute("PRAGMA table_info(price_history)")
        }
        if "shop" not in price_history_columns:
            cursor.execute("ALTER TABLE price_history ADD COLUMN shop TEXT")
        if "external_product_id" not in price_history_columns:
            cursor.execute(
                "ALTER TABLE price_history ADD COLUMN external_product_id TEXT"
            )
        
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS figure_enrichments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mfc_id INTEGER NOT NULL,
                field TEXT NOT NULL,
                value TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence TEXT NOT NULL DEFAULT 'unverified',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (mfc_id) REFERENCES figures (mfc_id)
                )
            '''
        )

        cursor.execute(
            '''
            CREATE INDEX IF NOT EXISTS idx_enrichments_mfc_field ON figure_enrichments(mfc_id, field)
            '''
        )
        
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()
