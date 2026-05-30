"""
SmartRescue AI — Accident & Prediction Models
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Request payload for ML prediction endpoint."""
    accelerometer_x: float
    accelerometer_y: float
    accelerometer_z: float
    gyroscope_x: float
    gyroscope_y: float
    gyroscope_z: float
    speed: float = Field(..., ge=0)
    heart_rate: Optional[float] = Field(None, ge=0, le=300)
    orientation_x: Optional[float] = None
    orientation_y: Optional[float] = None
    orientation_z: Optional[float] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    class Config:
        json_schema_extra = {
            "example": {
                "accelerometer_x": 15.2,
                "accelerometer_y": -25.8,
                "accelerometer_z": 8.3,
                "gyroscope_x": 2.5,
                "gyroscope_y": -1.8,
                "gyroscope_z": 3.1,
                "speed": 85.0,
                "heart_rate": 120.0,
                "orientation_x": 0.5,
                "orientation_y": -0.3,
                "orientation_z": 0.1,
                "latitude": 13.0827,
                "longitude": 80.2707
            }
        }


class PredictionResponse(BaseModel):
    """Response from ML prediction endpoint."""
    prediction: int = Field(..., description="0=No Accident, 1=Minor, 2=Severe")
    prediction_label: str = Field(..., description="Human-readable label")
    confidence_score: float = Field(..., ge=0, le=1)
    emergency_status: str = Field(
        ..., 
        description="no_emergency | confirmation_needed | auto_triggered"
    )
    probabilities: Dict[str, float] = Field(
        ..., description="Class probabilities"
    )
    case_id: Optional[str] = Field(None, description="Generated case ID if emergency triggered")

    class Config:
        json_schema_extra = {
            "example": {
                "prediction": 2,
                "prediction_label": "Severe Accident",
                "confidence_score": 0.92,
                "emergency_status": "auto_triggered",
                "probabilities": {
                    "no_accident": 0.03,
                    "minor_accident": 0.05,
                    "severe_accident": 0.92
                },
                "case_id": "SR-20260522-A7K3M"
            }
        }


class AccidentEvent(BaseModel):
    """Full accident event record stored in Firestore."""
    id: Optional[str] = None
    user_id: str
    latitude: float
    longitude: float
    severity: int = Field(..., ge=0, le=2)
    prediction_confidence: float
    sensor_snapshot: Dict[str, Any]
    timestamp: str
    case_id: Optional[str] = None


class SensorStreamResponse(BaseModel):
    """Response for continuous sensor data processing."""
    received: bool = True
    prediction: Optional[int] = None
    confidence: Optional[float] = None
    buffer_status: str = Field(
        ...,
        description="buffering | monitoring | alert_pending | emergency_triggered"
    )
    consecutive_severe_count: int = 0
    message: str = ""
