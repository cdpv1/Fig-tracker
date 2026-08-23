from backend.services.mfc import get_owned_collection_ids, get_mfc_figure
from backend.db import upsert_figure

def sync_owned_collection(username : str):
    owned_ids = get_owned_collection_ids(username)
    for mfc_id in owned_ids:
        figure = get_mfc_figure(mfc_id)
        upsert_figure(figure)