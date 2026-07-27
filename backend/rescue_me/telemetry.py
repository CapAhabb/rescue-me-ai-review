from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import sqlite3
import uuid

from .models import TelemetryEvent, utc_now


def ingest_telemetry(
    connection: sqlite3.Connection,
    session_id: str,
    payload: dict,
    provenance: str = "mobile-client",
) -> tuple[TelemetryEvent, bool]:
    raw_payload = canonical_json(payload)
    payload_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
    received_at = utc_now()
    event = TelemetryEvent(
        session_id=session_id,
        device_id=str(payload["device_id"]),
        device_sequence=int(payload["device_sequence"]),
        observed_at=str(payload["observed_at"]),
        received_at=received_at,
        latitude=float(payload["latitude"]),
        longitude=float(payload["longitude"]),
        gps_accuracy_m=float(payload["gps_accuracy_m"]),
        speed_mps=optional_float(payload.get("speed_mps")),
        course_deg=optional_float(payload.get("course_deg")),
        heading_deg=optional_float(payload.get("heading_deg")),
        battery_percent=optional_float(payload.get("battery_percent")),
        network_state=str(payload.get("network_state", "unknown")),
        provenance=provenance,
        payload_hash=payload_hash,
        raw_payload=payload,
    )

    try:
        connection.execute(
            """
            INSERT INTO telemetry_events (
              id, session_id, device_id, device_sequence, observed_at, received_at,
              latitude, longitude, gps_accuracy_m, speed_mps, course_deg,
              heading_deg, battery_percent, network_state, provenance,
              payload_hash, raw_payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                event.session_id,
                event.device_id,
                event.device_sequence,
                event.observed_at,
                event.received_at,
                event.latitude,
                event.longitude,
                event.gps_accuracy_m,
                event.speed_mps,
                event.course_deg,
                event.heading_deg,
                event.battery_percent,
                event.network_state,
                event.provenance,
                event.payload_hash,
                raw_payload,
            ),
        )
        connection.commit()
        return event, False
    except sqlite3.IntegrityError:
        existing = connection.execute(
            """
            SELECT * FROM telemetry_events
            WHERE session_id = ? AND device_id = ? AND device_sequence = ?
            """,
            (event.session_id, event.device_id, event.device_sequence),
        ).fetchone()
        return row_to_event(existing), True


def latest_telemetry(connection: sqlite3.Connection, session_id: str) -> TelemetryEvent | None:
    row = connection.execute(
        """
        SELECT * FROM telemetry_events
        WHERE session_id = ?
        ORDER BY observed_at DESC, received_at DESC
        LIMIT 1
        """,
        (session_id,),
    ).fetchone()
    return row_to_event(row) if row else None


def telemetry_replay(connection: sqlite3.Connection, session_id: str) -> list[TelemetryEvent]:
    rows = connection.execute(
        """
        SELECT * FROM telemetry_events
        WHERE session_id = ?
        ORDER BY observed_at ASC, device_sequence ASC, received_at ASC
        """,
        (session_id,),
    ).fetchall()
    return [row_to_event(row) for row in rows]


def row_to_event(row: sqlite3.Row) -> TelemetryEvent:
    return TelemetryEvent(
        session_id=row["session_id"],
        device_id=row["device_id"],
        device_sequence=row["device_sequence"],
        observed_at=row["observed_at"],
        received_at=row["received_at"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        gps_accuracy_m=row["gps_accuracy_m"],
        speed_mps=row["speed_mps"],
        course_deg=row["course_deg"],
        heading_deg=row["heading_deg"],
        battery_percent=row["battery_percent"],
        network_state=row["network_state"],
        provenance=row["provenance"],
        payload_hash=row["payload_hash"],
        raw_payload=json.loads(row["raw_payload_json"]),
    )


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def optional_float(value) -> float | None:
    return None if value is None else float(value)


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

