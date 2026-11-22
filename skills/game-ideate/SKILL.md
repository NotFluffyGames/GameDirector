---
name: game-ideate
description: Turn a game idea, or none, into a one-page pitch, pillars, a one-sentence core loop, tone/art/world direction and a measurable fun checklist. Phase 1 of the game-* workflow; also re-runs after a restart verdict.
disable-model-invocation: true
---

# Game Ideate

Writes the game's **durable assets**: the design every later decision is judged against, and the part that survives a restart. Read `docs/agents/game.md` first and follow its session rules.

## 1. Gather

- The seed: the idea from the task, an existing `docs/game/design.md`, `CONTEXT.md`.
- On a restart (`state.json` counters show restarts > 0): the latest verdict ADR's lessons. Keep the durable assets it says still hold; rework what it names as failing.
- Constraints: platforms, audience, budget from the prompt or `state.json` limits.

**Done when** you can state the seed and its constraints in two sentences, or "no seed" (you invent within the constraints).

## 2. Resolve the design tree

Walk the design tree with the `grilling` skill: audience, platform and input, player count and mode, session length, core verb, goal and fail state, progression, reference games, tone.

- **interactive**: grill the user.
- **autonomous**: grill yourself. Answer each question with the recommended answer, choosing the smallest game that delivers the seed within the budget. Record every answer in one "design assumptions" ADR so a human can overturn any of them later.

Scope the game so an agent can build and verify it in the session budget: one core loop, few systems, content made from reusable parts.

**Done when** every branch has an answer and none is "TBD".

## 3. Write the design

Write `docs/game/design.md` from [design-template.md](design-template.md).

**Done when** the pitch fits one page, the core loop is one sentence, there are 3–4 pillars, and the pillar test shows each pillar deciding for or against at least one of two sample features.

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

**Done when** `python3 docs/game/gamestate.py gate` passes.

## 5. Name things

With the `domain-modeling` skill, add the game's own nouns (the player's avatar, a match, a run, unit and resource names) to `CONTEXT.md`, so tickets, code and tests share one vocabulary.

## 6. Close

`gamestate.py check`, commit, progress entry. Reply with the pitch's first line, the pillars and the core loop.
