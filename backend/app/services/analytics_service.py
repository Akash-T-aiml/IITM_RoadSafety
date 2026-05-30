"""
SmartRescue AI — Analytics & Monitoring Service
Aggregates accident data, audit trails, response times, and active emergencies.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from app.firebase.firestore_db import FirestoreDB
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AnalyticsService:

    @staticmethod
    async def get_accident_analytics(timeframe_days: int = 30) -> Dict[str, Any]:
        """
        Aggregate analytical accident trends, severity distributions, response times,
        and success rates over a specified timeframe.
        """
        now = datetime.now(timezone.utc)
        cutoff_date = (now - timedelta(days=timeframe_days)).isoformat()

        # Query all cases
        cases = await FirestoreDB.query_collection(FirestoreDB.EMERGENCY_CASES)

        total_cases = 0
        resolved_count = 0
        cancelled_count = 0
        false_alarms = 0
        severe_count = 0
        minor_count = 0
        response_times = []
        total_durations = []

        for case in cases:
            # Timeframe filter (detected_at is stored as ISO format string)
            det_at = case.get("detected_at", "")
            if det_at < cutoff_date:
                continue

            total_cases += 1
            
            # Severity counts
            sev = case.get("severity", 2)
            if sev == 2:
                severe_count += 1
            elif sev == 1:
                minor_count += 1

            # Status breakdown
            status = case.get("status")
            if status == "resolved":
                resolved_count += 1
            elif status == "cancelled":
                cancelled_count += 1
            elif status == "false_alarm":
                false_alarms += 1

            # Response time analytics (detected to ambulance arrived)
            det_iso = case.get("detected_at")
            arr_iso = case.get("ambulance_arrived_at")
            res_iso = case.get("resolved_at")

            if det_iso and arr_iso:
                try:
                    t_det = datetime.fromisoformat(det_iso)
                    t_arr = datetime.fromisoformat(arr_iso)
                    diff = (t_arr - t_det).total_seconds() / 60.0
                    response_times.append(diff)
                except Exception:
                    pass

            if det_iso and res_iso:
                try:
                    t_det = datetime.fromisoformat(det_iso)
                    t_res = datetime.fromisoformat(res_iso)
                    diff = (t_res - t_det).total_seconds() / 60.0
                    total_durations.append(diff)
                except Exception:
                    pass

        # Calculate averages
        avg_resp = round(sum(response_times) / len(response_times), 1) if response_times else 0.0
        avg_dur = round(sum(total_durations) / len(total_durations), 1) if total_durations else 0.0

        # Success rate (resolved cases vs total real accidents)
        real_accidents = total_cases - false_alarms
        success_rate = round(resolved_count / real_accidents * 100, 1) if real_accidents > 0 else 100.0

        return {
            "timeframe_days": timeframe_days,
            "total_incidents": total_cases,
            "resolved_count": resolved_count,
            "cancelled_count": cancelled_count,
            "false_alarms": false_alarms,
            "active_count": total_cases - resolved_count - cancelled_count - false_alarms,
            "severity_distribution": {
                "severe": severe_count,
                "minor": minor_count,
                "no_accident_false_alarm": false_alarms
            },
            "performance_metrics": {
                "average_ambulance_response_time_minutes": avg_resp,
                "average_incident_resolution_time_minutes": avg_dur,
                "response_time_samples": len(response_times),
                "resolution_success_rate_percentage": success_rate
            }
        }

    @staticmethod
    async def get_active_emergencies() -> List[Dict[str, Any]]:
        """Retrieve all active emergencies in progress for the admin dashboard monitoring."""
        return await FirestoreDB.query_collection(
            FirestoreDB.EMERGENCY_CASES,
            filters=[("status", "not-in", ["resolved", "cancelled", "false_alarm"])]
        )

    @staticmethod
    async def get_audit_log(limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve chronological history of auditable system actions."""
        return await FirestoreDB.query_collection(
            FirestoreDB.AUDIT_LOG,
            order_by="timestamp",
            order_direction="DESCENDING",
            limit=limit
        )
