from backend.database.prices import add_price_observation
from backend.services.pricing.hlj import find_hlj_product
from backend.database.figures import get_figures, get_figure_by_id
from backend.database.enrichments import get_effective_barcode, add_enrichment, get_enrichments


def scan_hlj_price(figure):
    product = find_hlj_product(figure)

    if not product:
        return None

    add_price_observation(
        mfc_id=figure["mfc_id"],
        source=product["source"],
        price=product["price"],
        currency=product["currency"],
        item_condition=product["item_condition"],
        availability=product["availability"],
        listing_url=product["listing_url"],
    )

    return product


def main_scan(figure):
    result = scan_hlj_price(figure)
    found_barcode = result.get("barcode")
    if not found_barcode:
        return result  # scan found no barcode -> nothing to learn

    mfc_id = figure["mfc_id"]
    known_barcode = get_effective_barcode(mfc_id)

    if known_barcode is None:
        # first sighting ever: candidate, never truth
        add_enrichment(mfc_id, "barcode", found_barcode, result["source"], "unverified")

    elif found_barcode == known_barcode:
        # agreement -- but count *independent* origins, not repeats
        origins = set()
        mirror = get_figure_by_id(mfc_id)
        if mirror and mirror.get("barcode") == found_barcode:
            origins.add("mfc")
        for row in get_enrichments(mfc_id, "barcode"):
            if row["value"] == found_barcode and row["confidence"] != "conflict":
                origins.add(row["source"])
        origins.add(result["source"])
        if len(origins) >= 2:
            add_enrichment(mfc_id, "barcode", found_barcode, result["source"], "confirmed")
        # one source repeating itself -> nothing new, stay quiet

    else:
        # disagreement: never overwrite, flag for a human
        add_enrichment(mfc_id, "barcode", found_barcode, result["source"], "conflict")

    return result


print(main_scan(get_figure_by_id(2288148)))
print(get_enrichments(2288148, "barcode"))