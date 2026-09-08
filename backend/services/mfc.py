import os
from mfc_api import MFCClient, CollectionStatus
from backend.services.helpers import normalize_mfc_item
from mfc_api.transport import Transport
from http.cookies import SimpleCookie
from backend.config import MFC_COOKIE_HEADER

# retrieves a figure from MFC by its ID and normalizes the data


def get_mfc_figure(client: MFCClient, mfc_id: int):
    item = client.get_item(mfc_id)
    return normalize_mfc_item(item)

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
