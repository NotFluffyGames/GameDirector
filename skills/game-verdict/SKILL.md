---
name: game-verdict
description: Judge a game build against its fun checklist with bot runs, replays, captures and a human playtest kit; isolate failures with tuning knobs; record a ship, adjust or restart verdict as an ADR. Phase 4 of the game-* workflow, run after the core loop (scope core-loop) and before polish (scope full).
disable-model-invocation: true
---

# Game Verdict

Judges whether the game is fun enough to build on, before polish hides a weak core loop. Read `docs/agents/game.md` first and follow its session rules. Scope comes from the task (`core-loop` scores only core-loop items; `full` scores every item). Evidence goes to `docs/game/playtests/<date>-<scope>/`.

## 1. Fix the build

Run the adapter's `build` and note the commit. Every measurement in this verdict comes from this one build. Then run a 30-minute random-input fuzz (see [playtesting.md](playtesting.md)): a crash or softlock fails the verdict build outright. Dispatch-worthy bugs go back as `regression:` notes in your reply.

**Done when** the build is green and the fuzz run is clean.

## 2. Score the proxies

For each proxy item in scope, run its `how` with enough seeded runs for the threshold to mean something (at least 30, unless the item says otherwise) and compare the result with its threshold. [playtesting.md](playtesting.md) covers bot policies, sample sizes and the metrics format.

**Done when** every proxy item in scope has a value, pass or fail, and a path to its raw metrics.

## 3. Look at it

Capture the key moments: start, the core verb mid-loop, a win, a loss, every main UI screen. Judge them against `design.md`'s tone, art and readability rules. Record findings as notes; they inform the decision but score nothing.

## 4. Human items

- **interactive**: give the user the build and the playtest script from [playtesting.md](playtesting.md); score human items from their answers.
- **autonomous**: write the playtest kit into the evidence folder, add one human queue entry `playtest <scope>` pointing to it, and score human items `pending-human`.

## 5. Isolate failures

For each failing item, find its cause before deciding anything: toggle systems off and move tuning knobs one at a time, re-measuring after each change, until you can name the system responsible, or show the failure persists with every optional system off (the core loop itself). When a knob change alone makes the item pass, record the values: that is a cheap adjust.

**Done when** each failing item names its cause and, where found, the knob values that fix it.

## 6. Decide

- **ship**: every proxy in scope passes and no human item failed.
- **adjust**: failures trace to at most two systems or pillars, and the isolation shows what to change.
- **restart**: the core loop itself fails its items, or adjusts are used up (`state.json` counters against limits) with failures remaining.

In interactive mode, present the scores, the isolation findings and your recommendation, and let the user decide.

Write the verdict ADR: scope, build commit, a score table (item, value, threshold, result, evidence path), isolation findings and the outcome. For adjust: exactly what to change, including knob values. For restart: lessons (what failed, why, what changes next time, which durable assets still hold).

Append to `state.json` `verdicts`:

```json
{"scope": "core-loop", "outcome": "adjust", "adr": "docs/adr/0009-core-loop-verdict.md",
 "commit": "abc1234", "scores": {"FC1": {"result": "fail", "evidence": "docs/game/playtests/..."}}}
```

**Done when** `gamestate.py gate` passes. Close: check, commit, progress entry.
