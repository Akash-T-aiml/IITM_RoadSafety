"""
SmartRescue AI — Auth Service
Handles registration and login flows with Firebase + JWT.
"""

from typing import Any, Dict, Optional
from app.auth.firebase_auth import verify_firebase_token, set_custom_claims
from app.auth.jwt_handler import create_access_token
from app.firebase.firestore_db import FirestoreDB
from app.utils.logger import get_logger, audit_logger

logger = get_logger(__name__)


class AuthService:

    @staticmethod
    async def register_user(
        firebase_token: str, name: str, email: str, phone: Optional[str],
        role: str, fcm_token: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Register a new user, store in Firestore, issue JWT."""
        firebase_user = await verify_firebase_token(firebase_token)
        if not firebase_user:
            return {"success": False, "message": "Invalid Firebase token"}

        uid = firebase_user["uid"]

        # Check if user already exists
        existing = await FirestoreDB.get_document(FirestoreDB.USERS, uid)
        if existing:
            return {"success": False, "message": "User already registered"}

        # Set Firebase custom claims
        await set_custom_claims(uid, {"role": role})

        # Store user in Firestore
        user_data = {
            "uid": uid, "name": name, "email": email, "phone": phone,
            "role": role, "fcm_token": fcm_token, "is_active": True,
            "email_verified": firebase_user.get("email_verified", False),
        }
        if extra_data:
            user_data.update(extra_data)

        await FirestoreDB.create_document(FirestoreDB.USERS, user_data, doc_id=uid)

        # Role-specific registration
        if role == "ambulance" and extra_data:
            amb_data = {
                "uid": uid, "driver_name": name, "email": email,
                "vehicle_number": extra_data.get("vehicle_number", ""),
                "phone": phone, "government_id": extra_data.get("government_id", ""),
                "hospital_affiliation": extra_data.get("hospital_affiliation"),
                "verified": False, "available": False,
                "fcm_token": fcm_token,
            }
            await FirestoreDB.create_document(FirestoreDB.AMBULANCES, amb_data, doc_id=uid)

        elif role == "hospital" and extra_data:
            hosp_data = {
                "uid": uid, "hospital_name": extra_data.get("hospital_name", name),
                "email": email, "phone": phone,
                "latitude": extra_data.get("latitude", 0),
                "longitude": extra_data.get("longitude", 0),
                "address": extra_data.get("address"),
                "trauma_care_available": extra_data.get("trauma_care_available", False),
                "icu_beds": extra_data.get("icu_beds", 0),
                "total_beds": extra_data.get("total_beds", 0),
                "available_beds": extra_data.get("available_beds", 0),
                "verified": False, "fcm_token": fcm_token,
            }
            await FirestoreDB.create_document(FirestoreDB.HOSPITALS, hosp_data, doc_id=uid)

        # Generate JWT
        jwt_token = create_access_token(
            data={"sub": uid, "email": email, "name": name}, role=role
        )

        await audit_logger.log("USER_REGISTERED", uid, "user", uid, {"role": role})

        return {
            "success": True, "message": "Registration successful",
            "data": {"uid": uid, "token": jwt_token, "role": role, "name": name},
        }

    @staticmethod
    async def login_user(
        firebase_token: str, fcm_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Login existing user: verify Firebase token, issue JWT."""
        firebase_user = await verify_firebase_token(firebase_token)
        if not firebase_user:
            return {"success": False, "message": "Invalid Firebase token"}

        uid = firebase_user["uid"]
        user = await FirestoreDB.get_document(FirestoreDB.USERS, uid)
        if not user:
            return {"success": False, "message": "User not registered. Please register first."}

        # Update FCM token if provided
        if fcm_token:
            await FirestoreDB.update_document(FirestoreDB.USERS, uid, {"fcm_token": fcm_token})

        jwt_token = create_access_token(
            data={"sub": uid, "email": user.get("email"), "name": user.get("name")},
            role=user.get("role", "traveller"),
        )

        await audit_logger.log("USER_LOGIN", uid, "user", uid)

        return {
            "success": True, "message": "Login successful",
            "data": {
                "uid": uid, "token": jwt_token, "role": user.get("role"),
                "name": user.get("name"), "email": user.get("email"),
                "verified": user.get("verified", True),
            },
        }

    @staticmethod
    async def get_profile(uid: str) -> Optional[Dict[str, Any]]:
        """Get user profile from Firestore."""
        return await FirestoreDB.get_document(FirestoreDB.USERS, uid)

    @staticmethod
    async def update_profile(uid: str, updates: Dict[str, Any]) -> bool:
        """Update user profile fields."""
        allowed = {"name", "phone", "fcm_token"}
        filtered = {k: v for k, v in updates.items() if k in allowed and v is not None}
        if not filtered:
            return False
        return await FirestoreDB.update_document(FirestoreDB.USERS, uid, filtered)
