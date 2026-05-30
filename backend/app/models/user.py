"""
SmartRescue AI — User / Traveller Models
"""

from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class UserRegister(BaseModel):
    """Registration payload for traveller/user."""
    firebase_token: str = Field(..., description="Firebase ID token from client")
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., description="User email address")
    phone: Optional[str] = Field(None, max_length=15)
    role: str = Field(default="traveller", pattern="^(traveller|ambulance|hospital|admin)$")
    fcm_token: Optional[str] = Field(None, description="FCM device token for push notifications")

    class Config:
        json_schema_extra = {
            "example": {
                "firebase_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                "name": "Rahul Sharma",
                "email": "rahul@example.com",
                "phone": "+919876543210",
                "role": "traveller",
                "fcm_token": "dFjK8s7tRkG..."
            }
        }


class UserLogin(BaseModel):
    """Login payload — verify Firebase token, issue JWT."""
    firebase_token: str = Field(..., description="Firebase ID token")
    fcm_token: Optional[str] = Field(None, description="Updated FCM token")


class UserProfile(BaseModel):
    """User profile data (read model)."""
    uid: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    fcm_token: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_active: bool = True


class UserProfileUpdate(BaseModel):
    """Fields that can be updated on a user profile."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=15)
    fcm_token: Optional[str] = None


class EmergencyContactCreate(BaseModel):
    """Add an emergency contact."""
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    relationship: str = Field(..., min_length=2, max_length=50)
    email: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Priya Sharma",
                "phone": "+919876543211",
                "relationship": "Spouse",
                "email": "priya@example.com"
            }
        }


class EmergencyContactResponse(BaseModel):
    """Emergency contact read model."""
    id: str
    user_id: str
    name: str
    phone: str
    relationship: str
    email: Optional[str] = None


class SensorData(BaseModel):
    """Real-time sensor data from external simulator/device."""
    accelerometer_x: float = Field(..., description="Accelerometer X-axis (m/s²)")
    accelerometer_y: float = Field(..., description="Accelerometer Y-axis (m/s²)")
    accelerometer_z: float = Field(..., description="Accelerometer Z-axis (m/s²)")
    gyroscope_x: float = Field(..., description="Gyroscope X-axis (rad/s)")
    gyroscope_y: float = Field(..., description="Gyroscope Y-axis (rad/s)")
    gyroscope_z: float = Field(..., description="Gyroscope Z-axis (rad/s)")
    speed: float = Field(..., ge=0, description="Speed in km/h")
    heart_rate: Optional[float] = Field(None, ge=0, le=300, description="Heart rate BPM")
    orientation_x: Optional[float] = Field(None, description="Orientation pitch")
    orientation_y: Optional[float] = Field(None, description="Orientation roll")
    orientation_z: Optional[float] = Field(None, description="Orientation yaw")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: Optional[str] = Field(None, description="ISO timestamp from device")

    class Config:
        json_schema_extra = {
            "example": {
                "accelerometer_x": 0.5,
                "accelerometer_y": -9.8,
                "accelerometer_z": 0.3,
                "gyroscope_x": 0.01,
                "gyroscope_y": 0.02,
                "gyroscope_z": -0.01,
                "speed": 65.0,
                "heart_rate": 72.0,
                "orientation_x": 0.1,
                "orientation_y": 0.05,
                "orientation_z": -0.02,
                "latitude": 13.0827,
                "longitude": 80.2707,
                "timestamp": "2026-05-22T12:00:00Z"
            }
        }
