# Feel: dossier section

File: `docs/game/research/refs/<id>/feel.md`, with strips under `docs/game/research/refs/<id>/feel/`. Short; facts and sources.

## Required

- `how_studied`: `played`, `watched` (frames) or `not-assessed` with the reason.
- Per core action the reference shares with this game:
  - **Strip**: a saved frame strip path around the action.
  - **Timings**: first response, active and recovery in frames, read off the strip.
  - **Layers**: which feedback layers show, and how small and large events differ.
  - **Take / avoid**: tied to the action's adjectives.
- **Sources**: a list; every claim points to one.

## Audit rules

The creative `audit` flags a finding, anchored to the rule, when:

- `sourceless`: a claim has no source;
- `generic`: a line could describe a different game ("tight controls", "satisfying hits");
- `missing`: a strip, a timing in frames or a required field is absent and not marked `not-assessed` with a reason.
