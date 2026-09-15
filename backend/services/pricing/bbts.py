import json
import re
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup
from curl_cffi import requests
from rapidfuzz import fuzz

BASE_URL = "https://www.bigbadtoystore.com"
SEARCH_URL = f"{BASE_URL}/Search?SearchText={{query}}"


def find_bbts_product(figure):
    barcode = str(figure.get("barcode") or "").strip()
    name = (figure.get("name") or "").strip()
    manufacturer = (figure.get("manufacturer") or "").strip()
    if not barcode and not name:
        return None

    queries = [barcode] if barcode else []
    if name:
        queries.append(name)
        queries.extend(
            part.strip()
            for part in re.split(r"\s+-\s+|[()~]", name)
            if len(part.strip()) >= 4
        )

    seen_urls = set()
    best_product = None
    best_score = 0
    for query in queries:
        print(f"[bbts] searching {query!r}")
        for candidate in search_bbts(query):
            if candidate["url"] in seen_urls:
                continue
            seen_urls.add(candidate["url"])
            product = get_bbts_product(candidate["url"])
            if not product:
                continue
            product_barcode = str(product.get("barcode") or "").strip()
            if barcode and product_barcode == barcode:
                product["match_method"] = "barcode"
                product["match_score"] = 100
                return product
            score = fuzz.token_set_ratio(name, product.get("name") or "")
            product_manufacturer = (product.get("manufacturer") or "").strip()
            if (
                score < 95
                and manufacturer
                and product_manufacturer
                and fuzz.ratio(manufacturer.lower(), product_manufacturer.lower()) < 80
            ):
                continue
            if score > best_score:
                best_score = score
                best_product = product
        if best_score >= 95:
            break

    if best_product and best_score >= 85:
        best_product["match_method"] = "name"
        best_product["match_score"] = best_score
        return best_product
    return None


def search_bbts(query):
    try:
        response = requests.get(
            SEARCH_URL.format(query=quote(query)),
            impersonate="chrome",
            timeout=20,
        )
        response.raise_for_status()
    except Exception as exc:
        print(f"[bbts] search failed for {query!r}: {exc}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    candidates = []
    seen = set()
    for link in soup.select('a[href^="/product/"]'):
        url = urljoin(BASE_URL, link.get("href", ""))
        if not url or url in seen:
            continue
        seen.add(url)
        candidates.append({"name": link.get_text(" ", strip=True), "url": url})
    return candidates


def get_bbts_product(url):
    try:
        response = requests.get(url, impersonate="chrome", timeout=20)
        response.raise_for_status()
    except Exception as exc:
        print(f"[bbts] product request failed for {url}: {exc}")
        return None
    return _parse_product(response.text, url)


def _parse_product(html, url):
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        product = _product_from_json_ld(data, url)
        if product:
            return product
    return None


def _product_from_json_ld(data, url):
    if isinstance(data, list):
        for item in data:
            product = _product_from_json_ld(item, url)
            if product:
                return product
        return None
    if not isinstance(data, dict) or data.get("@type") != "Product":
        return None
    offers = data.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price = offers.get("price")
    currency = offers.get("priceCurrency") or "USD"
    if price is None:
        return None
    try:
        price = float(str(price).replace(",", ""))
    except ValueError:
        return None
    availability = str(offers.get("availability") or "").rsplit("/", 1)[-1]
    return {
        "source": "BBTS",
        "name": data.get("name"),
        "barcode": data.get("gtin13") or data.get("gtin"),
        "manufacturer": (data.get("brand") or {}).get("name")
        if isinstance(data.get("brand"), dict) else data.get("brand"),
        "price": price,
        "currency": currency,
        "item_condition": "New",
        "availability": availability or None,
        "listing_url": offers.get("url") or url,
        "external_product_id": data.get("sku") or data.get("productID"),
    }
