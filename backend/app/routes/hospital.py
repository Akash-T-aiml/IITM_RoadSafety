"""
SmartRescue AI — Hospital API Routes
Handles incoming emergency tracking, pre-arrival preparation, resource logs, and hospital dashboard.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.rbac import RoleChecker, Role
from app.models.common import APIResponse
from app.models.hospital import BedStatusUpdate, CasePreparation
from app.services.hospital_service import HospitalService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/hospital", tags=["Hospital"])


@router.get("/incoming-cases", response_model=APIResponse)
async def get_incoming_cases(
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.HOSPITAL]))
):
    """
    Get all active incoming emergency cases assigned to or nearby this hospital.
    """
    hospital_id = current_user["uid"]
    cases = await HospitalService.get_incoming_cases(hospital_id)
    
    return APIResponse(
        success=True,
        message="Incoming cases retrieved successfully",
        data=cases
    )


@router.post("/prepare-case/{case_id}", response_model=APIResponse)
async def prepare_case(
    case_id: str,
    payload: CasePreparation,
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.HOSPITAL]))
):
    """
    Initiate pre-arrival resources (trauma team, ICU beds, oxygen, surgery prep) for an incoming case.
    """
    hospital_id = current_user["uid"]
    prep_dict = payload.model_dump()
    
    success = await HospitalService.prepare_case(hospital_id, case_id, prep_dict)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to submit preparation data. Check case ID."
        )
        
    return APIResponse(
        success=True,
        message="Hospital preparation details updated and broadcasted"
    )


@router.post("/update-bed-status", response_model=APIResponse)
async def update_bed_status(
    payload: BedStatusUpdate,
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.HOSPITAL]))
):
    """
    Update live ICU beds, ventilator status, oxygen, and blood availability parameters.
    """
    hospital_id = current_user["uid"]
    bed_dict = payload.model_dump()
    
    success = await HospitalService.update_bed_status(hospital_id, bed_dict)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update hospital resources"
        )
        
    return APIResponse(
        success=True,
        message="Hospital bed and resource parameters updated successfully"
    )


@router.get("/dashboard", response_model=APIResponse)
async def get_hospital_dashboard(
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.HOSPITAL]))
):
    """
    Aggregate all critical monitoring feeds (live incoming ETAs, paramedic updates, trauma capacity)
    into a unified hospital response dashboard.
    """
    hospital_id = current_user["uid"]
    dashboard_data = await HospitalService.get_dashboard(hospital_id)
    
    return APIResponse(
        success=True,
        message="Hospital dashboard feed compiled successfully",
        data=dashboard_data
    )
