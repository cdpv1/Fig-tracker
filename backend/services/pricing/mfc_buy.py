import re
import time
import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from backend.services.mfc import create_mfc_client

BUY_URL = "https://myfigurecollection.net/item/{mfc_id}"
FORM = {"commit": "loadWindow", "window": "buyItem"}
XHR_HEADERS = {"X-Requested-With": "XMLHttpRequest"}

# Seconds to wait between requests. MFC is also your collection-sync source,
# so be polite: don't hammer it.
REQUEST_DELAY = 1.5
REQUEST_RETRIES = 2

_ROW_SPLIT = '<div class="stamp-anchor">'
_SHOP_RE = re.compile(r"<a[^>]*>([^<]+)</a>")
_STATUS_RE = re.compile(r'item-availability\s+(item-[a-z-]+)">([^<]+)')
_PRICE_RE = re.compile(r"<strong>([\d.,]+)</strong>\s*&nbsp;\s*(JPY|USD)")
_LINK_RE = re.compile(r'href="([^"]*?partnerId=\d+[^"]*)"')
_META_PRICE_RE = re.compile(
    r'<meta[^>]+itemprop=["\']price["\'][^>]+content=["\']([\d.,]+)["\']',
    re.IGNORECASE,
)
_META_CURRENCY_RE = re.compile(
    r'<meta[^>]+itemprop=["\']priceCurrency["\'][^>]+content=["\']([A-Z]{3})["\']',
    re.IGNORECASE,
)
_TEXT_PRICE_RE = re.compile(
    r"(?:JPY|USD|EUR|GBP|AUD|CAD|CNY|KRW|¥|\$|€|£)\s*([\d.,]+)"
    r"|([\d.,]+)\s*(JPY|USD|EUR|GBP|AUD|CAD|CNY|KRW)",
    re.IGNORECASE,
)

_client = None


def _session():
    global _client
    if _client is None:
        _client = create_mfc_client()
    return _client.transport._session


def get_buy_listings(mfc_id: int) -> list[dict]:
    """Partner buy listings for one MFC item. Each dict has
    shop, price (float), currency ("JPY"/"USD"), url, availability."""
    html = None
    for attempt in range(REQUEST_RETRIES + 1):
        try:
            time.sleep(REQUEST_DELAY if attempt == 0 else REQUEST_DELAY * attempt)
            resp = _session().post(
                BUY_URL.format(mfc_id=mfc_id),
                headers={
                    **XHR_HEADERS,
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Referer": BUY_URL.format(mfc_id=mfc_id),
                },
                data=FORM,
                timeout=(10, 30),
            )
            resp.raise_for_status()
            html = (resp.json().get("htmlValues") or {}).get("WINDOW") or ""
            break
        except Exception as e:
            if attempt == REQUEST_RETRIES:
                print(f"[mfc_buy] request failed for item {mfc_id}: {e}")
            else:
                print(f"[mfc_buy] request attempt {attempt + 1} failed for item {mfc_id}: {e}; retrying")

    if html is None:
        return []

    listings = []
    for row in html.split(_ROW_SPLIT)[1:]:
        listing = _parse_row(mfc_id, row)
        if listing:
            listings.append(listing)
    return listings


def _parse_row(mfc_id: int, row: str) -> dict | None:
    shop_m = _SHOP_RE.search(row)
    status_m = _STATUS_RE.search(row)
    price_m = _PRICE_RE.search(row)
    if not shop_m or not status_m:
        return None
    if status_m.group(2).split("|")[0].strip().lower() != "available":
        return None  # v1: skip "Maybe available" and anything else
    shop = shop_m.group(1).replace("(MFC Partner)", "").strip()
    link_m = _LINK_RE.search(row)
    url = (link_m.group(1).replace("&amp;", "&") if link_m
           else BUY_URL.format(mfc_id=mfc_id))

    currency = None
    if price_m:
        try:
            price = float(price_m.group(1).replace(",", ""))
        except ValueError:
            price = None
        else:
            currency = price_m.group(2)
    else:
        price, currency = _fetch_link_price(url)

    if price is None or currency is None:
        return None

    return {
        "shop": shop,
        "price": price,
        "currency": currency,
        "url": url,
        "availability": "in_stock",
    }


def _fetch_link_price(url: str) -> tuple[float | None, str | None]:
    """Resolve an MFC affiliate link and extract a shop page price."""
    try:
        time.sleep(REQUEST_DELAY)
        response = _session().get(
            urljoin(BUY_URL.format(mfc_id=0), url),
            timeout=20,
            allow_redirects=True,
        )
        response.raise_for_status()
    except Exception as e:
        print(f"[mfc_buy] linked listing request failed for {url}: {e}")
        return None, None

    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        price, currency = _price_from_json_ld(data)
        if price is not None and currency:
            return price, currency.upper()

    price_tag = soup.select_one('[itemprop="price"][content]')
    currency_tag = soup.select_one('[itemprop="priceCurrency"][content]')
    if price_tag and currency_tag:
        try:
            return float(price_tag["content"].replace(",", "")), currency_tag["content"].upper()
        except (KeyError, ValueError):
            pass

    price_m = _META_PRICE_RE.search(html)
    currency_m = _META_CURRENCY_RE.search(html)
    if price_m and currency_m:
        try:
            return float(price_m.group(1).replace(",", "")), currency_m.group(1).upper()
        except ValueError:
            pass

    text = soup.get_text(" ", strip=True)
    text_price_m = _TEXT_PRICE_RE.search(text)
    if not text_price_m:
        return None, None
    amount = text_price_m.group(1) or text_price_m.group(2)
    currency = text_price_m.group(3)
    if text_price_m.group(0).lstrip()[:1] in "$":
        currency = "USD"
    elif text_price_m.group(0).lstrip()[:1] == "¥":
        currency = "JPY"
    elif text_price_m.group(0).lstrip()[:1] == "€":
        currency = "EUR"
    elif text_price_m.group(0).lstrip()[:1] == "£":
        currency = "GBP"
    try:
        return float(amount.replace(",", "")), currency.upper()
    except (AttributeError, ValueError):
        return None, None


def _price_from_json_ld(data) -> tuple[float | None, str | None]:
    if isinstance(data, list):
        for item in data:
            price, currency = _price_from_json_ld(item)
            if price is not None and currency:
                return price, currency
        return None, None
    if not isinstance(data, dict):
        return None, None

    offers = data.get("offers")
    if isinstance(offers, list):
        offers = next((item for item in offers if isinstance(item, dict)), None)
    if not isinstance(offers, dict):
        return None, None

    price = offers.get("price")
    currency = offers.get("priceCurrency")
    if price is None or not currency:
        return None, None
    try:
        return float(str(price).replace(",", "")), str(currency)
    except ValueError:
        return None, None
