---
name: game-consolidate
description: Check the game wiki is complete and consistent once brainstorming settles, open topics for the gaps, then set the bar the game is judged by - the fun checklist and richness targets. Phase 3 of the game-* workflow, between brainstorm and plan.
disable-model-invocation: true
---

# Game Consolidate

Turns a wiki written one topic at a time into one coherent definition, then sets the **bar**: the fun checklist and richness targets every verdict scores. After this phase the bar can rise but never drop. Read `docs/agents/game.md` first and follow its session rules.

When the work doesn't fit one session, stop after a finished step; the next session resumes at the first step whose criterion is unmet.

## 1. Completeness

Walk `wiki/index.md` area by area. For each, the pages must answer what planning will ask:

- **Mechanics**: every object, action, win and fail condition, and edge case (ties, timeouts, simultaneous actions), precise enough to write tests from.
- **Controls**: every input action with its binding per device.
- **Systems**: each system's purpose, state, tuning knobs, and **which other systems it changes and how**.
- **Content**: each content type's kit pieces, target count, and what makes two pieces play differently.
- **Modes and sessions**, **Screens and onboarding**, **Feel**, **Tone, art and world**: enough to build and to judge against.

For each gap, open a topic (`core` when the core loop depends on it, otherwise `support`) with the question that would close it, and stop: the next sessions brainstorm them with a person.

**Done when** every area answers its questions, or every gap is an open topic.

## 2. Consistency

Read the pages along the index and the links between them. Fix contradictions, mismatched terms and stale cross-references that have an obvious answer, each in the page that is wrong, with a `Last changed` line. A contradiction that needs a design decision becomes a topic.

**Done when** no two pages disagree, and every term used is in `CONTEXT.md`.

## 3. Settle the tree

Every open topic left must be `core` or `support` work for a person, or wait: mark each `later` topic, and any `support` topic the brainstorm share left unanswered, `deferred` with a one-line reason (what it waits for). A deferred topic can be reopened in any later phase.

**Done when** `gamestate.py gate` lists no open core or support topic.

## 4. Write the fun checklist

Write 3–6 items to `docs/game/fun-checklist.json`, drawn from the vision's target feeling and the pages:

```json
{"items": [{"id": "FC1", "statement": "The last 30 seconds of a match feel tense",
  "scope": "core-loop", "kind": "proxy",
  "metric": "score gap in the final 30 s, and lead changes per match",
  "threshold": "gap within 1 point in at least 40% of bot matches",
  "how": "bot --policy greedy-vs-greedy --runs 50"}]}
```

- Each item is observable within one play session.
- `scope`: `core-loop` for items the core loop alone must satisfy, `full` for the rest. At least one core-loop item.
- `kind`: a **proxy** whenever a metric can stand for it ([fun-proxies.md](fun-proxies.md)); otherwise `human`, with `metric`, `threshold` and `how` left out.

In interactive mode, the user approves the checklist.

## 5. Set the richness targets

Write `docs/game/richness.json` with at least one target per aspect (depth, breadth, variety), each at or above the floor in [richness.md](richness.md) and grounded in the Systems and Content pages:

```json
{"targets": [{"id": "R1", "aspect": "depth", "statement": "Every system changes how matches go",
  "metric": "shift in the best bot policy's win rate with each system toggled off",
  "threshold": ">= 10 points for every system", "how": "bot --runs 100 per toggle"}]}
```

Ids share one namespace with the fun checklist. In interactive mode, the user approves the targets.

**Done when** `python3 docs/game/gamestate.py gate` passes.

## 6. Close

`gamestate.py check --since <base>`, commit, progress entry, `gamestate.py complete`.
