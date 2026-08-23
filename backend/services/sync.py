from backend.services.mfc import get_owned_collection_ids, get_mfc_figure
from backend.db import upsert_figure, upsert_collection
from backend.services.enums import FigureStatus
from mfc_api import MFCClient
import time

def sync_owned_collection(username : str):
    with MFCClient() as client:
        collection_data = get_owned_collection_ids(client, username)
        owned_ids = collection_data["ids"]
        processed_ids = 0
        max_retries = 3  # Set the maximum number of retries
        for mfc_id in owned_ids:
            for attempt in range(max_retries):
                try:
                    figure = get_mfc_figure(client, mfc_id)
                    upsert_figure(**figure)
                    upsert_collection(mfc_id, FigureStatus.OWNED)
                    processed_ids += 1
                    time.sleep(.2)  # Sleep for 0.2 seconds to avoid hitting the rate limit
                    break  # Exit the retry loop if successful
                except Exception as e:
                    if "HTTP 429" in str(e) and attempt < max_retries - 1:  # Too Many Requests
                        wait_time = 2 ** (attempt + 1)  # Exponential backoff
                        print(
                                f"Rate limited on MFC ID {mfc_id}. "
                                f"Retrying in {wait_time} seconds..."
                            )
                        time.sleep(wait_time)
                    else:
                        raise  # Re-raise the exception for other HTTP errors
    return {"processed_ids": processed_ids,"visible_ids": len(owned_ids),"total_ids_found": collection_data["total_items_found"],"reported_owned_count": collection_data["reported_owned_count"]}