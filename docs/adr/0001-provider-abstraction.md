# ADR 0001: Provider Abstraction Layer

## Status

Accepted.

## Context

The platform needs environmental data from NOAA ERDDAP, GNOME, NWS, USGS,
satellite products, buoys, local weather stations, IoT sensors, future
commercial providers, and possibly a self-hosted ERDDAP server.

The prediction core should not know which service supplied a signal.

## Decision

Define a common `EnvironmentalProvider` interface. Every source adapter returns
normalized environmental state. Public ERDDAP and hosted ERDDAP are separate
provider implementations that share the same contract.

## Consequences

- New providers can be added without rewriting prediction models.
- Hosted ERDDAP can be introduced when needed for mirrors, private feeds, or
  derived products.
- Dataset-specific quirks stay inside adapters and registry metadata.

