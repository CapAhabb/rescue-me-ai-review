from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import sqlite3
import uuid

from .models import utc_now


def create_share_token(
    connection: sqlite3.Connection,
    session_id: str,
    contact_id: str | None,
    ttl_minutes: int = 240,
    scope: str = "incident:read",
) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    connection.execute(
        """
        INSERT INTO incident_share_tokens (
          id, session_id, contact_id, token_hash, scope, expires_at, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()),
            session_id,
            contact_id,
            token_hash(token),
            scope,
            expires_at.isoformat().replace("+00:00", "Z"),
            utc_now(),
        ),
    )
    connection.commit()
    return token


def revoke_share_token(connection: sqlite3.Connection, token: str) -> None:
    connection.execute(
        "UPDATE incident_share_tokens SET revoked_at = ? WHERE token_hash = ?",
        (utc_now(), token_hash(token)),
    )
    connection.commit()


def validate_share_token(
    connection: sqlite3.Connection,
    token: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> sqlite3.Row | None:
    row = connection.execute(
        "SELECT * FROM incident_share_tokens WHERE token_hash = ?",
        (token_hash(token),),
    ).fetchone()
    token_id = row["id"] if row else None
    outcome = "not_found"
    if row:
        if row["revoked_at"]:
            outcome = "revoked"
            row = None
        elif parse_time(row["expires_at"]) <= datetime.now(timezone.utc):
            outcome = "expired"
            row = None
        else:
            outcome = "allowed"
    log_access(connection, token_id, ip_address, user_agent, outcome)
    return row


def acknowledge_contact(connection: sqlite3.Connection, contact_id: str, state: str = "ACKNOWLEDGED") -> None:
    connection.execute(
        """
        UPDATE emergency_contacts
        SET acknowledgment_state = ?, acknowledged_at = ?
        WHERE id = ?
        """,
        (state, utc_now(), contact_id),
    )
    connection.commit()


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def log_access(
    connection: sqlite3.Connection,
    token_id: str | None,
    ip_address: str | None,
    user_agent: str | None,
    outcome: str,
) -> None:
    connection.execute(
        """
        INSERT INTO incident_share_access_logs (
          id, token_id, accessed_at, ip_address, user_agent, outcome
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (str(uuid.uuid4()), token_id, utc_now(), ip_address, user_agent, outcome),
    )
    connection.commit()


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
