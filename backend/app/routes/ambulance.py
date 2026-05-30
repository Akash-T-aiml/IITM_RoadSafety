"""
SmartRescue AI — Ambulance API Routes
Handles nearby incident lookups, location streams, patient condition logging, and accepts/rejects.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body

from app.auth.rbac import RoleChecker, Role
from app.models.common import APIResponse
from app.models.ambulance import AmbulanceLocation, PatientStatusUpdate, AmbulanceAcceptCase
from app.services.ambulance_service import AmbulanceService
from app.services.location_service import LocationService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ambulance", tags=["Ambulance"])


@router.get("/nearby-cases", response_model=APIResponse)
async def get_nearby_cases(
    radius_km: float = 50.0,
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.AMBULANCE]))
):
    """
    Get active emergency cases within a given radius based on the ambulance's last known GPS location.
    """
    ambulance_id = current_user["uid"]
    cases = await AmbulanceService.get_nearby_cases(ambulance_id, radius_km)
    
    return APIResponse(
        success=True,
        message="Nearby cases retrieved",
        data=cases
    )


@router.post("/accept-case/{case_id}", response_model=APIResponse)
async def accept_case(
    case_id: str,
    payload: Optional[AmbulanceAcceptCase] = None,
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.AMBULANCE]))
):
    """
    Accept an emergency dispatch case. Marks ambulance as en-route and locks status.
    """
    ambulance_id = current_user["uid"]
    eta = payload.estimated_arrival_minutes if payload else None
    
    result = await AmbulanceService.accept_case(ambulance_id, case_id, eta)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
        
    return APIResponse(success=True, message=result["message"])


@router.post("/reject-case/{case_id}", response_model=APIResponse)
async def reject_case(
    case_id: str,
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.AMBULANCE]))
):
    """
    Reject an emergency dispatch case. Immediately triggers automatic reassignment to the next closest driver.
    """
    ambulance_id = current_user["uid"]
    result = await AmbulanceService.reject_case(ambulance_id, case_id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
        
    return APIResponse(success=True, message=result["message"])


@router.post("/update-location", response_model=APIResponse)
async def update_location(
    payload: AmbulanceLocation,
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.AMBULANCE]))
):
    """
    Stream real-time GPS location coordinates of the ambulance.
    Updates Firestore live_locations and broadcasts position to hospital and traveller websocket subscribers.
    """
    ambulance_id = current_user["uid"]
    loc_dict = payload.model_dump()
    
    success = await LocationService.update_location(
        entity_type="ambulance",
        entity_id=ambulance_id,
        latitude=loc_dict["latitude"],
        longitude=loc_dict["longitude"],
        heading=loc_dict.get("heading"),
        speed=loc_dict.get("speed")
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update ambulance location coordinates"
        )
        
    return APIResponse(success=True, message="Location updated successfully")


@router.post("/update-patient-status/{case_id}", response_model=APIResponse)
async def update_patient_status(
    case_id: str,
    payload: PatientStatusUpdate,
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.AMBULANCE]))
):
    """
    Log and stream live patient vital updates and diagnostics from inside the ambulance.
    This notifies the hospital so surgeons, blood banks, and ICU prep can begin before arrival.
    """
    ambulance_id = current_user["uid"]
    updates = payload.model_dump()
    
    success = await AmbulanceService.update_patient_status(ambulance_id, case_id, updates)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update patient conditions. Check case ID."
        )
        
    return APIResponse(success=True, message="Patient status updated and hospital notified")
