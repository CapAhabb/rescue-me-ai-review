from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlparse

from .bootstrap import activate_session, add_emergency_contact, add_float_plan_leg, create_session, seed_defaults
from .db import connect, migrate
from .forecast import create_drift_forecast, latest_forecast
from .share_tokens import acknowledge_contact, create_share_token, validate_share_token
from .state_machine import reconcile_session_state
from .telemetry import ingest_telemetry


class RescueApi(BaseHTTPRequestHandler):
    db_path = Path("rescue_me.sqlite3")

    def do_POST(self) -> None:
        connection = open_db(self.db_path)
        try:
            path = urlparse(self.path).path
            if path == "/sessions":
                body = self.read_json()
                session_id = create_session(connection, body["owner_contact"])
                for contact in body.get("emergency_contacts", []):
                    add_emergency_contact(
                        connection,
                        session_id,
                        contact["label"],
                        contact["email"],
                        contact.get("is_default_responder", False),
                    )
                for leg in body.get("float_plan_legs", []):
                    add_float_plan_leg(connection, session_id, leg)
                self.write_json(201, {"session_id": session_id, "state": "DRAFT"})
                return

            if path.endswith("/activate"):
                session_id = path.split("/")[2]
                activate_session(connection, session_id)
                self.write_json(200, {"session_id": session_id, "state": "ACTIVE"})
                return

            if path.endswith("/telemetry"):
                session_id = path.split("/")[2]
                event, duplicate = ingest_telemetry(connection, session_id, self.read_json())
                derived = reconcile_session_state(connection, session_id)
                self.write_json(
                    202,
                    {
                        "accepted": True,
                        "duplicate": duplicate,
                        "session_state": derived.state,
                        "event": {
                            "device_id": event.device_id,
                            "device_sequence": event.device_sequence,
                            "observed_at": event.observed_at,
                            "received_at": event.received_at,
                        },
                    },
                )
                return

            if path.endswith("/forecasts"):
                session_id = path.split("/")[2]
                forecast = create_drift_forecast(connection, session_id)
                self.write_json(201, forecast_to_json(forecast))
                return

            if path.endswith("/share-tokens"):
                session_id = path.split("/")[2]
                body = self.read_json()
                token = create_share_token(
                    connection,
                    session_id,
                    body.get("contact_id"),
                    body.get("ttl_minutes", 240),
                )
                self.write_json(201, {"token": token, "scope": "incident:read"})
                return

            if path.endswith("/acknowledge"):
                contact_id = path.split("/")[2]
                body = self.read_json()
                acknowledge_contact(connection, contact_id, body.get("state", "ACKNOWLEDGED"))
                self.write_json(200, {"contact_id": contact_id, "acknowledgment_state": body.get("state", "ACKNOWLEDGED")})
                return

            self.write_json(404, {"error": "not found"})
        finally:
            connection.close()

    def do_GET(self) -> None:
        connection = open_db(self.db_path)
        try:
            path = urlparse(self.path).path
            if path.startswith("/sessions/") and path.endswith("/state"):
                session_id = path.split("/")[2]
                derived = reconcile_session_state(connection, session_id)
                self.write_json(
                    200,
                    {
                        "session_id": session_id,
                        "state": derived.state,
                        "reason": derived.reason,
                        "active_alerts": derived.active_alerts,
                    },
                )
                return

            if path.startswith("/sessions/") and path.endswith("/forecasts/latest"):
                session_id = path.split("/")[2]
                forecast = latest_forecast(connection, session_id)
                self.write_json(200, forecast_to_json(forecast) if forecast else {"forecast": None})
                return

            if path == "/incident-share":
                token = self.headers.get("X-Incident-Share-Token", "")
                row = validate_share_token(
                    connection,
                    token,
                    self.client_address[0],
                    self.headers.get("User-Agent"),
                )
                if row is None:
                    self.write_json(403, {"error": "invalid, expired, or revoked token"})
                    return
                derived = reconcile_session_state(connection, row["session_id"])
                forecast = latest_forecast(connection, row["session_id"])
                self.write_json(
                    200,
                    {
                        "session_id": row["session_id"],
                        "state": derived.state,
                        "forecast": forecast_to_json(forecast) if forecast else None,
                    },
                )
                return

            self.write_json(404, {"error": "not found"})
        finally:
            connection.close()

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def write_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def open_db(path: Path):
    connection = connect(path)
    migrate(connection)
    seed_defaults(connection)
    return connection


def forecast_to_json(forecast) -> dict:
    return {
        "id": forecast.id,
        "session_id": forecast.session_id,
        "created_at": forecast.created_at,
        "model_name": forecast.model_name,
        "model_version": forecast.model_version,
        "environmental_provenance": forecast.environmental_provenance,
        "datum": forecast.datum,
        "datum_uncertainty": forecast.datum_uncertainty,
        "object_profile": forecast.object_profile,
        "horizon_minutes": forecast.horizon_minutes,
        "confidence_contours": forecast.confidence_contours,
        "assumptions": forecast.assumptions,
    }


def run(host: str = "127.0.0.1", port: int = 8088, db_path: str = "rescue_me.sqlite3") -> None:
    RescueApi.db_path = Path(db_path)
    server = ThreadingHTTPServer((host, port), RescueApi)
    print(f"rescue_me backend listening on http://{host}:{port}")
    server.serve_forever()

