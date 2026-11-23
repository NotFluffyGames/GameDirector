# UX: dossier section

File: `docs/game/research/refs/<id>/ux.md`, with saved images under `docs/game/research/refs/<id>/ux/`. Short; facts and sources.

## Required

- `how_studied`: `played`, `watched` (frames), `read` or `not-assessed` with the reason.
- **Shots**: at least two saved image paths (a first-minute moment and the HUD), or `not-assessed` with the reason.
- **First minute**: the steps in order, what each teaches, and its time in seconds from launch.
- **HUD**: what it holds, where it sits, which items are critical.
- **Input and access**: the input map, and the accessibility options it offers.
- **Take / avoid**: each tied to `north_stars.ux` or the target player.
- **Sources**: a list; every claim points to one.

## Audit rules

The creative `audit` flags a finding, anchored to the rule, when:

- `sourceless`: a claim has no source;
- `generic`: a line could describe a different game ("intuitive UI", "smooth onboarding");
- `missing`: an image, a timed first-minute step or a required field is absent and not marked `not-assessed` with a reason.
