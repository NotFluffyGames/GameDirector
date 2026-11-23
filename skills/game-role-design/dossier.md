# Design: dossier section

File: `docs/game/research/refs/<id>/design.md`. Short; facts and sources, no summary of the game.

## Required

- `how_studied`: `played`, `watched`, `read` or `not-assessed` with the reason.
- **Loop**: the decisions the player repeats, in order, with the cost of each option.
- **Verbs and systems**: each verb and system in one line, with at least three numbers (timings, costs, counts, run length) and where each came from.
- **Variance**: what makes two runs or matches differ.
- **Take / avoid**: each tied to this game's north star.
- **Sources**: a list; every claim above points to one.

## Audit rules

The creative `audit` flags a finding, anchored to the rule, when:

- `sourceless`: a claim has no source;
- `generic`: a line could describe a different game ("deep systems", "tight loop");
- `missing`: a required field or number is absent and not marked `not-assessed` with a reason.
