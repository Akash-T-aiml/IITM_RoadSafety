"""
SmartRescue AI — Firestore Database Operations
Generic CRUD helpers for all collections.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from google.cloud.firestore_v1 import FieldFilter
from app.firebase.client import get_firestore_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FirestoreDB:
    """Firestore CRUD operations wrapper."""

    # ── Collection Names ─────────────────────────────────────
    USERS = "users"
    AMBULANCES = "ambulances"
    HOSPITALS = "hospitals"
    ACCIDENTS = "accidents"
    EMERGENCY_CASES = "emergency_cases"
    LIVE_LOCATIONS = "live_locations"
    NOTIFICATIONS = "notifications"
    EMERGENCY_CONTACTS = "emergency_contacts"
    HOSPITAL_RESOURCES = "hospital_resources"
    AUDIT_LOG = "audit_log"
    SENSOR_BUFFER = "sensor_buffer"

    @staticmethod
    def _get_db():
        return get_firestore_client()

    # ── Create ───────────────────────────────────────────────
    @classmethod
    async def create_document(
        cls, collection: str, data: Dict[str, Any], doc_id: Optional[str] = None
    ) -> str:
        """Create a document. Returns the document ID."""
        db = cls._get_db()
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        data["updated_at"] = datetime.now(timezone.utc).isoformat()

        try:
            if doc_id:
                db.collection(collection).document(doc_id).set(data)
                logger.info(f"Created document {doc_id} in {collection}")
                return doc_id
            else:
                _, doc_ref = db.collection(collection).add(data)
                logger.info(f"Created document {doc_ref.id} in {collection}")
                return doc_ref.id
        except Exception as e:
            logger.error(f"Failed to create document in {collection}: {e}")
            raise

    # ── Read ─────────────────────────────────────────────────
    @classmethod
    async def get_document(cls, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a single document by ID."""
        db = cls._get_db()
        try:
            doc = db.collection(collection).document(doc_id).get()
            if doc.exists:
                result = doc.to_dict()
                result["id"] = doc.id
                return result
            return None
        except Exception as e:
            logger.error(f"Failed to get document {doc_id} from {collection}: {e}")
            raise

    @classmethod
    async def query_collection(
        cls,
        collection: str,
        filters: Optional[List[tuple]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "DESCENDING",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query a collection with optional filters, ordering, and limit.
        Filters format: [(field, operator, value), ...]
        """
        db = cls._get_db()
        try:
            query = db.collection(collection)

            if filters:
                for field, op, value in filters:
                    query = query.where(filter=FieldFilter(field, op, value))

            if order_by:
                from google.cloud.firestore_v1 import Query
                direction = (
                    Query.DESCENDING if order_direction == "DESCENDING"
                    else Query.ASCENDING
                )
                query = query.order_by(order_by, direction=direction)

            if limit:
                query = query.limit(limit)

            docs = query.stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)

            return results
        except Exception as e:
            logger.error(f"Failed to query {collection}: {e}")
            raise

    # ── Update ───────────────────────────────────────────────
    @classmethod
    async def update_document(
        cls, collection: str, doc_id: str, data: Dict[str, Any]
    ) -> bool:
        """Update fields in an existing document."""
        db = cls._get_db()
        data["updated_at"] = datetime.now(timezone.utc).isoformat()

        try:
            db.collection(collection).document(doc_id).update(data)
            logger.info(f"Updated document {doc_id} in {collection}")
            return True
        except Exception as e:
            logger.error(f"Failed to update document {doc_id} in {collection}: {e}")
            raise

    # ── Delete ───────────────────────────────────────────────
    @classmethod
    async def delete_document(cls, collection: str, doc_id: str) -> bool:
        """Delete a document by ID."""
        db = cls._get_db()
        try:
            db.collection(collection).document(doc_id).delete()
            logger.info(f"Deleted document {doc_id} from {collection}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id} from {collection}: {e}")
            raise

    # ── Array Operations ─────────────────────────────────────
    @classmethod
    async def append_to_array(
        cls, collection: str, doc_id: str, field: str, value: Any
    ) -> bool:
        """Append a value to an array field in a document."""
        from google.cloud.firestore_v1 import ArrayUnion
        db = cls._get_db()
        try:
            db.collection(collection).document(doc_id).update({
                field: ArrayUnion([value]),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            return True
        except Exception as e:
            logger.error(f"Failed to append to {field} in {doc_id}: {e}")
            raise

    # ── Batch Operations ─────────────────────────────────────
    @classmethod
    async def batch_create(
        cls, collection: str, documents: List[Dict[str, Any]]
    ) -> List[str]:
        """Create multiple documents in a batch."""
        db = cls._get_db()
        batch = db.batch()
        doc_ids = []

        try:
            for data in documents:
                data["created_at"] = datetime.now(timezone.utc).isoformat()
                data["updated_at"] = datetime.now(timezone.utc).isoformat()
                doc_ref = db.collection(collection).document()
                batch.set(doc_ref, data)
                doc_ids.append(doc_ref.id)

            batch.commit()
            logger.info(f"Batch created {len(doc_ids)} documents in {collection}")
            return doc_ids
        except Exception as e:
            logger.error(f"Batch create failed in {collection}: {e}")
            raise

    # ── Count ────────────────────────────────────────────────
    @classmethod
    async def count_documents(
        cls, collection: str, filters: Optional[List[tuple]] = None
    ) -> int:
        """Count documents matching optional filters."""
        db = cls._get_db()
        try:
            query = db.collection(collection)
            if filters:
                for field, op, value in filters:
                    query = query.where(filter=FieldFilter(field, op, value))

            count_query = query.count()
            results = count_query.get()
            return results[0][0].value
        except Exception as e:
            logger.error(f"Failed to count documents in {collection}: {e}")
            raise
