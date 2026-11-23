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

The game is made in two **stages**:

- **slice** (pre-production): setup → ideation (vision and vertical slice) → brainstorm (only the slice's topics) → consolidate → plan → build the core loop → verdict (core-loop, on bots) → build the rest of the slice to its quality bar → verdict (slice: the gate into production, after a person's playtest).
- **production**: brainstorm (the remaining topics) → consolidate → plan → build systems and content → verdict (full) → polish → verdict (final) → done.

Brainstorming doesn't end with its phase: any later phase opens a topic when it meets a question the wiki doesn't answer.

The game is made over **many sessions, one step per session**. A person starts a session and runs `/game-next`; `gamestate.py status` names the step, the session does it, checks it and stops. Steps that need no person can also run back to back unattended (the game-next skill's `unattended.md`).

## Autonomy

Mode: {{autonomous | interactive}}

Setup, ideation and brainstorm topics are always conversations with a person (`with-user:` steps), and the slice verdict always waits for a person's playtest, whatever the mode. The mode decides the rest:

- **autonomous**: other steps decide on their own. At each judgement call, take the recommended answer and record it in an ADR as an assumption a human can overturn. Work only a person can do goes to the **human queue**.
- **interactive**: the user also approves the fun checklist and richness targets (game-consolidate), the ticket breakdown (game-plan) and each verdict's outcome (game-verdict), when they are in the session.

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

## The wiki

The wiki is the living description of the game: precise enough to plan, build and test from. It holds the **current truth** only; why something changed lives in an ADR the page links to. Its pages live in the docs place next to the tasks, which `docs/agents/docs.md` names with how to read, write and comment there. A user who chose local files gets `docs/game/wiki/` instead; that is the only case where the wiki is in the repo.

`docs/game/wiki.json` indexes the pages, one entry each:

```json
{"pages": [
  {"id": "weapons", "title": "Weapons", "area": "Systems",
   "link": "https://example.com/docs/weapons", "version": 3, "updated": "2026-11-22",
   "flagged": {"topic": "T031", "note": "edited by hand; check against the page"}}
]}
```

- `id`: unique and stable; topics and features name pages by it.
- `area`: Vision, Mechanics, Controls, Systems, Content, Modes and sessions, Screens and onboarding, Feel, Tone, art and world. Each area is a section of the wiki's home page, listing its pages with one line each.
- `link`: the page's URL, or its repo-relative path for local files.
- `version` and `updated`: bumped by the session that writes the page; they are how a direct edit is noticed.
- `flagged`: set when a direct edit was detected. It names the open topic that reviews the edit, and clears when that topic resolves.
- The pages `vision`, `slice` and `concepts` always exist, all from ideation: `vision` (pitch, audience and platforms, pillars, anti-pillars, core loop, target feeling, tone, references, scope, kill condition), `slice` (what the vertical slice proves, what is in and out, its quality bar, its playtest) and `concepts` (the directions compared and the choice).
- Every other page has one subject (a system, a content type, a mode, a screen flow), is written by brainstorm topics and kept true by every phase. It starts with:

  ```markdown
  # <Title>

  Topics: T004, T019 · Decisions: ADR-0007 · Last changed: <date>, <what and why in one line>
  ```

- Link instead of repeating; split a page that passes about 200 lines; use the terms in `CONTEXT.md`.

**Comments only.** People comment on wiki pages; sessions edit them. A person's comment becomes a topic or a note, never a silent change. Each session compares the pages' versions with `wiki.json` and, for a page edited directly, sets `flagged` and opens a topic to review it.

**Pages are written last.** A session finishes its work first, then writes the pages and updates `wiki.json` in the same commit. When the docs place can't be reached, the session stops with `stop: <tracker> docs unreachable` (naming the tracker from `issue-tracker.md`) rather than writing the pages elsewhere. Local files are used only when the user chose them in setup.

**Setup is always `with-user:`.** Setup can't complete until `docs/agents/docs.md` exists and `state.json` has `docs_verified: {"place": "...", "date": "YYYY-MM-DD"}`, recording that the user's chosen place passed its smoke test.

### vision.json

`docs/game/vision.json` holds the vision's facts as data, so that checks and the verdict read them without parsing prose. The `vision` and `slice` pages explain them.

```json
{
  "pillars": [{"id": "P1", "statement": "Every fight is a negotiation"}],
  "anti_pillars": ["No grinding for stats"],
  "kill_condition": "Fewer than half of testers start a second match",
  "slice": {
    "test_question": "Is one match fun enough to repeat?",
    "quality_bar": {"code": "representative", "feel": "production", "art": "placeholder",
                    "audio": "placeholder", "ui": "representative", "onboarding": "placeholder"}
  },
  "directions": {"count": 3, "choice": "B"}
}
```

Each quality bar is `placeholder`, `representative`, `production` or `final`.

## Topics

`docs/game/topics.json` holds the brainstorm tree: every design question, open or answered. Each topic is brainstormed with a person, one per session, and mirrored as a `ready-for-human` ticket in the tracker.

```json
{"id": "T014", "title": "Weapon stealing", "parent": "T003",
 "question": "How does a player take an opponent's weapon, and what stops it from dominating?",
 "priority": "core", "stage": "slice", "status": "open",
 "pages": ["weapons"], "unblocks": ["F021"], "ticket": "#88",
 "resolution": ""}
```

- `priority`: `core` (the core loop depends on it), `support` (needed before planning is complete), `later` (depth that can wait).
- `stage`: `slice` when the vertical slice needs it answered, otherwise `production`. Production topics wait until the slice ships.
- `status`: `open`, `resolved` (its `pages` were written or updated and `resolution` gives the answer in a line) or `deferred` (`resolution` says why it waits). Any session may reopen a topic when the game changes under it.
- `unblocks`: features that can't be built until it is answered; the status tool brainstorms those topics before building them.

## The GDD

A game design document for people, kept next to the tasks in the docs place `docs/agents/docs.md` names. game-gdd writes it from the wiki in plain language and updates the pages whose wiki sources changed. The status tool makes it the next step before every phase or milestone change while `wiki.json` or `own-calls.md` has changed since the last `gdd-synced`. People read and comment there; their edits and comments come back as topics, never as silent changes to the wiki.

## Files

| Path | What | Written by |
| --- | --- | --- |
| `docs/game/seed.md` | the user's original prompt, verbatim | game-setup |
| `docs/game/wiki.json` | index of the wiki pages (the pages live in the docs place) | ideation, brainstorm, consolidate; every phase keeps it true |
| `docs/game/vision.json` | pillars, anti-pillars, kill condition, slice test question and quality bars, directions | ideation |
| `docs/game/topics.json` | the brainstorm tree | ideation, brainstorm; any phase opens topics |
| `docs/game/fun-checklist.json` | fun checklist | game-consolidate |
| `docs/game/keep.json` | what playtests and people said to keep, with pinned tuning values | game-verdict, game-gdd |
| `docs/game/own-calls.md` | player-visible choices agents made that no page specified | game-build, any session |
| `docs/game/richness.json` | richness targets | game-consolidate |
| `docs/game/features.json` | definition of done | game-plan, game-polish add items; game-build sets `passes` |
| `docs/game/state.json` | phase, milestone, task, counters, limits, attempts, verdicts, human queue, GDD sync point, `adapter_verified`, `docs_verified` | `gamestate.py`; skills append verdicts and queue entries; game-setup sets `docs_verified` and `adapter_verified` |
| `docs/game/progress.md` | append-only session log | every session |
| `docs/game/assets.md` | every asset's source and license | whoever adds an asset |
| `docs/game/engine-notes.md` | engine CLI, headless, test and export facts | game-plan |
| `docs/game/playtests/` | verdict evidence, captures, human playtest kits and answers | game-verdict, game-build |
| `docs/game/archive/restart-N/` | the definition of done and human queue from before restart N | `gamestate.py` |
| `docs/agents/docs.md` | where the wiki and GDD live and how to read, write and comment there | game-setup; game-gdd records new GDD pages |
| `docs/game/gamestate.py` | reads, checks and advances state; commits its own state changes | game-setup installs it |

Decisions are ADRs and game terms live in `CONTEXT.md`, both where `docs/agents/domain.md` says. Tickets live in the tracker `docs/agents/issue-tracker.md` describes, labelled with the roles in `docs/agents/triage-labels.md`. The wiki and GDD live where `docs/agents/docs.md` says.

## Vocabulary

- **Pillars**: 3–4 statements of the feelings or features the game delivers, in `vision.json`. Every feature serves one; a feature with no pillar is not in the game. **Anti-pillars** say what the game will never do and which pillar each protects.
- **Kill condition**: the playtest result, stated in `vision.json`, that would stop the game as conceived. The slice verdict checks it.
- **Vertical slice**: the small part of the game built first (`slice` page and `vision.json`): one complete start → challenge → resolution delivering the target feeling, at the quality bar the user chose per aspect (`placeholder`, `representative`, `production` or `final`). Its verdict, after a person's playtest, is the gate into production, and the sessions it took set the production budget.
- **Core loop**: the action the player repeats minute to minute, in one sentence.
- **Design-ready**: a topic's question is answered on a page precisely enough to plan features and write tests from. Brainstorming aims here, not at exhaustiveness.
- **Fun checklist**: statements that are true when the game is fun, each observable in one play session, with a `scope`: `core-loop`, `slice` or `full`. A **proxy** item has a metric, threshold and method a bot run or replay can measure. A **human** item needs a person.
- **Richness targets**: `richness.json` targets `{id, aspect, scope, statement, metric, threshold, how}` with `scope` `slice` or `full`; the full game needs at least one per aspect: **depth** (systems that change each other), **breadth** (distinct content), **variety** (playthroughs that differ).
- **Scope tiers**: `must`, `nice`, `cut`. Nice features are built after their milestone's must features, while the budget has room.
- **Tuning knobs**: per-system values and an on/off toggle, loaded from data so they change without code edits.
- **Simulation core / presentation shell**: game rules live in a deterministic core (fixed tick or turn, seeded RNG, input as data, serializable state) that runs headless. Rendering, audio and input devices live in a thin shell around it. Tests, bots and replays drive the core.
- **Tick**: one step of the simulation core: a fixed-timestep frame in a real-time game, one turn or action in a turn-based one.
- **Definition of done**: `features.json`. With the final verdict, it is how the goal above is checked.
- **Evidence**: the command run, its result (numbers, hash, artifact path) and the commit.
- **Task**: what the current phase still owes (`state.json` `task`, shown by status). Phase skills clear it with `gamestate.py complete` as their last step.
- **Gate**: a phase's completion criterion, checked by `gamestate.py gate`.
- **Verdict**: the scored judgement of a green build against the fun checklist and richness targets: `ship`, `adjust`, `restart` or `kill`. Scopes: `core-loop` (on bots, before the slice is polished), `slice` (the gate into production; waits for a person's playtest), `full` (before polish), `final` (after polish; shipping it completes the run). It runs again when playtest answers arrive. Each score is `pass` or `fail` with an evidence file, `not-assessed` with the reason it couldn't be measured, or `pending-human`; a ship needs every item to pass.
- **Kept values**: `keep.json` entries `{id, what, source, pins: [{file, key, value}], adr}` for what a playtest or a person said to keep. `gamestate.py check` holds each pinned tuning value (a dotted key in JSON, or a `key = value` / `key: value` line); changing or dropping one needs a new ADR in the entry's `adr`.
- **Own calls**: player-visible choices an agent made that no page specified, logged in `own-calls.md` and shown in the GDD for people to keep or change.
- **Durable assets**: seed.md, the wiki, `vision.json`, the fun checklist, richness targets, kept values, ADRs, CONTEXT.md and final art. They survive a restart. Code is disposable.
- **Human queue**: `state.json` `human_queue` entries `{id, what, why, how, unblocks: [feature ids]}` for work only a person can do, each mirrored as a `ready-for-human` ticket. The run moves past queued features and stops at the end for the queue; open playtest entries don't stop it. A person finishing an entry deletes it, and for a `human`-verified feature sets `passes: true` with evidence starting `human:`; the next `/game-next` session goes back to anything still failing. A playtest entry also has `kind: "playtest"`, `scope` and `answers` (a file path): the person writes their answers to that file and leaves the entry, and the next session reopens the verdict with them.

### features.json item

```json
{
  "id": "F012", "title": "Save and load a run",
  "pillar": "P2", "tier": "must", "milestone": "systems",
  "acceptance": ["Quitting mid-run and relaunching restores the same state hash"],
  "verify": {"kind": "replay", "how": "replay tests/replays/save-mid-run.json; state hash matches"},
  "pages": ["saves"], "measures": [], "tickets": ["#41"],
  "passes": false, "evidence": "", "blocked": "", "cut_reason": ""
}
```

`milestone` is one of `core-loop`, `slice` (the vertical slice), `systems`, `content`, `verdict-build` (production), `polish`. `verify.kind` is one of `test`, `sim`, `replay`, `bot`, `capture`, `check` (any scripted or recorded inspection) or `human`. `pages` lists the ids of the wiki pages the feature implements. `measures` lists the fun proxy and richness target ids whose metric this feature produces. Ids are never reused, including ids in `docs/game/archive/`. Build attempts are counted by `gamestate.py` in `state.json` `attempts`.

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
