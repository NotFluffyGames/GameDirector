---
name: game-consolidate
description: Check the game wiki is complete and consistent once a brainstorm pass settles, open topics for the gaps, then set the bar the game is judged by - the fun checklist and richness targets. Runs twice in the game-* workflow - for the vertical slice, and for production.
disable-model-invocation: true
---

# Game Consolidate

Turns a wiki written one topic at a time into one coherent definition, then sets the **bar**: the fun checklist and richness targets the verdicts score. It runs once per stage (`gamestate.py status` shows the stage):

- **slice** (task `game-consolidate`): the pages the vertical slice needs, and the bar for the slice.
- **production** (task `game-consolidate production`): the whole game, and the bar for the full game. The slice's bar stays as it is: after the slice stage it can rise but never drop.

Read `docs/agents/game.md` first and follow its session rules. When the work doesn't fit one session, stop after a finished step, committing your page drafts (session rule 6); the next session resumes at the first step whose criterion is unmet, and step 6 writes the drafts still in `docs/game/drafts/`.

## 1. Completeness

Walk the areas one by one (the list in "The wiki" in `docs/agents/game.md`, or the home page's sections), reading each area's pages (those in `docs/game/wiki.json` with that `area`) through the docs place; an area with no page is a gap; in the slice stage, only what the `slice` page's In list needs (Modes and sessions can wait). For each, the pages must answer what planning will ask:

- **Mechanics**: every object, action, win and fail condition, and edge case (ties, timeouts, simultaneous actions), precise enough to write tests from.
- **Controls**: every input action with its binding per device.
- **Systems**: each system's purpose, state, tuning knobs, and **which other systems it changes and how**.
- **Content**: each content type's kit pieces, target count, and what makes two pieces play differently.
- **Modes and sessions**, **Screens and onboarding**, **Feel**, **Tone, art and world**: enough to build and to judge against, at the quality bar the `slice` page sets.

For each gap, open a topic for this stage (`core` when the core loop depends on it, otherwise `support`) with the question that would close it, and stop: the next sessions brainstorm them with a person.

**Done when** every area this stage needs answers its questions, or every gap is an open topic.

## 2. Consistency and holism

Read the pages along the index and the links between them, and look at the design as a whole:

- contradictions, mismatched terms and stale cross-references;
- competing progression loops, and more systems demanding attention at once than a player can follow;
- resources with sources but no sinks (or the reverse), and feedback loops that run away;
- three to five scenarios that combine systems (two effects at once, an edge of one system meeting another), walked through step by step.

Fix what has an obvious answer in the page that is wrong: draft the fix in `docs/game/drafts/<page-id>.md` with a `Last changed` line (written at step 6). Anything that needs a design decision becomes a topic. A risk that can be measured becomes a candidate proxy for step 4 (for example, resource growth per run).

**Done when** no two pages disagree, every term used is in `CONTEXT.md`, and every holism finding is a committed page draft, a topic, or a candidate proxy.

## 3. Settle the tree

Every open topic of this stage must be `core` or `support` work for a person, or wait: mark each `later` topic, and any `support` topic the brainstorm share left unanswered, `deferred` with a one-line reason (what it waits for). When a topic you defer is the review of a flagged page, remove that page's `flagged` entry in `wiki.json` in the same commit as the deferral (check fails while a flag names a topic that isn't open), and draft the page without its note (written at step 6). A deferred topic can be reopened in any later phase. Production topics stay open through the slice stage.

**Done when** `gamestate.py gate` lists no open core or support topic for this stage.

## 4. Write the fun checklist

Write items to `docs/game/fun-checklist.json`, drawn from the vision's target feeling, the pages and step 2's candidates:

```json
{"items": [{"id": "FC1", "statement": "The last 30 seconds of a match feel tense",
  "scope": "core-loop", "kind": "proxy",
  "metric": "score gap in the final 30 s, and lead changes per match",
  "threshold": "gap within 1 point in at least 40% of bot matches",
  "how": "bot --policy greedy-vs-greedy --runs 50"}]}
```

- **Slice stage**: 3–6 items with scope `core-loop` (the core loop alone, judged on bots before the slice is polished) or `slice` (the slice as a whole). At least one core-loop proxy, and at least one `human` item for the slice playtest, matching the `slice` page's Playtest section and the vision's kill condition.
- **Production stage**: add items with scope `full` for what only the whole game can show; 10 items at most in all.
- Each item is observable within one play session. Make it a **proxy** whenever a metric can stand for it ([fun-proxies.md](fun-proxies.md)); otherwise `human`, with `metric`, `threshold` and `how` left out.

In interactive mode, the user approves the checklist.

**Done when** the gate lists nothing about the fun checklist for this stage.

## 5. Set the richness targets

Write `docs/game/richness.json`, each target at or above the floor in [richness.md](richness.md) and grounded in the Systems and Content pages:

```json
{"targets": [{"id": "R1", "aspect": "depth", "scope": "full", "statement": "Every system changes how matches go",
  "metric": "shift in the best bot policy's win rate with each system toggled off",
  "threshold": ">= 10 points for every system", "how": "bot --runs 100 per toggle"}]}
```

- **Slice stage**: optional targets with scope `slice`, for depth or variety the slice itself must show.
- **Production stage**: at least one target with scope `full` per aspect (depth, breadth, variety).

Ids share one namespace with the fun checklist. In interactive mode, the user approves the targets.

**Done when** `python3 docs/game/gamestate.py gate` passes.

## 6. Close

`gamestate.py check --since <base>`, commit with the drafts, progress entry. Then write each draft in `docs/game/drafts/` to its page in the docs place, last (an open topic's drafts stay for its brainstorm, session rule 6); in the pages commit, record each page's new `version` and `updated` in `docs/game/wiki.json` and delete the drafts (a change to the vision or slice also updates `docs/game/vision.json`, in the first commit). Then run `gamestate.py complete`.

**Done when** the page fixes and their `wiki.json` entries are committed, the only drafts left are an open topic's, and `complete` succeeds.
