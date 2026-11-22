---
name: game-plan
description: Turn the game design into tech ADRs, a verified walking skeleton, a definition of done (features.json) and tracer-bullet tickets in the configured tracker. Phase 2 of the game-* workflow; also handles adjust, checkpoint and unblock re-plans.
disable-model-invocation: true
---

# Game Plan

Read `docs/agents/game.md` first and follow its session rules. The mode comes from the task:

- **plan** (default): steps 1–5. They rarely fit one session. Do them in order and stop at a session boundary; the next dispatch resumes at the first step whose completion criterion is unmet.
- **adjust**, **checkpoint**, **unblock**: the sections at the end.

On a plan after a restart, first tag HEAD `game-restart-<n>`. Reuse code only where the restart ADR says a system survives.

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

Then fill and smoke-test the adapter: read the `game-setup` skill's SKILL.md (beside this skill) and run its adapter mode.

**Done when** `state.json` has `adapter_verified: true`.

## 3. Definition of done

Write `docs/game/features.json` items (schema in `docs/agents/game.md`), in dependency order within each milestone:

- **core-loop**: the core loop playable end to end with placeholder art.
- **systems**: every system the loop needs (progression, UI, save, settings, audio, netcode, ...). Each system's features include its tuning knobs and on/off toggle.
- **content**: levels, units, items and so on, functional but ugly: built from reusable kit pieces with placeholder art.
- **verdict-build**: what the verdict needs: a metrics feature for every proxy item (listed in its `measures`), the bot policies those metrics require, and a build that runs on every target platform.

Leave `polish` and `release` empty; game-release fills them. Every item needs a pillar, tier, observable acceptance criteria and a verify method. Choose verify kinds in this order of preference: `test`, `sim`, `replay`, `bot`, `capture`, `check`, `human`. A `human` item also gets a human queue entry when it is reached.

**Done when** every `must` feature traces to a pillar, the core loop is covered end to end, and `gamestate.py gate` shows no fun-checklist item missing from `measures`.

## 4. Tickets

Break the features into tickets in the configured tracker:

- each a **tracer bullet**: a thin vertical slice through every layer, verifiable on its own;
- each sized for one fresh session;
- each listing its blocking tickets and the feature ids it serves;
- labelled `ready-for-agent`, or `ready-for-human` for work only a person can do.

Write each ticket's references into its features' `tickets` lists. In interactive mode, show the user the numbered breakdown (title, blocked by, what it delivers) and iterate until they approve.

**Done when** every non-cut feature in the build milestones has a ticket and every ticket names a feature.

## 5. Budget

When `limits.budget_sessions` is empty, set it to about 1.5 × the ticket count plus 10 for verdicts and release. In interactive mode, confirm it with the user.

Close: `gamestate.py check` and `gate`, commit, progress entry.

## Adjust mode

The task names the verdict ADR. Change only the pillars and systems it names:

1. Apply knob-only fixes first: the verdict's suggested knob values go into the knob files.
2. Rewrite the affected features' acceptance or verify where the design changed, and set their `passes` to false; add new features and cut obsolete ones with a `cut_reason`.
3. Ticket the new and reset features.

**Done when** every change the ADR asks for is a feature or a knob change, and the gate passes.

## Checkpoint mode

`gamestate.py status` printed `checkpoint due`: sessions are running ahead of milestones. Cut `nice` features of the remaining build milestones, latest milestone first, until the remaining ticket count fits the remaining budget. Record the cuts in one ADR, then set `checkpoint_due: false` in `state.json`.

## Unblock mode

The task names blocked features. For each, read its `blocked` reason and ticket history, then do one of:

- **replace** it: add smaller features, or ones with a different approach (record the approach change in an ADR), with new tickets; then cut the original with `cut_reason: "replaced by F0xx, F0yy"`. Outside the plan phase this is the only way acceptance or verify changes.
- **cut** it with a reason, when it is not `must`;
- **hand it over**: a human queue entry that `unblocks` it, and its ticket relabelled `ready-for-human`.

**Done when** no failing `must` feature in the current milestone is blocked.
