from __future__ import annotations

from datetime import datetime, timezone
import json
import sqlite3
import uuid

from .geometry import bearing_deg, distance_to_leg_m, heading_delta_deg
from .models import DerivedSession, EscalationPolicy, FloatPlanLeg, utc_now
from .states import SessionState, TERMINAL_STATES
from .telemetry import latest_telemetry, parse_time


def derive_session_state(
    connection: sqlite3.Connection,
    session_id: str,
    now: datetime | None = None,
) -> DerivedSession:
    now = now or datetime.now(timezone.utc)
    session = connection.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if session is None:
        raise ValueError(f"unknown session {session_id}")

    stored_state = SessionState(session["state"])
    latest = latest_telemetry(connection, session_id)
    alerts: list[str] = []

    if stored_state in TERMINAL_STATES or stored_state == SessionState.DRAFT:
        return DerivedSession(session_id, stored_state.value, "stored terminal or draft state", latest, alerts)

    policy = load_policy(connection, session["policy_id"])
    if latest is None:
        elapsed = seconds_since(session["activated_at"] or session["created_at"], now)
    else:
        elapsed = (now - parse_time(latest.received_at)).total_seconds()
        if latest.battery_percent is not None and latest.battery_percent <= policy.low_battery_percent:
            alerts.append("LOW_BATTERY")
        if latest.network_state in {"offline", "poor", "unknown"}:
            alerts.append("NETWORK_DEGRADED")
        alerts.extend(route_alerts(connection, session_id, latest))

    state, reason = state_from_policy(policy, elapsed, alerts)
    return DerivedSession(session_id, state.value, reason, latest, alerts)


def reconcile_session_state(
    connection: sqlite3.Connection,
    session_id: str,
    now: datetime | None = None,
) -> DerivedSession:
    derived = derive_session_state(connection, session_id, now)
    current = connection.execute("SELECT state FROM sessions WHERE id = ?", (session_id,)).fetchone()["state"]
    if current != derived.state:
        connection.execute(
            "UPDATE sessions SET state = ? WHERE id = ?",
            (derived.state, session_id),
        )
        connection.execute(
            """
            INSERT INTO session_transition_events (
              id, session_id, from_state, to_state, reason, created_at, evidence_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                session_id,
                current,
                derived.state,
                derived.reason,
                utc_now(),
                json.dumps({"alerts": derived.active_alerts}),
            ),
        )
        connection.commit()
    return derived


def state_from_policy(
    policy: EscalationPolicy,
    seconds_since_contact: float,
    alerts: list[str],
) -> tuple[SessionState, str]:
    if seconds_since_contact >= policy.responder_handoff_after_s:
        return SessionState.RESPONDER_HANDOFF, "responder handoff threshold exceeded"
    if seconds_since_contact >= policy.emergency_active_after_s:
        return SessionState.EMERGENCY_ACTIVE, "emergency activation threshold exceeded"
    if seconds_since_contact >= policy.incident_pending_after_s:
        return SessionState.INCIDENT_PENDING, "incident pending threshold exceeded"
    if seconds_since_contact >= policy.contact_notification_after_s:
        return SessionState.CONTACT_NOTIFICATION, "contact notification threshold exceeded"
    if seconds_since_contact >= policy.user_warning_after_s or "OFF_ROUTE" in alerts:
        return SessionState.USER_WARNING, "user warning threshold or off-route alert"
    if seconds_since_contact >= policy.contact_degraded_after_s or "NETWORK_DEGRADED" in alerts:
        return SessionState.CONTACT_DEGRADED, "contact degraded by timeout or network state"
    if seconds_since_contact >= policy.heartbeat_late_after_s:
        return SessionState.HEARTBEAT_LATE, "heartbeat late threshold exceeded"
    return SessionState.ACTIVE, "heartbeat healthy"


def load_policy(connection: sqlite3.Connection, policy_id: str) -> EscalationPolicy:
    row = connection.execute("SELECT * FROM escalation_policies WHERE id = ?", (policy_id,)).fetchone()
    return EscalationPolicy(
        id=row["id"],
        heartbeat_late_after_s=row["heartbeat_late_after_s"],
        contact_degraded_after_s=row["contact_degraded_after_s"],
        user_warning_after_s=row["user_warning_after_s"],
        contact_notification_after_s=row["contact_notification_after_s"],
        incident_pending_after_s=row["incident_pending_after_s"],
        emergency_active_after_s=row["emergency_active_after_s"],
        responder_handoff_after_s=row["responder_handoff_after_s"],
        low_battery_percent=row["low_battery_percent"],
        off_route_grace_s=row["off_route_grace_s"],
        no_user_response_s=row["no_user_response_s"],
    )


def route_alerts(connection: sqlite3.Connection, session_id: str, latest) -> list[str]:
    legs = load_float_plan_legs(connection, session_id)
    if not legs:
        return []
    distances = [
        (
            distance_to_leg_m(
                latest.latitude,
                latest.longitude,
                leg.start_latitude,
                leg.start_longitude,
                leg.end_latitude,
                leg.end_longitude,
            ),
            leg,
        )
        for leg in legs
    ]
    distance, leg = min(distances, key=lambda item: item[0])
    alerts = []
    if distance > leg.corridor_radius_m + latest.gps_accuracy_m:
        alerts.append("OFF_ROUTE")
    if leg.min_speed_mps is not None and latest.speed_mps is not None and latest.speed_mps < leg.min_speed_mps:
        alerts.append("TOO_SLOW")
    if leg.max_speed_mps is not None and latest.speed_mps is not None and latest.speed_mps > leg.max_speed_mps:
        alerts.append("TOO_FAST")
    if leg.heading_tolerance_deg is not None and latest.course_deg is not None:
        expected = bearing_deg(leg.start_latitude, leg.start_longitude, leg.end_latitude, leg.end_longitude)
        if heading_delta_deg(expected, latest.course_deg) > leg.heading_tolerance_deg:
            alerts.append("HEADING_DEVIATION")
    return alerts


def load_float_plan_legs(connection: sqlite3.Connection, session_id: str) -> list[FloatPlanLeg]:
    rows = connection.execute(
        "SELECT * FROM float_plan_legs WHERE session_id = ? ORDER BY sequence",
        (session_id,),
    ).fetchall()
    return [
        FloatPlanLeg(
            sequence=row["sequence"],
            start_latitude=row["start_latitude"],
            start_longitude=row["start_longitude"],
            end_latitude=row["end_latitude"],
            end_longitude=row["end_longitude"],
            corridor_radius_m=row["corridor_radius_m"],
            min_speed_mps=row["min_speed_mps"],
            max_speed_mps=row["max_speed_mps"],
            heading_tolerance_deg=row["heading_tolerance_deg"],
            checkpoint_due_at=row["checkpoint_due_at"],
            stop_tolerance_s=row["stop_tolerance_s"],
            timing_tolerance_s=row["timing_tolerance_s"],
        )
        for row in rows
    ]


def seconds_since(value: str, now: datetime) -> float:
    return (now - parse_time(value)).total_seconds()

