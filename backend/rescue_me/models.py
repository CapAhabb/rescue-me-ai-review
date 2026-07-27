from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class TelemetryEvent:
    session_id: str
    device_id: str
    device_sequence: int
    observed_at: str
    received_at: str
    latitude: float
    longitude: float
    gps_accuracy_m: float
    speed_mps: float | None
    course_deg: float | None
    heading_deg: float | None
    battery_percent: float | None
    network_state: str
    provenance: str
    payload_hash: str
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FloatPlanLeg:
    sequence: int
    start_latitude: float
    start_longitude: float
    end_latitude: float
    end_longitude: float
    corridor_radius_m: float
    min_speed_mps: float | None
    max_speed_mps: float | None
    heading_tolerance_deg: float | None
    checkpoint_due_at: str | None
    stop_tolerance_s: int | None
    timing_tolerance_s: int


@dataclass(frozen=True)
class EscalationPolicy:
    id: str
    heartbeat_late_after_s: int
    contact_degraded_after_s: int
    user_warning_after_s: int
    contact_notification_after_s: int
    incident_pending_after_s: int
    emergency_active_after_s: int
    responder_handoff_after_s: int
    low_battery_percent: int
    off_route_grace_s: int
    no_user_response_s: int


@dataclass(frozen=True)
class DriftForecast:
    id: str
    session_id: str
    created_at: str
    model_name: str
    model_version: str
    environmental_provenance: list[dict[str, Any]]
    datum: dict[str, Any]
    datum_uncertainty: dict[str, Any]
    object_profile: dict[str, Any]
    horizon_minutes: int
    confidence_contours: list[dict[str, Any]]
    assumptions: list[str]


@dataclass(frozen=True)
class DerivedSession:
    session_id: str
    state: str
    reason: str
    latest_telemetry: TelemetryEvent | None
    active_alerts: list[str]


@dataclass(frozen=True)
class AiAdvisory:
    id: str
    session_id: str
    created_at: str
    model_name: str
    model_version: str
    advisory_text: str
    supporting_evidence: list[dict[str, Any]]
    confidence: float
    accepted_for_escalation: bool = False
