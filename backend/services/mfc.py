from mfc_api import MFCClient, CollectionStatus
from backend.services.helpers import normalize_mfc_item

#retrieves a figure from MFC by its ID and normalizes the data
def get_mfc_figure(mfc_id: int):
    with MFCClient() as client:
        item = client.get_item(mfc_id)
    return normalize_mfc_item(item)

#retrieves the collection of figures from a user in MFC
def get_owned_collection_ids(username: str):
    ids = []
    page = 1
    with MFCClient() as client:
        while True:
            collection = client.get_collection(username, status=CollectionStatus.OWNED, page=page)
            ids.extend([item.id for item in collection.items])
            page += 1
            if page > collection.pagination.total_pages:
                break
    return ids