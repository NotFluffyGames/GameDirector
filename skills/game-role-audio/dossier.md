# Audio: dossier section

File: `docs/game/research/refs/<id>/audio.md`. Short; facts and sources. Audio is not an image role: no image is required. State "unheard": the section comes from descriptions, reviews and listings.

## Required

- `how_studied`: `read`, `watched` (a description or transcript, not heard) or `not-assessed` with the reason. State "unheard".
- **Events and sound**: which gameplay events carry a sound, and which information is audio-first.
- **Music**: its role, its scheme (loops, layers, state changes) and where it is silent.
- **Voice and UI**: the voice scope (full, barks, gibberish, none) and what the UI sounds are described as.
- **Take / avoid**: each tied to a pillar or a `by_ear` line of `north_stars.audio`.
- **Sources**: a list; every claim points to one.

## Audit rules

The creative `audit` flags a finding, anchored to the rule, when:

- `sourceless`: a claim has no source;
- `generic`: a line could describe a different game ("great soundtrack", "punchy effects");
- `missing`: the word "unheard" or a required field is absent and not marked `not-assessed` with a reason.
