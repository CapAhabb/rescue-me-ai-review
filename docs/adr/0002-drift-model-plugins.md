# ADR 0002: Drift And Prediction Plugins

## Status

Accepted.

## Context

Search and rescue, marine response, HazMat, wildfire, fisheries, and debris
tracking use different prediction logic. Hardcoding one prediction path would
make the core brittle.

## Decision

Define a `DriftModel` interface with a `predict()` operation. Mission packages
select one or more model implementations and feed them normalized environmental,
incident, and resource state.

Initial model families:

- Marine drift
- River drift
- Pedestrian behavior
- Aircraft debris
- HazMat plume
- Fire spread

## Consequences

- Adding an incident type means adding a module.
- The mission orchestrator can compare model outputs.
- Tests can validate model contracts independently from data providers.

