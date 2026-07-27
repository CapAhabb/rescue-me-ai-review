# Agent Protocol

## Prime Directive

Build Rescue Me as a separate project in the Lake Command product family.

## Source Rules

- Do not edit `/home/captain/lake_command_in_depth`.
- Preserve the Lake Command-family visual system, navigation logic, component
  behavior, spacing, and interaction patterns.
- Keep mission-specific data and functions distinct for Rescue Me.
- Do not blindly copy Lake Command source files; reuse the family design
  language intentionally.
- Prefer small changes that keep the app runnable.

## Runtime Rule

The project must remain runnable with:

```bash
python3 -m http.server 4173 -d frontend/web
```

If an agent introduces a build system, it must preserve the static fallback or
replace it with a documented one-command local run path.

## Agent Lanes

### Product Architect Agent

Owns:

- `docs/architecture/ARCHITECTURE_PLAN.md`
- `docs/architecture/AGENT_TASK_BOARD.md`
- `docs/architecture/DECISIONS.md`

Stop condition:

- Plan is concrete enough for implementation agents to work without guessing.

### Shell UI Agent

Owns:

- `frontend/web/index.html`
- `frontend/web/styles.css`
- `frontend/web/main.js`

Job:

- Build the Lake Command-family command shell.
- Keep controls dense, readable, and operational.
- Avoid marketing-page layout.

### Data Adapter Agent

Owns:

- `data/*`
- future `frontend/web/data/*` or `src/data/*`
- future `frontend/web/providers.js` or `src/providers/*`

Job:

- Define ERDDAP dataset discovery and query contracts.
- Keep mock fixtures shaped like real ERDDAP responses.
- Cache for offline use.
- Keep public ERDDAP and hosted ERDDAP behind the same provider interface.

### Model Agent

Owns:

- future `src/model/*` or `frontend/web/model/*`
- future `src/prediction/*` or `frontend/web/drift-models.js`

Job:

- Define the conceptual model interface.
- Define drift and behavior model plugin contracts.
- Support provider swap: local rules first, optional external model later.
- Return auditable recommendations with source signals.

### QA Agent

Owns:

- verification commands and test reports.

Job:

- Run the app locally.
- Check layout at desktop and mobile widths.
- Confirm no dependency or network requirement was introduced accidentally.

## Handoff Format

Every agent reports:

- Files changed
- Check command run
- Result
- Risk or unknown
- Next recommended task
