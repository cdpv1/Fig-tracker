import json
import re
import time
from threading import Lock
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup
from curl_cffi import requests
from rapidfuzz import fuzz


_REQUEST_LOCK = Lock()
_NEXT_REQUEST_AT = 0.0
REQUEST_INTERVAL = 3.0
_PROVIDER_BLOCKED_UNTIL = {}
BLOCKED_COOLDOWN = 900.0

RETAILERS = {
    "SOLARIS": {
        "base_url": "https://solarisjapan.com",
        "search_url": "https://solarisjapan.com/search?q={query}",
        "link_pattern": "/products/",
        "currency": "JPY",
    },
    "NINNIN_GAME": {
        "retailer": "NINNIN_GAME",
        "base_url": "https://www.nin-nin-game.com",
        "search_url": "https://www.nin-nin-game.com/en/search?controller=search&search_query={query}",
        "link_pattern": "/en/",
        "currency": "JPY",
    },
    "HOBBY_GENKI": {
        "retailer": "HOBBY_GENKI",
        "base_url": "https://hobby-genki.com",
        "search_url": "https://hobby-genki.com/en/search?controller=search&search_query={query}",
        "link_pattern": "/en/",
        "currency": "JPY",
    },
}

GOOD_SMILE_BASE_URL = "https://www.goodsmile.com"
GOOD_SMILE_SUGGEST_URL = (
    f"{GOOD_SMILE_BASE_URL}/en/search/suggest?search_keyword={{query}}"
)


def find_retailer_product(figure, retailer):
    if _retailer_blocked(retailer):
        return None
    if retailer == "SOLARIS":
        products = find_solaris_products(figure)
        return products[0] if products else None
    if retailer == "GOOD_SMILE":
        return _find_good_smile_product(figure)
    config = RETAILERS[retailer]
    barcode = str(figure.get("barcode") or "").strip()
    name = _normalized_name(figure.get("name"))
    manufacturer = _normalized_name(figure.get("manufacturer"))
    queries = ([barcode] if barcode else []) + _name_queries(name, manufacturer)
    seen = set()

    for query in queries:
        for candidate in _search(config, query):
            if candidate["url"] in seen:
                continue
            seen.add(candidate["url"])
            product = _get_product(config, candidate["url"])
            if not product:
                continue
            product_barcode = str(product.get("barcode") or "").strip()
            if barcode and product_barcode == barcode:
                product["match_method"] = "barcode"
                product["match_score"] = 100
                return product
            score = fuzz.token_set_ratio(name, _normalized_name(product.get("name")))
            product_manufacturer = _normalized_name(product.get("manufacturer"))
            if score < 92:
                continue
            if manufacturer and product_manufacturer and fuzz.token_set_ratio(
                manufacturer, product_manufacturer
            ) < 80:
                continue
            product["match_method"] = "name"
            product["match_score"] = score
            return product
    return None


def refresh_retailer_product(figure, retailer, url):
    if retailer == "SOLARIS":
        products = _solaris_products(
            url if url.endswith(".json") else f"{url}.json"
        )
        return _matching_solaris_products(figure, products)
    if retailer == "GOOD_SMILE":
        product = _get_good_smile_product(url)
        return [product] if product and _product_matches(figure, product) else []
    config = RETAILERS.get(retailer)
    if not config:
        return []
    product = _get_product(config, url)
    if not product:
        return []
    return [product] if _product_matches(figure, product) else []


def _retailer_blocked(retailer):
    return time.monotonic() < _PROVIDER_BLOCKED_UNTIL.get(retailer, 0)


def is_retailer_blocked(retailer):
    return _retailer_blocked(retailer)


def _mark_retailer_blocked(retailer):
    _PROVIDER_BLOCKED_UNTIL[retailer] = time.monotonic() + BLOCKED_COOLDOWN


def find_solaris_products(figure):
    barcode = str(figure.get("barcode") or "").strip()
    name = _normalized_name(figure.get("name"))
    manufacturer = _normalized_name(figure.get("manufacturer"))
    queries = ([barcode] if barcode else []) + _name_queries(name, manufacturer)
    seen = set()
    for query in queries:
        for candidate in _solaris_search(query):
            if candidate["url"] in seen:
                continue
            seen.add(candidate["url"])
            matching = _matching_solaris_products(figure, _solaris_products(candidate["url"]))
            if matching:
                return matching
    return []


