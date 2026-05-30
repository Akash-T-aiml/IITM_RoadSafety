"""
SmartRescue AI — Common Pydantic Models
Shared types used across the application.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GPSCoordinates(BaseModel):
    """GPS location coordinates."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    accuracy: Optional[float] = Field(None, description="Accuracy in meters")


class APIResponse(BaseModel):
    """Standardized API response wrapper."""
    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None
    errors: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {},
                "errors": None,
            }
        }


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    order_by: Optional[str] = None
    order_direction: str = Field(default="DESCENDING", pattern="^(ASCENDING|DESCENDING)$")


class LocationUpdate(BaseModel):
    """Generic location update payload."""
    entity_id: str
    entity_type: str = Field(..., pattern="^(ambulance|traveller|hospital)$")
    coordinates: GPSCoordinates
    heading: Optional[float] = Field(None, ge=0, le=360, description="Heading in degrees")
    speed: Optional[float] = Field(None, ge=0, description="Speed in km/h")
