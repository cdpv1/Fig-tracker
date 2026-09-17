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


def get_latest_listing(mfc_id, source):
    conn = get_connection()
    try:
        row = conn.execute(
            '''
            SELECT listing_url
            FROM price_history
            WHERE mfc_id = ? AND source = ? AND listing_url IS NOT NULL
            ORDER BY recorded_at DESC, id DESC
            LIMIT 1
            ''',
            (mfc_id, source),
        ).fetchone()
        return row["listing_url"] if row else None
    finally:
        conn.close()

# inserts a new price history record for a figure


def add_price_observation(
    mfc_id,
    source,
    price,
    currency,
    item_condition=None,
    availability=None,
    listing_url=None,
    external_product_id=None,
    shop=None,
):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        latest = cursor.execute(
            '''
            SELECT price, currency, item_condition, availability, listing_url,
                   external_product_id, shop
            FROM price_history
            WHERE mfc_id = ? AND source = ?
              AND COALESCE(shop, '') = COALESCE(?, '')
              AND COALESCE(external_product_id, '') = COALESCE(?, '')
            ORDER BY recorded_at DESC, id DESC
            LIMIT 1
            ''',
            (mfc_id, source, shop, external_product_id),
        ).fetchone()
        current = (
            price,
            currency,
            item_condition,
            availability,
            listing_url,
            external_product_id,
            shop,
        )
        if latest and tuple(latest) == current:
            return False

        record = cursor.execute(
            '''
            INSERT INTO price_history (
                mfc_id, source, shop, price, currency, item_condition,
                availability, listing_url, external_product_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                mfc_id,
                source,
                shop,
                price,
                currency,
                item_condition,
                availability,
                listing_url,
                external_product_id,
            )
        )
        conn.commit()
        return True
    except:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_price_summary(mfc_id):
    """Return current comparable observations grouped by currency.

    Only the newest observation for each source/shop/product is included.
    Currency groups are intentionally kept separate; averaging JPY and USD
    without an exchange-rate policy would produce a meaningless market value.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            '''
            SELECT ph.*
            FROM price_history ph
            WHERE ph.mfc_id = ?
              AND ph.id = (
                SELECT newest.id
                FROM price_history newest
                WHERE newest.mfc_id = ph.mfc_id
                  AND newest.source = ph.source
                  AND COALESCE(newest.shop, '') = COALESCE(ph.shop, '')
                  AND COALESCE(newest.external_product_id, '') =
                      COALESCE(ph.external_product_id, '')
                ORDER BY newest.recorded_at DESC, newest.id DESC
                LIMIT 1
              )
            ORDER BY ph.currency, ph.price
            ''',
            (mfc_id,),
        ).fetchall()
        observations = [dict(row) for row in rows]
        markets = {}
        for observation in observations:
            currency = observation["currency"]
            market = markets.setdefault(currency, {"currency": currency, "observations": []})
            market["observations"].append(observation)

        for market in markets.values():
            prices = [row["price"] for row in market["observations"]]
            in_stock = [
                row for row in market["observations"]
                if str(row.get("availability") or "").lower()
                in {"in_stock", "instock", "available"}
            ]
            comparable = [row["price"] for row in in_stock] or prices
            average = sum(comparable) / len(comparable)
            market["average"] = round(average, 2)
            market["minimum"] = min(comparable)
            market["maximum"] = max(comparable)
            market["observation_count"] = len(market["observations"])
            market["in_stock_count"] = len(in_stock)
            market["shops"] = sorted({
                row["shop"] or row["source"]
                for row in in_stock
            })
            for row in market["observations"]:
                row["percent_from_average"] = round(
                    ((row["price"] - average) / average) * 100, 2
                ) if average else 0

        return {
            "mfc_id": mfc_id,
            "markets": list(markets.values()),
            "last_updated": observations[0]["recorded_at"] if observations else None,
        }
    finally:
        conn.close()
