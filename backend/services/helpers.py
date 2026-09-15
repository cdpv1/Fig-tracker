from datetime import datetime
import json
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse


def _full_size_nsp_url(url):
    if not url or "commit=nsp" not in url:
        return url
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["size"] = "2"
    return urlunparse(parsed._replace(query=urlencode(query)))


def _image_urls_from_html(html):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    picture_metadata = soup.select_one("div.item-picture meta[name='pictures']")
    if not picture_metadata or not picture_metadata.get("content"):
        return []
    try:
        pictures = json.loads(unquote(picture_metadata["content"]))
    except json.JSONDecodeError:
        return []

    result = []
    for picture in pictures:
        url = picture.get("src") if isinstance(picture, dict) else None
        if not url:
            continue
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.hostname not in ("myfigurecollection.net", "static.myfigurecollection.net"):
            continue
        canonical = _full_size_nsp_url(url)
        if canonical not in result:
            result.append(canonical)
    return result

def normalize_mfc_item(item, image_urls=None):
    manufacturer = next(
        (
            company.name
            for company in item.companies
            if (company.role or "").strip().casefold() == "manufacturer"
        ),
        None,
    )
    if manufacturer is None and item.companies:
        manufacturer = item.companies[0].name
    if manufacturer is None:
        manufacturer = "Unknown"

    origin = (
        item.origins[0].name
        if item.origins
        else None
    )

    release = (
        item.releases[0]
        if item.releases
        else None
    )
    image_urls = image_urls or []
    picture_url = _full_size_nsp_url(
        image_urls[0] if image_urls else item.picture
    )
    return {
        "mfc_id": item.id,
        "name": item.name,
        "mfc_url": item.url,
        "picture_url": picture_url,
        "thumbnail_url": item.thumbnail,
        "gallery_urls": list(dict.fromkeys(
            url for url in image_urls[1:]
        )),
        "category": item.category_name,
        "scale": item.scale,
        "height_mm": item.height_mm,
        "origin": origin,
        "manufacturer": manufacturer,
        "release_date": normalize_date(release.date) if release else None,
        "barcode": release.barcode if release else None,
        "msrp": release.price if release else None,
        "currency": release.currency if release else None,
        "rating": item.rating,
    }
    
def normalize_date(date_str):
    if date_str is None:
        return None
    formats = [
        ("%m/%d/%Y", "%Y-%m-%d"),
        ("%m/%Y", "%Y-%m"),
    ]

    for input_format, output_format in formats:
        try:
            parsed_date = datetime.strptime(date_str, input_format)
            return parsed_date.strftime(output_format)
        except ValueError:
            continue

    return None