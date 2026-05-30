"""
SmartRescue AI — Authentication API Routes
Contains register, login, and verify token endpoints.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body

from app.services.auth_service import AuthService
from app.auth.rbac import get_current_user
from app.models.common import APIResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=APIResponse)
async def register(payload: Dict[str, Any] = Body(...)):
    """
    Register a new user in the SmartRescue ecosystem.
    Supports Traveller, Ambulance Driver, and Hospital Admin.
    
    Fields required based on role:
    - role = 'traveller': name, email, firebase_token
    - role = 'ambulance': name, email, firebase_token, vehicle_number, government_id, phone
    - role = 'hospital': name, email, firebase_token, hospital_name, latitude, longitude, phone, total_beds, icu_beds
    """
    firebase_token = payload.get("firebase_token")
    role = payload.get("role", "traveller")
    name = payload.get("name")
    email = payload.get("email")
    phone = payload.get("phone")
    fcm_token = payload.get("fcm_token")

    if not firebase_token or not name or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required registration fields (firebase_token, name, email)"
        )

    # Clean and bundle extra role-specific data
    extra_data = {}
    if role == "ambulance":
        extra_data = {
            "vehicle_number": payload.get("vehicle_number"),
            "government_id": payload.get("government_id"),
            "hospital_affiliation": payload.get("hospital_affiliation")
        }
        if not extra_data["vehicle_number"] or not extra_data["government_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="vehicle_number and government_id are required for ambulance role"
            )
    elif role == "hospital":
        extra_data = {
            "hospital_name": payload.get("hospital_name") or name,
            "latitude": float(payload.get("latitude", 0)),
            "longitude": float(payload.get("longitude", 0)),
            "address": payload.get("address"),
            "trauma_care_available": bool(payload.get("trauma_care_available", True)),
            "total_beds": int(payload.get("total_beds", 0)),
            "icu_beds": int(payload.get("icu_beds", 0)),
            "available_beds": int(payload.get("available_beds", 0)),
            "specializations": payload.get("specializations", [])
        }
        if extra_data["latitude"] == 0 or extra_data["longitude"] == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="valid latitude and longitude coordinates are required for hospital role"
            )

    result = await AuthService.register_user(
        firebase_token=firebase_token,
        name=name,
        email=email,
        phone=phone,
        role=role,
        fcm_token=fcm_token,
        extra_data=extra_data
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    return APIResponse(
        success=True,
        message=result["message"],
        data=result["data"]
    )


@router.post("/login", response_model=APIResponse)
async def login(
    firebase_token: str = Body(..., embed=True),
    fcm_token: Optional[str] = Body(None, embed=True)
):
    """
    Login using a Firebase ID token.
    Validates token and returns internal JWT token for Role-based routing.
    """
    result = await AuthService.login_user(firebase_token, fcm_token)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"]
        )

    return APIResponse(
        success=True,
        message=result["message"],
        data=result["data"]
    )


@router.get("/verify-token", response_model=APIResponse)
async def verify_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Validate the internal JWT token.
    Returns current user info and verified status.
    """
    profile = await AuthService.get_profile(current_user["uid"])
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return APIResponse(
        success=True,
        message="Token is valid",
        data={
            "uid": current_user["uid"],
            "name": profile.get("name"),
            "email": profile.get("email"),
            "role": profile.get("role"),
            "verified": profile.get("verified", True)
        }
    )
