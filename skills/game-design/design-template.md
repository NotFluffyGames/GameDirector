# Design template

Copy into `docs/game/design.md` and fill every section. Keep the `##` headings exactly; `gamestate.py gate` looks for them.

```markdown
# <Game title>

## Pitch

What the game is, in two or three sentences. Who it is for. Platforms and input devices. Session length. The two or three reference games and what this one takes from each. At most one page.

## Pillars

- **P1**: <a feeling or feature the game delivers, phrased so it can reject a feature>
- **P2**: ...
- **P3**: ...

## Core loop

<One sentence: the action the player repeats minute to minute, and what it feeds.>

## Mechanics and rules

The objects in the game, the actions on them and the rules that resolve them: movement, interaction, combat or scoring, resources, win and fail conditions, edge cases (ties, timeouts, simultaneous actions). Precise enough to write tests from.

## Controls

Every input action, its binding per input device, and what it does in each context (gameplay, menus). Input actions are what the simulation core receives.

## Systems

One subsection per system (progression, economy, AI, difficulty, ...): its purpose, its state, its tuning knobs, and **which other systems it changes and how**. Interacting systems are where depth comes from; a system that touches nothing is a candidate to cut.

## Content

Every content type (levels or arenas, characters, enemies, items, abilities, events, ...) with: its kit pieces (the reusable parts it is built from), a target count, and what makes two pieces of it play differently.

## Modes and sessions

The modes (single, versus, co-op, endless, campaign, ...), how a session starts, flows and ends, and how sessions connect (unlocks, meta-progression, saved runs).

## Screens and onboarding

The screen flow from launch to quit (title, menus, settings, game, pause, results), and how a new player learns the core verb in their first minute without leaving the game.

## Feel

For each core action: the feedback it gets (visual, audio, camera, timing such as hit-stop), the response time it needs, and the reference it should feel like.

## Tone, art and world

A written style guide, which also serves as the prompt source for generated assets:

- **Palette**: 4–6 colours with hex codes and what each signals (player, enemy, danger, reward, UI).
- **Shape language and camera**: dominant shapes, silhouette rules, perspective, scale of characters on screen.
- **UI tone**: typography feel, how much text, diegetic or overlay.
- **Audio mood**: instrumentation, tempo, how feedback sounds.
- **Readability rules**: what must be recognisable at a glance, at the smallest target screen size.
- **World**: the setting in one or two paragraphs; lore only as deep as the game shows it.

## Pillar test

Two sample feature ideas, and for each, how every pillar votes:

| Feature idea | P1 | P2 | P3 | Verdict |
| --- | --- | --- | --- | --- |
| <idea> | for / against: why | ... | ... | in / out |
```
