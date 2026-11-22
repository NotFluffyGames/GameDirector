---
name: game-plan
description: Turn the game design into tech ADRs, a verified walking skeleton, a definition of done (features.json) and tracer-bullet tickets in the configured tracker. Phase 2 of the game-* workflow; also handles adjust, restart, checkpoint and unblock re-plans.
disable-model-invocation: true
---

# Game Plan

Read `docs/agents/game.md` first and follow its session rules. The mode comes from the task:

| Task | Mode |
| --- | --- |
| `game-plan` | steps 1–5 |
| `game-plan restart <adr>` | tag HEAD `game-restart-<n>`, then steps 1–5; keep code only where the ADR says a system survives |
| `game-plan adjust <adr>` | Adjust mode |
| `game-plan checkpoint` | Checkpoint mode |
| `game-plan unblock <ids>` | Unblock mode |

Steps 1–5 rarely fit one session. Do them in order and stop at a session boundary; the same task is dispatched again and resumes at the first step whose completion criterion is unmet.

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

- **core-loop**: the core loop playable end to end with placeholder art.
- **systems**: every system the loop needs (progression, UI, save, settings, audio, netcode, ...). Each system's features include its tuning knobs and on/off toggle.
- **content**: levels, units, items and so on, functional but ugly: built from reusable kit pieces with placeholder art.
- **verdict-build**: what the verdict needs: a metrics feature for every proxy item (listed in its `measures`), the bot policies those metrics require, and a build that runs on every target platform the agent can build for.

Leave `polish` and `release` empty; game-release fills them. Every item needs a pillar, tier, observable acceptance criteria and a verify method. Choose verify kinds in this order of preference: `test`, `sim`, `replay`, `bot`, `capture`, `check`, `human`. When the adapter marks `sim`, `replay` or `bot` `n/a`, proxy metrics come from instrumented `test` runs or the item becomes `human`.

**Done when** every `must` feature traces to a pillar, the core loop is covered end to end, and `gamestate.py gate` shows no fun-checklist item missing from `measures`.

## 4. Tickets

Break the features into tickets in the configured tracker:

- each a **tracer bullet**: a thin vertical slice through every layer, verifiable on its own;
- each sized for one fresh session;
- each listing its blocking tickets and the feature ids it serves;
- labelled with the `ready-for-agent` role from `docs/agents/triage-labels.md`, or `ready-for-human` for work only a person can do.

Write each ticket's references into its features' `tickets` lists. In interactive mode the user approves the numbered breakdown (title, blocked by, what it delivers), through the questions protocol when you can't reach them.

**Done when** every non-cut feature in the build milestones has a ticket and every ticket names a feature.

## 5. Budget

Set `limits.budget_sessions` to sessions already used, plus 1.5 × the open tickets, plus 20 for verdicts and release. In interactive mode, the user confirms it.

**Done when** the budget is set. Close: `gamestate.py check --since <base>`, commit, progress entry, `gamestate.py complete`.

## Adjust mode

The task names the verdict ADR. Change only the pillars and systems it names:

1. Apply knob-only fixes first: the verdict's suggested knob values go into the knob files.
2. Rewrite the affected features' acceptance or verify where the design changed and set their `passes` to false; add new features; cut obsolete ones with a `cut_reason`.
3. Ticket the new and reset features; re-estimate the budget as in step 5.

**Done when** every change the ADR asks for is a knob change or a feature with a ticket. Close as in step 5, including `complete`.

## Checkpoint mode

Sessions are running ahead of milestones. Cut `nice` features of the remaining build milestones, latest milestone first, until 1.5 × the open tickets fits the remaining budget. Record the cuts in one ADR. If cutting every remaining nice feature still doesn't fit, add a human queue entry asking whether to raise the budget or cut must features. Then set `checkpoint_due: false` in `state.json`.

**Done when** `checkpoint_due` is false and the cuts are committed.

## Unblock mode

The task names blocked features (a `blocked` reason, or `max_attempts` build sessions spent). For each, read the reason and ticket history, then do one of:

- **replace** it: add smaller features, or ones with a different approach (record the approach change in an ADR), with new tickets; then cut the original with `cut_reason: "replaced by F0xx, F0yy"`. Outside the plan phase this is the only way a must item's acceptance or verify changes.
- **cut** it with a reason, when it is not `must`;
- **hand it over**: a human queue entry that `unblocks` it, and its ticket relabelled `ready-for-human`.

**Done when** no failing `must` feature named in the task is still blocked.
