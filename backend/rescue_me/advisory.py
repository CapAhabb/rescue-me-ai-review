from __future__ import annotations

import json
import sqlite3
import uuid

from .models import AiAdvisory, utc_now


def record_ai_advisory(
    connection: sqlite3.Connection,
    session_id: str,
    model_name: str,
    model_version: str,
    advisory_text: str,
    supporting_evidence: list[dict],
    confidence: float,
) -> AiAdvisory:
    if not supporting_evidence:
        raise ValueError("AI advisory requires supporting evidence")
    advisory = AiAdvisory(
        id=str(uuid.uuid4()),
        session_id=session_id,
        created_at=utc_now(),
        model_name=model_name,
        model_version=model_version,
        advisory_text=advisory_text,
        supporting_evidence=supporting_evidence,
        confidence=confidence,
    )
    connection.execute(
        """
        INSERT INTO ai_advisories (
          id, session_id, created_at, model_name, model_version,
          advisory_text, supporting_evidence_json, confidence,
          accepted_for_escalation
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            advisory.id,
            advisory.session_id,
            advisory.created_at,
            advisory.model_name,
            advisory.model_version,
            advisory.advisory_text,
            json.dumps(advisory.supporting_evidence),
            advisory.confidence,
        ),
    )
    connection.commit()
    return advisory

