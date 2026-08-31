import math
from datetime import datetime
from typing import Dict, Optional, Tuple


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Haversine distance in meters between two GPS coordinates."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def compute_spatial_similarity(
    lat1: Optional[float],
    lon1: Optional[float],
    lat2: Optional[float],
    lon2: Optional[float],
    max_radius_meters: float = 2000.0,
) -> float:
    """Compute spatial similarity score between 0.0 (far) and 1.0 (co-located)."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0.5  # Neutral score if location missing

    dist = haversine_distance_meters(lat1, lon1, lat2, lon2)
    if dist >= max_radius_meters:
        return 0.0
    return max(0.0, 1.0 - (dist / max_radius_meters))


def compute_temporal_similarity(
    dt1, dt2, max_delta_seconds: float = 7200.0
) -> float:
    """Compute temporal similarity score between 0.0 (hours apart) and 1.0 (simultaneous)."""
    if isinstance(dt1, (int, float)):
        dt1 = datetime.utcfromtimestamp(dt1)
    if isinstance(dt2, (int, float)):
        dt2 = datetime.utcfromtimestamp(dt2)

    delta_sec = abs((dt1 - dt2).total_seconds())
    if delta_sec >= max_delta_seconds:
        return 0.0
    return max(0.0, 1.0 - (delta_sec / max_delta_seconds))


def compute_categorical_similarity(cat1: str, cat2: str) -> float:
    """Compute categorical similarity score."""
    c1 = (cat1 or "").strip().lower()
    c2 = (cat2 or "").strip().lower()
    if not c1 or not c2:
        return 0.5
    if c1 == c2:
        return 1.0

    # Category grouping overlap checks
    related_groups = [
        {"fire", "explosion", "smoke", "wildfire"},
        {"flood", "tsunami", "water_leak", "inundation"},
        {"medical", "casualty", "injury", "outbreak"},
        {"structure_collapse", "earthquake", "landslide", "debris"},
    ]
    for group in related_groups:
        if c1 in group and c2 in group:
            return 0.75
    return 0.0


def compute_text_similarity(desc1: str, desc2: str) -> float:
    """Compute text similarity score using token Jaccard similarity."""
    t1 = set(w.lower() for w in (desc1 or "").split() if len(w) > 2)
    t2 = set(w.lower() for w in (desc2 or "").split() if len(w) > 2)
    if not t1 or not t2:
        return 0.0
    intersection = t1.intersection(t2)
    union = t1.union(t2)
    return len(intersection) / float(len(union))


class IncidentSimilarityEngine:
    """Multi-factor similarity scoring engine combining spatial, temporal, categorical, and text metrics."""

    def __init__(
        self,
        weight_spatial: float = 0.35,
        weight_temporal: float = 0.25,
        weight_categorical: float = 0.20,
        weight_text: float = 0.20,
    ):
        self.weight_spatial = weight_spatial
        self.weight_temporal = weight_temporal
        self.weight_categorical = weight_categorical
        self.weight_text = weight_text

    def calculate_similarity_score(
        self,
        report1_data: dict,
        report2_data: dict,
    ) -> Dict[str, float]:
        """
        Calculate composite multi-factor similarity score between two reports or report & incident.
        Expects keys: lat, lon, created_at (datetime), category, description.
        """
        s_spatial = compute_spatial_similarity(
            report1_data.get("lat"),
            report1_data.get("lon"),
            report2_data.get("lat"),
            report2_data.get("lon"),
        )
        s_temporal = compute_temporal_similarity(
            report1_data.get("created_at") or datetime.utcnow(),
            report2_data.get("created_at") or datetime.utcnow(),
        )
        s_cat = compute_categorical_similarity(
            report1_data.get("category", ""),
            report2_data.get("category", ""),
        )
        s_text = compute_text_similarity(
            report1_data.get("description", ""),
            report2_data.get("description", ""),
        )

        composite = (
            (s_spatial * self.weight_spatial)
            + (s_temporal * self.weight_temporal)
            + (s_cat * self.weight_categorical)
            + (s_text * self.weight_text)
        )

        return {
            "composite": round(composite, 4),
            "spatial": round(s_spatial, 4),
            "temporal": round(s_temporal, 4),
            "categorical": round(s_cat, 4),
            "text": round(s_text, 4),
        }
