import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rescue_me.bootstrap import (
    activate_session,
    add_emergency_contact,
    add_float_plan_leg,
    create_session,
    seed_defaults,
)
from rescue_me.advisory import record_ai_advisory
from rescue_me.db import connect, migrate
from rescue_me.forecast import create_drift_forecast
from rescue_me.share_tokens import acknowledge_contact, create_share_token, revoke_share_token, validate_share_token
from rescue_me.state_machine import derive_session_state, reconcile_session_state
from rescue_me.telemetry import ingest_telemetry, parse_time, telemetry_replay


class MonitoredSessionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3")
        self.db = connect(self.tmp.name)
        migrate(self.db)
        seed_defaults(self.db)
        self.session_id = create_session(self.db, "owner@example.com")
        add_float_plan_leg(
            self.db,
            self.session_id,
            {
                "sequence": 1,
                "start_latitude": 43.0,
                "start_longitude": -87.9,
                "end_latitude": 43.1,
                "end_longitude": -87.7,
                "corridor_radius_m": 750,
                "min_speed_mps": 0.2,
                "max_speed_mps": 15,
                "heading_tolerance_deg": 70,
                "timing_tolerance_s": 300,
            },
        )
        activate_session(self.db, self.session_id)

    def tearDown(self):
        self.db.close()
        self.tmp.close()

    def test_duplicate_telemetry_is_idempotent(self):
        payload = telemetry_payload(device_sequence=1)
        first, first_duplicate = ingest_telemetry(self.db, self.session_id, payload)
        second, second_duplicate = ingest_telemetry(self.db, self.session_id, payload)

        rows = self.db.execute("SELECT COUNT(*) AS count FROM telemetry_events").fetchone()
        self.assertFalse(first_duplicate)
        self.assertTrue(second_duplicate)
        self.assertEqual(first.device_sequence, second.device_sequence)
        self.assertEqual(rows["count"], 1)

    def test_replay_orders_out_of_order_packets_by_observed_time(self):
        later = telemetry_payload(device_sequence=2, observed_at="2026-07-21T14:10:00Z")
        earlier = telemetry_payload(device_sequence=1, observed_at="2026-07-21T14:00:00Z")
        ingest_telemetry(self.db, self.session_id, later)
        ingest_telemetry(self.db, self.session_id, earlier)

        replay = telemetry_replay(self.db, self.session_id)

        self.assertEqual([event.device_sequence for event in replay], [1, 2])

    def test_state_transitions_are_policy_driven(self):
        event, _ = ingest_telemetry(self.db, self.session_id, telemetry_payload())
        receipt_time = parse_time(event.received_at)
        derived = derive_session_state(
            self.db,
            self.session_id,
            now=receipt_time + timedelta(seconds=120),
        )
        late = reconcile_session_state(
            self.db,
            self.session_id,
            now=receipt_time + timedelta(seconds=480),
        )

        self.assertEqual(derived.state, "ACTIVE")
        self.assertEqual(late.state, "USER_WARNING")

    def test_off_route_packet_triggers_user_warning(self):
        event, _ = ingest_telemetry(
            self.db,
            self.session_id,
            telemetry_payload(latitude=44.0, longitude=-88.6, gps_accuracy_m=5),
        )
        receipt_time = parse_time(event.received_at)

        derived = reconcile_session_state(
            self.db,
            self.session_id,
            now=receipt_time + timedelta(seconds=60),
        )

        self.assertEqual(derived.state, "USER_WARNING")
        self.assertIn("OFF_ROUTE", derived.active_alerts)

    def test_forecast_returns_contours_not_primary_precise_point(self):
        ingest_telemetry(self.db, self.session_id, telemetry_payload())

        forecast = create_drift_forecast(self.db, self.session_id)

        self.assertEqual(forecast.model_version, "marine-drift-rule-0.1.0")
        self.assertGreaterEqual(len(forecast.confidence_contours), 3)
        self.assertIn("radius_m", forecast.confidence_contours[0])
        self.assertIn("datum_uncertainty", forecast.__dict__)

    def test_share_token_expires_revokes_logs_and_acknowledges(self):
        contact_id = add_emergency_contact(self.db, self.session_id, "Primary", "contact@example.com")
        token = create_share_token(self.db, self.session_id, contact_id, ttl_minutes=5)

        allowed = validate_share_token(self.db, token, "127.0.0.1", "test")
        acknowledge_contact(self.db, contact_id)
        revoke_share_token(self.db, token)
        revoked = validate_share_token(self.db, token, "127.0.0.1", "test")
        logs = self.db.execute("SELECT COUNT(*) AS count FROM incident_share_access_logs").fetchone()
        contact = self.db.execute("SELECT acknowledgment_state FROM emergency_contacts WHERE id = ?", (contact_id,)).fetchone()

        self.assertIsNotNone(allowed)
        self.assertIsNone(revoked)
        self.assertEqual(logs["count"], 2)
        self.assertEqual(contact["acknowledgment_state"], "ACKNOWLEDGED")

    def test_ai_advisory_requires_evidence_and_cannot_drive_escalation(self):
        with self.assertRaises(ValueError):
            record_ai_advisory(
                self.db,
                self.session_id,
                "advisor",
                "0.1",
                "Escalate now",
                [],
                0.9,
            )

        advisory = record_ai_advisory(
            self.db,
            self.session_id,
            "advisor",
            "0.1",
            "Check shoreline access points",
            [{"type": "telemetry", "id": "latest"}],
            0.6,
        )
        row = self.db.execute("SELECT accepted_for_escalation FROM ai_advisories WHERE id = ?", (advisory.id,)).fetchone()

        self.assertEqual(row["accepted_for_escalation"], 0)


def telemetry_payload(
    device_sequence=1,
    observed_at="2026-07-21T14:00:00Z",
    latitude=43.05,
    longitude=-87.8,
    gps_accuracy_m=8,
):
    return {
        "device_id": "phone-1",
        "device_sequence": device_sequence,
        "observed_at": observed_at,
        "latitude": latitude,
        "longitude": longitude,
        "gps_accuracy_m": gps_accuracy_m,
        "speed_mps": 2.4,
        "course_deg": 63,
        "heading_deg": 64,
        "battery_percent": 80,
        "network_state": "online",
    }


if __name__ == "__main__":
    unittest.main()
