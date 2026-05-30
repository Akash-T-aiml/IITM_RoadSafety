"""
SmartRescue AI — Accident Service
Handles processing of sensor data, ML predictions, and emergency workflows.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from app.firebase.firestore_db import FirestoreDB
from app.ml.predictor import predictor
from app.ml.confidence import confidence_evaluator
from app.services.location_service import LocationService
from app.services.notification_service import NotificationService
from app.websocket.manager import ws_manager
from app.websocket.events import WSEventType, build_ws_event
from app.utils.case_id import generate_case_id, generate_accident_id
from app.utils.helpers import utc_now, build_timeline_entry
from app.utils.logger import get_logger, audit_logger

logger = get_logger(__name__)


class AccidentService:

    @staticmethod
    async def process_sensor_data(user_id: str, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process continuous sensor data streamed by a traveller:
        1. Run ML prediction & evaluate confidence.
        2. Update buffer for false-alarm filtering.
        3. Trigger workflow if severe accident is detected with high confidence or buffered threshold.
        """
        # Run prediction
        pred_class, probabilities = predictor.predict(sensor_data)
        eval_result = confidence_evaluator.evaluate_confidence(probabilities)
        
        confidence = eval_result["confidence_score"]
        status = eval_result["emergency_status"]
        
        # Update false-alarm filter buffer
        buffer_result = confidence_evaluator.update_buffer(user_id, pred_class)
        
        response = {
            "prediction": pred_class,
            "prediction_label": predictor.PREDICTION_LABELS.get(pred_class, "Unknown"),
            "confidence_score": confidence,
            "emergency_status": status,
            "buffer_status": buffer_result["buffer_status"],
            "consecutive_severe_count": buffer_result["consecutive_severe_count"],
            "probabilities": eval_result["probabilities"]
        }

        # Auto-trigger if ML confidence is extremely high OR false alarm buffer tells us it's time to trigger
        if (status == confidence_evaluator.ESCALATION_AUTO) or buffer_result["should_trigger"]:
            # Check if there is already an active case for this user to avoid double triggering
            active_cases = await FirestoreDB.query_collection(
                FirestoreDB.EMERGENCY_CASES,
                filters=[("user_id", "==", user_id), ("status", "not-in", ["resolved", "cancelled", "false_alarm"])]
            )
            if not active_cases:
                case_id = await AccidentService.trigger_emergency_workflow(
                    user_id=user_id,
                    severity=pred_class,
                    confidence=confidence,
                    latitude=sensor_data["latitude"],
                    longitude=sensor_data["longitude"],
                    sensor_snapshot=sensor_data,
                    auto_triggered=True
                )
                response["case_id"] = case_id
                response["emergency_status"] = "auto_triggered"
                logger.info(f"Auto-triggered emergency case: {case_id} for user {user_id}")
            else:
                response["case_id"] = active_cases[0]["case_id"]
                response["message"] = "Emergency already active for this user."

        elif status == confidence_evaluator.ESCALATION_CONFIRM or buffer_result["should_ask_confirmation"]:
            # Check if already active or pending confirmation
            active_cases = await FirestoreDB.query_collection(
                FirestoreDB.EMERGENCY_CASES,
                filters=[("user_id", "==", user_id), ("status", "not-in", ["resolved", "cancelled", "false_alarm"])]
            )
            if not active_cases:
                case_id = await AccidentService.create_pending_emergency(
                    user_id=user_id,
                    severity=pred_class,
                    confidence=confidence,
                    latitude=sensor_data["latitude"],
                    longitude=sensor_data["longitude"],
                    sensor_snapshot=sensor_data
                )
                response["case_id"] = case_id
                response["emergency_status"] = "confirmation_needed"
                
                # Notify traveller via WebSocket to confirm
                await ws_manager.broadcast(
                    f"user:{user_id}",
                    build_ws_event(
                        WSEventType.CONFIRMATION_REQUESTED,
                        {"case_id": case_id, "confidence": confidence, "severity": pred_class},
                        case_id=case_id
                    )
                )
            else:
                response["case_id"] = active_cases[0]["case_id"]

        # Save sensor data snapshot in standard stream buffer collection for analytics/offline review
        await FirestoreDB.create_document(
            FirestoreDB.SENSOR_BUFFER,
            {
                "user_id": user_id,
                "sensor_data": sensor_data,
                "prediction": pred_class,
                "confidence": confidence,
                "timestamp": utc_now()
            }
        )

        return response

    @staticmethod
    async def create_pending_emergency(
        user_id: str, severity: int, confidence: float,
        latitude: float, longitude: float, sensor_snapshot: Dict[str, Any]
    ) -> str:
        """Create an emergency case in 'confirmation_pending' status."""
        case_id = generate_case_id()
        accident_id = generate_accident_id()

        # Get user details
        user = await FirestoreDB.get_document(FirestoreDB.USERS, user_id)
        user_name = user.get("name") if user else "Unknown Traveller"
        user_phone = user.get("phone") if user else ""

        # Create accident record
        accident_data = {
            "id": accident_id,
            "user_id": user_id,
            "latitude": latitude,
            "longitude": longitude,
            "severity": severity,
            "prediction_confidence": confidence,
            "sensor_snapshot": sensor_snapshot,
            "timestamp": utc_now(),
            "case_id": case_id
        }
        await FirestoreDB.create_document(FirestoreDB.ACCIDENTS, accident_data, doc_id=accident_id)

        # Create pending emergency case
        case_data = {
            "case_id": case_id,
            "accident_id": accident_id,
            "user_id": user_id,
            "user_name": user_name,
            "user_phone": user_phone,
            "status": "confirmation_pending",
            "severity": severity,
            "severity_label": predictor.PREDICTION_LABELS.get(severity, "Severe Accident"),
            "confidence_score": confidence,
            "accident_latitude": latitude,
            "accident_longitude": longitude,
            "detected_at": utc_now(),
            "auto_triggered": False,
            "reassignment_count": 0,
            "timeline": [
                build_timeline_entry("Accident detected by AI. Awaiting traveller confirmation.", "AI_Predictor", "system")
            ]
        }
        await FirestoreDB.create_document(FirestoreDB.EMERGENCY_CASES, case_data, doc_id=case_id)
        
        await audit_logger.log("ACCIDENT_PENDING", user_id, "emergency_case", case_id, {"confidence": confidence})
        return case_id

    @staticmethod
    async def confirm_emergency(case_id: str, confirmed: bool) -> bool:
        """Confirm or reject a pending emergency."""
        case = await FirestoreDB.get_document(FirestoreDB.EMERGENCY_CASES, case_id)
        if not case or case.get("status") != "confirmation_pending":
            logger.warning(f"Cannot confirm/deny case {case_id}: not in pending status.")
            return False

        user_id = case.get("user_id")

        if confirmed:
            # Trigger full emergency workflow
            logger.info(f"User confirmed emergency case {case_id}")
            # Update case status to confirmed
            await FirestoreDB.update_document(
                FirestoreDB.EMERGENCY_CASES,
                case_id,
                {
                    "status": "confirmed",
                    "confirmed_at": utc_now(),
                }
            )
            await FirestoreDB.append_to_array(
                FirestoreDB.EMERGENCY_CASES,
                case_id,
                "timeline",
                build_timeline_entry("Emergency confirmed by traveller.", user_id, "traveller")
            )
            
            # Start workflow (ambulance allocation, hospital alerts, etc.)
            await AccidentService.execute_response_workflow(case_id)
            await ws_manager.broadcast(
                f"case:{case_id}",
                build_ws_event(WSEventType.EMERGENCY_CONFIRMED, {"case_id": case_id}, case_id=case_id)
            )
            await audit_logger.log("ACCIDENT_CONFIRMED", user_id, "emergency_case", case_id)
        else:
            # Mark as false alarm/cancelled
            logger.info(f"User marked emergency case {case_id} as false alarm")
            await FirestoreDB.update_document(
                FirestoreDB.EMERGENCY_CASES,
                case_id,
                {
                    "status": "false_alarm",
                    "resolved_at": utc_now(),
                }
            )
            await FirestoreDB.append_to_array(
                FirestoreDB.EMERGENCY_CASES,
                case_id,
                "timeline",
                build_timeline_entry("Accident alert rejected by traveller (False Alarm).", user_id, "traveller")
            )
            confidence_evaluator.clear_buffer(user_id)
            await ws_manager.broadcast(
                f"case:{case_id}",
                build_ws_event(WSEventType.FALSE_ALARM, {"case_id": case_id}, case_id=case_id)
            )
            await audit_logger.log("ACCIDENT_FALSE_ALARM", user_id, "emergency_case", case_id)

        return True

    @staticmethod
    async def trigger_emergency_workflow(
        user_id: str, severity: int, confidence: float,
        latitude: float, longitude: float, sensor_snapshot: Dict[str, Any],
        auto_triggered: bool = True
    ) -> str:
        """Create accident and case document, then execute the emergency allocation & notifications."""
        case_id = generate_case_id()
        accident_id = generate_accident_id()

        # Get user details
        user = await FirestoreDB.get_document(FirestoreDB.USERS, user_id)
        user_name = user.get("name") if user else "Unknown Traveller"
        user_phone = user.get("phone") if user else ""

        # Create accident record
        accident_data = {
            "id": accident_id,
            "user_id": user_id,
            "latitude": latitude,
            "longitude": longitude,
            "severity": severity,
            "prediction_confidence": confidence,
            "sensor_snapshot": sensor_snapshot,
            "timestamp": utc_now(),
            "case_id": case_id
        }
        await FirestoreDB.create_document(FirestoreDB.ACCIDENTS, accident_data, doc_id=accident_id)

        # Create active emergency case
        case_data = {
            "case_id": case_id,
            "accident_id": accident_id,
            "user_id": user_id,
            "user_name": user_name,
            "user_phone": user_phone,
            "status": "detected" if auto_triggered else "confirmed",
            "severity": severity,
            "severity_label": predictor.PREDICTION_LABELS.get(severity, "Severe Accident"),
            "confidence_score": confidence,
            "accident_latitude": latitude,
            "accident_longitude": longitude,
            "detected_at": utc_now(),
            "confirmed_at": utc_now() if auto_triggered else None,
            "auto_triggered": auto_triggered,
            "reassignment_count": 0,
            "timeline": [
                build_timeline_entry(
                    f"Severe accident auto-triggered. Confidence: {confidence:.2f}",
                    "AI_Predictor",
                    "system"
                )
            ]
        }
        await FirestoreDB.create_document(FirestoreDB.EMERGENCY_CASES, case_data, doc_id=case_id)
        
        await audit_logger.log("ACCIDENT_AUTO_TRIGGERED", user_id, "emergency_case", case_id, {"confidence": confidence})

        # Run allocation workflow
        await AccidentService.execute_response_workflow(case_id)
        return case_id

    @staticmethod
    async def execute_response_workflow(case_id: str):
        """
        Executes the emergency response workflow:
        1. Find nearest available ambulance.
        2. If found, notify them. Otherwise, mark case as pending ambulance assignment.
        3. Notify nearby hospitals.
        4. Notify emergency contacts.
        5. Broadcast updates via WebSockets.
        """
        case = await FirestoreDB.get_document(FirestoreDB.EMERGENCY_CASES, case_id)
        if not case:
            logger.error(f"Cannot execute response workflow: case {case_id} not found.")
            return

        lat = case.get("accident_latitude")
        lon = case.get("accident_longitude")
        user_id = case.get("user_id")

        # 1. Notify emergency contacts first
        await NotificationService.notify_emergency_contacts(user_id, case)

        # 2. Find nearest available ambulance
        # We query the nearest available ambulances within 50km
        nearest_ambs = await LocationService.find_nearest_ambulances(lat, lon, radius_km=50.0, limit=5)
        
        assigned_ambulance_id = None
        if nearest_ambs:
            # Select the closest one
            closest_amb = nearest_ambs[0]
            assigned_ambulance_id = closest_amb.get("uid") or closest_amb.get("id")
            
            logger.info(f"Allocating ambulance {assigned_ambulance_id} to case {case_id}")
            
            # Calculate distance and straight-line ETA
            dist = closest_amb["distance_km"]
            eta = closest_amb.get("distance_km", 0.0) * 1.3 / 40.0 * 60.0 # simple road ETA minutes

            # Update case to ambulance_notified
            await FirestoreDB.update_document(
                FirestoreDB.EMERGENCY_CASES,
                case_id,
                {
                    "status": "ambulance_notified",
                    "ambulance_id": assigned_ambulance_id,
                    "ambulance_vehicle": closest_amb.get("vehicle_number"),
                    "estimated_arrival_minutes": round(eta, 1),
                }
            )

            # Append to timeline
            await FirestoreDB.append_to_array(
                FirestoreDB.EMERGENCY_CASES,
                case_id,
                "timeline",
                build_timeline_entry(
                    f"Ambulance {closest_amb.get('vehicle_number')} notified (ETA: {eta:.1f} mins, distance: {dist} km).",
                    assigned_ambulance_id,
                    "ambulance"
                )
            )

            # Notify the ambulance
            await NotificationService.notify_ambulance(assigned_ambulance_id, case)
            
            # Update ambulance availability status to busy (available = False)
            await FirestoreDB.update_document(
                FirestoreDB.AMBULANCES,
                assigned_ambulance_id,
                {"available": False, "active_case_id": case_id}
            )
            
            # Notify driver through their personal WS channel
            await ws_manager.broadcast(
                f"ambulance:{assigned_ambulance_id}",
                build_ws_event(
                    WSEventType.AMBULANCE_NOTIFIED,
                    {"case_id": case_id, "latitude": lat, "longitude": lon, "eta_minutes": round(eta, 1)},
                    case_id=case_id
                )
            )
        else:
            logger.warning(f"No available ambulance found within 50km for case {case_id}")
            await FirestoreDB.append_to_array(
                FirestoreDB.EMERGENCY_CASES,
                case_id,
                "timeline",
                build_timeline_entry("No available ambulance found nearby. Awaiting assignment.", "system", "system")
            )

        # 3. Find and notify nearest hospitals
        # We query the nearest hospitals within 50km
        nearest_hospitals = await LocationService.find_nearest_hospitals(lat, lon, radius_km=50.0, limit=3)
        notified_hospitals = []
        
        for hosp in nearest_hospitals:
            hosp_id = hosp.get("uid") or hosp.get("id")
            await NotificationService.notify_hospital(hosp_id, case)
            notified_hospitals.append({
                "id": hosp_id,
                "name": hosp.get("hospital_name"),
                "distance_km": hosp.get("distance_km")
            })

            # Broadcast to hospital dashboard WS
            await ws_manager.broadcast(
                f"hospital:{hosp_id}",
                build_ws_event(
                    WSEventType.HOSPITAL_NOTIFIED,
                    {
                        "case_id": case_id,
                        "accident_latitude": lat,
                        "accident_longitude": lon,
                        "severity": case.get("severity"),
                        "severity_label": case.get("severity_label"),
                        "user_name": case.get("user_name")
                    },
                    case_id=case_id
                )
            )

        # Update case with hospital options
        await FirestoreDB.update_document(
            FirestoreDB.EMERGENCY_CASES,
            case_id,
            {"notified_hospitals": notified_hospitals}
        )

        # 4. Broadcast the new case creation to all relevant WebSocket channels
        # E.g. to the traveller, and generic active-cases monitors
        general_case_event = build_ws_event(
            WSEventType.ACCIDENT_DETECTED,
            {
                "case_id": case_id,
                "accident_latitude": lat,
                "accident_longitude": lon,
                "severity": case.get("severity"),
                "severity_label": case.get("severity_label"),
                "status": "detected" if case.get("status") == "detected" else "confirmed"
            },
            case_id=case_id
        )
        
        await ws_manager.broadcast(f"user:{user_id}", general_case_event)
        await ws_manager.broadcast("admin:dashboard", general_case_event)
