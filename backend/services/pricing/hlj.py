from rapidfuzz import fuzz
import json
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from itertools import combinations
from threading import Lock
import time

BASE_URL = "https://www.hlj.com"
MAX_SEARCH_QUERIES = 12
_SEARCH_CACHE = {}
_PRODUCT_CACHE = {}
REQUEST_INTERVAL = 2.0
_REQUEST_LOCK = Lock()
_NEXT_REQUEST_AT = 0.0


def _request(url, **kwargs):
    global _NEXT_REQUEST_AT
    with _REQUEST_LOCK:
        wait = _NEXT_REQUEST_AT - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        response = requests.get(url, impersonate="chrome", **kwargs)
        _NEXT_REQUEST_AT = time.monotonic() + REQUEST_INTERVAL
        return response


def get_hlj_product(product_url):
    if product_url in _PRODUCT_CACHE:
        return _PRODUCT_CACHE[product_url]

    response = _request(product_url, timeout=30)

    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)

        except json.JSONDecodeError:
            continue

        if data.get("@type") != "Product":
            continue

        offers = data.get("offers", {})

        availability = offers.get("availability")

        if availability:
            availability = availability.rsplit("/", 1)[-1]

        product = {
            "source": "HLJ",
            "name": data.get("name"),
            "barcode": data.get("gtin13"),
            "manufacturer": data.get("brand", {}).get("name"),
            "price": float(offers["price"]) if offers.get("price") else None,
            "currency": offers.get("priceCurrency"),
            "item_condition": "New",
            "availability": availability,
            "listing_url": offers.get("url") or product_url,
            "external_product_id": data.get("productID"),
        }
        _PRODUCT_CACHE[product_url] = product
        return product

    _PRODUCT_CACHE[product_url] = None
    return None


def find_hlj_product(figure):
    barcode = str(figure.get("barcode") or "").strip()
    name = (figure.get("name") or "").strip()
    manufacturer = (figure.get("manufacturer") or "").strip()

    # Best case: exact barcode match. Keep this path to one search and cache
    # product pages so later name matching does not request them again.
    if barcode:
        candidates = search_hlj(barcode)

        for candidate in candidates:
            product = get_hlj_product(candidate["url"])

            if not product:
                continue

            product_barcode = str(product.get("barcode") or "").strip()

            if product_barcode == barcode:
                product["match_method"] = "barcode"
                product["match_score"] = 100
                return product

    if not name:
        return None

    candidates_by_sku = {}
    exact_candidate = None

    for query in build_hlj_search_queries(figure):
        print(f"Searching HLJ for: {query!r}")

        candidates = search_hlj(query)

        for candidate in candidates:
            candidates_by_sku.setdefault(candidate["sku"], candidate)

            score = fuzz.token_set_ratio(
                name,
                candidate["name"],
            )

            if score == 100 and exact_candidate is None:
                exact_candidate = candidate

        # Once a complete name query produces an exact candidate, later
        # fallback queries are redundant and are usually the source of the
        # slow, repetitive HLJ scans.
        if exact_candidate is not None:
            break

    ranked_candidates = sorted(
        candidates_by_sku.values(),
        key=lambda candidate: fuzz.token_set_ratio(name, candidate["name"]),
        reverse=True,
    )

    products = []
    for candidate in ranked_candidates:
        score = fuzz.token_set_ratio(name, candidate["name"])
        if score < 85:
            break
        product = get_hlj_product(candidate["url"])
        if product:
            product["_match_score"] = score
            products.append(product)

    valid_products = [
        product for product in products
        if _manufacturer_matches(manufacturer, product)
    ]

    if exact_candidate is not None:
        exact_products = [
            product for product in valid_products
            if product["_match_score"] == 100
        ]
        if exact_products:
            selected = exact_products[0]
            selected["match_method"] = "name"
            selected["match_score"] = 100
            selected["barcode_evidence"] = _barcode_evidence(valid_products)
            selected.pop("_match_score", None)
            return selected

    # No perfect match, use the best result we found
    if not valid_products:
        return None

    selected = valid_products[0]
    selected["match_method"] = "name"
    selected["match_score"] = selected.pop("_match_score")
    selected["barcode_evidence"] = _barcode_evidence(valid_products)
    return selected


def _manufacturer_matches(manufacturer, product):
    product_manufacturer = (product.get("manufacturer") or "").strip()
    return not (
        manufacturer
        and product_manufacturer
        and fuzz.ratio(manufacturer.lower(), product_manufacturer.lower()) < 80
    )


