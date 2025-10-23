from __future__ import annotations

import logging
from typing import Dict, Any

from celery import shared_task

from maps_view.realtime.publisher import broadcast_dashboard_status
from maps_view.views import get_hosts_status_data

logger = logging.getLogger(__name__)


@shared_task(queue="mapspro_default")
def broadcast_dashboard_snapshot() -> Dict[str, Any]:
    """
    Celery task that captures the current dashboard snapshot and pushes it to
    the realtime channel layer. Returns a small summary for logging/inspection.
    """
    try:
        snapshot = get_hosts_status_data()
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Failed to capture dashboard snapshot: %s", exc)
        return {"broadcasted": False, "error": str(exc)}

    if not snapshot:
        return {"broadcasted": False, "reason": "empty_snapshot"}

    broadcasted = broadcast_dashboard_status(snapshot)
    if not broadcasted:
        logger.debug("No channel layer configured; realtime broadcast skipped.")

    return {
        "broadcasted": broadcasted,
        "hosts_count": len(snapshot.get("hosts_status", [])),
    }
