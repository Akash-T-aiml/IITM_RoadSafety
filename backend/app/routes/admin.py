"""
SmartRescue AI — Admin API Routes
Handles service approvals, system audit logs, live analytics, and overall emergency monitoring.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.auth.rbac import RoleChecker, Role
from app.models.common import APIResponse
from app.firebase.firestore_db import FirestoreDB
from app.services.analytics_service import AnalyticsService
from app.utils.logger import get_logger, audit_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin Portal"])


@router.post("/approve-ambulance/{ambulance_id}", response_model=APIResponse)
async def approve_ambulance(
    ambulance_id: str,
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.ADMIN]))
):
    """
    Approve and verify a registered ambulance driver profile.
    This activates the ambulance so they can receive emergency alerts and accept cases.
    """
    admin_id = current_user["uid"]
    
    # Fetch ambulance
    ambulance = await FirestoreDB.get_document(FirestoreDB.AMBULANCES, ambulance_id)
    if not ambulance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ambulance driver profile not found"
        )
        
    # Update verification status
    await FirestoreDB.update_document(
        FirestoreDB.AMBULANCES,
        ambulance_id,
        {"verified": True, "available": True}
    )
    
    await audit_logger.log(
        action="AMBULANCE_APPROVED",
        actor_id=admin_id,
        resource_type="ambulance",
        resource_id=ambulance_id,
        details={"driver_name": ambulance.get("driver_name")}
    )
    
    return APIResponse(
        success=True,
        message=f"Ambulance driver verified and activated successfully"
    )


@router.post("/approve-hospital/{hospital_id}", response_model=APIResponse)
async def approve_hospital(
    hospital_id: str,
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.ADMIN]))
):
    """
    Approve and verify a registered hospital facility profile.
    This activates the hospital and exposes them to nearest-hospital lookups and case notifications.
    """
    admin_id = current_user["uid"]
    
    # Fetch hospital
    hospital = await FirestoreDB.get_document(FirestoreDB.HOSPITALS, hospital_id)
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital profile not found"
        )
        
    # Update verification status
    await FirestoreDB.update_document(
        FirestoreDB.HOSPITALS,
        hospital_id,
        {"verified": True}
    )
    
    await audit_logger.log(
        action="HOSPITAL_APPROVED",
        actor_id=admin_id,
        resource_type="hospital",
        resource_id=hospital_id,
        details={"hospital_name": hospital.get("hospital_name")}
    )
    
    return APIResponse(
        success=True,
        message=f"Hospital profile verified and activated successfully"
    )


@router.get("/active-emergencies", response_model=APIResponse)
async def get_active_emergencies(
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.ADMIN]))
):
    """
    Fetch all active, uncompleted emergency cases inside the SmartRescue ecosystem.
    Useful for system-wide monitoring and dispatcher interventions.
    """
    cases = await AnalyticsService.get_active_emergencies()
    return APIResponse(
        success=True,
        message="Active emergencies retrieved",
        data=cases
    )


@router.get("/analytics", response_model=APIResponse)
async def get_system_analytics(
    timeframe_days: int = Query(default=30, ge=1, le=365),
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.ADMIN]))
):
    """
    Get detailed historical statistics (total incidents, performance metrics, success rates, severity trends).
    """
    stats = await AnalyticsService.get_accident_analytics(timeframe_days)
    return APIResponse(
        success=True,
        message="Historical system analytics compiled",
        data=stats
    )


@router.get("/audit-log", response_model=APIResponse)
async def get_audit_log(
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.ADMIN]))
):
    """
    Get chronological log history of all security-sensitive and transactional operations.
    """
    logs = await AnalyticsService.get_audit_log(limit)
    return APIResponse(
        success=True,
        message="System audit logs retrieved",
        data=logs
    )