def _matching_solaris_products(figure, products):
    barcode = str(figure.get("barcode") or "").strip()
    name = _normalized_name(figure.get("name"))
    manufacturer = _normalized_name(figure.get("manufacturer"))
    matching = []
    for product in products:
        product_barcode = str(product.get("barcode") or "").strip()
        if barcode and product_barcode == barcode:
            product["match_method"] = "barcode"
            product["match_score"] = 100
            matching.append(product)
            continue
        if barcode:
            continue
        score = fuzz.token_set_ratio(name, _normalized_name(product.get("name")))
        if score < 92:
            continue
        if manufacturer and product.get("manufacturer") and fuzz.token_set_ratio(
            manufacturer, _normalized_name(product["manufacturer"])
        ) < 80:
            continue
        product["match_method"] = "name"
        product["match_score"] = score
        matching.append(product)
    return matching


def _product_matches(figure, product):
    barcode = str(figure.get("barcode") or "").strip()
    if barcode:
        return str(product.get("barcode") or "").strip() == barcode
    return fuzz.token_set_ratio(
        _normalized_name(figure.get("name")),
        _normalized_name(product.get("name")),
    ) >= 92


def _solaris_search(query):
    url = (
        "https://solarisjapan.com/search/suggest.json"
        f"?q={quote(query)}&resources[type]=product&resources[limit]=10"
    )
    try:
        payload = _request(url).json()
    except Exception as exc:
        print(f"[SOLARIS] search failed for {query!r}: {exc}")
        return []
    candidates = []
    for item in payload.get("resources", {}).get("results", {}).get("products", []):
        handle = item.get("handle")
        if handle:
            candidates.append({
                "name": item.get("title") or "",
                "url": f"https://solarisjapan.com/products/{handle}.json",
            })
    return candidates


def _solaris_products(url):
    try:
        payload = _request(url).json().get("product") or {}
    except Exception as exc:
        print(f"[SOLARIS] product request failed for {url}: {exc}")
        return []
    products = []
    for variant in payload.get("variants") or []:
        barcode = _valid_barcode(variant.get("barcode"))
        price = variant.get("price")
        if price is None:
            continue
        try:
            price = float(price)
        except (TypeError, ValueError):
            continue
        if price <= 0:
            continue
        products.append({
            "source": "SOLARIS",
            "name": payload.get("title"),
            "barcode": barcode,
            "manufacturer": payload.get("vendor"),
            "price": price,
            "currency": variant.get("price_currency") or "USD",
            "item_condition": (
                "Used" if "used" in str(variant.get("title", "")).lower()
                else "New"
            ),
            "availability": "InStock" if variant.get("available") else "OutOfStock",
            "listing_url": f"https://solarisjapan.com/products/{payload.get('handle')}",
            "external_product_id": str(variant.get("id") or payload.get("id")),
        })
    return products


def _valid_barcode(value):
    barcode = str(value or "").strip()
    return barcode if re.fullmatch(r"\d{8,14}", barcode) else None


def _find_good_smile_product(figure):
    barcode = str(figure.get("barcode") or "").strip()
    name = _normalized_name(figure.get("name"))
    manufacturer = _normalized_name(figure.get("manufacturer"))
    queries = ([barcode] if barcode else []) + _name_queries(name, manufacturer)
    seen = set()
    for query in queries:
        for candidate in _good_smile_search(query):
            if candidate["url"] in seen:
                continue
            seen.add(candidate["url"])
            product = _get_good_smile_product(candidate["url"])
            if not product:
                continue
            if barcode and str(product.get("barcode") or "").strip() == barcode:
                product["match_method"] = "barcode"
                product["match_score"] = 100
                return product
            score = fuzz.token_set_ratio(name, _normalized_name(product.get("name")))
            if score < 92:
                continue
            if manufacturer and product.get("manufacturer") and fuzz.token_set_ratio(
                manufacturer, _normalized_name(product["manufacturer"])
            ) < 80:
                continue
            product["match_method"] = "name"
            product["match_score"] = score
            return product
    return None


