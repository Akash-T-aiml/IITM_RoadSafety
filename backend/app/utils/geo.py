"""
SmartRescue AI — Geospatial Utilities
Haversine distance calculation and nearest entity search.
"""

import math
from typing import List, Dict, Any, Optional, Tuple


def haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate the great-circle distance between two GPS coordinates.
    
    Args:
        lat1, lon1: Latitude and longitude of point 1 (in degrees)
        lat2, lon2: Latitude and longitude of point 2 (in degrees)
    
    Returns:
        Distance in kilometers.
    """
    R = 6371.0  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def find_nearest(
    target_lat: float,
    target_lon: float,
    candidates: List[Dict[str, Any]],
    radius_km: float,
    limit: int = 5,
    lat_field: str = "latitude",
    lon_field: str = "longitude",
) -> List[Dict[str, Any]]:
    """
    Find the nearest candidates within a given radius, sorted by distance.
    
    Args:
        target_lat, target_lon: Target GPS coordinates
        candidates: List of dicts, each with lat/lon fields
        radius_km: Maximum search radius in km
        limit: Maximum number of results
        lat_field, lon_field: Field names for coordinates in candidate dicts
    
    Returns:
        Sorted list of candidates with added 'distance_km' field.
    """
    results = []

    for candidate in candidates:
        clat = candidate.get(lat_field)
        clon = candidate.get(lon_field)

        if clat is None or clon is None:
            continue

        try:
            distance = haversine_distance(target_lat, target_lon, float(clat), float(clon))
        except (ValueError, TypeError):
            continue

        if distance <= radius_km:
            candidate_with_distance = candidate.copy()
            candidate_with_distance["distance_km"] = round(distance, 2)
            results.append(candidate_with_distance)

    results.sort(key=lambda x: x["distance_km"])
    return results[:limit]


def estimate_eta_minutes(
    distance_km: float,
    avg_speed_kmh: float = 40.0,
) -> float:
    """
    Estimate travel time in minutes based on straight-line distance.
    Applies a 1.3x road-factor to account for non-straight routes.
    """
    road_distance = distance_km * 1.3  # Approximate road factor
    if avg_speed_kmh <= 0:
        return 0.0
    return round((road_distance / avg_speed_kmh) * 60, 1)


def is_within_radius(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    radius_km: float,
) -> bool:
    """Check if two points are within a given radius."""
    return haversine_distance(lat1, lon1, lat2, lon2) <= radius_km


def get_bounding_box(
    lat: float, lon: float, radius_km: float
) -> Tuple[float, float, float, float]:
    """
    Get a bounding box around a point for pre-filtering queries.
    Returns (min_lat, max_lat, min_lon, max_lon).
    """
    lat_delta = radius_km / 111.0  # ~111 km per degree latitude
    lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))

    return (
        lat - lat_delta,
        lat + lat_delta,
        lon - lon_delta,
        lon + lon_delta,
    )
