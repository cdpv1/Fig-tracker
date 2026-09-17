import re
from rapidfuzz import fuzz

from backend.database.prices import add_price_observation, get_latest_listing
from backend.services.pricing.hlj import find_hlj_product, get_hlj_product
from backend.services.pricing.mfc_buy import get_buy_listings
from backend.services.pricing.amiami import (
    find_amiami_product,
    get_amiami_product,
    is_rate_limited,
)
from backend.services.pricing.bbts import find_bbts_product
from backend.services.pricing.retailers import (
    find_retailer_product,
    find_solaris_products,
    refresh_retailer_product,
)
from backend.database.figures import get_figures, get_figure_by_id
from backend.database.enrichments import (
    get_effective_barcode,
    add_enrichment,
    get_enrichments,
    is_valid_barcode,
)
from backend.services.pricing.provider_status import (
    get_provider_status,
    mark_provider,
)


def scan_hlj_price(figure):
    search_figure = dict(figure)
    search_figure["barcode"] = get_effective_barcode(figure["mfc_id"])
    saved = get_latest_listing(figure["mfc_id"], "HLJ")
    if saved:
        product = get_hlj_product(saved)
        if product and _saved_product_matches(search_figure, product):
            product["match_method"] = "saved_url"
            return [product]
    product = find_hlj_product(search_figure)

    if not product:
        return []

    return [product]


def scan_mfc_buy(figure):
    """Adapt MFC partner rows to the common price-listing shape."""
    listings = []
    for listing in get_buy_listings(int(figure["mfc_id"])):
        result = {
            **listing,
            "source": "MFC_BUY",
            "listing_url": listing["url"],
        }
        jan_match = re.search(r"[?&]jan=([^&]*)", listing["url"])
        jan = jan_match.group(1).strip() if jan_match else ""
        if jan:
            result["barcode"] = jan
        listings.append(result)
    return listings


def scan_amiami_price(figure):
    print(f"[amiami] scanning figure {figure.get('mfc_id')}")
    search_figure = dict(figure)
    search_figure["barcode"] = get_effective_barcode(figure["mfc_id"])
    saved = get_latest_listing(figure["mfc_id"], "AMIAMI")
    if saved:
        product = get_amiami_product(saved)
        if product and _saved_product_matches(search_figure, product):
            product["match_method"] = "saved_url"
            return [product]
    product = find_amiami_product(search_figure)
    if not product:
        print(f"[amiami] no matching product for figure {figure.get('mfc_id')}")
    return [product] if product else []


def scan_bbts_price(figure):
    print(f"[bbts] scanning figure {figure.get('mfc_id')}")
    product = find_bbts_product(figure)
    if not product:
        print(f"[bbts] no matching product for figure {figure.get('mfc_id')}")
    return [product] if product else []


def _scan_retailer(figure, retailer):
    search_figure = dict(figure)
    search_figure["barcode"] = get_effective_barcode(figure["mfc_id"])
    saved = get_latest_listing(figure["mfc_id"], retailer)
    if saved:
        products = refresh_retailer_product(search_figure, retailer, saved)
        if products:
            for product in products:
                product["match_method"] = "saved_url"
                product["source"] = retailer
            return products
    product = find_retailer_product(search_figure, retailer)
    if not product:
        return []
    product["source"] = retailer
    return [product]


def scan_solaris_price(figure):
    search_figure = dict(figure)
    search_figure["barcode"] = get_effective_barcode(figure["mfc_id"])
    saved = get_latest_listing(figure["mfc_id"], "SOLARIS")
    if saved:
        products = refresh_retailer_product(search_figure, "SOLARIS", saved)
        if products:
            for product in products:
                product["match_method"] = "saved_url"
            return products
    return find_solaris_products(search_figure)


def _saved_product_matches(figure, product):
    barcode = str(figure.get("barcode") or "").strip()
    if barcode:
        return str(product.get("barcode") or "").strip() == barcode
    return fuzz.token_set_ratio(
        str(figure.get("name") or ""),
        str(product.get("name") or ""),
    ) >= 85


def scan_good_smile_price(figure):
    return _scan_retailer(figure, "GOOD_SMILE")


def scan_ninnin_price(figure):
    return _scan_retailer(figure, "NINNIN_GAME")


def scan_hobby_genki_price(figure):
    return _scan_retailer(figure, "HOBBY_GENKI")


# BBTS remains available for manual experiments, but is not trusted for
# automatic observations until it can provide reliable product identifiers.
SCANNERS = (
    scan_amiami_price,
    scan_hlj_price,
    scan_solaris_price,
    scan_good_smile_price,
    scan_ninnin_price,
    scan_hobby_genki_price,
    scan_mfc_buy,
)


def main_scan(figure):
    results = []
    for scanner in SCANNERS:
        provider = _scanner_provider(scanner)
        mark_provider(provider, "running")
        try:
            listings = scanner(figure)
        except Exception as error:
            mark_provider(provider, "error", error=error)
            print(f"[scan] {provider} failed for figure {figure['mfc_id']}: {error}")
            continue
        if provider == "AMIAMI" and is_rate_limited():
            mark_provider(provider, "rate_limited")
        else:
            mark_provider(provider, "available")
        if scanner is scan_mfc_buy:
            direct_shops = {
                alias
                for result in results
                if result["source"] in {
                    "AMIAMI", "SOLARIS", "GOOD_SMILE",
                    "NINNIN_GAME", "HOBBY_GENKI",
                }
                for alias in _provider_shop_aliases(result["source"])
            }
            listings = [
                listing
                for listing in listings
                if _normalize_shop_name(listing.get("shop")) not in direct_shops
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


def _scanner_provider(scanner):
    return {
        scan_amiami_price: "AMIAMI",
        scan_hlj_price: "HLJ",
        scan_solaris_price: "SOLARIS",
        scan_good_smile_price: "GOOD_SMILE",
        scan_ninnin_price: "NINNIN_GAME",
        scan_hobby_genki_price: "HOBBY_GENKI",
        scan_mfc_buy: "MFC_BUY",
    }.get(scanner, scanner.__name__)


def scan_all_figures():
    """Scan every locally imported figure and return per-figure results."""
    report = []
    for figure in get_figures():
        mfc_id = figure["mfc_id"]
        try:
            results = main_scan(figure)
            report.append({
                "mfc_id": mfc_id,
                "name": figure.get("name"),
                "results": results,
                "error": None,
            })
        except Exception as error:
            print(f"[scan] figure {mfc_id} failed: {error}")
            report.append({
                "mfc_id": mfc_id,
                "name": figure.get("name"),
                "results": [],
                "error": str(error),
            })
    return report


def _normalize_shop_name(shop):
    return "".join(
        character.lower()
        for character in str(shop or "")
        if character.isalnum()
    )


def _provider_shop_aliases(source):
    aliases = {
        "AMIAMI": ("amiami",),
        "SOLARIS": ("solaris", "solarisjapan"),
        "GOOD_SMILE": ("goodsmile", "goodsmilecompany"),
        "NINNIN_GAME": ("ninningame",),
        "HOBBY_GENKI": ("hobbygenki",),
    }
    return aliases.get(source, (_normalize_shop_name(source),))


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
    if not is_valid_barcode(found_barcode):
        return result
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

print(main_scan(get_figure_by_id(641513)))