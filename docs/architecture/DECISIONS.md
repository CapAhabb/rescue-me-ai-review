# Decisions

## Accepted

- Project is separate from Lake Command.
- Lake Command is reference only.
- Initial app must run with no dependency install.
- ERDDAP-compatible sources are the target data path.
- A self-hosted ERDDAP server is allowed as an adapter when it helps with
  stability, private sensor data, derived products, or local caching.
- Model behavior starts as a conceptual interface with local rules.
- GNOME desktop design patterns may guide shell behavior and layout.
- Provider and prediction boundaries are captured in ADRs.

## Open

- Correct final spelling: `resuce_me.ai` or `rescue_me.ai`.
- Final app stack: static web, PWA, Tauri, GTK/libadwaita, or Flutter desktop.
- Exact ERDDAP servers and datasets.
- Whether to host ERDDAP in the first runnable milestone or defer until live data
  integration.
- Whether model will be cloned, fine-tuned, or provider-backed.
- Authentication and privacy requirements for real incidents.

## Rejected For Now

- Copying Lake Command source.
- Large backend before the local workflow works.
- Paid agent swarm before MVP validation.
