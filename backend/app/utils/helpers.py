"""
SmartRescue AI — Miscellaneous Helpers
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def utc_now() -> str:
    """Get current UTC time as ISO format string."""
    return datetime.now(timezone.utc).isoformat()


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from a dictionary."""
    return {k: v for k, v in data.items() if v is not None}


def format_timestamp(dt: datetime) -> str:
    """Format a datetime to a human-readable string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def severity_label(prediction: int) -> str:
    """Convert prediction integer to severity label."""
    labels = {
        0: "No Accident",
        1: "Minor Accident",
        2: "Severe Accident",
    }
    return labels.get(prediction, "Unknown")


def build_timeline_entry(
    event: str,
    actor_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a standardized timeline entry for emergency cases."""
    return {
        "event": event,
        "timestamp": utc_now(),
        "actor_id": actor_id,
        "actor_role": actor_role,
        "details": details or {},
    }


def calculate_response_time_minutes(start_iso: str, end_iso: str) -> float:
    """Calculate time difference in minutes between two ISO timestamps."""
    try:
        start = datetime.fromisoformat(start_iso)
        end = datetime.fromisoformat(end_iso)
        delta = (end - start).total_seconds()
        return round(delta / 60, 2)
    except Exception:
        return 0.0
