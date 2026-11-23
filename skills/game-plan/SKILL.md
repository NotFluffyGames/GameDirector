---
name: game-plan
description: Turn the game wiki into tech ADRs, a verified walking skeleton, a definition of done (features.json) and tracer-bullet tickets in the configured tracker - first for the vertical slice, then for production. Phase 4 of the game-* workflow; also handles adjust, restart, checkpoint and unblock re-plans.
disable-model-invocation: true
---

# Game Plan

Derives everything from the wiki (pages indexed in `docs/game/wiki.json`, read through the docs place), and invents no design: when the wiki is silent on something a feature needs, open a topic for it with that feature in `unblocks`, and plan around it. Engineering choices the wiki doesn't cover (tech, architecture, tooling) are ADRs, not topics. Read `docs/agents/game.md` first and follow its session rules. The mode comes from the task:

| Task | Mode |
| --- | --- |
| `game-plan` | the vertical slice: steps 1–5 |
| `game-plan production` | the rest of the game: steps 3–5 (1–2 only for tech the slice didn't settle) |
| `game-plan restart <adr>` | tag HEAD `game-restart-<n>`, then steps 1–5; keep code only where the ADR says a system survives |
| `game-plan adjust <adr>` | Adjust mode |
| `game-plan checkpoint` | Checkpoint mode |
| `game-plan unblock <ids>` | Unblock mode |

Steps 1–5 rarely fit one session. Do them in order and stop at a session boundary; the next session gets the same step and resumes at the first step whose completion criterion is unmet.

## 1. Tech decisions

Write one ADR (with `domain-modeling`) for each of:

- engine and language (choose with [tech-decisions.md](tech-decisions.md));
- target platforms and input devices;
- multiplayer and netcode architecture, when there is more than one player: decided now, because it can't be retrofitted;
- save format and settings storage;
- performance budget per platform: frame time, load time, memory, build size;
- asset sources per asset type: placeholder, generated, sourced (with license), or human.

Then gather the chosen engine's CLI, headless, test-runner and export facts from official docs with the `research` skill into `docs/game/engine-notes.md`.

**Done when** each decision has an ADR and engine-notes.md says how to do every command in the game-setup skill's adapter contract.

## 2. Walking skeleton

Scaffold the smallest project that builds, runs, tests and proves itself, around the **simulation core / presentation shell** seam (shape it with `codebase-design`; see [tech-decisions.md](tech-decisions.md)): a fixed tick, seeded RNG, input as data, serializable state, a tuning-knob file loaded at start, a metrics hook that emits JSON, and one trivial test.

Then fill and smoke-test the adapter: read the `game-setup` skill's SKILL.md (beside this skill) and do its adapter mode.

**Done when** `state.json` has `adapter_verified: true`.

## 3. Definition of done

Write `docs/game/features.json` items (schema in `docs/agents/game.md`; after a restart, number ids after the highest id in `docs/game/archive/`), in dependency order within each milestone:

For the **vertical slice** (`game-plan`), only what the `slice` page's In list needs:

- **core-loop**: the core loop playable end to end with placeholder art, following the Mechanics and Controls pages, plus metrics for every `core-loop` proxy. The core-loop verdict judges it on bots before anything else is built.
- **slice**: everything else the slice contains (its systems, content, screens and onboarding), each aspect brought to the quality bar the `slice` page sets (a `final` art bar means final art features here), metrics for every `slice` proxy and target, and a build a person can play for the slice playtest.

For **production** (`game-plan production`), the rest of the game from the full wiki:

- **systems**: every system on the Systems pages not finished in the slice, with its interactions with the others. Each system's features include its tuning knobs and on/off toggle.
- **content**: every content type at its target count, built from the Content pages' kit pieces at the slice's quality bar. Modes, sessions and the full screen flow land here too.
- **verdict-build**: what the full verdict needs: a metrics feature for every `full` proxy and richness target (listed in its `measures`), the bot policies those metrics require, and a build that runs on every target platform the agent can build for.

Leave `polish` empty; game-polish fills it. Every item needs a pillar, tier, the wiki `pages` (ids from `wiki.json`) it implements, observable acceptance criteria taken from those pages, and a verify method. Choose verify kinds in this order of preference: `test`, `sim`, `replay`, `bot`, `capture`, `check`, `human`. When the adapter marks `sim`, `replay` or `bot` `n/a`, proxy metrics come from instrumented `test` runs or the item becomes `human`.

**Done when** every `must` feature traces to a pillar, everything this stage covers (the slice's In list, or the full wiki) has features, and `gamestate.py gate` shows no proxy or richness target of this stage missing from `measures`.

## 4. Tickets

Break the features into tickets in the configured tracker:

- each a **tracer bullet**: a thin vertical slice through every layer, verifiable on its own;
- each sized for one fresh session;
- each listing its blocking tickets and the feature ids it serves;
- labelled with the `ready-for-agent` role from `docs/agents/triage-labels.md`, or `ready-for-human` for work only a person can do.

Write each ticket's references into its features' `tickets` lists. In interactive mode the user approves the numbered breakdown (title, blocked by, what it delivers).

**Done when** every non-cut feature in the build milestones has a ticket and every ticket names a feature.

## 5. Budget

Set `limits.budget_sessions` to sessions already used plus the sessions the open tickets need: 1.5 per ticket for the slice; for production, the slice's real rate (status shows the sessions the slice took; divide by the slice's tickets) per ticket. Add 25 for verdicts and polish. In interactive mode, the user confirms it.

**Done when** the budget is set, `gamestate.py check --since <base>` passes, and `gamestate.py complete` succeeds after the commit and progress entry.

## Adjust mode

The task names the verdict ADR. Change only the pillars and systems it names:

1. Apply knob-only fixes first: the verdict's suggested knob values go into the knob files, and into drafts of the pages that state them (as in 2).
2. Where the ADR changes the design, draft the changed wiki pages in `docs/game/drafts/`, linking the ADR (session rule 6: committed with the state, written last at the close, their `wiki.json` entries updated in the pages commit); a change to the vision or slice also updates `docs/game/vision.json`. A change that needs a design decision the ADR doesn't make becomes a topic, brainstormed with a person before the features it `unblocks`.
3. Rewrite the affected features' acceptance or verify where the design changed and set their `passes` to false; add new features; cut obsolete ones with a `cut_reason`.
4. Ticket the new and reset features; re-estimate the budget as in step 5.

**Done when** every change the ADR asks for is a knob change, a page change with its features, or an open topic. Close as in step 5: check, commit with the drafts, progress entry, then write the drafts and make the pages commit, then `complete`.

## Checkpoint mode

Sessions are running ahead of milestones. Cut `nice` features of the remaining build milestones, latest milestone first, until 1.5 × the open tickets fits the remaining budget. Record the cuts in one ADR. If cutting every remaining nice feature still doesn't fit, add a human queue entry asking whether to raise the budget or cut must features. Then set `checkpoint_due: false` in `state.json`.

**Done when** `checkpoint_due` is false and the cuts are committed.

## Unblock mode

The task names blocked features (a `blocked` reason, or `max_attempts` build sessions spent). For each, read the reason and ticket history, then do one of:

- **replace** it: add smaller features, or ones with a different approach (record the approach change in an ADR), with new tickets; then cut the original with `cut_reason: "replaced by F0xx, F0yy"`. Outside the plan phase this is the only way a must item's acceptance or verify changes.
- **cut** it with a reason, when it is not `must`;
- **hand it over**: a human queue entry that `unblocks` it, and its ticket relabelled `ready-for-human`.

**Done when** no failing `must` feature named in the task is still blocked.
