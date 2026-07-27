# Rescue Me

**Intelligent Incident Monitoring & Predictive Search Platform**

Live review build:

```text
https://capahabb.github.io/rescue-me-ai-review/
```

Rescue Me is an AI-assisted emergency preparedness and incident response platform
designed to improve situational awareness before, during, and after an emergency.

Unlike traditional GPS tracking applications, Rescue Me combines live telemetry,
float plans, environmental intelligence, predictive modeling, and decision-support
tools to assist users, emergency contacts, and responders when communication is
lost or an incident occurs.

The platform is built around a modular architecture that supports search and
rescue, marine operations, outdoor recreation, disaster response, and future
mission-specific extensions.

## Mission

Reduce uncertainty.

Provide responders with actionable information instead of a single stale GPS point.

## Core Features

- Float Plan Management
- Live Mission Monitoring
- GPS Heartbeat Tracking
- Intelligent Route Deviation Detection
- Emergency Escalation Engine
- Predictive Drift Modeling
- Environmental Intelligence
- AI Decision Support
- Emergency Contact Portal
- Responder Dashboard
- Incident Timeline Replay

## Planned Integrations

- NOAA GNOME
- NOAA GLERL ERDDAP
- National Weather Service
- USGS
- AIS
- ADS-B
- Garmin Devices
- Satellite Data
- Weather Stations
- IoT Sensors

## Project Architecture

```text
Mobile Client
        |
Telemetry API
        |
Mission Session Engine
        |
 +-- Float Plan Engine
 +-- Heartbeat Service
 +-- Deviation Detector
 +-- Environmental Providers
 +-- Prediction Engine
 +-- AI Reasoning
 +-- Emergency Escalation
 +-- Emergency Contact Portal
        |
Responder Dashboard
```

## Repository Structure

```text
Rescue-Me/
├── assets/
├── docs/
├── backend/
├── frontend/
├── shared/
├── scripts/
├── infrastructure/
├── examples/
├── LICENSE
├── NOTICE
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── ROADMAP.md
├── INSTALL.md
├── DEPLOYMENT.md
├── SECURITY_REVIEW.md
└── README.md
```

## Technology Stack

- Flutter
- Dart
- Python
- Docker
- OpenLayers
- REST API
- AI-assisted reasoning

The current review backend is Python standard library plus SQLite. The broader
production architecture may add PostgreSQL, PostGIS, Redis, WebSockets, and
additional provider integrations later.

## Run The Web Console

No install is required for the current static frontend.

```bash
python3 -m http.server 4173 -d frontend/web
```

Open:

```text
http://127.0.0.1:4173/
```

## Run The Backend

The monitored-session backend currently uses Python stdlib and SQLite while the
production stack is being designed.

```bash
python3 backend/run_backend.py
```

Default API URL:

```text
http://127.0.0.1:8088
```

Run backend checks:

```bash
python3 -m unittest discover -s backend/tests
python3 -m py_compile backend/rescue_me/*.py backend/run_backend.py
```

## Project Status

This repository is under active development.

Features, APIs, architecture, and documentation may change as the project evolves.

## Copyright

Copyright (c) 2026 Michael E. Anderson. All Rights Reserved.

See [LICENSE](LICENSE) and [NOTICE](NOTICE) for ownership, restrictions, and
third-party notices.

## Contributing

Collaboration is welcome by invitation or written agreement.

Please open an issue if you would like to discuss ideas, report bugs, or request
features before submitting significant changes.
