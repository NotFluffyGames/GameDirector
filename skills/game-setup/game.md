# Game workflow

Config for the game-* skills. Every game-* session reads this file first. Edit it freely; it is the project's, not the skills'.

## The goal

A game that is **fun, playable, rich, working, testable and tested**, described by an up-to-date wiki and GDD. Publishing it is out of scope. The run is complete when:

| Quality | Checked by |
| --- | --- |
| Playable | the packaged build launches without dev tools and plays from title screen to the end of a session, on every target platform this machine can build for |
| Working | every `must` feature passes; a long crash and softlock fuzz run is clean |
| Tested | tests, replays and bot runs cover the core rules and every feature, green on the final build |
| Testable | the simulation core is deterministic and the adapter commands re-run every check |
| Rich | every richness target passes on the final build |
| Fun | every fun proxy passes on the final build, and the playtest kit is ready; people's answers can still reopen the verdict |

The phases: setup → ideation → brainstorm → consolidate → plan → build → verdict (core-loop) → build → verdict (full) → polish → verdict (final) → done. Brainstorming doesn't end with its phase: any later phase opens a topic when it meets a question the wiki doesn't answer.

The game is made over **many sessions, one step per session**. A person starts a session and runs `/game-next`; `gamestate.py status` names the step, the session does it, checks it and stops. Steps that need no person can also run back to back unattended (the game-next skill's `unattended.md`).

## Autonomy

Mode: {{autonomous | interactive}}

Ideation and brainstorm topics are always conversations with a person (`with-user:` steps), whatever the mode. The mode decides the rest:

- **autonomous**: other steps decide on their own. At each judgement call, take the recommended answer and record it in an ADR as an assumption a human can overturn. Work only a person can do goes to the **human queue**.
- **interactive**: the user also approves the ticket breakdown (game-plan) and decides each verdict's outcome (game-verdict), when they are in the session.

## Session rules

Every game-* session is a **fresh session** doing **one task**:

1. Start: note your base commit (`git rev-parse HEAD`) and run `python3 docs/game/gamestate.py status`. Read only the files your task names; reach for more only when the work demands it.
2. Hand reading-heavy exploration to a subagent or the `research` skill, which returns a summary or writes notes to a file.
3. When the step outgrows the session (a second unplanned subsystem appears, or you are past roughly half your context), split: write the remainder as new tickets, features or topics, commit what is green, stop. The next dispatch of the same task resumes from what is on disk.
4. Leave the repo green: commit only work whose tests pass.
5. **Keep the wiki true.** When your work changes what the game is or how it plays, update the wiki page that describes it in the same commit. When you meet a design question no page answers, open a topic for it rather than deciding silently.
6. End: `gamestate.py check --since <base>` passing; a commit; a progress entry of at most 10 lines appended to `docs/game/progress.md`; when the task is the phase's own (status shows `task:`) and every step is done, `gamestate.py complete`; and a short report: what changed, the **evidence**, what is left.

**Asking the user.** Ask the person in the session directly, one question at a time, each with your recommended answer. In an unattended session (`--unattended`), take the recommended answer and record it in an ADR as an assumption.

**The bar only rises.** Outside the plan phase a feature is never deleted and its `acceptance`, `verify` and `milestone` never change; a `must` feature leaves `must` only as `tier: "cut"` with `cut_reason: "replaced by F0xx[, F0yy]"` naming live must features. After consolidate, fun checklist items and richness targets can be added but not changed or removed. Set `passes: true` only with evidence from a run in this session. `gamestate.py check` enforces all of this against your base commit. The wiki, by contrast, changes freely: it describes the game, it doesn't judge it.

## The wiki (agent-facing)

`docs/game/wiki/` is the living description of the game, written for agents: precise enough to plan, build and test from. It holds the **current truth** only; why something changed lives in an ADR the page links to.

- `index.md`: the map. One `##` section per area (Vision, Mechanics, Controls, Systems, Content, Modes and sessions, Screens and onboarding, Feel, Tone, art and world), each listing its pages as relative links with one line each. Every page is reachable from it.
- `vision.md` (pitch, audience and platforms, pillars, core loop, target feeling, tone, references, scope) and `concepts.md` (the directions compared and the choice), both from ideation.
- Every other page: one subject (a system, a content type, a mode, a screen flow), written by brainstorm topics and kept true by every phase. A page starts with:

  ```markdown
  # <Title>

  Topics: T004, T019 · Decisions: ADR-0007 · Last changed: <date>, <what and why in one line>
  ```

- Link instead of repeating; split a page that passes about 200 lines; use the terms in `CONTEXT.md`.

## Topics

`docs/game/topics.json` holds the brainstorm tree: every design question, open or answered. Each topic is brainstormed with a person, one per session, and mirrored as a `ready-for-human` ticket in the tracker.

```json
{"id": "T014", "title": "Weapon stealing", "parent": "T003",
 "question": "How does a player take an opponent's weapon, and what stops it from dominating?",
 "priority": "core", "status": "open",
 "pages": ["wiki/systems/weapons.md"], "unblocks": ["F021"], "ticket": "#88",
 "resolution": ""}
```

- `priority`: `core` (the core loop depends on it), `support` (needed before planning is complete), `later` (depth that can wait).
- `status`: `open`, `resolved` (its `pages` were written or updated and `resolution` gives the answer in a line) or `deferred` (`resolution` says why it waits). Any session may reopen a topic when the game changes under it.
- `unblocks`: features that can't be built until it is answered; the status tool brainstorms those topics before building them.

## The GDD (human-facing)

A game design document for people, kept next to the tasks, where `docs/agents/human-docs.md` says. game-gdd writes it from the wiki in plain language and updates the pages whose wiki sources changed; the status tool makes it the next step before every phase or milestone change while the wiki has changed since the last sync. People read and comment there; their edits and comments come back as topics, never as silent changes to the wiki.

## Files

| Path | What | Written by |
| --- | --- | --- |
| `docs/game/seed.md` | the user's original prompt, verbatim | game-setup |
| `docs/game/wiki/` | the living, agent-facing description of the game | ideation, brainstorm, consolidate; every phase keeps it true |
| `docs/game/topics.json` | the brainstorm tree | ideation, brainstorm; any phase opens topics |
| `docs/game/fun-checklist.json` | fun checklist | game-consolidate |
| `docs/game/richness.json` | richness targets | game-consolidate |
| `docs/game/features.json` | definition of done | game-plan, game-polish add items; game-build sets `passes` |
| `docs/game/state.json` | phase, milestone, task, counters, limits, attempts, verdicts, human queue, GDD sync point | `gamestate.py`; skills append verdicts and queue entries and set `adapter_verified` |
| `docs/game/progress.md` | append-only session log | every session |
| `docs/game/assets.md` | every asset's source and license | whoever adds an asset |
| `docs/game/engine-notes.md` | engine CLI, headless, test and export facts | game-plan |
| `docs/game/playtests/` | verdict evidence, captures, human playtest kits and answers | game-verdict, game-build |
| `docs/game/archive/restart-N/` | the definition of done and human queue from before restart N | `gamestate.py` |
| `docs/game/gamestate.py` | reads, checks and advances state; commits its own state changes | game-setup installs it |

Decisions are ADRs and game terms live in `CONTEXT.md`, both where `docs/agents/domain.md` says. Tickets live in the tracker `docs/agents/issue-tracker.md` describes, labelled with the roles in `docs/agents/triage-labels.md`. Human-facing documents live where `docs/agents/human-docs.md` says.

## Vocabulary

- **Pillars**: 3–4 statements of the feelings or features the game delivers, written `- **P1**: ...` in `wiki/vision.md`. Every feature serves one; a feature with no pillar is not in the game.
- **Core loop**: the action the player repeats minute to minute, in one sentence.
- **Design-ready**: a topic's question is answered on a page precisely enough to plan features and write tests from. Brainstorming aims here, not at exhaustiveness.
- **Fun checklist**: 3–6 statements that are true when the game is fun, each observable in one play session. A **proxy** item has a metric, threshold and method a bot run or replay can measure. A **human** item needs a person.
- **Richness targets**: `richness.json` targets `{id, aspect, statement, metric, threshold, how}`, at least one per aspect: **depth** (systems that change each other), **breadth** (distinct content), **variety** (playthroughs that differ). Scored at the full and final verdicts.
- **Scope tiers**: `must`, `nice`, `cut`. Nice features are built after their milestone's must features, while the budget has room.
- **Tuning knobs**: per-system values and an on/off toggle, loaded from data so they change without code edits.
- **Simulation core / presentation shell**: game rules live in a deterministic core (fixed tick or turn, seeded RNG, input as data, serializable state) that runs headless. Rendering, audio and input devices live in a thin shell around it. Tests, bots and replays drive the core.
- **Tick**: one step of the simulation core: a fixed-timestep frame in a real-time game, one turn or action in a turn-based one.
- **Definition of done**: `features.json`. With the final verdict, it is how the goal above is checked.
- **Evidence**: the command run, its result (numbers, hash, artifact path) and the commit.
- **Task**: what the current phase still owes (`state.json` `task`, shown by status). Phase skills clear it with `gamestate.py complete` as their last step.
- **Gate**: a phase's completion criterion, checked by `gamestate.py gate`.
- **Verdict**: the scored judgement of a green build against the fun checklist and richness targets: `ship`, `adjust` or `restart`. Scopes: `core-loop` (after the core-loop milestone), `full` (before polish), `final` (after polish; shipping it completes the run). It runs again when playtest answers arrive.
- **Durable assets**: seed.md, the wiki, the fun checklist, richness targets, ADRs, CONTEXT.md and final art. They survive a restart. Code is disposable.
- **Human queue**: `state.json` `human_queue` entries `{id, what, why, how, unblocks: [feature ids]}` for work only a person can do, each mirrored as a `ready-for-human` ticket. The run moves past queued features and stops at the end for the queue; open playtest entries don't stop it. A person finishing an entry deletes it, and for a `human`-verified feature sets `passes: true` with evidence starting `human:`; the next `/game-next` session goes back to anything still failing. A playtest entry also has `kind: "playtest"`, `scope` and `answers` (a file path): the person writes their answers to that file and leaves the entry, and the next session reopens the verdict with them.

### features.json item

```json
{
  "id": "F012", "title": "Save and load a run",
  "pillar": "P2", "tier": "must", "milestone": "systems",
  "acceptance": ["Quitting mid-run and relaunching restores the same state hash"],
  "verify": {"kind": "replay", "how": "replay tests/replays/save-mid-run.json; state hash matches"},
  "pages": ["wiki/systems/saves.md"], "measures": [], "tickets": ["#41"],
  "passes": false, "evidence": "", "blocked": "", "cut_reason": ""
}
```

`milestone` is one of `core-loop`, `systems`, `content`, `verdict-build`, `polish`. `verify.kind` is one of `test`, `sim`, `replay`, `bot`, `capture`, `check` (any scripted or recorded inspection) or `human`. `pages` lists the wiki pages the feature implements. `measures` lists the fun proxy and richness target ids whose metric this feature produces. Ids are never reused, including ids in `docs/game/archive/`. Build attempts are counted by `gamestate.py` in `state.json` `attempts`.

## Limits

In `docs/game/state.json` `limits`:

| Limit | Default | When reached |
| --- | --- | --- |
| `budget_sessions` | 150 sessions, re-estimated by game-plan and game-polish | the run stops |
| `brainstorm_share` | 0.2 of the budget for brainstorm sessions | support topics wait; consolidate defers what is left |
| `max_adjusts` | 2 | the run stops for a human decision |
| `max_restarts` | 1 | the run stops for a human decision |
| `max_attempts` | 3 build sessions per feature since it last passed | the feature counts as blocked and goes to game-plan's unblock mode |
| `max_repeats` | 5 sessions in a row on the same step | the run stops as stalled |

## Commands

The adapter: how this project builds, runs and proves itself. Contract: the game-setup skill's `adapter-contract.md`. Empty until game-plan picks the engine.

| Name | Command | Verified |
| --- | --- | --- |
| bootstrap | | |
| build | | |
| test | | |
| run | | |
| sim | | |
| replay | | |
| bot | | |
| capture | | |
| package | | |

## Companion skills

The game-* skills lean on these. When one isn't installed, do what its "If missing" column says.

| Skill | Used for | If missing |
| --- | --- | --- |
| `grilling` | walking a design tree | ask, or answer, one question at a time until every branch is resolved |
| `domain-modeling` | CONTEXT.md terms and ADRs | ADR = context, decision, consequences, in the ADR folder, numbered |
| `codebase-design` | the simulation core / presentation shell seam, deep modules | small interfaces over large implementations; test at the seam |
| `prototype` | a clickable demo of a mechanic or UI for a person to judge (interactive mode only) | skip the demo; build the feature and let the verdict judge it |
| `tdd` | building game rules test-first in the simulation core | red, green, refactor, one behaviour at a time |
| `code-review` | reviewing each session's diff | review the diff against the ticket, the wiki pages it implements and the repo's standards |
| `diagnosing-bugs` | a red verify or a regression | reproduce, minimise, hypothesise, fix, add the regression test |
| `research` | reference games, engine and platform facts from primary sources | read primary sources; save the facts with links to a notes file |
| `wizard` | a walkthrough for a multi-step human queue entry | a numbered checklist with exact URLs, clicks and where each value goes |
