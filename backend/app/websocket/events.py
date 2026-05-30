"""
SmartRescue AI — WebSocket Event Types
"""

from enum import Enum


class WSEventType(str, Enum):
    LOCATION_UPDATE = "location_update"
    AMBULANCE_LOCATION = "ambulance_location"
    ACCIDENT_DETECTED = "accident_detected"
    CONFIRMATION_REQUESTED = "confirmation_requested"
    EMERGENCY_CONFIRMED = "emergency_confirmed"
    EMERGENCY_CANCELLED = "emergency_cancelled"
    FALSE_ALARM = "false_alarm"
    AMBULANCE_NOTIFIED = "ambulance_notified"
    AMBULANCE_ASSIGNED = "ambulance_assigned"
    AMBULANCE_REJECTED = "ambulance_rejected"
    AMBULANCE_REASSIGNED = "ambulance_reassigned"
    AMBULANCE_EN_ROUTE = "ambulance_en_route"
    AMBULANCE_ARRIVED = "ambulance_arrived"
    PATIENT_PICKED_UP = "patient_picked_up"
    PATIENT_UPDATE = "patient_update"
    HOSPITAL_NOTIFIED = "hospital_notified"
    HOSPITAL_PREPARING = "hospital_preparing"
    HOSPITAL_READY = "hospital_ready"
    ETA_UPDATE = "eta_update"
    CASE_STATUS_CHANGE = "case_status_change"
    CASE_RESOLVED = "case_resolved"
    HEARTBEAT = "heartbeat"
    CONNECTION_ACK = "connection_ack"
    ERROR = "error"


def build_ws_event(event_type: WSEventType, data: dict, case_id: str = None, actor_id: str = None) -> dict:
    from app.utils.helpers import utc_now
    event = {"event": event_type.value, "timestamp": utc_now(), "data": data}
    if case_id:
        event["case_id"] = case_id
    if actor_id:
        event["actor_id"] = actor_id
    return event
