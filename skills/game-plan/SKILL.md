---
name: game-plan
description: Turn the game wiki into tech ADRs, a walking skeleton that captures and logs itself, a capture protocol, a definition of done (features.json) that opens with the visual and feel targets and gives visible features roles and measured checks, and tracer-bullet tickets in the configured tracker - first for the vertical slice, then for production. Runs after consolidate in the game-* workflow; also handles adjust, restart, checkpoint and unblock re-plans.
disable-model-invocation: true
---

# Game Plan

Derives everything from the wiki (pages indexed in `docs/game/wiki.json`, read through the docs place), and invents no design: when the wiki is silent on something a feature needs, open a topic for it with that feature in `unblocks`, and plan around it. Engineering choices the wiki doesn't cover (tech, architecture, tooling) are ADRs, not topics. Read `docs/agents/game.md` first and follow its session rules. The mode comes from the task:

| Task | Mode |
| --- | --- |
| `game-plan` | the vertical slice: steps 1–6 |
| `game-plan production` | the rest of the game: steps 3–6 (1–2 only for tech the slice didn't settle) |
| `game-plan restart <adr>` | tag HEAD `game-restart-<n>`, then steps 1–6; keep code only where the ADR says a system survives |
| `game-plan adjust <adr>` | Adjust mode |
| `game-plan checkpoint` | Checkpoint mode |
| `game-plan unblock <ids>` | Unblock mode |

Steps 1–6 rarely fit one session. Do them in order and stop at a session boundary; the next session gets the same step and resumes at the first step whose completion criterion is unmet.

## 1. Tech decisions

Write one ADR (with `domain-modeling`) for each of:

- engine and language (choose with [tech-decisions.md](tech-decisions.md));
- target platforms and input devices;
- multiplayer and netcode architecture, when there is more than one player: decided now, because it can't be retrofitted;
- save format and settings storage;
- performance budget per platform: frame time, load time, memory, build size;
- asset sources per asset type: placeholder, generated, sourced (with license), or human.

Then gather the chosen engine's CLI, headless, off-screen rendering, test-runner and export facts from official docs with the `research` skill into `docs/game/engine-notes.md`.

**Done when** each decision has an ADR and engine-notes.md says how to do every command in the game-setup skill's adapter contract.

## 2. Walking skeleton

Scaffold the smallest project that builds, runs, tests and proves itself, around the **simulation core / presentation shell** seam (shape it with `codebase-design`; see [tech-decisions.md](tech-decisions.md)): a fixed tick, seeded RNG, input as data, serializable state, a tuning-knob file loaded at start, a metrics hook that emits JSON, and one trivial test.

The skeleton also shows and logs itself for the roles' reviews: `capture` of named states and frame strips, the event log from `sim`, `replay` and `bot`, and the dumps and loudness the engine can give, as the adapter contract's "What the roles read" defines them (how to build them on the seam: [tech-decisions.md](tech-decisions.md)). Add the contract's test fixture (Smoke test, "Test fixtures"), so each is proven before the game has content of its own.

Then fill and smoke-test the adapter: read the `game-setup` skill's SKILL.md (beside this skill) and do its adapter mode against [adapter-contract.md](../game-setup/adapter-contract.md).

**Done when** `state.json` has `adapter_verified: true`, with named states, strips, the event log, the dumps and loudness each verified on the test fixture or `n/a` because the engine can't give it.

## 3. Capture protocol

Name what the roles will look at, and record it in `docs/game/engine-notes.md` under "Capture protocol", each definition holding what the adapter contract's "What the roles read" asks of it:

- **Named states**, each a seed, a tick or replay prefix, and a camera: a beauty view of the visual target's area, a typical play moment, peak effects load, each main menu, and the HUD over the brightest and the darkest areas of play. Name each for what it shows (`beauty`, `hud-dark`).
- **Frame strips**, one per core action on the `feel` page, named as the feel sheets and the event log name the action: its scripted input file, the frame count and the step, enough frames to show the action from input to recovery.

The replay prefixes and input files are made by the features that first show them (step 4). In production, add the states and strips the production pages bring (each new menu, mode or area), keeping the names already recorded.

**Done when** the capture protocol in engine-notes.md defines every state and strip above that this stage's pages call for.

## 4. Definition of done

Write `docs/game/features.json` items (schema in `docs/agents/game.md`; after a restart, number ids after the highest id in `docs/game/archive/`), in dependency order within each milestone:

For the **vertical slice** (`game-plan`), only what the `slice` page's In list needs:

- **core-loop** opens with the **feel target** (`target: feel`, tier `must`), after only what it depends on: the core action at its feel sheet's targets, at the feel bar (`vision.json` `slice.quality_bar.feel`). Then the core loop playable end to end with placeholder art, following the Mechanics and Controls pages, plus metrics for every `core-loop` proxy. The core-loop verdict judges it on bots before anything else is built.
- **slice** opens with the **visual target** (`target: visual`, tier `must`): one in-game scene, the area the `slice` page's Means column names, built to the art bar (`slice.quality_bar.art`). Then everything else the slice contains (its systems, content, screens and onboarding), each aspect brought to the quality bar the `slice` page sets (a `final` art bar means final art features here), metrics for every `slice` proxy and target, and a build a person can play for the slice playtest.

The gate asks for each target while its role (`feel`, `art`) is active.

For **production** (`game-plan production`), the rest of the game from the full wiki:

- **systems**: every system on the Systems pages not finished in the slice, with its interactions with the others. Each system's features include its tuning knobs and on/off toggle.
- **content**: every content type at its target count, built from the Content pages' kit pieces at the slice's quality bar. Modes, sessions and the full screen flow land here too.
- **verdict-build**: what the full verdict needs: a metrics feature for every `full` proxy and richness target (listed in its `measures`), the bot policies those metrics require, and a build that runs on every target platform the agent can build for.

Leave `polish` empty; game-polish fills it. Every item needs a pillar, tier, the wiki `pages` (ids from `wiki.json`) it implements, observable acceptance criteria taken from those pages, and a verify method. Choose verify kinds in this order of preference: `test`, `sim`, `replay`, `bot`, `capture`, `check`, `human`. When the adapter marks `sim`, `replay` or `bot` `n/a`, proxy metrics come from instrumented `test` runs or the item becomes `human`.

**Roles.** Give every feature its `roles` as "Which roles are in charge" in `docs/agents/game.md` says: the roles of its pages' areas when the player sees, hears or does it with their hands; `[]` when it is rules-only; never `design`.

**Measured checks.** A visible feature's acceptance adds the measured checks its roles' pages imply, at its milestone's quality bar: the "Checked first" lines of each role's `checklist.md` (`../game-role-<role>/` beside this skill), filled with the page's numbers: a palette share outside the art bible's table, a value range, a contrast ratio, input-to-response frames and feedback channels in the event log, sound coverage, a loudness target, a launch-to-control time, a string length. One check per acceptance line, so a review can quote the line it fails: frozen after plan, these lines are the only measured facts that can block a feature. The bar per milestone:

- core-loop: `placeholder`, except the feel target at the feel bar;
- slice: `vision.json` `slice.quality_bar`, narrowed per area as the `slice` page's Means column says: the visual target's area at the art bar, the rest of the slice at the level its Means column gives;
- production milestones: the slice's bars.

An aspect at `placeholder` gets no measured checks. A check whose input the adapter marks `n/a` becomes a `human` verify item, as the adapter contract's "When the engine resists" says.

**Captures.** The first feature that shows a named state or strip (step 3) makes it render, in one acceptance line ("`capture --state hud-dark` renders the HUD over the darkest area").

**Done when** every `must` feature traces to a pillar; everything this stage covers (the slice's In list, or the full wiki) has features; every visible feature has `roles` and the measured checks of its milestone's bar; every named state and strip has the feature that makes it render; and `gamestate.py gate` names no missing visual or feel target and no proxy or richness target of this stage missing from `measures`.

## 5. Tickets

Break the features into tickets in the configured tracker:

- each a **tracer bullet**: a thin vertical slice through every layer, verifiable on its own;
- each sized for one fresh session;
- each listing its blocking tickets and the feature ids it serves;
- labelled with the `ready-for-agent` role from `docs/agents/triage-labels.md`, or `ready-for-human` for work only a person can do.

Write each ticket's references into its features' `tickets` lists. In interactive mode the user approves the numbered breakdown (title, blocked by, what it delivers).

**Done when** every non-cut feature in the build milestones has a ticket and every ticket names a feature.

## 6. Budget

Set `limits.budget_sessions` to sessions already used plus the sessions the open tickets need: 1.5 per ticket for the slice; for production, the slice's real rate (status shows the sessions the slice took; divide by the slice's tickets) per ticket. Add 25 for verdicts and polish. In interactive mode, the user confirms it.

**Done when** the budget is set, `gamestate.py check --since <base>` passes, and `gamestate.py complete` succeeds after the commit and progress entry.

## Adjust mode

The task names the verdict ADR. Change only the pillars and systems it names:

1. Apply knob-only fixes first: the verdict's suggested knob values go into the knob files, and into drafts of the pages that state them (as in 2).
2. Where the ADR changes the design, draft the changed wiki pages in `docs/game/drafts/`, linking the ADR (session rule 6: committed with the state, written last at the close, their `wiki.json` entries updated in the pages commit); a change to the vision or slice also updates `docs/game/vision.json`. A change that needs a design decision the ADR doesn't make becomes a topic, brainstormed with a person before the features it `unblocks`.
3. Rewrite the affected features' acceptance or verify where the design changed and set their `passes` to false; add new features; cut obsolete ones with a `cut_reason`. When the ADR changes `north_stars.art`, the visual target is among them: rebuilt to the new direction, its pass queues a fresh calibration kit.
4. Ticket the new and reset features; re-estimate the budget as in step 6.

**Done when** every change the ADR asks for is a knob change, a page change with its features, or an open topic. Close as in step 6: check, commit with the drafts, progress entry, then write the drafts and make the pages commit, then `complete`.

## Checkpoint mode

Sessions are running ahead of milestones. Cut `nice` features of the remaining build milestones, latest milestone first, until 1.5 × the open tickets fits the remaining budget. Record the cuts in one ADR. If cutting every remaining nice feature still doesn't fit, add a human queue entry asking whether to raise the budget or cut must features. Then set `checkpoint_due: false` in `state.json`.

**Done when** `checkpoint_due` is false and the cuts are committed.

## Unblock mode

The task names blocked features (a `blocked` reason, or `max_attempts` build sessions spent). For each, read the reason and ticket history, then do one of:

- **replace** it: add smaller features, or ones with a different approach (record the approach change in an ADR), with new tickets; then cut the original with `cut_reason: "replaced by F0xx, F0yy"`. Outside the plan phase this is the only way a must item's acceptance or verify changes.
- **cut** it with a reason, when it is not `must`;
- **hand it over**: a human queue entry that `unblocks` it, and its ticket relabelled `ready-for-human`.

**Done when** no failing `must` feature named in the task is still blocked.
