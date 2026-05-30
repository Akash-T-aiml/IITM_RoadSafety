"""
SmartRescue AI — Emergency Case Models
Full lifecycle model for an emergency case from detection to resolution.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EmergencyCaseStatus(str, Enum):
    """Status lifecycle of an emergency case."""
    DETECTED = "detected"
    CONFIRMATION_PENDING = "confirmation_pending"
    CONFIRMED = "confirmed"
    AMBULANCE_NOTIFIED = "ambulance_notified"
    AMBULANCE_ASSIGNED = "ambulance_assigned"
    AMBULANCE_EN_ROUTE = "ambulance_en_route"
    AMBULANCE_ARRIVED = "ambulance_arrived"
    PATIENT_PICKED_UP = "patient_picked_up"
    EN_ROUTE_HOSPITAL = "en_route_hospital"
    ARRIVED_HOSPITAL = "arrived_hospital"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"
    FALSE_ALARM = "false_alarm"


class TimelineEntry(BaseModel):
    """Single entry in emergency case timeline."""
    event: str
    timestamp: str
    actor_id: Optional[str] = None
    actor_role: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PatientUpdate(BaseModel):
    """Patient condition update from ambulance."""
    timestamp: str
    updated_by: str
    patient_condition: str
    oxygen_needed: bool = False
    blood_required: bool = False
    blood_type: Optional[str] = None
    icu_required: bool = False
    surgery_preparation_needed: bool = False
    consciousness_level: Optional[str] = None
    vital_signs: Optional[Dict[str, Any]] = None
    additional_notes: Optional[str] = None


class EmergencyCase(BaseModel):
    """
    Complete emergency case document.
    Represents the full lifecycle from accident detection to resolution.
    """
    case_id: str = Field(..., description="Unique case ID (SR-YYYYMMDD-XXXXX)")
    accident_id: str
    user_id: str
    user_name: Optional[str] = None
    user_phone: Optional[str] = None

    # Assignment
    ambulance_id: Optional[str] = None
    ambulance_vehicle: Optional[str] = None
    hospital_id: Optional[str] = None
    hospital_name: Optional[str] = None

    # Case details
    status: EmergencyCaseStatus = EmergencyCaseStatus.DETECTED
    severity: int = Field(..., ge=0, le=2)
    severity_label: str = ""
    confidence_score: float = 0.0

    # Location
    accident_latitude: float = 0.0
    accident_longitude: float = 0.0
    
    # ETA
    estimated_arrival_minutes: Optional[float] = None

    # Updates
    timeline: List[TimelineEntry] = Field(default_factory=list)
    patient_updates: List[PatientUpdate] = Field(default_factory=list)

    # Hospital preparation
    hospital_preparation: Optional[Dict[str, Any]] = None

    # Timestamps
    detected_at: str = ""
    confirmed_at: Optional[str] = None
    ambulance_dispatched_at: Optional[str] = None
    ambulance_arrived_at: Optional[str] = None
    resolved_at: Optional[str] = None

    # Metadata
    response_time_minutes: Optional[float] = None
    total_duration_minutes: Optional[float] = None
    auto_triggered: bool = False
    reassignment_count: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "case_id": "SR-20260522-A7K3M",
                "accident_id": "ACC-20260522120000-AB12",
                "user_id": "firebase-uid-123",
                "user_name": "Rahul Sharma",
                "status": "ambulance_en_route",
                "severity": 2,
                "severity_label": "Severe Accident",
                "confidence_score": 0.92,
                "accident_latitude": 13.0827,
                "accident_longitude": 80.2707,
                "ambulance_id": "amb-456",
                "hospital_id": "hosp-789",
                "estimated_arrival_minutes": 8.5,
                "auto_triggered": True,
            }
        }


class EmergencyConfirmation(BaseModel):
    """User confirmation/denial of detected emergency."""
    confirmed: bool = Field(..., description="True to confirm, False to cancel")
    case_id: str
