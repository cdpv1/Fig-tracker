from datetime import datetime, timezone
from threading import Lock


_LOCK = Lock()
_STATUS = {}


def mark_provider(name, status, error=None, retry_at=None):
    with _LOCK:
        _STATUS[name] = {
            "provider": name,
            "status": status,
            "error": str(error) if error else None,
            "retry_at": retry_at,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }


def get_provider_status():
    with _LOCK:
        return list(_STATUS.values())
