# ADR 0003: Hosted ERDDAP Option

## Status

Proposed.

## Context

The captain can host an ERDDAP server if needed. This could improve stability,
allow private/local sensor feeds, and publish derived mission-ready datasets.

## Decision

Keep hosted ERDDAP optional until the first provider contract is implemented.
When introduced, it will be represented as `HostedErddapProvider`, not as a core
platform dependency.

## Hosted ERDDAP Responsibilities

- Mirror public datasets that are operationally important.
- Serve private or local sensor feeds.
- Publish derived grids or tables prepared for mission use.
- Provide stable cached access during poor connectivity.

## Consequences

- The app can start with public endpoints and fixtures.
- Prediction code remains independent from ERDDAP deployment choices.
- Hosting can be added later without breaking the provider interface.

