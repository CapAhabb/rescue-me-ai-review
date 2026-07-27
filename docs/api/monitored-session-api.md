# Monitored Session API

The mobile client is a telemetry producer only. The backend owns session state,
escalation timers, contact permissions, and forecast history.

## Create Session

`POST /sessions`

```json
{
  "owner_contact": "captain@example.com",
  "emergency_contacts": [
    {
      "label": "Primary contact",
      "email": "contact@example.com"
    }
  ],
  "float_plan_legs": [
    {
      "sequence": 1,
      "start_latitude": 43.0,
      "start_longitude": -87.9,
      "end_latitude": 43.1,
      "end_longitude": -87.7,
      "corridor_radius_m": 750,
      "min_speed_mps": 0.5,
      "max_speed_mps": 12,
      "heading_tolerance_deg": 55,
      "timing_tolerance_s": 300
    }
  ]
}
```

## Activate Session

`POST /sessions/{session_id}/activate`

## Ingest Telemetry

`POST /sessions/{session_id}/telemetry`

Telemetry ingestion is idempotent by `(session_id, device_id, device_sequence)`.

```json
{
  "device_id": "phone-1",
  "device_sequence": 42,
  "observed_at": "2026-07-21T14:00:00Z",
  "latitude": 43.05,
  "longitude": -87.85,
  "gps_accuracy_m": 8,
  "speed_mps": 2.3,
  "course_deg": 72,
  "heading_deg": 74,
  "battery_percent": 81,
  "network_state": "online"
}
```

## Read State

`GET /sessions/{session_id}/state`

Returns derived state, reason, and active alerts.

## Create Forecast

`POST /sessions/{session_id}/forecasts`

Returns probability contours and uncertainty metadata. The primary forecast is
never a single precise predicted point.

## Create Incident Share Token

`POST /sessions/{session_id}/share-tokens`

```json
{
  "contact_id": "optional-contact-id",
  "ttl_minutes": 240
}
```

## Read Incident Share

`GET /incident-share`

Header:

```text
X-Incident-Share-Token: token
```

Access is logged. Expired and revoked tokens are denied.

## AI Advisory Rule

AI outputs are not accepted as escalation transitions. They may be stored as
advisories only when they include supporting evidence. Deterministic policy
evaluation remains responsible for state changes.
