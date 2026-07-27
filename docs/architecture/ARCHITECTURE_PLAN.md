# Architecture Plan

## Product Shape

`resuce_me.ai` is an Incident OS. Its first mission package is search and
rescue, but the core platform should also support marine response, HazMat,
wildfire, fisheries, and environmental monitoring modules.

It takes the useful Lake Command product ideas, then re-expresses them for
rescue and environmental decision support:

- layered operational map
- environmental signal panels
- scenario and route planning
- field notes and incident timeline
- agent-generated recommendations
- offline-first behavior

The first usable version should feel like a focused desktop command surface, not
a landing page.

## System Map

```text
Incident OS
  Environmental Intelligence
    EnvironmentalProvider adapters
    normalized environmental state
  Incident State Engine
    timeline
    evidence
    witnesses
    sensors
    AI memory
  Resource State Engine
    personnel
    vehicles
    aircraft
    boats
    drones
  Prediction Core
    drift physics
    behavior models
    probability engine
  Mission Orchestrator
    SAR
    HazMat
    Marine
    Wildfire
  Command Dashboard
```

## Non-Negotiables

- Lake Command is not modified.
- Lake Command code is not copied.
- ERDDAP replaces mock Lake Command datasets.
- Model integration starts behind an interface.
- The app remains runnable with little setup.
- Agents receive narrow tasks with explicit file ownership.
- Architecture Decision Records are written beside meaningful design choices.

## External References

- ERDDAP tabledap and griddap provide URL-addressable scientific dataset access
  in common formats, including CSV and JSON.
- ERDDAP uses standardized spatial/time names such as `longitude`, `latitude`,
  `altitude`, `depth`, and `time`, which should become the normalized internal
  signal vocabulary.
- GNOME design direction should guide simplicity, reduced user effort,
  adaptive layout, accessibility, and consistent desktop controls.
- GTK/libadwaita is reference material for desktop shell behavior. The web stub
  can imitate the interaction model without requiring GTK.

Useful source links:

- https://coastwatch.pfeg.noaa.gov/erddap/information.html
- https://coastwatch.pfeg.noaa.gov/erddap/rest.html
- https://coastwatch.pfeg.noaa.gov/erddap/tabledap/documentation.html
- https://developer.gnome.org/hig/principles.html
- https://developer.gnome.org/hig/guidelines.html
- https://developer.gnome.org/documentation/introduction/overview/libraries.html

## Target Modules

### 1. Shell UI

Purpose:

- Present an operator-focused command surface.
- Offer quick switching between map, signals, timeline, assets, and plan.

Initial views:

- Command Map
- Signals
- Incident Timeline
- Assets
- Plan

Initial controls:

- Layer toggles
- Mission status selector
- Time range selector
- Area of interest selector
- Recommendation panel

### 2. Provider Abstraction Layer

Purpose:

- Hide source-specific APIs from the prediction engine.
- Normalize all environmental data into one internal state model.
- Allow NOAA, NWS, USGS, local sensors, and hosted ERDDAP to coexist.

Core interface:

```ts
interface EnvironmentalProvider {
  getWind(request: EnvironmentalRequest): Promise<EnvironmentalState>;
  getCurrent(request: EnvironmentalRequest): Promise<EnvironmentalState>;
  getWaveHeight(request: EnvironmentalRequest): Promise<EnvironmentalState>;
  getWaveDirection(request: EnvironmentalRequest): Promise<EnvironmentalState>;
  getWaterTemperature(request: EnvironmentalRequest): Promise<EnvironmentalState>;
  getRiverDischarge(request: EnvironmentalRequest): Promise<EnvironmentalState>;
  getVisibility(request: EnvironmentalRequest): Promise<EnvironmentalState>;
  getForecast(request: EnvironmentalRequest): Promise<EnvironmentalState>;
}
```

Initial adapters:

- `MockEnvironmentalProvider`
- `PublicErddapProvider`
- `HostedErddapProvider`
- `NwsProvider`
- `UsgsProvider`
- future `CommercialProvider`
- future `LocalStationProvider`
- future `BuoyProvider`
- future `IotSensorProvider`

Self-hosted ERDDAP guidance:

- Treat the hosted server as a source adapter, not the core source of truth.
- Keep public and hosted ERDDAP behind the same provider interface.
- Use hosted ERDDAP when public datasets need stable mirrors, derived products,
  private sensor feeds, or preprocessing before mission use.
- Store dataset metadata in the registry so the app can swap public and hosted
  endpoints without prediction-core changes.

### 3. Data Registry

Purpose:

- Keep a catalog of candidate ERDDAP servers and datasets.
- Describe query variables, units, spatial bounds, update cadence, and license.

Initial dataset families:

- weather observations
- water temperature
- wind
- currents
- wave height
- lake/ocean surface conditions
- station/buoy observations

### 4. ERDDAP Adapter

Purpose:

- Convert app requests into ERDDAP URL requests.
- Normalize ERDDAP JSON/CSV into internal signals.
- Cache last successful responses.

Initial contract:

```ts
type SignalRequest = {
  datasetId: string;
  variables: string[];
  bounds?: { west: number; south: number; east: number; north: number };
  timeStart?: string;
  timeEnd?: string;
};

type SignalPoint = {
  id: string;
  source: string;
  observedAt: string;
  latitude?: number;
  longitude?: number;
  depth?: number;
  values: Record<string, number | string | null>;
  units: Record<string, string>;
};
```

### 5. Drift Model Interface

Purpose:

- Let incident types add prediction behavior as plugins.
- Keep the mission orchestrator from depending on one hardcoded prediction
  algorithm.

Core interface:

```ts
interface DriftModel {
  predict(input: PredictionInput): Promise<PredictionResult>;
}
```

Initial model families:

- `MarineDrift`
- `RiverDrift`
- `PedestrianBehavior`
- `AircraftDebris`
- `HazMatPlume`
- `FireSpread`

### 6. Conceptual Model Interface

Purpose:

- Allow the recommendation engine to run locally first.
- Permit later cloning, fine-tuning, or external model replacement.
- Keep recommendations explainable.

Initial contract:

```ts
type SituationAssessment = {
  severity: "low" | "guarded" | "elevated" | "critical";
  summary: string;
  recommendedActions: string[];
  supportingSignals: string[];
  confidence: number;
};
```

### 7. Incident State Engine

Purpose:

- Maintain the operational state of the mission.
- Provide timeline, evidence, witness, sensor, and AI-memory context to mission
  packages and prediction models.

### 8. Resource State Engine

Purpose:

- Track available and assigned response resources.
- Normalize personnel, vehicles, aircraft, boats, drones, and local teams into
  one resource picture.

### 9. Mission Orchestrator

Purpose:

- Compose provider data, incident state, resource state, and model predictions.
- Allow mission packages to be added without rewriting the core.

Initial mission packages:

- SAR
- Marine
- HazMat
- Wildfire

### 10. Scenario Engine

Purpose:

- Join environmental signals with incident context.
- Produce route, timing, and risk guidance.

MVP scenarios:

- missing person near shoreline
- overdue small vessel
- severe weather approach
- water temperature exposure risk

### 11. Local Store

Purpose:

- Keep incident notes, cached signals, and selected datasets available offline.

Initial storage:

- browser `localStorage` for static stub
- later IndexedDB or SQLite depending on selected app stack

## MVP Workflow

1. Open command shell.
2. Select mission type.
3. Select area of interest.
4. Load cached/mock environmental signals.
5. Toggle operational layers.
6. Generate a local conceptual assessment.
7. Save incident note.
8. Export a simple mission summary.

## Suggested Implementation Path

### Phase 0: Static Operational Stub

Deliverable:

- dependency-free HTML/CSS/JS command shell
- mock ERDDAP-shaped signal data
- basic layer toggles and local assessment

Verification:

```bash
python3 -m http.server 4173 -d frontend/web
```

### Phase 1: Module Split

Deliverable:

- move shell, data adapter, model interface, and store into modules
- preserve static run path
- create ADRs for provider abstraction and plugin model boundaries

Verification:

```bash
python3 -m http.server 4173 -d frontend/web
```

### Phase 2: ERDDAP Discovery

Deliverable:

- dataset registry file
- tabledap/griddap URL builder
- JSON parser for table responses
- mock test fixtures
- hosted ERDDAP provider config shape

Verification:

- local fixture parse works without network
- generated URLs are printed and inspectable

### Phase 3: Real Data Toggle

Deliverable:

- optional live fetch mode
- cache results locally
- graceful fallback to fixtures when offline

Verification:

- app works offline
- live fetch errors are visible but non-blocking

### Phase 4: Desktop App Decision

Deliverable:

- choose final shell technology:
  - web/PWA
  - Tauri
  - GNOME native GTK/libadwaita
  - Flutter desktop

Decision criteria:

- easiest offline install
- best map rendering
- fastest agent iteration
- long-term desktop feel

### Phase 5: Hosted ERDDAP Decision

Deliverable:

- decide whether to host ERDDAP immediately or defer
- define server responsibility:
  - mirror public datasets
  - serve private/local sensor data
  - publish derived mission-ready grids
  - provide stable cache during poor connectivity

Rule:

- Self-hosted ERDDAP must not leak into prediction logic. It remains one
  provider implementation.

## Immediate Agent Tasks

See `docs/architecture/AGENT_TASK_BOARD.md`.