def _good_smile_search(query):
    try:
        payload = _request(
            GOOD_SMILE_SUGGEST_URL.format(query=quote(query))
        ).json()
    except Exception as exc:
        print(f"[GOOD_SMILE] search failed for {query!r}: {exc}")
        return []
    candidates = []
    values = payload if isinstance(payload, list) else payload.get("products", [])
    for item in values:
        product_id = item.get("id") or item.get("product_id")
        if product_id:
            candidates.append({
                "name": item.get("name") or item.get("title") or "",
                "url": f"{GOOD_SMILE_BASE_URL}/en/product/{product_id}",
            })
    return candidates


def _get_good_smile_product(url):
    try:
        response = _request(url)
    except Exception as exc:
        print(f"[GOOD_SMILE] product request failed for {url}: {exc}")
        return None
    soup = BeautifulSoup(response.text, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        product = _from_json_ld(data, url, "JPY")
        if product:
            product["source"] = "GOOD_SMILE"
            return product
    return None


def _name_queries(name, manufacturer):
    if not name:
        return []
    parts = [
        part.strip()
        for part in re.split(r"\s+-\s+|[()~]", name)
        if len(part.strip()) >= 5
    ]
    queries = [name]
    if manufacturer:
        queries.append(f"{name} {manufacturer}")
    queries.extend(parts[:4])
    return list(dict.fromkeys(queries))


def _normalized_name(value):
    value = str(value or "").lower()
    value = re.sub(r"\[[^\]]+\]|\([^)]*\)", " ", value)
    value = re.sub(r"\b(complete figure|figure|original|no brand girls)\b", " ", value)
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _request(url):
    global _NEXT_REQUEST_AT
    with _REQUEST_LOCK:
        wait = _NEXT_REQUEST_AT - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        response = requests.get(url, impersonate="chrome", timeout=30)
        _NEXT_REQUEST_AT = time.monotonic() + REQUEST_INTERVAL
        response.raise_for_status()
        return response


def _search(config, query):
    retailer = config.get("retailer")
    if retailer and _retailer_blocked(retailer):
        return []
    try:
        response = _request(config["search_url"].format(query=quote(query)))
    except Exception as exc:
        if retailer and "HTTP Error 403" in str(exc):
            _mark_retailer_blocked(retailer)
        print(f"[{config['base_url']}] search failed for {query!r}: {exc}")
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    candidates = []
    seen = set()
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if config["link_pattern"] not in href:
            continue
        url = urljoin(config["base_url"], href)
        if url in seen or url.rstrip("/") == config["base_url"]:
            continue
        seen.add(url)
        candidates.append({"name": link.get_text(" ", strip=True), "url": url})
    return candidates[:20]


def _get_product(config, url):
    try:
        response = _request(url)
    except Exception as exc:
        if config.get("retailer") and "HTTP Error 403" in str(exc):
            _mark_retailer_blocked(config["retailer"])
        print(f"[{config['base_url']}] product request failed for {url}: {exc}")
        return None
    soup = BeautifulSoup(response.text, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        product = _from_json_ld(data, url, config["currency"])
        if product:
            return product
    return None


def _from_json_ld(data, url, default_currency):
    if isinstance(data, list):
        for item in data:
            product = _from_json_ld(item, url, default_currency)
            if product:
                return product
        return None
    if not isinstance(data, dict):
        return None
    if data.get("@type") != "Product":
        return None
    offers = data.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price = offers.get("price")
    if price is None:
        return None
    try:
        price = float(str(price).replace(",", ""))
    except ValueError:
        return None
    brand = data.get("brand")
    return {
        "source": None,
        "name": data.get("name"),
        "barcode": _valid_barcode(
            data.get("gtin13") or data.get("gtin") or data.get("mpn")
        ),
        "manufacturer": brand.get("name") if isinstance(brand, dict) else brand,
        "price": price,
        "currency": offers.get("priceCurrency") or default_currency,
        "item_condition": "New",
        "availability": str(offers.get("availability") or "").rsplit("/", 1)[-1] or None,
        "listing_url": offers.get("url") or url,
        "external_product_id": data.get("sku") or data.get("productID") or data.get("mpn"),
    }