def _barcode_evidence(products):
    evidence = {}
    for product in products:
        found_barcode = str(product.get("barcode") or "").strip()
        if found_barcode:
            evidence.setdefault(found_barcode, 0)
            evidence[found_barcode] += 1
    return [
        {"barcode": found_barcode, "matches": matches}
        for found_barcode, matches in evidence.items()
    ]


def search_hlj(query):
    query = re.sub(r"\s+", " ", query).strip()
    if query in _SEARCH_CACHE:
        return _SEARCH_CACHE[query]

    response = _request(
        f"{BASE_URL}/search/",
        params={"Word": query},
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    candidates = []
    seen_skus = set()

    # Each search result has a wishlist link containing its HLJ SKU:
    # /account/wishlist/add/MYE91134
    wishlist_links = soup.select('a[href*="/account/wishlist/add/"]')

    for wishlist_link in wishlist_links:
        wishlist_url = wishlist_link.get("href", "")
        sku = wishlist_url.rstrip("/").split("/")[-1]

        if not sku or sku in seen_skus:
            continue

        seen_skus.add(sku)

        # Find the actual product link that ends with this SKU.
        product_links = soup.find_all(
            "a",
            href=lambda href: (
                href
                and href.rstrip("/").lower().endswith(f"-{sku.lower()}")
            ),
        )

        if not product_links:
            continue

        # Prefer the link containing the visible product name
        product_link = next(
            (
                link
                for link in product_links
                if link.get_text(" ", strip=True)
            ),
            product_links[0],
        )

        name = product_link.get_text(" ", strip=True)
        product_url = urljoin(BASE_URL, product_link["href"])

        candidates.append({
            "sku": sku,
            "name": name,
            "url": product_url,
        })

    _SEARCH_CACHE[query] = candidates
    return candidates


def build_hlj_search_queries(figure):
    name = (figure.get("name") or "").strip()
    manufacturer = (figure.get("manufacturer") or "").strip()
    scale = (figure.get("scale") or "").strip()
    origin = (figure.get("origin") or "").strip()

    if not name:
        return []

    queries = []

    def add_query(query):
        query = re.sub(r"\s+", " ", query).strip()

        if query and query not in queries:
            queries.append(query)

    # 1. Original MFC name
    add_query(name)

    # 2. Cleaned-up full name
    cleaned_name = re.sub(r"[~()\-]", " ", name)
    add_query(cleaned_name)

    # Split MFC name into chunks
    parts = [
        part.strip()
        for part in re.split(r"\s+-\s+", name)
        if part.strip()
    ]

    useful_parts = [
        part
        for part in parts
        if not re.fullmatch(r"1/\d+", part)
    ]

    # 3. Useful chunks combined
    if useful_parts:
        add_query(" ".join(useful_parts))

    # 4. Metadata-assisted queries
    if manufacturer:
        for part in useful_parts:
            add_query(f"{part} {manufacturer}")

    if scale:
        for part in useful_parts:
            add_query(f"{part} {scale}")

    if origin:
        for part in useful_parts:
            add_query(f"{part} {origin}")

    # Manufacturer + scale
    if manufacturer and scale:
        add_query(f"{manufacturer} {scale}")

    # Manufacturer + origin
    if manufacturer and origin:
        add_query(f"{manufacturer} {origin}")

    # Origin + scale
    if origin and scale:
        add_query(f"{origin} {scale}")

    # 5. Useful chunk combinations
    for combo_size in (3, 2):
        if len(useful_parts) >= combo_size:
            for combo in combinations(useful_parts, combo_size):
                add_query(" ".join(combo))

    # 6. Keyword-based fallback searches
    stop_words = {
        "no",
        "to",
        "the",
        "of",
        "and",
        "ver",
        "version",
    }

    words = [
        word
        for word in re.findall(r"[A-Za-z0-9]+", name)
        if word.lower() not in stop_words
    ]

    product_words = [
        word
        for word in words
        if word.lower() in {
            "figure",
            "noodle",
            "stopper",
            "scale",
            "nendoroid",
            "figma",
            "bunny",
            "popup",
            "parade",
        }
    ]

    for word in words:
        if len(word) < 4:
            continue

        if product_words:
            add_query(" ".join([word] + product_words))

        if manufacturer:
            add_query(f"{word} {manufacturer}")

        if scale:
            add_query(f"{word} {scale}")

        if origin:
            add_query(f"{word} {origin}")

    # 7. Broadest fallback: individual MFC chunks
    for part in useful_parts:
        add_query(part)

    # The broad word-by-word fallbacks are useful only as a last resort and
    # cause a large number of near-duplicate requests. Keep the highest-signal
    # queries generated first.
    return queries[:MAX_SEARCH_QUERIES]
