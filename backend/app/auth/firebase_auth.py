"""
SmartRescue AI — Firebase Authentication
Verify Firebase ID tokens for initial login, then issue internal JWTs.
"""

from typing import Dict, Any, Optional

from firebase_admin import auth
from app.firebase.client import get_firebase_auth
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def verify_firebase_token(id_token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a Firebase ID token and return decoded claims.
    
    Returns:
        Dict with uid, email, and custom claims if valid.
        None if verification fails.
    """
    try:
        decoded = auth.verify_id_token(id_token)
        logger.info(
            "Firebase token verified",
            extra={"uid": decoded.get("uid")}
        )
        return {
            "uid": decoded["uid"],
            "email": decoded.get("email"),
            "email_verified": decoded.get("email_verified", False),
            "name": decoded.get("name"),
            "picture": decoded.get("picture"),
            "provider": decoded.get("firebase", {}).get("sign_in_provider"),
        }
    except auth.InvalidIdTokenError:
        logger.warning("Invalid Firebase ID token")
        return None
    except auth.ExpiredIdTokenError:
        logger.warning("Expired Firebase ID token")
        return None
    except auth.RevokedIdTokenError:
        logger.warning("Revoked Firebase ID token")
        return None
    except Exception as e:
        logger.error(f"Firebase token verification error: {e}")
        return None


async def set_custom_claims(uid: str, claims: Dict[str, Any]) -> bool:
    """Set custom claims on a Firebase user (e.g., role)."""
    try:
        auth.set_custom_user_claims(uid, claims)
        logger.info(f"Set custom claims for user {uid}: {claims}")
        return True
    except Exception as e:
        logger.error(f"Failed to set custom claims: {e}")
        return False


async def get_firebase_user(uid: str) -> Optional[Dict[str, Any]]:
    """Get Firebase user record by UID."""
    try:
        user = auth.get_user(uid)
        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "phone_number": user.phone_number,
            "photo_url": user.photo_url,
            "disabled": user.disabled,
            "email_verified": user.email_verified,
        }
    except auth.UserNotFoundError:
        logger.warning(f"Firebase user not found: {uid}")
        return None
    except Exception as e:
        logger.error(f"Failed to get Firebase user: {e}")
        return None
