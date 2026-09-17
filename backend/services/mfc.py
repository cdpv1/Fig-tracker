import os
import hashlib
import json
import uuid
from mfc_api import MFCClient, CollectionStatus
from mfc_api.parsers.item import ItemParser
from mfc_api.urls import item as item_url
from backend.services.helpers import normalize_mfc_item, _image_urls_from_html
from mfc_api.transport import Transport
from http.cookies import SimpleCookie
from backend.config import MFC_COOKIE_HEADER
from backend.config import BASE_DIR


IMAGE_CACHE_DIR = BASE_DIR / "data" / "image-cache"


# retrieves a figure from MFC by its ID and normalizes the data


def get_mfc_figure(client: MFCClient, mfc_id: int):
    url = item_url(mfc_id)
    html = client.transport.get(url)
    item = ItemParser(html, url=url).parse()
    # The page metadata can contain the full-size image even when the visible
    # item-picture element is replaced by MFC's NSFW placeholder.
    image_urls = _image_urls_from_html(html)
    return normalize_mfc_item(item, image_urls=image_urls)


def fetch_mfc_image(url: str):
    transport = Transport(cache_ttl=0)
    try:
        if MFC_COOKIE_HEADER:
            add_mfc_cookies(transport._session, MFC_COOKIE_HEADER)
        response = transport._session.get(url, timeout=30)
        response.raise_for_status()
        return response.content, response.headers.get("content-type", "image/jpeg")
    finally:
        transport.close()


def fetch_cached_mfc_image(url: str):
    """Fetch an MFC image once and retain the full-resolution response on disk."""
    IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    image_path = IMAGE_CACHE_DIR / f"{cache_key}.image"
    metadata_path = IMAGE_CACHE_DIR / f"{cache_key}.json"

    try:
        content = image_path.read_bytes()
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        content_type = metadata.get("content_type")
        if not content_type:
            raise ValueError("Cached image metadata is missing content type.")
        return content, content_type
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
        content, content_type = fetch_mfc_image(url)

    temporary_suffix = f".tmp.{uuid.uuid4().hex}"
    temporary_image_path = image_path.with_name(image_path.name + temporary_suffix)
    temporary_metadata_path = metadata_path.with_name(metadata_path.name + temporary_suffix)
    try:
        temporary_image_path.write_bytes(content)
        temporary_metadata_path.write_text(
            json.dumps({"content_type": content_type}),
            encoding="utf-8",
        )
        os.replace(temporary_image_path, image_path)
        os.replace(temporary_metadata_path, metadata_path)
    except OSError:
        for temporary_path in (temporary_image_path, temporary_metadata_path):
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
        raise

    return content, content_type

# retrieves the collection of figures from a user in MFC


def get_owned_collection_ids(client: MFCClient, username: str):
    ids = []
    page = 1
    while True:
        collection = client.get_collection(
            username, status=CollectionStatus.OWNED, page=page)
        ids.extend([item.id for item in collection.items])
        page += 1
        if page > collection.pagination.total_pages:
            break
    return {"ids": ids, "reported_owned_count": collection.stats.owned, "total_items_found": collection.pagination.total_items}

# creates an MFCClient instance with the cookie header from the environment variable
# MFC Transport does not currently expose its session publicly.
# Access the internal session so authenticated MFC cookies can be added.


def create_mfc_client():
    transport = Transport(cache_ttl=0)

    if MFC_COOKIE_HEADER:
        add_mfc_cookies(
            transport._session,
            MFC_COOKIE_HEADER,
        )

    return MFCClient(transport=transport)


def add_mfc_cookies(session, cookie_header):
    parsed_cookies = SimpleCookie()
    parsed_cookies.load(cookie_header)

    for name, morsel in parsed_cookies.items():
        session.cookies.set(
            name,
            morsel.value,
            domain=".myfigurecollection.net",
            path="/",
        )
