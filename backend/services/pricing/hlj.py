from rapidfuzz import fuzz
import json
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from itertools import combinations

BASE_URL = "https://www.hlj.com"


def get_hlj_product(product_url):
    response = requests.get(product_url, impersonate="chrome")

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

        return {
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

    return None


def find_hlj_product(figure):
    barcode = str(figure.get("barcode") or "").strip()
    name = (figure.get("name") or "").strip()
    manufacturer = (figure.get("manufacturer") or "").strip()

    # Best case: exact barcode match
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

    seen_skus = set()
    best_candidate = None
    best_score = 0

    for query in build_hlj_search_queries(figure):
        print(f"Searching HLJ for: {query!r}")

        candidates = search_hlj(query)

        for candidate in candidates:
            if candidate["sku"] in seen_skus:
                continue

            seen_skus.add(candidate["sku"])

            score = fuzz.token_set_ratio(
                name,
                candidate["name"],
            )

            if score > best_score:
                best_score = score
                best_candidate = candidate

            # Potential perfect match -- stop searching
            if score == 100:
                product = get_hlj_product(candidate["url"])

                if not product:
                    continue

                # If both sides have manufacturer info, sanity-check it
                product_manufacturer = (
                    product.get("manufacturer") or ""
                ).strip()

                if (
                    manufacturer
                    and product_manufacturer
                    and fuzz.ratio(
                        manufacturer.lower(),
                        product_manufacturer.lower(),
                    ) < 80
                ):
                    continue

                product["match_method"] = "name"
                product["match_score"] = score

                return product

    # No perfect match, use the best result we found
    if not best_candidate or best_score < 85:
        return None

    product = get_hlj_product(best_candidate["url"])

    if not product:
        return None

    product["match_method"] = "name"
    product["match_score"] = best_score

    return product


def search_hlj(query):
    response = requests.get(
        f"{BASE_URL}/search/",
        params={"Word": query},
        impersonate="chrome",
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

    return queries
