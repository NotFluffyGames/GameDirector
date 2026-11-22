---
name: game-build
description: Build and prove one feature of the game's definition of done in one fresh session - claim its ticket, build it test-first, run its verify method, review, commit and record the evidence. Phase 4 of the game-* workflow; also builds nice and polish features and fixes regressions.
disable-model-invocation: true
---

# Game Build

One session, one feature. Read `docs/agents/game.md` first and follow its session rules.

## 1. Pick

- The feature the task names (`game-build F012 …`). If its ticket is blocked in the tracker, take the first alternative the task lists whose ticket isn't.
- A `regression: …` task: find the feature whose verify now fails, set its `passes` to false, and build it back to green.

Claim the ticket as `docs/agents/issue-tracker.md` describes. Read the ticket, the feature, `CONTEXT.md`, the ADRs the ticket touches, and the engine-notes.md entries for the commands you will run. A feature that was tried before has notes on its ticket: start from them.

**Done when** you can state the acceptance criteria and the exact verify command you will run at the end.

## 2. Build

- Game rules go in the **simulation core**, built test-first with the `tdd` skill. Rendering, audio and input devices stay in the thin **presentation shell**.
- Every value a designer would tweak becomes a **tuning knob** in the system's knob file; every system keeps its on/off toggle working.
- When it's unclear whether a mechanic or UI works, answer it with the `prototype` skill first, then build the real thing.
- Assets: placeholders before the polish milestone; final assets in polish, from the source the asset ADR names, in the style `design.md` sets. Record every added asset's source and license in `docs/game/assets.md`.
- Run single tests while working and the adapter's full `test` command at the end.

**Done when** the acceptance criteria hold in tests and the full test suite is green.

## 3. Verify

Run the feature's verify method through the adapter commands:

- `test`, `sim`, `replay`, `bot`, `check`: run it; the output must meet the acceptance criteria.
- `capture`: render, open the image and check it shows what the acceptance criteria describe and follows `design.md`'s readability rules. Save it under `docs/game/playtests/evidence/<feature-id>/`.
- `human`: add a human queue entry that `unblocks` the feature, saying exactly what to check and how; label the ticket `ready-for-human`; go to step 4 without setting `passes`.

Red: run the `diagnosing-bugs` loop, fix, verify again.

**Done when** the verify command is green in this session, against committed code.

## 4. Review and record

1. Review the diff since the base commit with the `code-review` skill. Fix what it finds; verify again if code changed.
2. In `features.json`, set `passes: true` and `evidence`: the command, the result (numbers, hash, artifact path) and the commit.
3. Close the ticket, commit, append the progress entry.

**Done when** `gamestate.py check --since <base>` passes on the final commit.

## When the feature doesn't fit the session

- **Too big**: split the remainder into new tickets with blocking edges (the feature stays failing until they land), commit the green part, stop.
- **Still red at the end**: write on the ticket what you tried and what you learned, commit only green work, stop. The tool counts the attempt; after `max_attempts` the feature goes to game-plan's unblock mode.
- **Needs a person** (credentials, hardware, a judgement call): human queue entry that `unblocks` it, ticket `ready-for-human`, stop.
