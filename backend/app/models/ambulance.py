"""
SmartRescue AI — Ambulance Models
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class AmbulanceRegister(BaseModel):
    """Ambulance driver registration payload."""
    firebase_token: str = Field(..., description="Firebase ID token")
    driver_name: str = Field(..., min_length=2, max_length=100)
    vehicle_number: str = Field(..., min_length=4, max_length=20, description="Vehicle registration number")
    phone: str = Field(..., min_length=10, max_length=15)
    government_id: str = Field(..., min_length=5, max_length=30, description="Government-issued ID number")
    email: str = Field(..., description="Driver email")
    hospital_affiliation: Optional[str] = Field(None, description="Affiliated hospital name or ID")
    fcm_token: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "firebase_token": "eyJhbGciOiJSUzI1NiIs...",
                "driver_name": "Suresh Kumar",
                "vehicle_number": "TN-01-AB-1234",
                "phone": "+919876543212",
                "government_id": "ABCDE1234F",
                "email": "suresh@ambulance.com",
                "hospital_affiliation": "Apollo Hospital Chennai",
                "fcm_token": "dFjK8s7tRkG..."
            }
        }


class AmbulanceProfile(BaseModel):
    """Ambulance profile read model."""
    id: str
    driver_name: str
    vehicle_number: str
    phone: str
    government_id: str
    email: str
    hospital_affiliation: Optional[str] = None
    verified: bool = False
    available: bool = False
    active_case_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fcm_token: Optional[str] = None
    created_at: Optional[str] = None


class AmbulanceLocation(BaseModel):
    """Ambulance GPS location update."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    heading: Optional[float] = Field(None, ge=0, le=360)
    speed: Optional[float] = Field(None, ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 13.0827,
                "longitude": 80.2707,
                "heading": 45.0,
                "speed": 55.0
            }
        }


class PatientStatusUpdate(BaseModel):
    """Updates from ambulance nurse/paramedic about patient condition."""
    patient_condition: str = Field(..., description="Current patient condition description")
    oxygen_needed: bool = Field(default=False)
    blood_required: bool = Field(default=False)
    blood_type: Optional[str] = Field(None, pattern="^(A|B|AB|O)[+-]$")
    icu_required: bool = Field(default=False)
    surgery_preparation_needed: bool = Field(default=False)
    consciousness_level: Optional[str] = Field(
        None,
        pattern="^(conscious|semi-conscious|unconscious)$"
    )
    vital_signs: Optional[dict] = Field(None, description="BP, pulse, SpO2, etc.")
    additional_notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "patient_condition": "Multiple fractures, internal bleeding suspected",
                "oxygen_needed": True,
                "blood_required": True,
                "blood_type": "O+",
                "icu_required": True,
                "surgery_preparation_needed": True,
                "consciousness_level": "semi-conscious",
                "vital_signs": {
                    "blood_pressure": "90/60",
                    "pulse": 110,
                    "spo2": 88
                },
                "additional_notes": "Patient requires immediate trauma surgery"
            }
        }


class AmbulanceAcceptCase(BaseModel):
    """Ambulance acceptance of an emergency case."""
    estimated_arrival_minutes: Optional[float] = Field(
        None, ge=0, description="Driver-estimated arrival time"
    )
