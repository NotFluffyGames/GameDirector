---
name: game-design
description: Turn the chosen game concept into a complete game definition - pitch, pillars, core loop, mechanics and rules, controls, systems, content plan, modes, screens, feel and art direction - plus the fun checklist and richness targets the game is judged by. Phase 2 of the game-* workflow; also re-runs after a restart.
disable-model-invocation: true
---

# Game Design

Writes the complete **game definition**: everything game-plan needs to turn into features without inventing design. `design.md`, `fun-checklist.json` and `richness.json` are **durable assets** and the bar the game is judged against; after this phase they can grow but never drop. Read `docs/agents/game.md` first and follow its session rules.

The definition is large. When it doesn't fit one session, stop after a finished section; the next session resumes at the first section that is missing or empty.

## 1. Gather

- `docs/game/seed.md` and `docs/game/concepts.md`: the chosen concept, the ideas borrowed from others, the prototype evidence and the open risks.
- `CONTEXT.md` and existing ADRs.
- A `restart <adr>` task: that ADR's lessons. Keep what it says still holds.

**Done when** you can state the chosen concept, its evidence and its open risks.

## 2. Resolve the design tree

Walk the design tree with the `grilling` skill over what the concept leaves open: audience; platforms and input; player count and modes; session length; goal and fail state; progression; the systems and how each changes the others; content types and amounts; difficulty; onboarding; screens.

- **interactive**: the user answers, through the questions protocol when you can't reach them.
- **autonomous**: grill yourself. Take the recommended answer, aiming for the richest game the session budget can build and verify: depth from systems that change each other first, breadth from content built out of reusable kit pieces second. Record every answer in one "design assumptions" ADR so a human can overturn it later.

**Done when** every branch has an answer and none is "TBD".

## 3. Write the definition

Write `docs/game/design.md` from [design-template.md](design-template.md).

**Done when** every section is filled, the core loop is one sentence, there are 3–4 pillars with a pillar test, every system names the systems it affects, and every content type has a count.

## 4. Write the fun checklist

Write 3–6 items to `docs/game/fun-checklist.json`:

```json
{"items": [{"id": "FC1", "statement": "The last 30 seconds of a match feel tense",
  "scope": "core-loop", "kind": "proxy",
  "metric": "score gap in the final 30 s, and lead changes per match",
  "threshold": "gap within 1 point in at least 40% of bot matches",
  "how": "bot --policy greedy-vs-greedy --runs 50"}]}
```

- Each item is observable within one play session.
- `scope`: `core-loop` for items the core loop alone must satisfy, `full` for the rest. At least one core-loop item.
- `kind`: make an item a **proxy** whenever a metric can stand for it; [fun-proxies.md](fun-proxies.md) lists proxies for common fun statements. Items no metric captures ("players ask for one more round") are `human`, with `metric`, `threshold` and `how` left out.

**Done when** the gate lists nothing about the fun checklist.

## 5. Set the richness targets

Write `docs/game/richness.json` with at least one target per aspect (depth, breadth, variety), each at or above the floor in [richness.md](richness.md):

```json
{"targets": [{"id": "R1", "aspect": "depth", "statement": "Every system changes how matches go",
  "metric": "shift in the best bot policy's win rate with each system toggled off",
  "threshold": ">= 10 points for every system", "how": "bot --runs 100 per toggle"}]}
```

Ids share one namespace with the fun checklist.

**Done when** `python3 docs/game/gamestate.py gate` passes.

## 6. Name things

With the `domain-modeling` skill, add the game's own nouns (the player's avatar, a match, a run, unit, item and resource names) to `CONTEXT.md`, so tickets, code and tests share one vocabulary.

**Done when** every noun the definition uses is in `CONTEXT.md`.

## 7. Close

`gamestate.py check --since <base>`, commit, progress entry, `gamestate.py complete`. Reply with the pitch's first line, the pillars, the core loop, and the richness targets in one line each.
