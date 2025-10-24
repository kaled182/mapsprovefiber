from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt
from typing import Iterable, List, Dict, Any

__all__ = ["haversine_km", "calculate_path_length", "sanitize_path_points"]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula a distância entre dois pontos geográficos usando Haversine."""
    radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return radius_km * c


def calculate_path_length(path_points: Iterable[Dict[str, float]]) -> float:
    """Soma a distância aproximada de uma rota em quilômetros."""
    points: List[Dict[str, float]] = list(path_points or [])
    if len(points) < 2:
        return 0.0

    total = 0.0
    for current, nxt in zip(points, points[1:]):
        lat1, lng1 = current.get("lat"), current.get("lng")
        lat2, lng2 = nxt.get("lat"), nxt.get("lng")
        if None in (lat1, lng1, lat2, lng2):
            continue
        total += haversine_km(float(lat1), float(lng1), float(lat2), float(lng2))
    return round(total, 3)


def sanitize_path_points(raw_points: Any, *, allow_empty: bool = False) -> List[Dict[str, float]]:
    """
    Normaliza uma lista de pontos de rota, filtrando entradas inválidas.

    Quando `allow_empty=False`, exige pelo menos dois pontos válidos.
    """
    sanitized: List[Dict[str, float]] = []
    if not isinstance(raw_points, list):
        raw_points = []

    for entry in raw_points:
        if not isinstance(entry, dict):
            continue
        lat = entry.get("lat")
        lng = entry.get("lng")
        try:
            lat = float(lat)
            lng = float(lng)
        except (TypeError, ValueError):
            continue
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            sanitized.append({"lat": lat, "lng": lng})

    if len(sanitized) == 1:
        raise ValueError("Path precisa de pelo menos 2 pontos válidos")

    if not allow_empty and len(sanitized) < 2:
        raise ValueError("Path precisa de pelo menos 2 pontos válidos")
    return sanitized
