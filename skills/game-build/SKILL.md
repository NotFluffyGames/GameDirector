---
name: game-build
description: Build and prove one feature of the game's definition of done in one fresh session - claim its ticket, build it test-first, run its verify method, have its roles review it, commit and record the evidence, and queue the person's calibration kit when the visual target passes; also applies a person's A/B picks. Runs after plan in the game-* workflow; also builds nice and polish features and fixes regressions.
disable-model-invocation: true
---

# Game Build

One session, one feature. Read `docs/agents/game.md` first and follow its session rules.

## 1. Pick

- The feature the task names (`game-build F012 …`). If its ticket is blocked in the tracker, take the first alternative the task lists whose ticket isn't.

Claim the ticket as `docs/agents/issue-tracker.md` describes. Read the ticket, the feature, the wiki `pages` it implements (ids in `docs/game/wiki.json`, read through the docs place), `CONTEXT.md`, the ADRs those pages link, and the engine-notes.md entries for the commands you will run. A feature that was tried before has notes on its ticket: start from them. A polish feature verified by A/B picks takes two sessions, the second a task ending `picks <answers>`: [kits.md](kits.md) ("Compare kit") says what each does.

**Done when** you can state the acceptance criteria and the exact verify command you will run at the end.

## 2. Build

- Game rules go in the **simulation core**, built test-first with the `tdd` skill. Rendering, audio and input devices stay in the thin **presentation shell**.
- Every value a designer would tweak becomes a **tuning knob** in the system's knob file; every system keeps its on/off toggle working. Values pinned in `docs/game/keep.json` stay as they are.
- The pages are the spec. When building shows they are wrong or incomplete in a small, obvious way (a missing edge case, a number that needs tuning), draft the fix in `docs/game/drafts/<page-id>.md` with a `Last changed` line (session rule 6; written at step 5.5), and log it as an **own call** (step 5). When it raises a real design question, open a topic with this feature in `unblocks`, commit what is green with your drafts, write them as step 5.5 does, and stop: the question is brainstormed with a person first.
- In interactive mode, when it's unclear whether a mechanic or UI works for a person, the `prototype` skill can make a quick demo for the user to judge.
- Assets at the quality bar the feature's acceptance carries: placeholders at a `placeholder` bar, the visual target's area at the slice's art bar, final assets in polish; from the source the asset ADR names, in the style the art bible sets. Record every added asset's source and license in `docs/game/assets.md`.
- The named states and strips this feature first shows (the capture protocol in `docs/game/engine-notes.md`) are part of its work: their replay prefixes and scripted inputs land with it, so `capture` renders them from this build.
- Run single tests while working and the adapter's full `test` command at the end. When the full suite shows an already-passing feature now failing, set its `passes` to false and say so in your report: the state tool sends it back to build.

**Done when** the acceptance criteria hold in tests and the full test suite is green.

## 3. Verify

Run the feature's verify method through the adapter commands:

- `test`, `sim`, `replay`, `bot`, `check`: run it; the output must meet the acceptance criteria.
- `capture`: render, open the image and check it shows what the acceptance criteria describe; judging how it looks is the roles' work in step 4. Save it under `docs/game/playtests/evidence/<feature-id>/`.
- `human`: add a human queue entry that `unblocks` the feature, saying exactly what to check and how; label the ticket `ready-for-human`; go to step 4 without setting `passes`. A polish feature verified by A/B picks makes its compare kit instead, in its first session; its picks session follows [kits.md](kits.md).

Red: run the `diagnosing-bugs` loop, fix, verify again.

**Done when** the verify command is green in this session, against committed code.

## 4. Review

1. Review the diff since the base commit with the `code-review` skill, against the ticket and the pages it implements. Fix what it finds; verify again if code changed.
2. **The roles' review**, for a feature with `roles` (a rules-only feature, `roles: []`, skips it, and so does the first session of a feature verified by A/B picks: its roles review the picked build). With the verify and the full suite green, run `game-review feature <id>`, or `game-review polish <id>` for a polish feature: read the game-review skill's SKILL.md (`../game-review/SKILL.md` beside this skill) and follow it with that task. It commits your green work, captures and measures this build, has the roles review it, fixes the blocking notes and `fixed` decisions within its two rounds (re-running the feature's verify and the full suite after each fix), records the reviews in the feature's `reviews`, and commits its own work. It reports per role the result and each note's decision, the blocking notes still open, and the last fix commit.
3. A blocking note still open after game-review's rounds keeps the feature failing (game-review's step 7): go to "Still red at the end" below.

**Done when** the code review's findings are fixed with the verify green again, and, for a feature its roles review this session, game-review has reported no blocking note open and the feature's `reviews` holds a record for every role in its `roles`.

## 5. Record

1. In `features.json`, set `passes: true` and `evidence`: the command, the result (numbers, hash, artifact path) and the commit. When game-review fixed anything, the commit is its last fix commit and the result is that commit's verify run. A `human` verify leaves `passes` to the person, or to the A/B picks session.
2. **Own calls**: for every choice a player could notice that no page specified (a timing, a number, a behaviour, a visual), append a row to `docs/game/own-calls.md` (date, feature, the call, the page now stating it). People see them in the GDD and keep or change each.
3. **Calibration**: when this feature is the kit's trigger (the visual target; with `art` off, the feel target; with `feel` off too, the first slice feature with `roles`), queue the person's calibration kit as [kits.md](kits.md) ("Calibration kit") says, in this step's commit.
4. Close the ticket, commit with your drafts, append the progress entry.
5. Write each of your drafts to its page in the docs place, last; in the pages commit, record each page's new `version` and `updated` in `docs/game/wiki.json` and delete the drafts.

**Done when** `gamestate.py check --since <base>` passes on the final commit, every page fix is written with its `wiki.json` entry committed and its draft gone, and a calibration trigger that passed has its `calibrate` entry committed, unless labels for the current art direction already exist.

## When the feature doesn't fit the session

Each of these commits the green work with the drafts that describe it, and writes those as step 5.5 does before it stops:

- **Too big**: split the remainder into new tickets with blocking edges (the feature stays failing until they land), commit the green part, stop.
- **Still red at the end**: write on the ticket what you tried and what you learned (for an open blocking note, its role, rule and evidence), commit only green work, stop. The tool counts the attempt; after `max_attempts` the feature goes to game-plan's unblock mode.
- **Needs a person** (credentials, hardware, a judgement call): human queue entry that `unblocks` it, ticket `ready-for-human`, stop.
