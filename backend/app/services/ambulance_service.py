"""
SmartRescue AI — Ambulance Service
Handles ambulance registration, verification, updates, acceptance, rejection, and reassignment logic.
"""

from typing import Dict, Any, List, Optional
from app.firebase.firestore_db import FirestoreDB
from app.services.location_service import LocationService
from app.services.notification_service import NotificationService
from app.websocket.manager import ws_manager
from app.websocket.events import WSEventType, build_ws_event
from app.utils.helpers import utc_now, build_timeline_entry
from app.utils.logger import get_logger, audit_logger

logger = get_logger(__name__)


class AmbulanceService:

    @staticmethod
    async def register_ambulance(uid: str, data: Dict[str, Any]) -> bool:
        """Register or update ambulance profile info."""
        amb_data = {
            "uid": uid,
            "driver_name": data.get("driver_name"),
            "vehicle_number": data.get("vehicle_number"),
            "phone": data.get("phone"),
            "government_id": data.get("government_id"),
            "hospital_affiliation": data.get("hospital_affiliation"),
            "verified": False, # Requires admin approval
            "available": False,
            "active_case_id": None,
            "fcm_token": data.get("fcm_token"),
            "created_at": utc_now()
        }
        await FirestoreDB.create_document(FirestoreDB.AMBULANCES, amb_data, doc_id=uid)
        await audit_logger.log("AMBULANCE_REGISTERED", uid, "ambulance", uid)
        return True

    @staticmethod
    async def get_nearby_cases(ambulance_id: str, radius_km: float = 50.0) -> List[Dict[str, Any]]:
        """Find pending or active cases near the ambulance's current location."""
        # Get ambulance location
        ambulance = await FirestoreDB.get_document(FirestoreDB.AMBULANCES, ambulance_id)
        if not ambulance or "latitude" not in ambulance or "longitude" not in ambulance:
            return []

        alat = ambulance["latitude"]
        alon = ambulance["longitude"]

        # Fetch cases that are active (not resolved/cancelled)
        active_cases = await FirestoreDB.query_collection(
            FirestoreDB.EMERGENCY_CASES,
            filters=[("status", "not-in", ["resolved", "cancelled", "false_alarm"])]
        )

        from app.utils.geo import find_nearest
        # Use find_nearest helper
        cases_with_dist = find_nearest(
            alat, alon, active_cases, radius_km, limit=10,
            lat_field="accident_latitude", lon_field="accident_longitude"
        )
        return cases_with_dist

    @staticmethod
    async def accept_case(ambulance_id: str, case_id: str, estimated_arrival: Optional[float] = None) -> Dict[str, Any]:
        """Ambulance driver accepts an emergency case assignment."""
        case = await FirestoreDB.get_document(FirestoreDB.EMERGENCY_CASES, case_id)
        if not case:
            return {"success": False, "message": "Emergency case not found"}

        if case.get("ambulance_id") != ambulance_id:
            return {"success": False, "message": "This case is not assigned to this ambulance"}

        current_status = case.get("status")
        if current_status in ["resolved", "cancelled", "false_alarm"]:
            return {"success": False, "message": "Case is already inactive"}

        # Update case state
        update_data = {
            "status": "ambulance_assigned",
            "ambulance_dispatched_at": utc_now(),
        }
        if estimated_arrival is not None:
            update_data["estimated_arrival_minutes"] = estimated_arrival

        await FirestoreDB.update_document(FirestoreDB.EMERGENCY_CASES, case_id, update_data)

        # Update ambulance state
        await FirestoreDB.update_document(
            FirestoreDB.AMBULANCES,
            ambulance_id,
            {"available": False, "active_case_id": case_id}
        )

        # Update timeline
        eta_str = f"Estimated arrival: {estimated_arrival} mins." if estimated_arrival else "ETA calculation in progress."
        await FirestoreDB.append_to_array(
            FirestoreDB.EMERGENCY_CASES,
            case_id,
            "timeline",
            build_timeline_entry(
                f"Ambulance driver accepted case. {eta_str}",
                ambulance_id,
                "ambulance"
            )
        )

        # Notify hospital(s) that ambulance has accepted and is en-route
        hospital_id = case.get("hospital_id")
        if hospital_id:
            await ws_manager.broadcast(
                f"hospital:{hospital_id}",
                build_ws_event(
                    WSEventType.AMBULANCE_ASSIGNED,
                    {"case_id": case_id, "ambulance_id": ambulance_id, "eta_minutes": estimated_arrival},
                    case_id=case_id
                )
            )

        # Notify traveller that help is on the way
        user_id = case.get("user_id")
        await ws_manager.broadcast(
            f"user:{user_id}",
            build_ws_event(
                WSEventType.AMBULANCE_ASSIGNED,
                {"case_id": case_id, "ambulance_id": ambulance_id, "eta_minutes": estimated_arrival},
                case_id=case_id
            )
        )

        # Broadcast case status change
        event = build_ws_event(
            WSEventType.CASE_STATUS_CHANGE,
            {"case_id": case_id, "status": "ambulance_assigned", "eta_minutes": estimated_arrival},
            case_id=case_id
        )
        await ws_manager.broadcast(f"case:{case_id}", event)
        await ws_manager.broadcast("admin:dashboard", event)

        await audit_logger.log("AMBULANCE_ACCEPTED", ambulance_id, "emergency_case", case_id)
        return {"success": True, "message": "Case accepted successfully"}

    @staticmethod
    async def reject_case(ambulance_id: str, case_id: str) -> Dict[str, Any]:
        """
        Ambulance driver rejects the emergency assignment.
        Triggers automatic reassignment workflow to find next closest ambulance.
        """
        case = await FirestoreDB.get_document(FirestoreDB.EMERGENCY_CASES, case_id)
        if not case:
            return {"success": False, "message": "Emergency case not found"}

        if case.get("ambulance_id") != ambulance_id:
            return {"success": False, "message": "This case is not assigned to this ambulance"}

        logger.info(f"Ambulance {ambulance_id} rejected case {case_id}. Triggering reassignment.")

        # Update rejecting ambulance's state to available
        await FirestoreDB.update_document(
            FirestoreDB.AMBULANCES,
            ambulance_id,
            {"available": True, "active_case_id": None}
        )

        # Record rejection on the case document
        rejected_list = case.get("rejected_ambulances", [])
        if ambulance_id not in rejected_list:
            rejected_list.append(ambulance_id)

        reassignment_cnt = case.get("reassignment_count", 0) + 1

        # Save record of rejection in timeline
        rejection_timeline_entry = build_timeline_entry(
            f"Ambulance driver rejected the case.",
            ambulance_id,
            "ambulance"
        )
        await FirestoreDB.update_document(
            FirestoreDB.EMERGENCY_CASES,
            case_id,
            {
                "rejected_ambulances": rejected_list,
                "reassignment_count": reassignment_cnt,
            }
        )
        await FirestoreDB.append_to_array(FirestoreDB.EMERGENCY_CASES, case_id, "timeline", rejection_timeline_entry)

        # Notify general case channel of rejection
        await ws_manager.broadcast(
            f"case:{case_id}",
            build_ws_event(WSEventType.AMBULANCE_REJECTED, {"case_id": case_id, "rejected_ambulance_id": ambulance_id}, case_id=case_id)
        )

        # ── Trigger Automatic Reassignment ──
        lat = case.get("accident_latitude")
        lon = case.get("accident_longitude")

        # Find available ambulances within 50km
        nearest_ambs = await LocationService.find_nearest_ambulances(lat, lon, radius_km=50.0, limit=10)
        
        # Filter out already attempted/rejected ones
        next_ambulance = None
        for amb in nearest_ambs:
            aid = amb.get("uid") or amb.get("id")
            if aid not in rejected_list:
                next_ambulance = amb
                break

        if next_ambulance:
            next_amb_id = next_ambulance.get("uid") or next_ambulance.get("id")
            dist = next_ambulance["distance_km"]
            eta = next_ambulance["distance_km"] * 1.3 / 40.0 * 60.0

            logger.info(f"Reassigning case {case_id} to next closest ambulance: {next_amb_id}")

            # Assign to the new ambulance
            await FirestoreDB.update_document(
                FirestoreDB.EMERGENCY_CASES,
                case_id,
                {
                    "status": "ambulance_notified",
                    "ambulance_id": next_amb_id,
                    "ambulance_vehicle": next_ambulance.get("vehicle_number"),
                    "estimated_arrival_minutes": round(eta, 1),
                }
            )

            # Mark new ambulance as occupied
            await FirestoreDB.update_document(
                FirestoreDB.AMBULANCES,
                next_amb_id,
                {"available": False, "active_case_id": case_id}
            )

            # Timeline log
            await FirestoreDB.append_to_array(
                FirestoreDB.EMERGENCY_CASES,
                case_id,
                "timeline",
                build_timeline_entry(
                    f"Ambulance reassigned automatically. New assignment: Vehicle {next_ambulance.get('vehicle_number')} (Distance: {dist} km, ETA: {eta:.1f} mins).",
                    next_amb_id,
                    "ambulance"
                )
            )

            # Notify the new ambulance
            await NotificationService.notify_ambulance(next_amb_id, case)
            
            # Send real-time WS alert to driver
            await ws_manager.broadcast(
                f"ambulance:{next_amb_id}",
                build_ws_event(
                    WSEventType.AMBULANCE_NOTIFIED,
                    {"case_id": case_id, "latitude": lat, "longitude": lon, "eta_minutes": round(eta, 1)},
                    case_id=case_id
                )
            )

            # Broadcast reassignment details to dashboard and client channels
            reassign_event = build_ws_event(
                WSEventType.AMBULANCE_REASSIGNED,
                {
                    "case_id": case_id,
                    "ambulance_id": next_amb_id,
                    "ambulance_vehicle": next_ambulance.get("vehicle_number"),
                    "eta_minutes": round(eta, 1)
                },
                case_id=case_id
            )
            await ws_manager.broadcast(f"case:{case_id}", reassign_event)
            await ws_manager.broadcast("admin:dashboard", reassign_event)

        else:
            logger.warning(f"Reassignment failed for case {case_id}: no other available ambulances nearby.")
            await FirestoreDB.update_document(
                FirestoreDB.EMERGENCY_CASES,
                case_id,
                {
                    "status": "confirmed", # Keep it confirmed but unassigned
                    "ambulance_id": None,
                    "ambulance_vehicle": None,
                    "estimated_arrival_minutes": None
                }
            )
            await FirestoreDB.append_to_array(
                FirestoreDB.EMERGENCY_CASES,
                case_id,
                "timeline",
                build_timeline_entry("No other available ambulance found nearby. Awaiting assignment.", "system", "system")
            )

            # Broadcast failure/waiting status
            wait_event = build_ws_event(
                WSEventType.CASE_STATUS_CHANGE,
                {"case_id": case_id, "status": "confirmed", "message": "Ambulance assignment pending availability"},
                case_id=case_id
            )
            await ws_manager.broadcast(f"case:{case_id}", wait_event)
            await ws_manager.broadcast("admin:dashboard", wait_event)

        await audit_logger.log("AMBULANCE_REJECTED", ambulance_id, "emergency_case", case_id)
        return {"success": True, "message": "Case rejected and processed"}

    @staticmethod
    async def update_patient_status(ambulance_id: str, case_id: str, updates: Dict[str, Any]) -> bool:
        """Paramedic/Nurse inside ambulance streams live patient diagnostics update to the affiliated/assigned hospital."""
        case = await FirestoreDB.get_document(FirestoreDB.EMERGENCY_CASES, case_id)
        if not case:
            return False

        # Add update entry to array
        update_entry = {
            "timestamp": utc_now(),
            "updated_by": ambulance_id,
            "patient_condition": updates.get("patient_condition"),
            "oxygen_needed": updates.get("oxygen_needed", False),
            "blood_required": updates.get("blood_required", False),
            "blood_type": updates.get("blood_type"),
            "icu_required": updates.get("icu_required", False),
            "surgery_preparation_needed": updates.get("surgery_preparation_needed", False),
            "consciousness_level": updates.get("consciousness_level"),
            "vital_signs": updates.get("vital_signs"),
            "additional_notes": updates.get("additional_notes")
        }

        # Update Firestore emergency case
        await FirestoreDB.append_to_array(FirestoreDB.EMERGENCY_CASES, case_id, "patient_updates", update_entry)

        # Notify hospital in realtime via WS
        hospital_id = case.get("hospital_id")
        if hospital_id:
            hosp_event = build_ws_event(
                WSEventType.PATIENT_UPDATE,
                {"case_id": case_id, "update": update_entry},
                case_id=case_id,
                actor_id=ambulance_id
            )
            await ws_manager.broadcast(f"hospital:{hospital_id}", hosp_event)
            await ws_manager.broadcast(f"case:{case_id}", hosp_event)

        logger.info(f"Patient status updated for case {case_id} by ambulance {ambulance_id}")
        return True
