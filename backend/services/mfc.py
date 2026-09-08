from mfc_api import MFCClient, CollectionStatus
from backend.services.helpers import normalize_mfc_item

#retrieves a figure from MFC by its ID and normalizes the data
def get_mfc_figure(client: MFCClient, mfc_id: int):
    item = client.get_item(mfc_id)
    return normalize_mfc_item(item)

#retrieves the collection of figures from a user in MFC
def get_owned_collection_ids(client: MFCClient, username: str):
    ids = []
    page = 1
    while True:
        collection = client.get_collection(username, status=CollectionStatus.OWNED, page=page)
        ids.extend([item.id for item in collection.items])
        page += 1
        if page > collection.pagination.total_pages:
            break 
    return {"ids": ids,"reported_owned_count": collection.stats.owned,"total_items_found": collection.pagination.total_items}

import os

from mfc_api import MFCClient
from mfc_api.transport import Transport


def create_mfc_client():
    cookie_header = os.getenv("MFC_COOKIE_HEADER")

    transport = Transport(
        cache_ttl=0,
    )

    if cookie_header:
        transport._session.headers.update({
            "Cookie": cookie_header,
        })

    return MFCClient(transport=transport)