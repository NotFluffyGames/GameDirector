---
name: game-verdict
description: Judge a game build against its fun checklist with bot runs, replays, captures and a human playtest kit; isolate failures with tuning knobs; record a ship, adjust or restart verdict as an ADR. Phase 4 of the game-* workflow, run after the core loop (scope core-loop), before polish (scope full), and when playtest answers arrive.
disable-model-invocation: true
---

# Game Verdict

Judges whether the game is fun enough to build on, before polish hides a weak core loop. Read `docs/agents/game.md` first and follow its session rules.

The task gives the scope: `game-verdict core-loop` scores only core-loop items, `game-verdict full` scores every item, and `game-verdict <scope> answers <file>` re-judges with a person's playtest answers (see the end). The status tool only dispatches a verdict once the scope's must features pass.

Work in `docs/game/playtests/<date>-<scope>/`. Keep `notes.md` there with one line per finished step (result and file paths), committed as you go: a verdict often spans sessions, and the next one resumes at the first step `notes.md` doesn't record.

## 1. Fix the build

Run the adapter's `build` and note the commit; every measurement in this verdict comes from this one build. Then fuzz it as [playtesting.md](playtesting.md) describes.

A crash or softlock: add a `must` feature "Fix: <symptom>" to the scope's latest milestone (`core-loop`, or `verdict-build` for full), with the failure's replay as its `replay` verify, and a ticket; commit and stop without recording a verdict. The run builds the fix and dispatches the verdict again.

**Done when** the build is green and the fuzz run is clean.

## 2. Score the proxies

For each proxy item in scope, run its `how` with enough seeded runs for the threshold to mean something (at least 30 unless the item says otherwise) and compare the result with its threshold. [playtesting.md](playtesting.md) covers bot policies, sample sizes and the metrics format.

**Done when** every proxy item in scope has a value, pass or fail, and a path to its raw metrics.

## 3. Look at it

Capture the key moments: start, the core verb mid-loop, a win, a loss, every main UI screen. Judge them against `design.md`'s tone, art and readability rules. Record findings as notes; they inform the decision but score nothing.

## 4. Human items

Write the playtest kit ([playtesting.md](playtesting.md)) into the evidence folder and add a human queue entry: `{"id": "...", "what": "playtest <scope>", "kind": "playtest", "scope": "<scope>", "answers": "<evidence folder>/answers.md", "how": "<path to the kit>"}`. Score human items `pending-human`. In interactive mode, also tell the user the kit is ready.

## 5. Isolate failures

For each failing item, find its cause before deciding anything: toggle systems off and move tuning knobs one at a time, re-measuring after each change, until you can name the system responsible or show the failure persists with every optional system off (the core loop itself). At most 8 re-measurements per item; past that, record the item's cause as unknown. When a knob change alone makes the item pass, record the values: that is a cheap adjust.

**Done when** each failing item names its cause (or "unknown after 8 probes") and, where found, the knob values that fix it.

## 6. Decide

- **ship**: every proxy in scope passes and no human item failed.
- **adjust**: failures trace to at most two systems or pillars, and the isolation shows what to change.
- **restart**: the core loop itself fails its items, or adjusts are used up (`state.json` counters against limits) with failures remaining.

In interactive mode the user decides, given the scores, the isolation findings and your recommendation (through the questions protocol when you can't reach them).

Write the verdict ADR where `docs/agents/domain.md` puts ADRs: scope, build commit, a score table (item, value, threshold, result, evidence path), isolation findings and the outcome. For adjust: exactly what to change, including knob values. For restart: lessons (what failed, why, what changes next time, which durable assets still hold).

Append to `state.json` `verdicts`:

```json
{"scope": "core-loop", "outcome": "adjust", "adr": "<path to the ADR>",
 "commit": "abc1234", "scores": {"FC1": {"result": "fail", "evidence": "docs/game/playtests/..."}}}
```

**Done when** every item in scope is scored. Close: `gamestate.py check --since <base>`, commit, progress entry, `gamestate.py complete`.

## Answers mode

`game-verdict <scope> answers <file>`: a person played the kit. Read their answers and score the human items from them. Take the proxy scores from the latest verdict of the same scope when the build commit is unchanged; otherwise redo steps 1–2. Then steps 5–6, writing a follow-up verdict ADR that links the earlier one.
