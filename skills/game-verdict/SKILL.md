---
name: game-verdict
description: Judge a game build against its fun checklist with bot runs, replays, captures and a human playtest kit; isolate failures with tuning knobs; record a ship, adjust or restart verdict as an ADR. Run after the core loop (scope core-loop), before polish (full), after polish as the last gate (final), and when playtest answers arrive.
disable-model-invocation: true
---

# Game Verdict

Judges whether the game is fun and rich enough to build on, before polish hides a weak core loop, and whether the finished game still is. Read `docs/agents/game.md` first and follow its session rules.

The task gives the scope:

- `game-verdict core-loop`: the core-loop fun items.
- `game-verdict full`: every fun item and every richness target, on the unpolished game.
- `game-verdict final`: the same on the polished game, plus the playable-build checks in step 1. Shipping it ends the run.
- `game-verdict <scope> answers <file>`: re-judge with a person's playtest answers (see the end).

The status tool only schedules a verdict once the scope's must features pass.

Work in `docs/game/playtests/<date>-<scope>/`. Keep `notes.md` there with one line per finished step (result and file paths), committed as you go: a verdict often spans sessions, and the next one resumes at the first step `notes.md` doesn't record.

## 1. Fix the build

Run the adapter's `build` and note the commit; every measurement in this verdict comes from this one build. Then fuzz it as [playtesting.md](playtesting.md) describes. For `final`, also: the full `test` suite green, and every packaged build launching and playing from title screen to the end of a session in a smoke run.

A crash, softlock or failing check: add a `must` feature "Fix: <symptom>" to the scope's latest milestone (`core-loop`, `verdict-build` for full, `polish` for final), with the failure's replay as its `replay` verify, and a ticket; commit and stop without recording a verdict. The run builds the fix and dispatches the verdict again.

**Done when** the build is green and every check in this step is clean.

## 2. Score the proxies and richness targets

For each proxy item in scope, and for `full` and `final` each richness target, run its `how` with enough seeded runs for the threshold to mean something (at least 30 unless the item says otherwise) and compare the result with its threshold. [playtesting.md](playtesting.md) covers bot policies, sample sizes and the metrics format.

**Done when** every proxy item and richness target in scope has a value, pass or fail, and a path to its raw metrics.

## 3. Look at it, and at the wiki

Capture the key moments: start, the core verb mid-loop, a win, a loss, every main UI screen. Judge them against the art pages' tone and readability rules. Record findings as notes; they inform the decision but score nothing.

Then check the wiki against what was built, for the features in scope: where the game now differs from its pages in a small, settled way, fix the page with a `Last changed` line; where the difference is a design question, open a topic.

## 4. Human items

Write the playtest kit ([playtesting.md](playtesting.md)) into the evidence folder and add a human queue entry: `{"id": "...", "what": "playtest <scope>", "kind": "playtest", "scope": "<scope>", "answers": "<evidence folder>/answers.md", "how": "<path to the kit>"}`. Score human items `pending-human`. Remove unanswered playtest entries of this scope or a narrower one (core-loop < full < final): this kit supersedes them. In interactive mode, also tell the user the kit is ready.

## 5. Isolate failures

For each failing item, find its cause before deciding anything: toggle systems off and move tuning knobs one at a time, re-measuring after each change, until you can name the system responsible or show the failure persists with every optional system off (the core loop itself). At most 8 re-measurements per item; past that, record the item's cause as unknown. When a knob change alone makes the item pass, record the values: that is a cheap adjust.

**Done when** each failing item names its cause (or "unknown after 8 probes") and, where found, the knob values that fix it.

## 6. Decide

- **ship**: every proxy and richness target in scope passes and no human item failed.
- **adjust**: failures trace to at most two systems or pillars, and the isolation shows what to change. A richness target short of its threshold is an adjust: more content, or a system connected to the others. At `final`, an item polish broke is an adjust naming the polish change.
- **restart**: the core loop itself fails its items, or adjusts are used up (`state.json` counters against limits) with failures remaining.

In interactive mode the user decides, given the scores, the isolation findings and your recommendation.

Write the verdict ADR where `docs/agents/domain.md` puts ADRs: scope, build commit, a score table (item or target, value, threshold, result, evidence path), isolation findings and the outcome. For adjust: exactly what to change, including knob values. For restart: lessons (what failed, why, what changes next time, which durable assets still hold).

Append to `state.json` `verdicts`:

```json
{"scope": "core-loop", "outcome": "adjust", "adr": "<path to the ADR>",
 "commit": "abc1234", "scores": {"FC1": {"result": "fail", "evidence": "docs/game/playtests/..."}}}
```

**Done when** every item and target in scope is scored. Close: `gamestate.py check --since <base>`, commit, progress entry, `gamestate.py complete`.

## Answers mode

`game-verdict <scope> answers <file>`: a person played the kit. Read their answers and score the human items from them. Take the proxy scores from the latest verdict of the same scope when the build commit is unchanged; otherwise redo steps 1–2. Then steps 5–6, writing a follow-up verdict ADR that links the earlier one.
