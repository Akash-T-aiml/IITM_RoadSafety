"""
SmartRescue AI — Hospital Service
Handles hospital registrations, bed status management, case preparation, and hospital dashboards.
"""

from typing import Dict, Any, List, Optional
from app.firebase.firestore_db import FirestoreDB
from app.websocket.manager import ws_manager
from app.websocket.events import WSEventType, build_ws_event
from app.utils.helpers import utc_now, build_timeline_entry
from app.utils.logger import get_logger, audit_logger

logger = get_logger(__name__)


class HospitalService:

    @staticmethod
    async def register_hospital(uid: str, data: Dict[str, Any]) -> bool:
        """Register a new hospital or update details."""
        hosp_data = {
            "uid": uid,
            "hospital_name": data.get("hospital_name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "address": data.get("address"),
            "trauma_care_available": data.get("trauma_care_available", True),
            "icu_beds": data.get("icu_beds", 0),
            "total_beds": data.get("total_beds", 0),
            "available_beds": data.get("available_beds", 0),
            "specializations": data.get("specializations", []),
            "verified": False, # Requires Admin approval
            "fcm_token": data.get("fcm_token"),
            "created_at": utc_now()
        }
        await FirestoreDB.create_document(FirestoreDB.HOSPITALS, hosp_data, doc_id=uid)
        
        # Initialize hospital resource details doc
        res_data = {
            "hospital_id": uid,
            "icu_beds": data.get("icu_beds", 0),
            "icu_available": data.get("icu_beds", 0),
            "total_beds": data.get("total_beds", 0),
            "available_beds": data.get("available_beds", 0),
            "ventilators_available": 0,
            "oxygen_available": True,
            "blood_bank_available": True,
            "updated_at": utc_now()
        }
        await FirestoreDB.create_document(FirestoreDB.HOSPITAL_RESOURCES, res_data, doc_id=uid)
        
        await audit_logger.log("HOSPITAL_REGISTERED", uid, "hospital", uid)
        return True

    @staticmethod
    async def get_incoming_cases(hospital_id: str) -> List[Dict[str, Any]]:
        """Get list of active incoming cases destined for this hospital."""
        # Query active cases where hospital_id is assigned or the hospital has been notified
        cases = await FirestoreDB.query_collection(
            FirestoreDB.EMERGENCY_CASES,
            filters=[("status", "not-in", ["resolved", "cancelled", "false_alarm"])]
        )

        incoming = []
        for case in cases:
            # Check if hospital_id is explicitly assigned OR if the hospital is in notified list
            notified_list = case.get("notified_hospitals", [])
            notified_ids = [n.get("id") for n in notified_list if n.get("id")]
            
            if case.get("hospital_id") == hospital_id or hospital_id in notified_ids:
                incoming.append(case)

        return incoming

    @staticmethod
    async def prepare_case(hospital_id: str, case_id: str, prep_data: Dict[str, Any]) -> bool:
        """
        Hospital prepares trauma beds, surgery, ICU, or equipment ahead of patient arrival.
        Updates emergency case with preparation status and logs to timeline.
        """
        case = await FirestoreDB.get_document(FirestoreDB.EMERGENCY_CASES, case_id)
        if not case:
            logger.warning(f"Case {case_id} not found for preparation.")
            return False

        # If hospital is not assigned to the case, assign it now!
        updates = {
            "hospital_preparation": prep_data,
            "hospital_id": hospital_id,
        }

        # Get hospital details
        hospital = await FirestoreDB.get_document(FirestoreDB.HOSPITALS, hospital_id)
        if hospital:
            updates["hospital_name"] = hospital.get("hospital_name")

        # Check if case status needs to progress
        if case.get("status") in ["confirmed", "detected", "ambulance_notified", "ambulance_assigned"]:
            updates["status"] = "en_route_hospital" # Transition en-route as hospital takes charge of prep

        await FirestoreDB.update_document(FirestoreDB.EMERGENCY_CASES, case_id, updates)

        # Build timeline entries
        items_prepared = []
        if prep_data.get("bed_allocated"): items_prepared.append("Emergency Bed allocated")
        if prep_data.get("icu_allocated"): items_prepared.append("ICU Bed allocated")
        if prep_data.get("surgery_team_standby"): items_prepared.append("Trauma Surgery Team standby")
        if prep_data.get("blood_arranged"): items_prepared.append("Blood units arranged")
        if prep_data.get("oxygen_ready"): items_prepared.append("Oxygen cylinders ready")

        prep_summary = ", ".join(items_prepared) if items_prepared else "Equipment and resource preparation initialized"
        await FirestoreDB.append_to_array(
            FirestoreDB.EMERGENCY_CASES,
            case_id,
            "timeline",
            build_timeline_entry(
                f"Hospital preparation started: {prep_summary}.",
                hospital_id,
                "hospital"
            )
        )

        # Notify ambulance driver and user via WebSocket
        prep_event = build_ws_event(
            WSEventType.HOSPITAL_PREPARING,
            {"case_id": case_id, "hospital_id": hospital_id, "preparation": prep_data},
            case_id=case_id,
            actor_id=hospital_id
        )
        
        await ws_manager.broadcast(f"case:{case_id}", prep_event)
        
        # Notify paramedic in ambulance channel specifically
        amb_id = case.get("ambulance_id")
        if amb_id:
            await ws_manager.broadcast(f"ambulance:{amb_id}", prep_event)

        logger.info(f"Hospital {hospital_id} prepared for case {case_id}: {prep_data}")
        await audit_logger.log("HOSPITAL_PREPARED", hospital_id, "emergency_case", case_id, prep_data)
        return True

    @staticmethod
    async def update_bed_status(hospital_id: str, bed_data: Dict[str, Any]) -> bool:
        """Update hospital beds, ICU units, and oxygen/blood resources in real-time."""
        hosp_updates = {}
        if "total_beds" in bed_data: hosp_updates["total_beds"] = bed_data["total_beds"]
        if "available_beds" in bed_data: hosp_updates["available_beds"] = bed_data["available_beds"]
        if "icu_beds" in bed_data: hosp_updates["icu_beds"] = bed_data["icu_beds"]

        if hosp_updates:
            await FirestoreDB.update_document(FirestoreDB.HOSPITALS, hospital_id, hosp_updates)

        # Update the detailed resource document
        res_updates = {k: v for k, v in bed_data.items() if v is not None}
        res_updates["updated_at"] = utc_now()

        await FirestoreDB.update_document(FirestoreDB.HOSPITAL_RESOURCES, hospital_id, res_updates)

        logger.info(f"Hospital {hospital_id} updated bed status: {bed_data}")
        return True

    @staticmethod
    async def get_dashboard(hospital_id: str) -> Dict[str, Any]:
        """
        Aggregate active incoming cases, emergency response status, paramedic notes,
        ETA, and current trauma care capacity metrics.
        """
        # Capacity
        hospital = await FirestoreDB.get_document(FirestoreDB.HOSPITALS, hospital_id)
        resources = await FirestoreDB.get_document(FirestoreDB.HOSPITAL_RESOURCES, hospital_id)
        
        # Cases
        incoming = await HospitalService.get_incoming_cases(hospital_id)

        # Clean/format dashboard data
        active_cases_list = []
        for case in incoming:
            active_cases_list.append({
                "case_id": case.get("case_id"),
                "accident_id": case.get("accident_id"),
                "user_name": case.get("user_name", "Unknown Traveller"),
                "user_phone": case.get("user_phone", ""),
                "status": case.get("status"),
                "severity": case.get("severity"),
                "severity_label": case.get("severity_label"),
                "accident_latitude": case.get("accident_latitude"),
                "accident_longitude": case.get("accident_longitude"),
                "ambulance_id": case.get("ambulance_id"),
                "ambulance_vehicle": case.get("ambulance_vehicle"),
                "estimated_arrival_minutes": case.get("estimated_arrival_minutes"),
                "patient_updates": case.get("patient_updates", []),
                "hospital_preparation": case.get("hospital_preparation"),
                "detected_at": case.get("detected_at"),
            })

        capacity = {
            "total_beds": hospital.get("total_beds", 0) if hospital else 0,
            "available_beds": hospital.get("available_beds", 0) if hospital else 0,
            "icu_beds": hospital.get("icu_beds", 0) if hospital else 0,
            "icu_available": resources.get("icu_available", 0) if resources else 0,
            "ventilators_available": resources.get("ventilators_available", 0) if resources else 0,
            "oxygen_available": resources.get("oxygen_available", True) if resources else True,
            "blood_bank_available": resources.get("blood_bank_available", True) if resources else True,
        }

        return {
            "hospital_id": hospital_id,
            "hospital_name": hospital.get("hospital_name", "Unknown") if hospital else "Unknown",
            "capacity": capacity,
            "incoming_cases": active_cases_list,
            "timestamp": utc_now(),
        }
