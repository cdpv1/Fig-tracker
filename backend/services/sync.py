from backend.services.mfc import get_owned_collection_ids, get_mfc_figure
from backend.db import upsert_figure, upsert_collection_status
from backend.services.enums import FigureStatus
from mfc_api import MFCClient
import time
import uuid


sync_jobs = {}


def sync_owned_collection(username: str, progress_callback=None):
    with MFCClient() as client:
        collection_data = get_owned_collection_ids(client, username)
        owned_ids = collection_data["ids"]
        processed_ids = 0
        max_retries = 3  # Set the maximum number of retries
        if progress_callback:
            progress_callback(
                processed=0,
                total=len(owned_ids),
                current_mfc_id=None,
            )
        for mfc_id in owned_ids:
            for attempt in range(max_retries):
                try:
                    figure = get_mfc_figure(client, mfc_id)
                    upsert_figure(**figure)
                    upsert_collection_status(mfc_id, FigureStatus.OWNED)
                    processed_ids += 1
                    if progress_callback:
                        progress_callback(
                            processed=processed_ids,
                            total=len(owned_ids),
                            current_mfc_id=mfc_id,
                        )
                    # Sleep for 0.2 seconds to avoid hitting the rate limit
                    time.sleep(1)
                    break  # Exit the retry loop if successful
                except Exception as e:
                    # Too Many Requests
                    if "HTTP 429" in str(e) and attempt < max_retries - 1:
                        wait_time = 2 ** (attempt + 1)  # Exponential backoff
                        print(
                            f"Rate limited on MFC ID {mfc_id}. "
                            f"Retrying in {wait_time} seconds..."
                        )
                        time.sleep(wait_time)
                    else:
                        raise  # Re-raise the exception for other HTTP errors
    return {"processed_ids": processed_ids, "visible_ids": len(owned_ids), "total_ids_found": collection_data["total_items_found"], "reported_owned_count": collection_data["reported_owned_count"]}


def run_sync_job(job_id: str, username: str):
    try:
        sync_jobs[job_id]["status"] = "running"

        def update_progress(processed, total, current_mfc_id):
            sync_jobs[job_id]["processed"] = processed
            sync_jobs[job_id]["total"] = total
            sync_jobs[job_id]["current_mfc_id"] = current_mfc_id

        result = sync_owned_collection(
            username,
            progress_callback=update_progress,
        )

        sync_jobs[job_id]["status"] = "completed"
        sync_jobs[job_id]["result"] = result

    except Exception as e:
        sync_jobs[job_id]["status"] = "failed"
        sync_jobs[job_id]["error"] = str(e)


def create_sync_job(username: str, background_tasks):
    job_id = str(uuid.uuid4())

    sync_jobs[job_id] = {
        "status": "queued",
        "processed": 0,
        "total": 0,
        "current_mfc_id": None,
        "error": None,
    }

    background_tasks.add_task(run_sync_job, job_id, username)

    return job_id


def get_sync_job(job_id: str):
    return sync_jobs.get(job_id)
