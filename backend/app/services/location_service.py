"""
SmartRescue AI — Location Service
Live location tracking and nearest entity search.
"""

from typing import Any, Dict, List, Optional
from app.firebase.firestore_db import FirestoreDB
from app.utils.geo import haversine_distance, find_nearest, estimate_eta_minutes
from app.utils.helpers import utc_now
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LocationService:

    @staticmethod
    async def update_location(
        entity_type: str, entity_id: str,
        latitude: float, longitude: float,
        heading: Optional[float] = None, speed: Optional[float] = None,
    ) -> bool:
        """Update live location for an entity (ambulance/traveller)."""
        location_data = {
            "entity_id": entity_id, "entity_type": entity_type,
            "latitude": latitude, "longitude": longitude,
            "heading": heading, "speed": speed,
            "updated_at": utc_now(),
        }
        try:
            doc = await FirestoreDB.get_document(FirestoreDB.LIVE_LOCATIONS, entity_id)
            if doc:
                await FirestoreDB.update_document(FirestoreDB.LIVE_LOCATIONS, entity_id, location_data)
            else:
                await FirestoreDB.create_document(FirestoreDB.LIVE_LOCATIONS, location_data, doc_id=entity_id)

            # Also update the entity's own collection
            if entity_type == "ambulance":
                await FirestoreDB.update_document(
                    FirestoreDB.AMBULANCES, entity_id,
                    {"latitude": latitude, "longitude": longitude}
                )
            return True
        except Exception as e:
            logger.error(f"Failed to update location for {entity_type}/{entity_id}: {e}")
            return False

    @staticmethod
    async def get_location(entity_id: str) -> Optional[Dict[str, Any]]:
        """Get current location for an entity."""
        return await FirestoreDB.get_document(FirestoreDB.LIVE_LOCATIONS, entity_id)

    @staticmethod
    async def find_nearest_ambulances(
        latitude: float, longitude: float,
        radius_km: float = 50.0, limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find nearest available, verified ambulances."""
        ambulances = await FirestoreDB.query_collection(
            FirestoreDB.AMBULANCES,
            filters=[("verified", "==", True), ("available", "==", True)],
        )

        return find_nearest(
            latitude, longitude, ambulances, radius_km, limit,
            lat_field="latitude", lon_field="longitude",
        )

    @staticmethod
    async def find_nearest_hospitals(
        latitude: float, longitude: float,
        radius_km: float = 100.0, limit: int = 5,
        trauma_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Find nearest verified hospitals."""
        filters = [("verified", "==", True)]
        if trauma_only:
            filters.append(("trauma_care_available", "==", True))

        hospitals = await FirestoreDB.query_collection(FirestoreDB.HOSPITALS, filters=filters)

        return find_nearest(
            latitude, longitude, hospitals, radius_km, limit,
            lat_field="latitude", lon_field="longitude",
        )

    @staticmethod
    async def calculate_eta(
        origin_lat: float, origin_lon: float,
        dest_lat: float, dest_lon: float,
        avg_speed_kmh: float = 40.0,
    ) -> Dict[str, Any]:
        """Calculate ETA between two points."""
        distance = haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
        eta = estimate_eta_minutes(distance, avg_speed_kmh)
        return {"distance_km": round(distance, 2), "eta_minutes": eta, "avg_speed_kmh": avg_speed_kmh}
