"""
SmartRescue AI — Notification Service
FCM push notifications + Firestore notification records.
"""

from typing import Any, Dict, List, Optional
from app.firebase.firestore_db import FirestoreDB
from app.firebase.fcm import FCMService
from app.utils.case_id import generate_notification_id
from app.utils.helpers import utc_now
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NotificationService:

    @staticmethod
    async def _store_notification(
        recipient_id: str, notif_type: str, title: str,
        body: str, data: Optional[Dict] = None,
    ) -> str:
        """Store notification record in Firestore."""
        notif_id = generate_notification_id()
        notif = {
            "recipient_id": recipient_id, "type": notif_type,
            "title": title, "body": body, "data": data or {},
            "read": False, "timestamp": utc_now(),
        }
        await FirestoreDB.create_document(FirestoreDB.NOTIFICATIONS, notif, doc_id=notif_id)
        return notif_id

    @staticmethod
    async def notify_ambulance(ambulance_id: str, case_data: Dict[str, Any]) -> bool:
        """Send emergency alert to ambulance driver."""
        ambulance = await FirestoreDB.get_document(FirestoreDB.AMBULANCES, ambulance_id)
        if not ambulance:
            return False

        title = "🚨 Emergency Alert — Accident Detected"
        body = f"Severity: {case_data.get('severity_label', 'Unknown')} | Case: {case_data.get('case_id', 'N/A')}"

        await NotificationService._store_notification(ambulance_id, "emergency_alert", title, body, case_data)

        fcm_token = ambulance.get("fcm_token")
        if fcm_token:
            await FCMService.send_emergency_alert(
                token=fcm_token, case_id=case_data.get("case_id", ""),
                severity=case_data.get("severity", 2),
                location={"latitude": case_data.get("latitude", 0), "longitude": case_data.get("longitude", 0)},
                message_body=body,
            )
        return True

    @staticmethod
    async def notify_hospital(hospital_id: str, case_data: Dict[str, Any]) -> bool:
        """Send incoming emergency alert to hospital."""
        hospital = await FirestoreDB.get_document(FirestoreDB.HOSPITALS, hospital_id)
        if not hospital:
            return False

        title = "🏥 Incoming Emergency Patient"
        body = f"Case {case_data.get('case_id')} | Severity: {case_data.get('severity_label', 'Unknown')}"

        await NotificationService._store_notification(hospital_id, "incoming_emergency", title, body, case_data)

        fcm_token = hospital.get("fcm_token")
        if fcm_token:
            await FCMService.send_to_device(token=fcm_token, title=title, body=body,
                data={"type": "INCOMING_EMERGENCY", "case_id": str(case_data.get("case_id", "")),
                      "severity": str(case_data.get("severity", 0))})
        return True

    @staticmethod
    async def notify_emergency_contacts(user_id: str, case_data: Dict[str, Any]) -> int:
        """Notify all emergency contacts for a user. Returns count of notifications sent."""
        contacts = await FirestoreDB.query_collection(
            FirestoreDB.EMERGENCY_CONTACTS, filters=[("user_id", "==", user_id)]
        )
        count = 0
        for contact in contacts:
            await NotificationService._store_notification(
                contact.get("id", ""), "emergency_contact_alert",
                "🚨 Emergency — Your contact had an accident",
                f"Case: {case_data.get('case_id')} | Location: ({case_data.get('latitude')}, {case_data.get('longitude')})",
                case_data,
            )
            count += 1
        logger.info(f"Notified {count} emergency contacts for user {user_id}")
        return count

    @staticmethod
    async def get_notifications(recipient_id: str, unread_only: bool = False, limit: int = 50) -> List[Dict]:
        """Get notifications for a user."""
        filters = [("recipient_id", "==", recipient_id)]
        if unread_only:
            filters.append(("read", "==", False))
        return await FirestoreDB.query_collection(
            FirestoreDB.NOTIFICATIONS, filters=filters,
            order_by="timestamp", order_direction="DESCENDING", limit=limit,
        )

    @staticmethod
    async def mark_as_read(notification_id: str) -> bool:
        """Mark a notification as read."""
        return await FirestoreDB.update_document(FirestoreDB.NOTIFICATIONS, notification_id, {"read": True})
