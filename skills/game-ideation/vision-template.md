# Vision template

Page template for the `vision` page (area Vision) in the docs place; fill every section. Keep the `##` headings exactly. The pillars, anti-pillars, kill condition, north stars and invariants also go into `docs/game/vision.json`, which `gamestate.py gate` reads.

```markdown
# Vision

Topics: T1 · Decisions: <vision assumptions ADR> · Last changed: <date>, first version

## Pitch

What the game is, in two or three sentences, the way a player would describe it to a friend.

## Audience and platforms

Who it is for, what they already play, where and how long they play. Target platforms and input devices.

## Comps and hook

- Comps that count as "us": <R1 title>, <R3 title>, ... (ids from `references.json`)
- Anchors kept: <what players of the genre expect, and keep getting>
- Anchors broken: <the anchor, and why this game breaks it>
- Hook: <the anchor genre plus this game's departure, in one phrase>

## Pillars

- **P1**: <a feeling or feature the game delivers, phrased so it can reject a feature>
- **P2**: ...
- **P3**: ...

## Anti-pillars

- **We will not** <do X>, because it would compromise <P1>.
- ...

## Core loop

<One sentence: the action the player repeats minute to minute, and what it feeds.>

## Target feeling

The feeling a session should leave (tension, mastery, discovery, expression, fellowship, ...), and the moment that delivers it.

## Direction per role

**Creative.** <statement: one sentence>

- Genre default: <what most games of this kind do>
- Departure: <where this game differs, felt by the player>
- References: <title: what we take> · <title: what we take>

**Design.** <the core loop's decisions in one sentence> · Runs differ by: <variety>

**Feel.** <statement> · <action>: <words>, ... · Never: <never>

**Art.** <slogan>, direction <choice> of <directions> compared

**Audio.** <the audio pillars> · By ear: <what the player does by ear> · Voice: <voice>

**Narrative.** <fantasy line> · Tone: <three words>, not <three anti-words>

**UX.** <what a new player understands in the first minute> · Player: <player> · Input: <devices>

**<Role>.** Off, because <its reason in roles_off>.

### Identity invariants

1. <testable on a capture or in play>
2. <...>

## References

The references the vision and the north stars name, each `open` for the research phase to study:

- **<R2 title>** (R2; <roles>): what this game takes from it, and what it does differently.
- ...

## Scope

What is in (modes, rough content size, session length) and what is explicitly out.

## Kill condition

The evidence that would mean this game should not be made as conceived, judged at the slice verdict: "If people who play the slice <observable result>, we stop or go back to ideation." Concrete enough that a playtest can meet it or not.
```

The roles' references in "Direction per role" are titles; the "References" section ties each to its `references.json` id. The invariants here and in `vision.json` are the same strings.
