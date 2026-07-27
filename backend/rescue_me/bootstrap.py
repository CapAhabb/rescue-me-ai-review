from __future__ import annotations

import sqlite3
import uuid

from .models import utc_now
from .states import SessionState


DEFAULT_POLICY_ID = "default-sar"


def seed_defaults(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO escalation_policies (
          id, heartbeat_late_after_s, contact_degraded_after_s,
          user_warning_after_s, contact_notification_after_s,
          incident_pending_after_s, emergency_active_after_s,
          responder_handoff_after_s, low_battery_percent, off_route_grace_s,
          no_user_response_s
        )
        VALUES (?, 180, 300, 420, 600, 900, 1200, 1800, 15, 120, 300)
        """,
        (DEFAULT_POLICY_ID,),
    )
    connection.commit()


def create_session(
    connection: sqlite3.Connection,
    owner_contact: str,
    policy_id: str = DEFAULT_POLICY_ID,
) -> str:
    session_id = str(uuid.uuid4())
    now = utc_now()
    connection.execute(
        """
        INSERT INTO sessions (id, state, policy_id, owner_contact, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (session_id, SessionState.DRAFT.value, policy_id, owner_contact, now),
    )
    connection.commit()
    return session_id


def activate_session(connection: sqlite3.Connection, session_id: str) -> None:
    connection.execute(
        "UPDATE sessions SET state = ?, activated_at = ? WHERE id = ?",
        (SessionState.ACTIVE.value, utc_now(), session_id),
    )
    connection.commit()


def add_emergency_contact(
    connection: sqlite3.Connection,
    session_id: str,
    label: str,
    email: str,
    is_default_responder: bool = False,
) -> str:
    contact_id = str(uuid.uuid4())
    connection.execute(
        """
        INSERT INTO emergency_contacts (id, session_id, label, email, is_default_responder)
        VALUES (?, ?, ?, ?, ?)
        """,
        (contact_id, session_id, label, email, int(is_default_responder)),
    )
    connection.commit()
    return contact_id


def add_float_plan_leg(connection: sqlite3.Connection, session_id: str, leg: dict) -> str:
    leg_id = str(uuid.uuid4())
    connection.execute(
        """
        INSERT INTO float_plan_legs (
          id, session_id, sequence, start_latitude, start_longitude,
          end_latitude, end_longitude, corridor_radius_m, min_speed_mps,
          max_speed_mps, heading_tolerance_deg, checkpoint_due_at,
          stop_tolerance_s, timing_tolerance_s
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            leg_id,
            session_id,
            leg["sequence"],
            leg["start_latitude"],
            leg["start_longitude"],
            leg["end_latitude"],
            leg["end_longitude"],
            leg["corridor_radius_m"],
            leg.get("min_speed_mps"),
            leg.get("max_speed_mps"),
            leg.get("heading_tolerance_deg"),
            leg.get("checkpoint_due_at"),
            leg.get("stop_tolerance_s"),
            leg.get("timing_tolerance_s", 300),
        ),
    )
    connection.commit()
    return leg_id

