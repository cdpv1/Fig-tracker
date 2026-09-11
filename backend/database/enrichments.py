from .connection import get_connection
from .figures import get_figure_by_id

# confidence levels, weakest to strongest:
# unverified   - one source claimed this, nobody confirmed it
# confirmed    - two independent sources agree
# user_verified- a human checked it by hand
# conflict     - sources disagree, needs a human to resolve


def add_enrichment(mfc_id, field, value, source, confidence="unverified"):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            INSERT INTO figure_enrichments (mfc_id, field, value, source, confidence)
            VALUES (?, ?, ?, ?, ?)
            ''', (mfc_id, field, value, source, confidence)
        )
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_enrichments(mfc_id, field):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        rows = cursor.execute(
            '''
            SELECT * FROM figure_enrichments
            WHERE mfc_id = ? AND field = ?
            ORDER BY created_at DESC
            ''', (mfc_id, field)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_effective_barcode(mfc_id):
    rows = get_enrichments(mfc_id, "barcode")

    # 1. your hand-check always wins
    for row in rows:
        if row["confidence"] == "user_verified":
            return row["value"]
    # 2. then anything two independent sources agreed on
    for row in rows:
        if row["confidence"] == "confirmed":
            return row["value"]
    # 3. then the MFC mirror
    figure = get_figure_by_id(mfc_id)
    if figure and figure.get("barcode"):
        return figure["barcode"]
    # 4. then a single unverified claim (better than nothing)
    for row in rows:
        if row["confidence"] == "unverified":
            return row["value"]
    # conflict rows are skipped on purpose: a human resolves those
    return None
