from __future__ import annotations

import json
import sqlite3
import uuid

from .models import DriftForecast, utc_now
from .telemetry import latest_telemetry


MODEL_VERSION = "marine-drift-rule-0.1.0"


def create_drift_forecast(
    connection: sqlite3.Connection,
    session_id: str,
    object_profile: dict | None = None,
    horizon_minutes: int = 180,
) -> DriftForecast:
    latest = latest_telemetry(connection, session_id)
    if latest is None:
        raise ValueError("cannot forecast without telemetry datum")

    object_profile = object_profile or {
        "type": "person_or_small_vessel",
        "windage": "unknown",
        "leeway_factor": "conservative_default",
    }
    uncertainty_radius_m = max(250.0, latest.gps_accuracy_m * 4)
    datum = {
        "latitude": latest.latitude,
        "longitude": latest.longitude,
        "observed_at": latest.observed_at,
        "received_at": latest.received_at,
    }
    forecast = DriftForecast(
        id=str(uuid.uuid4()),
        session_id=session_id,
        created_at=utc_now(),
        model_name="MarineDrift",
        model_version=MODEL_VERSION,
        environmental_provenance=[
            {
                "provider": "mock-environmental-provider",
                "datasets": ["signals.mock.json"],
                "note": "fixture provenance until live providers are configured",
            }
        ],
        datum=datum,
        datum_uncertainty={
            "radius_m": uncertainty_radius_m,
            "basis": "gps accuracy and stale-contact conservative expansion",
        },
        object_profile=object_profile,
        horizon_minutes=horizon_minutes,
        confidence_contours=[
            contour(latest.latitude, latest.longitude, uncertainty_radius_m, 0.5),
            contour(latest.latitude + 0.01, latest.longitude + 0.015, uncertainty_radius_m * 2.2, 0.75),
            contour(latest.latitude + 0.025, latest.longitude + 0.032, uncertainty_radius_m * 3.8, 0.9),
        ],
        assumptions=[
            "Forecast is a probability surface, not a precise predicted point.",
            "Last known telemetry datum is valid.",
            "Environmental source is fixture data until provider registry is connected.",
            "Object profile uses conservative defaults when vessel/person details are unknown.",
        ],
    )
    connection.execute(
        """
        INSERT INTO drift_forecasts (
          id, session_id, created_at, model_name, model_version,
          environmental_provenance_json, datum_json, datum_uncertainty_json,
          object_profile_json, horizon_minutes, confidence_contours_json,
          assumptions_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            forecast.id,
            forecast.session_id,
            forecast.created_at,
            forecast.model_name,
            forecast.model_version,
            json.dumps(forecast.environmental_provenance),
            json.dumps(forecast.datum),
            json.dumps(forecast.datum_uncertainty),
            json.dumps(forecast.object_profile),
            forecast.horizon_minutes,
            json.dumps(forecast.confidence_contours),
            json.dumps(forecast.assumptions),
        ),
    )
    connection.commit()
    return forecast


def latest_forecast(connection: sqlite3.Connection, session_id: str) -> DriftForecast | None:
    row = connection.execute(
        """
        SELECT * FROM drift_forecasts
        WHERE session_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (session_id,),
    ).fetchone()
    return row_to_forecast(row) if row else None


def row_to_forecast(row: sqlite3.Row) -> DriftForecast:
    return DriftForecast(
        id=row["id"],
        session_id=row["session_id"],
        created_at=row["created_at"],
        model_name=row["model_name"],
        model_version=row["model_version"],
        environmental_provenance=json.loads(row["environmental_provenance_json"]),
        datum=json.loads(row["datum_json"]),
        datum_uncertainty=json.loads(row["datum_uncertainty_json"]),
        object_profile=json.loads(row["object_profile_json"]),
        horizon_minutes=row["horizon_minutes"],
        confidence_contours=json.loads(row["confidence_contours_json"]),
        assumptions=json.loads(row["assumptions_json"]),
    )


def contour(latitude: float, longitude: float, radius_m: float, probability: float) -> dict:
    return {
        "type": "circle",
        "center": {"latitude": latitude, "longitude": longitude},
        "radius_m": round(radius_m, 2),
        "probability": probability,
    }

