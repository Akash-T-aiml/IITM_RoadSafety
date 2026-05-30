"""
SmartRescue AI — Firebase Admin SDK Initialization
Singleton pattern: initialized once at application startup.
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore, auth, messaging
from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_firebase_app: firebase_admin.App | None = None
_firestore_client = None


def initialize_firebase() -> firebase_admin.App:
    """
    Initialize Firebase Admin SDK with service account credentials.
    Safe to call multiple times — returns existing app if already initialized.
    """
    global _firebase_app, _firestore_client

    if _firebase_app is not None:
        logger.info("Firebase already initialized, reusing existing app")
        return _firebase_app

    settings = get_settings()
    cred_path = settings.FIREBASE_CREDENTIALS_PATH

    try:
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred, {
                "projectId": settings.FIREBASE_PROJECT_ID,
            })
            logger.info(
                "Firebase initialized with service account",
                extra={"project_id": settings.FIREBASE_PROJECT_ID}
            )
        else:
            # Fallback: use Application Default Credentials (for Cloud Run, GCE, etc.)
            _firebase_app = firebase_admin.initialize_app(options={
                "projectId": settings.FIREBASE_PROJECT_ID,
            })
            logger.warning(
                "Firebase initialized with ADC (no service account file found)",
                extra={"expected_path": cred_path}
            )

        _firestore_client = firestore.client()
        return _firebase_app

    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise


def get_firestore_client():
    """Get the Firestore client instance."""
    global _firestore_client
    if _firestore_client is None:
        initialize_firebase()
    return _firestore_client


def get_firebase_auth():
    """Get Firebase Auth module."""
    if _firebase_app is None:
        initialize_firebase()
    return auth


def get_firebase_messaging():
    """Get Firebase Cloud Messaging module."""
    if _firebase_app is None:
        initialize_firebase()
    return messaging
