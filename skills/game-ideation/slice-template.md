# Vertical slice template

Copy into `docs/game/wiki/slice.md` and fill every section. Keep the `##` headings exactly; `gamestate.py gate` looks for them.

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
| Game feel | representative | <feedback, timing> |
| Art | representative | placeholder art already in the target style |
| Audio | representative | |
| UI | representative | |
| Onboarding | representative | a new player gets going without help |

Each bar is `placeholder`, `representative` or `final`, chosen by the user. Representative is the default; final is for an aspect the slice must prove (an art direction that is itself the risk).

## Playtest

Who plays it (how many people, and who: the target audience if possible), how many sessions each, what they are told (nothing beyond the controls), and what result counts as a pass, alongside the kill condition in the vision.
```
