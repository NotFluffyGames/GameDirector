# Narrative: dossier section

File: `docs/game/research/refs/<id>/narrative.md`. Short; facts and sources. Narrative is not an image role: no image is required.

## Required

- `how_studied`: `played`, `watched` (frames), `read` or `not-assessed` with the reason.
- **Premise**: the fantasy line and the setting in a sentence each.
- **Tone**: the tone in three words, from the sources.
- **Samples**: two or three short quoted strings (UI text, a bark, an item name), each with its source.
- **Naming and UI voice**: how it names things and how its interface speaks.
- **Take / avoid**: each tied to a tone word or anti-word of `north_stars.narrative`.
- **Sources**: a list; every claim points to one.

## Audit rules

The creative `audit` flags a finding, anchored to the rule, when:

- `sourceless`: a claim has no source;
- `generic`: a line could describe a different game ("immersive world", "witty writing");
- `missing`: a quoted sample or a required field is absent and not marked `not-assessed` with a reason.
