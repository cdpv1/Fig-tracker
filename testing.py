# from backend.services.mfc import create_mfc_client
# from backend.database.figures import get_figure_by_id
# from bs4 import BeautifulSoup

# client = create_mfc_client()
# session = client.transport._session  # the HTTP session with your MFC login cookies

# # find a figure that HAS a barcode (buy section only appears then)
# fig = get_figure_by_id("2057629")
# print(fig["name"], fig["barcode"])

# r = session.get(fig["mfc_url"])
# print(r.status_code)                 # want 200
# print("buy" in r.text.lower())       # want True

# soup = BeautifulSoup(open("mfc_item.html", encoding="utf-8").read(), "lxml")

# for h in soup.find_all(["h1", "h2", "h3"]):
#     print(h.name, "|", h.get_text(strip=True)[:60])

"""One-off test: fetch the ¥ Buy popup data the same way your browser does.
Run from the repo root:  python test_buy_xhr.py 2057629
"""
from backend.services.mfc import create_mfc_client
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


ITEM_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 2057629
URL = f"https://myfigurecollection.net/item/{ITEM_ID}"

# reuses your existing MFC login, nothing new to set up
client = create_mfc_client()
session = client.transport._session

resp = session.post(
    URL,
    headers={"X-Requested-With": "XMLHttpRequest"},
    data={"commit": "loadWindow", "window": "buyItem"},
)

resp.raise_for_status()

print("status:", resp.status_code, flush=True)
print("content-type:", resp.headers.get("content-type"), flush=True)
print("body starts with:", resp.text[:200], flush=True)

data = resp.json()
window_html = (data.get("htmlValues") or {}).get("WINDOW")
if not window_html:
    print("Unexpected response keys:", list(data.keys()))
    raise SystemExit(1)
html = window_html

# Each partner row starts at a stamp-anchor div: shop name, status, optional price.
rows = html.split('<div class="stamp-anchor">')[1:]

print(f"Partner rows found: {len(rows)}\n")

for row in rows:
    shop_m = re.search(r"<a[^>]*>([^<]+)</a>", row)
    status_m = re.search(r'item-availability\s+(item-[a-z-]+)">([^<]+)', row)
    price_m = re.search(r"<strong>([\d.,]+)</strong>\s*&nbsp;\s*(JPY|USD)", row)

    shop = shop_m.group(1).replace("(MFC Partner)", "").strip() if shop_m else "?"
    status = status_m.group(2).split("|")[0].strip() if status_m else "?"
    price = f"{price_m.group(1)} {price_m.group(2)}" if price_m else "(no price - skipped in v1)"

    print(f"{shop:28} {status:16} {price}")

