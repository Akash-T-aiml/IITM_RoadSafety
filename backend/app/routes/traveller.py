"""
SmartRescue AI — Traveller API Routes
Handles AI prediction, continuous sensor streaming, history, and contact management.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.auth.rbac import RoleChecker, Role
from app.models.common import APIResponse
from app.models.user import SensorData, EmergencyContactCreate
from app.models.accident import PredictionRequest, PredictionResponse
from app.services.accident_service import AccidentService
from app.firebase.firestore_db import FirestoreDB
from app.ml.predictor import predictor
from app.ml.confidence import confidence_evaluator
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/traveller", tags=["Traveller"])


@router.post("/predict", response_model=PredictionResponse)
async def predict_accident(payload: PredictionRequest):
    """
    Run ad-hoc ML prediction on a single snapshot of sensor values.
    Returns prediction label, confidence, and emergency escalation level.
    """
    sensor_dict = payload.model_dump()
    
    # Predict
    pred_class, probabilities = predictor.predict(sensor_dict)
    eval_result = confidence_evaluator.evaluate_confidence(probabilities)
    
    return PredictionResponse(
        prediction=pred_class,
        prediction_label=predictor.PREDICTION_LABELS.get(pred_class, "Unknown"),
        confidence_score=eval_result["confidence_score"],
        emergency_status=eval_result["emergency_status"],
        probabilities=eval_result["probabilities"]
    )


@router.post("/send-sensor-data", response_model=APIResponse)
async def send_sensor_data(
    payload: SensorData,
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.TRAVELLER]))
):
    """
    Stream real-time sensor data from external simulator/traveller app.
    Runs AI detection pipeline, updates filters, and triggers emergency if severe.
    """
    user_id = current_user["uid"]
    sensor_dict = payload.model_dump()
    
    # Process
    result = await AccidentService.process_sensor_data(user_id, sensor_dict)
    
    return APIResponse(
        success=True,
        message="Sensor data processed successfully",
        data=result
    )


@router.post("/confirm-emergency", response_model=APIResponse)
async def confirm_emergency(
    case_id: str,
    confirmed: bool,
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.TRAVELLER]))
):
    """
    Confirm or deny a pending emergency alert.
    If confirmed=True, initiates the immediate rescue allocation workflow.
    """
    success = await AccidentService.confirm_emergency(case_id, confirmed)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update emergency case status. Verify case ID."
        )
    
    msg = "Emergency dispatch initiated." if confirmed else "False alarm reported. Buffer reset."
    return APIResponse(success=True, message=msg)


@router.get("/emergency-status/{case_id}", response_model=APIResponse)
async def get_emergency_status(
    case_id: str,
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.TRAVELLER, Role.ADMIN]))
):
    """
    Fetch the live status, ETA, and progress of an active emergency case.
    """
    case = await FirestoreDB.get_document(FirestoreDB.EMERGENCY_CASES, case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency case not found"
        )
    
    return APIResponse(
        success=True,
        message="Emergency status retrieved",
        data=case
    )


@router.get("/user-history", response_model=APIResponse)
async def get_user_history(
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.TRAVELLER]))
):
    """
    Retrieve past accident history and emergency logs for the authenticated traveller.
    """
    user_id = current_user["uid"]
    
    # Query cases where user_id matches
    cases = await FirestoreDB.query_collection(
        FirestoreDB.EMERGENCY_CASES,
        filters=[("user_id", "==", user_id)]
    )
    
    return APIResponse(
        success=True,
        message="User history retrieved",
        data=cases
    )


@router.post("/emergency-contacts", response_model=APIResponse)
async def add_emergency_contact(
    payload: EmergencyContactCreate,
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.TRAVELLER]))
):
    """
    Add a new emergency contact for the user.
    """
    user_id = current_user["uid"]
    contact_data = payload.model_dump()
    contact_data["user_id"] = user_id
    
    # Create document
    from app.utils.case_id import generate_notification_id
    cid = f"CNT-{generate_notification_id()}"
    contact_data["id"] = cid
    
    await FirestoreDB.create_document(
        FirestoreDB.EMERGENCY_CONTACTS,
        contact_data,
        doc_id=cid
    )
    
    return APIResponse(
        success=True,
        message="Emergency contact added successfully",
        data={"contact_id": cid}
    )


@router.get("/emergency-contacts", response_model=APIResponse)
async def get_emergency_contacts(
    current_user: Dict[str, Any] = Depends(RoleChecker([Role.TRAVELLER]))
):
    """
    Retrieve all registered emergency contacts for the user.
    """
    user_id = current_user["uid"]
    contacts = await FirestoreDB.query_collection(
        FirestoreDB.EMERGENCY_CONTACTS,
        filters=[("user_id", "==", user_id)]
    )
    return APIResponse(
        success=True,
        message="Emergency contacts retrieved",
        data=contacts
    )
