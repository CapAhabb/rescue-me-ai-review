from math import atan2, cos, degrees, radians, sin, sqrt

EARTH_RADIUS_M = 6_371_000


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)
    a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * atan2(sqrt(a), sqrt(1 - a))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    delta_lambda = radians(lon2 - lon1)
    y = sin(delta_lambda) * cos(phi2)
    x = cos(phi1) * sin(phi2) - sin(phi1) * cos(phi2) * cos(delta_lambda)
    return (degrees(atan2(y, x)) + 360) % 360


def heading_delta_deg(expected: float, actual: float) -> float:
    return abs((actual - expected + 180) % 360 - 180)


def distance_to_leg_m(
    lat: float,
    lon: float,
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
) -> float:
    start_distance = haversine_m(lat, lon, start_lat, start_lon)
    end_distance = haversine_m(lat, lon, end_lat, end_lon)
    leg_distance = max(haversine_m(start_lat, start_lon, end_lat, end_lon), 1)
    s = (start_distance + end_distance + leg_distance) / 2
    area_term = max(s * (s - start_distance) * (s - end_distance) * (s - leg_distance), 0)
    return 2 * sqrt(area_term) / leg_distance

