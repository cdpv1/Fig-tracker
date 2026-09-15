import json
import re
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup
from curl_cffi import requests
from rapidfuzz import fuzz

BASE_URL = "https://www.amiami.com"
SEARCH_URL = f"{BASE_URL}/eng/search/list/?s_keywords={{query}}"
API_URL = "https://api.amiami.com/api/v1.0/items"
API_HEADERS = {"X-User-Key": "amiami_dev"}
MAX_SEARCH_QUERIES = 10


def find_amiami_product(figure):
    barcode = str(figure.get("barcode") or "").strip()
    name = (figure.get("name") or "").strip()
    manufacturer = (figure.get("manufacturer") or "").strip()

    candidates_by_url = {}
    if barcode:
        print(f"[amiami] searching barcode {barcode!r}")
        for candidate in search_amiami(barcode):
            candidates_by_url.setdefault(candidate["url"], candidate)
        for candidate in candidates_by_url.values():
            product = get_amiami_product(candidate["url"])
            if product and str(product.get("barcode") or "").strip() == barcode:
                product["match_method"] = "barcode"
                product["match_score"] = 100
                return product

    queries = []
    if name:
        queries.append(name)
        parts = [
            part.strip()
            for part in re.split(r"\s+-\s+|[()~]", name)
            if len(part.strip()) >= 4
        ]
        queries.extend(parts)
        if manufacturer:
            queries.extend(f"{part} {manufacturer}" for part in parts[:3])

    seen_queries = set()
    best_product = None
    best_score = 0
    for query in queries:
        query = re.sub(r"\s+", " ", query).strip()
        if not query or query in seen_queries:
            continue
        seen_queries.add(query)
        if len(seen_queries) > MAX_SEARCH_QUERIES:
            break
        print(f"[amiami] searching {query!r}")
        for candidate in search_amiami(query):
            candidates_by_url.setdefault(candidate["url"], candidate)

    for candidate in candidates_by_url.values():
        product = get_amiami_product(candidate["url"])
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
            score < 85
            or (
                score < 95
                and manufacturer
                and product_manufacturer
                and fuzz.ratio(
                    manufacturer.lower(), product_manufacturer.lower()
                ) < 80
            )
        ):
            continue
        if score > best_score:
            best_score = score
            best_product = product

    if best_product:
        best_product["match_method"] = "name"
        best_product["match_score"] = best_score
        return best_product
    return None


def search_amiami(query):
    try:
        response = requests.get(
            API_URL,
            headers=API_HEADERS,
            params={"pagemax": 20, "lang": "eng", "s_keywords": query},
            impersonate="chrome",
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        api_candidates = [
            _api_candidate(item)
            for item in (payload.get("items") or [])
            if item.get("gcode") and item.get("gname")
        ]
        if api_candidates:
            return api_candidates
    except Exception as exc:
        print(f"[amiami] API search failed for {query!r}: {exc}")

    # Older/site-rendered fallback.
    try:
        response = requests.get(
            SEARCH_URL.format(query=quote(query)),
            impersonate="chrome",
            timeout=20,
        )
        response.raise_for_status()
    except Exception as exc:
        print(f"[amiami] search failed for {query!r}: {exc}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    candidates = []
    seen = set()
    links = soup.select('a[href*="/eng/detail/"]')
    if not links:
        # The current AmiAmi frontend is client-rendered, but some responses
        # still contain product URLs in serialized state or preload markup.
        links = soup.find_all("a", href=re.compile(r"/eng/detail/"))
    for link in links:
        url = urljoin(BASE_URL, link.get("href", ""))
        if not url or url in seen:
            continue
        seen.add(url)
        candidates.append({"name": link.get_text(" ", strip=True), "url": url})
    if candidates:
        return candidates

    # Keep this fallback deliberately narrow: only accept AmiAmi detail URLs
    # and derive the visible name from the URL when the SPA provides no links.
    for raw_url in re.findall(r'https?://www\.amiami\.com/eng/detail/[^"\'<> ]+', response.text):
        url = raw_url.replace("\\u0026", "&")
        if url in seen:
            continue
        seen.add(url)
        candidates.append({"name": url.rsplit("/", 1)[-1], "url": url})
    return candidates


def _api_candidate(item):
    gcode = item["gcode"]
    return {
        "name": item["gname"],
        "url": f"{BASE_URL}/eng/detail/?gcode={quote(gcode)}",
        "api_item": item,
    }


def get_amiami_product(url):
    gcode = re.search(r"[?&]gcode=([^&]+)", url)
    if gcode:
        try:
            response = requests.get(
                API_URL,
                headers=API_HEADERS,
                params={"pagemax": 20, "lang": "eng", "s_keywords": gcode.group(1)},
                impersonate="chrome",
                timeout=20,
            )
            response.raise_for_status()
            for item in response.json().get("items") or []:
                if item.get("gcode") == gcode.group(1):
                    return _product_from_api_item(item, url)
        except Exception as exc:
            print(f"[amiami] API product request failed for {url}: {exc}")

    try:
        response = requests.get(url, impersonate="chrome", timeout=20)
        response.raise_for_status()
    except Exception as exc:
        print(f"[amiami] product request failed for {url}: {exc}")
        return None
    return _parse_product(response.text, url)


def _product_from_api_item(item, url):
    price = item.get("c_price_taxed") or item.get("min_price")
    if price is None:
        return None
    availability = "InStock" if item.get("instock_flg") else "OutOfStock"
    return {
        "source": "AMIAMI",
        "name": item.get("gname"),
        "barcode": item.get("jancode"),
        "manufacturer": item.get("maker_name"),
        "price": float(price),
        "currency": "JPY",
        "item_condition": "New",
        "availability": availability,
        "listing_url": url,
        "external_product_id": item.get("gcode"),
    }


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
    for tag in soup.select('[itemtype*="Product"]'):
        name = tag.select_one('[itemprop="name"]')
        price = tag.select_one('[itemprop="price"]')
        currency = tag.select_one('[itemprop="priceCurrency"]')
        if name and price and currency:
            try:
                return {
                    "source": "AMIAMI",
                    "name": name.get("content") or name.get_text(" ", strip=True),
                    "barcode": (
                        tag.select_one('[itemprop="gtin13"]')
                        or tag.select_one('[itemprop="gtin"]')
                    ).get("content"),
                    "manufacturer": None,
                    "price": float(
                        (price.get("content") or price.get_text()).replace(",", "")
                    ),
                    "currency": currency.get("content") or currency.get_text(strip=True),
                    "item_condition": "New",
                    "availability": "InStock",
                    "listing_url": url,
                    "external_product_id": None,
                }
            except (AttributeError, TypeError, ValueError):
                continue
    return None


def _product_from_json_ld(data, url):
    if isinstance(data, list):
        for item in data:
            product = _product_from_json_ld(item, url)
            if product:
                return product
        return None
    if not isinstance(data, dict):
        return None
    if data.get("@type") == "BreadcrumbList":
        return None
    if data.get("@type") == "WebPage" and isinstance(data.get("mainEntity"), dict):
        data = data["mainEntity"]
    if data.get("@type") != "Product":
        return None
    offers = data.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price = offers.get("price")
    currency = offers.get("priceCurrency")
    if price is None or not currency:
        return None
    try:
        price = float(str(price).replace(",", ""))
    except ValueError:
        return None
    availability = str(offers.get("availability") or "").rsplit("/", 1)[-1]
    return {
        "source": "AMIAMI",
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
