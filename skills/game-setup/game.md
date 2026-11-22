# Game workflow

Config for the game-* skills. Every game-* session reads this file first. Edit it freely; it is the project's, not the skills'.

## Autonomy

Mode: {{autonomous | interactive}}

- **autonomous**: ask nothing. At each judgement call, take the recommended answer and record it in an ADR as an assumption a human can overturn. Work only a person can do goes to the **human queue**.
- **interactive**: ask the user at three points: the design tree (game-ideate), the ticket breakdown (game-plan) and the verdict outcome (game-verdict). Everything else runs as in autonomous mode.

## Session rules

Every game-* session is a **fresh session** doing **one task**:

1. Start with `python3 docs/game/gamestate.py status`. Read only the files your task names; reach for more only when the work demands it.
2. Hand reading-heavy exploration to a subagent or the `research` skill, which returns a summary or writes notes to a file.
3. When the task outgrows the session (a second unplanned subsystem appears, or you are past roughly half your context), split: write the remainder as new tickets or features, commit what is green, stop.
4. Leave the repo green: commit only work whose tests pass.
5. End with: `gamestate.py check` passing, a commit, a progress entry of at most 10 lines appended to `docs/game/progress.md`, and a reply of at most 150 words: what changed, the **evidence**, the gate status.

The **definition of done** only grows. Cut an item (`tier: "cut"` plus `cut_reason`) rather than deleting it. Set `passes: true` only with evidence from a run in this session. Outside the plan phase, `acceptance` and `verify` are fixed; `gamestate.py check` enforces both.

## Files

| Path | What | Written by |
| --- | --- | --- |
| `docs/game/design.md` | pitch, pillars, core loop, tone/art/world, pillar test | game-ideate |
| `docs/game/fun-checklist.json` | fun checklist | game-ideate |
| `docs/game/features.json` | definition of done | game-plan, game-release add items; game-build sets `passes` |
| `docs/game/state.json` | phase, milestone, counters, limits, verdicts, human queue | `gamestate.py advance`; skills append verdicts and queue entries |
| `docs/game/progress.md` | append-only session log | every session |
| `docs/game/assets.md` | every asset's source and license | whoever adds an asset |
| `docs/game/engine-notes.md` | engine CLI, headless, test and export facts | game-plan |
| `docs/game/playtests/` | verdict evidence, capture output, human playtest kits | game-verdict, game-build |
| `docs/game/gamestate.py` | reads, checks and advances state | game-setup installs it |

Decisions are ADRs and game terms live in `CONTEXT.md`, both as `docs/agents/domain.md` describes. Tickets live in the tracker `docs/agents/issue-tracker.md` describes, with the labels in `docs/agents/triage-labels.md`.

## Vocabulary

- **Pillars**: 3–4 statements of the feelings or features the game delivers, written `- **P1**: ...` in design.md. Every feature serves one; a feature with no pillar is not in the game.
- **Core loop**: the action the player repeats minute to minute, in one sentence.
- **Fun checklist**: 3–6 statements that are true when the game is fun, each observable in one play session. A **proxy** item has a metric, threshold and method a bot run or replay can measure. A **human** item needs a person.
- **Scope tiers**: `must`, `nice`, `cut`.
- **Tuning knobs**: per-system values and an on/off toggle, loaded from data so they change without code edits.
- **Simulation core / presentation shell**: game rules live in a deterministic core (fixed tick, seeded RNG, input as data, serializable state) that runs headless. Rendering, audio and input devices live in a thin shell around it. Tests, bots and replays drive the core.
- **Definition of done**: `features.json`. The game is complete when every `must` item passes or waits in the human queue.
- **Evidence**: the command run, its result (numbers, hash, artifact path) and the commit.
- **Gate**: a phase's completion criterion, checked by `gamestate.py gate`.
- **Verdict**: the scored judgement of a build against the fun checklist: `ship`, `adjust` or `restart`. Runs once after the core-loop milestone (scope `core-loop`) and once before polish (scope `full`).
- **Durable assets**: design.md, the fun checklist, ADRs, CONTEXT.md and final art. They survive a restart. Code is disposable.
- **Human queue**: `state.json` `human_queue` entries `{id, what, why, unblocks: [feature ids], how}` for work only a person can do. Mirror each as a `ready-for-human` ticket. The run moves past queued features and stops at the end for the queue. A person finishing an entry deletes it, and for a `human`-verified feature sets `passes: true` with evidence starting `human:`; the next `/game-director` run resumes anything still failing.

### features.json item

```json
{
  "id": "F012", "title": "Save and load a run",
  "pillar": "P2", "tier": "must", "milestone": "systems",
  "acceptance": ["Quitting mid-run and relaunching restores the same state hash"],
  "verify": {"kind": "replay", "how": "replay tests/replays/save-mid-run.json; state hash matches"},
  "measures": [], "tickets": ["#41"],
  "passes": false, "evidence": "", "attempts": 0, "blocked": "", "cut_reason": ""
}
```

`milestone` is one of `core-loop`, `systems`, `content`, `verdict-build`, `polish`, `release`. `verify.kind` is one of `test`, `sim`, `replay`, `bot`, `capture`, `check` (any scripted or recorded inspection) or `human`. `measures` lists the fun-checklist proxy ids whose metric this feature produces.

## Limits

In `docs/game/state.json` `limits`: `budget_sessions` (dispatched sessions before the run stops), `max_adjusts` (default 2), `max_restarts` (default 1), `max_attempts` (failed build sessions per feature before it is marked blocked, default 3). Passing a limit stops the run for a human.

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
| `grilling` | walking the design tree | ask, or answer, one question at a time until every branch is resolved |
| `domain-modeling` | CONTEXT.md terms and ADRs | ADR = context, decision, consequences, in the ADR folder, numbered |
| `codebase-design` | the simulation core / presentation shell seam, deep modules | small interfaces over large implementations; test at the seam |
| `prototype` | a throwaway check of a mechanic or UI before committing to it | a scratch file or branch, deleted once the question is answered |
| `tdd` | building game rules test-first in the simulation core | red, green, refactor, one behaviour at a time |
| `code-review` | reviewing each session's diff | review the diff against the ticket and the repo's standards |
| `diagnosing-bugs` | a red verify or a regression | reproduce, minimise, hypothesise, fix, add the regression test |
| `research` | engine and platform facts from primary docs | read official docs; save the facts with links to a notes file |
| `wizard` | scripted walkthroughs for human-only steps | a numbered checklist with exact URLs, clicks and where each value goes |
