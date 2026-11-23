# Vertical slice template

Page template for the `slice` page (area Vision) in the docs place; fill every section. Keep the `##` headings exactly. The test question and the quality bars also go into `docs/game/vision.json` `slice`, which `gamestate.py gate` reads.

```markdown
# Vertical slice

Topics: T1 · Decisions: <ADR> · Last changed: <date>, <why>

## What it proves

The test question the slice can fail: "Does a player, starting from nothing, <experience the target feeling> within <N> minutes without help, and can we build it in about <S> sessions?" Then the two or three risks it retires (the core loop is fun, the art direction works, the pipeline holds).

## In the slice

The part of the game it covers (a mode, a level, an encounter, a match type), how long one play of it lasts, and the systems and content it needs, by name. Enough that a player meets the core loop, its main decision and one complete start → challenge → resolution.

## Out of the slice

What the full game has that the slice leaves out, by name, so nobody builds it early.

## Quality bar

| Aspect | Bar | Means |
| --- | --- | --- |
| Code and architecture | production | the real simulation core and shell; nothing hard-coded that tuning knobs should hold |
| Game feel | production | every core action at its feel sheet's targets |
| Art | production | the visual target's area (<the scene built first>) at production; the rest of the slice representative: placeholder art already in the target style |
| Audio | representative | the signature sounds (<names>) near final; the rest representative |
| UI | representative | |
| Onboarding | representative | a new player gets going without help |

Each bar is `placeholder`, `representative`, `production` or `final`, chosen by the user; the bars above are the recommendation. A slice that leaves art or audio at placeholder can't show whether the game will look and sound right. The roles review against these bars as `vision.json` holds them: art reads Art, feel Game feel, audio Audio, ux UI and Onboarding, narrative UI. The Means column narrows a bar to an area, as the Art row does, and game-plan's acceptance per feature carries the narrowing.

## Playtest

Who plays it (how many people, and who: the target audience if possible), how many sessions each, what they are told (nothing beyond the controls), and what result counts as a pass, alongside the kill condition in the vision.
```
