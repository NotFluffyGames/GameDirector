# Design template

Copy into `docs/game/design.md` and fill every section. Keep the headings exactly; `gamestate.py gate` looks for them.

```markdown
# <Game title>

## Pitch

What the game is, in two or three sentences. Who it is for. Platforms and input devices. Session length. Two or three reference games and what this one takes from each. At most one page.

## Pillars

- **P1**: <a feeling or feature the game delivers, phrased so it can reject a feature>
- **P2**: ...
- **P3**: ...

## Core loop

<One sentence: the action the player repeats minute to minute, and what it feeds.>

## Tone, art and world

A written style guide, which also serves as the prompt source for generated assets:

- **Palette**: 4–6 colours with hex codes and what each signals (player, enemy, danger, reward, UI).
- **Shape language and camera**: dominant shapes, silhouette rules, perspective, scale of characters on screen.
- **UI tone**: typography feel, how much text, diegetic or overlay.
- **Audio mood**: instrumentation, tempo, how feedback sounds.
- **Readability rules**: what must be recognisable at a glance, at the smallest target screen size.
- **World**: one paragraph of setting. The full story or lore waits for a ship verdict.

## Pillar test

Two sample feature ideas, and for each, how every pillar votes:

| Feature idea | P1 | P2 | P3 | Verdict |
| --- | --- | --- | --- | --- |
| <idea> | for / against: why | ... | ... | in / out |
```
