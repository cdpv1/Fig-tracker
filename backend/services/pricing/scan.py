from backend.database.prices import add_price_observation
from backend.services.pricing.hlj import find_hlj_product
from backend.services.pricing.mfc_buy import get_buy_listings
from backend.services.pricing.amiami import find_amiami_product
from backend.services.pricing.bbts import find_bbts_product
from backend.database.figures import get_figure_by_id
from backend.database.enrichments import get_effective_barcode, add_enrichment, get_enrichments


def scan_hlj_price(figure):
    search_figure = dict(figure)
    if not search_figure.get("barcode"):
        search_figure["barcode"] = get_effective_barcode(figure["mfc_id"])
    product = find_hlj_product(search_figure)

    if not product:
        return []

    return [product]


def scan_mfc_buy(figure):
    """Adapt MFC partner rows to the common price-listing shape."""
    return [
        {
            **listing,
            "source": "MFC_BUY",
            "listing_url": listing["url"],
        }
        for listing in get_buy_listings(int(figure["mfc_id"]))
    ]


def scan_amiami_price(figure):
    print(f"[amiami] scanning figure {figure.get('mfc_id')}")
    product = find_amiami_product(figure)
    if not product:
        print(f"[amiami] no matching product for figure {figure.get('mfc_id')}")
    return [product] if product else []


def scan_bbts_price(figure):
    print(f"[bbts] scanning figure {figure.get('mfc_id')}")
    product = find_bbts_product(figure)
    if not product:
        print(f"[bbts] no matching product for figure {figure.get('mfc_id')}")
    return [product] if product else []


# BBTS remains available for manual experiments, but is not trusted for
# automatic observations until it can provide reliable product identifiers.
SCANNERS = (scan_amiami_price, scan_hlj_price, scan_mfc_buy)


def main_scan(figure):
    results = []
    for scanner in SCANNERS:
        listings = scanner(figure)
        if scanner is scan_mfc_buy and any(
            result["source"] == "AMIAMI" for result in results
        ):
            listings = [
                listing
                for listing in listings
                if _normalize_shop_name(listing.get("shop")) != "amiami"
            ]
        for result in listings:
            add_price_observation(
                mfc_id=figure["mfc_id"],
                source=result["source"],
                shop=result.get("shop"),
                price=result["price"],
                currency=result["currency"],
                item_condition=result.get("item_condition"),
                availability=result.get("availability"),
                listing_url=result.get("listing_url"),
                external_product_id=result.get("external_product_id"),
            )
            record_barcode_learning(figure["mfc_id"], result)
            results.append(result)
    return results


def _normalize_shop_name(shop):
    return "".join(
        character.lower()
        for character in str(shop or "")
        if character.isalnum()
    )


def record_barcode_learning(mfc_id, result):
    evidence = result.get("barcode_evidence")
    if evidence:
        evidence_barcodes = set()
        for item in evidence:
            barcode = str(item.get("barcode") or "").strip()
            if barcode and barcode not in evidence_barcodes:
                evidence_barcodes.add(barcode)
                _record_barcode(mfc_id, barcode, result["source"])
    else:
        evidence_barcodes = set()

    found_barcode = str(result.get("barcode") or "").strip()
    if not found_barcode or found_barcode in evidence_barcodes:
        return result

    _record_barcode(mfc_id, found_barcode, result["source"])
    return result


def _record_barcode(mfc_id, found_barcode, source):
    found_barcode = str(found_barcode).strip()
    if not found_barcode:
        return

    rows = get_enrichments(mfc_id, "barcode")
    if any(
        row["value"] == found_barcode and row["source"] == source
        for row in rows
    ):
        return

    known_barcode = get_effective_barcode(mfc_id)

    if known_barcode is None:
        add_enrichment(mfc_id, "barcode", found_barcode,
                       source, "unverified")
    elif found_barcode == known_barcode:
        origins = set()
        mirror = get_figure_by_id(mfc_id)
        if mirror and mirror.get("barcode") == found_barcode:
            origins.add("mfc")
        for row in rows:
            if row["value"] == found_barcode and row["confidence"] != "conflict":
                origins.add(row["source"])
        origins.add(source)
        if len(origins) >= 2:
            if not any(
                row["value"] == found_barcode
                and row["confidence"] == "confirmed"
                for row in rows
            ):
                add_enrichment(mfc_id, "barcode", found_barcode,
                               source, "confirmed")
        else:
            add_enrichment(mfc_id, "barcode", found_barcode,
                           source, "unverified")
    else:
        add_enrichment(mfc_id, "barcode", found_barcode,
                       source, "conflict")

print(main_scan(get_figure_by_id(1155763)))