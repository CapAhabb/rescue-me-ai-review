# ADR 0004: Server-Authoritative Monitored Sessions

## Status

Accepted.

## Context

Rescue Me needs live GPS monitoring against a float plan, emergency escalation
when the user stops responding, and responder access after a device dies. A
mobile device cannot be the authoritative server because it may lose network,
enter battery-saving mode, break GPS access, or power off.

## Decision

Implement monitored sessions as an event-driven, server-authoritative state
machine.

- Mobile clients only produce telemetry.
- Raw telemetry is append-only.
- Session state is derived by replaying telemetry and deterministic policy rules.
- Escalation timing is stored as configurable policy data.
- AI outputs are advisory and must include supporting evidence.
- AI advisories are persisted separately and are not accepted as escalation
  transitions.
- Drift forecasts are versioned records with probability contours, provenance,
  uncertainty, object profile, horizon, and assumptions.
- Incident-share access uses expiring read-only tokens with revocation and
  access logging.

## Consequences

- Duplicate, delayed, offline-cached, and out-of-order packets can be accepted
  without overwriting history.
- Emergency contacts can open a read-only incident view after the phone stops.
- Response teams receive a probability surface and evidence trail, not a false
  precise point.
- State transitions remain auditable and testable.
