"""
SmartRescue AI — Hospital Models
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class HospitalRegister(BaseModel):
    """Hospital registration payload."""
    firebase_token: str = Field(..., description="Firebase ID token")
    hospital_name: str = Field(..., min_length=2, max_length=200)
    email: str = Field(..., description="Hospital admin email")
    phone: str = Field(..., min_length=10, max_length=15, description="Emergency contact number")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = Field(None, max_length=500)
    trauma_care_available: bool = Field(default=False)
    icu_beds: int = Field(default=0, ge=0)
    total_beds: int = Field(default=0, ge=0)
    available_beds: int = Field(default=0, ge=0)
    specializations: Optional[List[str]] = Field(default=None, description="List of specializations")
    fcm_token: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "firebase_token": "eyJhbGciOiJSUzI1NiIs...",
                "hospital_name": "Apollo Trauma Centre",
                "email": "admin@apollotrauma.com",
                "phone": "+914428290200",
                "latitude": 13.0604,
                "longitude": 80.2496,
                "address": "21, Greams Road, Chennai, Tamil Nadu 600006",
                "trauma_care_available": True,
                "icu_beds": 20,
                "total_beds": 200,
                "available_beds": 45,
                "specializations": ["Trauma Surgery", "Neurosurgery", "Orthopedics"],
                "fcm_token": "dFjK8s7tRkG..."
            }
        }


class HospitalProfile(BaseModel):
    """Hospital profile read model."""
    id: str
    hospital_name: str
    email: str
    phone: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    trauma_care_available: bool = False
    icu_beds: int = 0
    total_beds: int = 0
    available_beds: int = 0
    specializations: Optional[List[str]] = None
    verified: bool = False
    fcm_token: Optional[str] = None
    created_at: Optional[str] = None


class BedStatusUpdate(BaseModel):
    """Update hospital bed/resource availability."""
    total_beds: Optional[int] = Field(None, ge=0)
    available_beds: Optional[int] = Field(None, ge=0)
    icu_beds: Optional[int] = Field(None, ge=0)
    icu_available: Optional[int] = Field(None, ge=0)
    ventilators_available: Optional[int] = Field(None, ge=0)
    oxygen_available: bool = True
    blood_bank_available: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "total_beds": 200,
                "available_beds": 42,
                "icu_beds": 20,
                "icu_available": 5,
                "ventilators_available": 8,
                "oxygen_available": True,
                "blood_bank_available": True
            }
        }


class CasePreparation(BaseModel):
    """Hospital preparation actions for an incoming emergency."""
    bed_allocated: bool = Field(default=False)
    icu_allocated: bool = Field(default=False)
    surgery_team_standby: bool = Field(default=False)
    blood_arranged: bool = Field(default=False)
    blood_type: Optional[str] = Field(None, pattern="^(A|B|AB|O)[+-]$")
    oxygen_ready: bool = Field(default=False)
    trauma_team_alerted: bool = Field(default=False)
    equipment_prepared: Optional[List[str]] = Field(
        default=None,
        description="List of equipment prepared"
    )
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "bed_allocated": True,
                "icu_allocated": True,
                "surgery_team_standby": True,
                "blood_arranged": True,
                "blood_type": "O+",
                "oxygen_ready": True,
                "trauma_team_alerted": True,
                "equipment_prepared": ["Ventilator", "Defibrillator", "Surgical Kit"],
                "notes": "OR-3 prepared for emergency trauma surgery"
            }
        }


class HospitalDashboardFilters(BaseModel):
    """Filters for hospital dashboard API."""
    status: Optional[str] = Field(None, pattern="^(active|resolved|all)$")
    severity: Optional[int] = Field(None, ge=0, le=2)
    limit: int = Field(default=20, ge=1, le=100)
