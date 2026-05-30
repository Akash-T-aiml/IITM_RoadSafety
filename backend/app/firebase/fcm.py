"""
SmartRescue AI — Firebase Cloud Messaging Service
Push notifications to devices, topics, and batch recipients.
"""

from typing import Any, Dict, List, Optional

from firebase_admin import messaging
from app.firebase.client import get_firebase_messaging
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FCMService:
    """Firebase Cloud Messaging operations."""

    @staticmethod
    async def send_to_device(
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        priority: str = "high",
    ) -> Optional[str]:
        """Send push notification to a single device."""
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
                android=messaging.AndroidConfig(
                    priority=priority,
                    notification=messaging.AndroidNotification(
                        channel_id="emergency_channel",
                        sound="emergency_alert",
                        priority="max",
                    ),
                ),
            )

            response = messaging.send(message)
            logger.info(f"FCM sent to device: {response}")
            return response
        except messaging.UnregisteredError:
            logger.warning(f"FCM token unregistered: {token[:20]}...")
            return None
        except Exception as e:
            logger.error(f"FCM send failed: {e}")
            return None

    @staticmethod
    async def send_to_multiple(
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Send push notification to multiple devices."""
        if not tokens:
            return {"success": 0, "failure": 0}

        try:
            messages = [
                messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    data=data or {},
                    token=token,
                    android=messaging.AndroidConfig(
                        priority="high",
                        notification=messaging.AndroidNotification(
                            channel_id="emergency_channel",
                            sound="emergency_alert",
                            priority="max",
                        ),
                    ),
                )
                for token in tokens
            ]

            response = messaging.send_each(messages)
            logger.info(
                f"FCM batch: {response.success_count} success, "
                f"{response.failure_count} failures"
            )
            return {
                "success": response.success_count,
                "failure": response.failure_count,
            }
        except Exception as e:
            logger.error(f"FCM batch send failed: {e}")
            return {"success": 0, "failure": len(tokens), "error": str(e)}

    @staticmethod
    async def send_to_topic(
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Send push notification to a topic."""
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                topic=topic,
            )

            response = messaging.send(message)
            logger.info(f"FCM sent to topic '{topic}': {response}")
            return response
        except Exception as e:
            logger.error(f"FCM topic send failed: {e}")
            return None

    @staticmethod
    async def send_emergency_alert(
        token: str,
        case_id: str,
        severity: int,
        location: Dict[str, float],
        message_body: str,
    ) -> Optional[str]:
        """Send high-priority emergency alert with structured data."""
        data = {
            "type": "EMERGENCY_ALERT",
            "case_id": case_id,
            "severity": str(severity),
            "latitude": str(location.get("latitude", 0)),
            "longitude": str(location.get("longitude", 0)),
            "click_action": "OPEN_EMERGENCY",
        }

        return await FCMService.send_to_device(
            token=token,
            title="🚨 EMERGENCY ALERT",
            body=message_body,
            data=data,
            priority="high",
        )

    @staticmethod
    async def subscribe_to_topic(tokens: List[str], topic: str) -> bool:
        """Subscribe device tokens to a topic."""
        try:
            response = messaging.subscribe_to_topic(tokens, topic)
            logger.info(
                f"Subscribed {response.success_count} devices to topic '{topic}'"
            )
            return response.success_count > 0
        except Exception as e:
            logger.error(f"Topic subscription failed: {e}")
            return False
