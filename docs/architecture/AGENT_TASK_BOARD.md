# Agent Task Board

## Ready

### T00: Verify Clean Boundary

Owner: QA Agent

Files:

- `README.md`
- `AGENTS.md`

Task:

- Confirm the repo does not contain copied Lake Command source.
- Confirm Lake Command path is referenced only as read-only context.

Check:

```bash
find . -maxdepth 3 -type f
```

Done when:

- Output contains only `resuce_me.ai` files.

### T01: Improve Static Shell

Owner: Shell UI Agent

Files:

- `frontend/web/index.html`
- `frontend/web/styles.css`
- `frontend/web/main.js`

Task:

- Make the first screen an operational command surface.
- Keep dense desktop layout with adaptive mobile behavior.
- Add layer buttons for weather, water, wind, currents, assets, and notes.

Check:

```bash
python3 -m http.server 4173 -d frontend/web
```

Done when:

- The browser view loads without build tools.
- Layer toggles visibly update the command map.

### T02: ERDDAP Fixture Shape

Owner: Data Adapter Agent

Files:

- `data/signals.mock.json`
- future `frontend/web/erddap.js`
- future `frontend/web/providers.js`

Task:

- Keep fixture data shaped like ERDDAP table JSON:
  - `table.columnNames`
  - `table.columnTypes`
  - `table.columnUnits`
  - `table.rows`
- Add a normalizer that produces `SignalPoint` records.

Check:

```bash
python3 -m http.server 4173 -d frontend/web
```

Done when:

- Shell renders normalized mock points.

### T02A: Provider Contract

Owner: Data Adapter Agent

Files:

- `frontend/web/providers.js`
- `docs/adr/0001-provider-abstraction.md`

Task:

- Create the `EnvironmentalProvider` contract in code comments or JSDoc.
- Implement `MockEnvironmentalProvider`.
- Stub `PublicErddapProvider` and `HostedErddapProvider` without live network
  dependency.

Check:

```bash
python3 -m http.server 4173 -d frontend/web
```

Done when:

- The dashboard reads environmental state through the provider contract.

### T03: Conceptual Assessment

Owner: Model Agent

Files:

- `frontend/web/main.js`
- future `frontend/web/model.js`

Task:

- Implement a local rule-based assessment.
- Return severity, summary, recommended actions, supporting signals, and
  confidence.

Check:

```bash
python3 -m http.server 4173 -d frontend/web
```

Done when:

- Changing mission type or active layers changes the assessment.

### T03A: Drift Model Contract

Owner: Model Agent

Files:

- future `frontend/web/drift-models.js`
- `docs/adr/0002-drift-model-plugins.md`

Task:

- Define a `DriftModel` contract.
- Add stub implementations for marine drift, river drift, pedestrian behavior,
  aircraft debris, HazMat plume, and fire spread.
- Wire only one local mock model into the dashboard.

Check:

```bash
python3 -m http.server 4173 -d frontend/web
```

Done when:

- Mission type selects a named model family without changing dashboard code.

### T04: Architecture Decisions Log

Owner: Product Architect Agent

Files:

- `docs/architecture/DECISIONS.md`
- `docs/adr/*`

Task:

- Record decisions about stack, ERDDAP use, model interface, offline behavior,
  and naming.

Check:

```bash
sed -n '1,220p' docs/architecture/DECISIONS.md
```

Done when:

- A future agent can see what is decided versus still open.

### T06: Hosted ERDDAP Readiness

Owner: Data Adapter Agent

Files:

- `docs/adr/0003-hosted-erddap.md`
- future `data/provider-registry.json`

Task:

- Define hosted ERDDAP server config shape.
- Mark hosted ERDDAP as optional until provider contract exists.
- Document which datasets would justify hosting.

Check:

```bash
sed -n '1,220p' docs/adr/0003-hosted-erddap.md
```

Done when:

- The team can add self-hosted ERDDAP without changing prediction code.

## Blocked Until Captain Provides Architecture Chat Details

### T05: Fold In Missing Main Build Points

Owner: Product Architect Agent

Files:

- `docs/architecture/ARCHITECTURE_PLAN.md`
- `docs/architecture/AGENT_TASK_BOARD.md`

Need:

- pasted notes from the architecture chat or an accessible export.

Done when:

- The plan reflects the exact main build points from that discussion.
