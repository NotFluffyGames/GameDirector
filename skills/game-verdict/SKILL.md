---
name: game-verdict
description: Judge a game build against its fun checklist and richness targets with bot runs, replays, captures and a human playtest; isolate failures with tuning knobs; record a ship, adjust, restart or kill verdict as an ADR. Runs on the core loop, on the vertical slice (the gate into production, which waits for a person's playtest), on the full game, after polish, and when playtest answers arrive.
disable-model-invocation: true
---

# Game Verdict

Judges whether the game is fun and rich enough to build on: the core loop before the slice is polished, the slice before production, the full game before polish, and the finished game. Read `docs/agents/game.md` first and follow its session rules.

The task gives the scope:

| Task | Scores | Notes |
| --- | --- | --- |
| `game-verdict core-loop` | `core-loop` fun items | on bots, before the slice is polished |
| `game-verdict slice` | `core-loop` and `slice` items, `slice` richness targets | the gate into production; waits for a person's playtest, and checks the kill condition |
| `game-verdict full` | every item and target | the unpolished full game |
| `game-verdict final` | every item and target, plus the playable-build checks in step 1 | shipping it ends the run |
| `game-verdict <scope> answers <file>` | the human items, from a person's answers | Answers mode, at the end |

The status tool only schedules a verdict once the scope's must features pass.

Work in `docs/game/playtests/<date>-<scope>/`. Keep `notes.md` there with one line per finished step (result and file paths), committed as you go: a verdict often spans sessions, and the next one resumes at the first step `notes.md` doesn't record.

**Every score is honest.** Each item gets `pass` or `fail` with an evidence file (raw metrics, captures, the answers file), `not-assessed` with the reason it could not be measured (the run crashed, the machine can't render, too few runs to tell), or `pending-human` for a human item nobody has played yet. A check that didn't run is `not-assessed`, never a pass. `gamestate.py` refuses a ship with any `fail` or `not-assessed`, or with an evidence file that doesn't exist.

## 1. Fix the build

Run the adapter's `build` and note the commit; every measurement in this verdict comes from this one build. Then fuzz it as [playtesting.md](playtesting.md) describes. For `final`, also: the full `test` suite green, and every packaged build launching and playing from title screen to the end of a session in a smoke run.

A crash, softlock or failing check: add a `must` feature "Fix: <symptom>" to the scope's latest milestone (`core-loop`, `slice`, `verdict-build` for full, `polish` for final), with the failure's replay as its `replay` verify, and a ticket; commit and stop without recording a verdict. The run builds the fix and schedules the verdict again.

**Done when** the build is green and every check in this step is clean.

## 2. Score the proxies and richness targets

For each proxy item and richness target in scope, run its `how` with enough seeded runs for the threshold to mean something (at least 30 unless the item says otherwise), compare the result with its threshold, and save the raw metrics as its evidence file. [playtesting.md](playtesting.md) covers bot policies, sample sizes and the metrics format.

**Done when** every proxy item and richness target in scope is `pass` or `fail` with an evidence file, or `not-assessed` with its reason.

## 3. Look at it, and at the wiki

Capture the key moments: start, the core verb mid-loop, a win, a loss, every main UI screen. Judge them against the art pages' tone and readability rules, and for the slice against the `slice` page's quality bar. Record findings as notes; they inform the decision but score nothing.

Then check the wiki against what was built, for the features in scope, reading their pages through the docs place: where the game now differs from its pages in a small, settled way, fix the page with a `Last changed` line (drafted now, written in the docs place after step 6's commit); where the difference is a design question, open a topic.

**Done when** the captures are saved and every difference between the game and its pages is a page fix or a topic.

## 4. Human items

Write the playtest kit ([playtesting.md](playtesting.md)) into the evidence folder, following the `slice` page's Playtest section for the slice, and add a human queue entry: `{"id": "...", "what": "playtest <scope>", "kind": "playtest", "scope": "<scope>", "answers": "<evidence folder>/answers.md", "how": "<path to the kit>"}`. Remove unanswered playtest entries of this scope or a narrower one (core-loop < slice < full < final): this kit supersedes them. Tell the user the kit is ready.

- **slice**: stop here and record no verdict yet. The run waits until a person has played the slice and written the answers file; the next session runs Answers mode.
- **other scopes**: score human items `pending-human` and go on.

**Done when** the kit and its queue entry are committed.

## 5. Isolate failures

For each failing item, find its cause before deciding anything: toggle systems off and move tuning knobs one at a time, re-measuring after each change, until you can name the system responsible or show the failure persists with every optional system off (the core loop itself). At most 8 re-measurements per item; past that, record the item's cause as unknown. When a knob change alone makes the item pass, record the values: that is a cheap adjust. Leave every pinned value in `docs/game/keep.json` where it is.

**Done when** each failing item names its cause (or "unknown after 8 probes") and, where found, the knob values that fix it.

## 6. Decide

- **ship**: every proxy and richness target in scope passes and no human item failed. For the slice, every human item has been played and passes.
- **adjust**: failures trace to at most two systems or pillars, and the isolation shows what to change. A richness target short of its threshold is an adjust: more content, or a system connected to the others. At `final`, an item polish broke is an adjust naming the polish change.
- **restart**: the core loop itself fails its items, or adjusts are used up (`state.json` counters against limits) with failures remaining.
- **kill** (slice only): the playtest meets the vision's kill condition. The run stops for the user to decide: keep going anyway, restart from ideation, or stop the game.

In interactive mode the user decides, given the scores, the isolation findings and your recommendation.

Write the verdict ADR where `docs/agents/domain.md` puts ADRs: scope, build commit, a score table (item or target, value, threshold, result, evidence path), isolation findings and the outcome. For the slice: the answer to the `slice` page's test question, and the kill condition checked. For adjust: exactly what to change, including knob values. For restart or kill: lessons (what failed, why, what changes next time, which durable assets still hold).

Append to `state.json` `verdicts`:

```json
{"scope": "slice", "outcome": "ship", "adr": "<path to the ADR>", "commit": "abc1234",
 "scores": {"FC1": {"result": "pass", "evidence": "docs/game/playtests/2026-12-01-slice/fc1-metrics.json"},
            "FC5": {"result": "not-assessed", "evidence": "capture unavailable on this machine"}}}
```

After the commit and the progress entry, write the page fixes from step 3 in the docs place, last, and record each page's new `version` and `updated` in `docs/game/wiki.json` in a second commit.

**Done when** every item and target in scope is scored, the page fixes are written with their `wiki.json` entries committed, and `gamestate.py complete` succeeds after `check --since <base>`.

## Answers mode

`game-verdict <scope> answers <file>`: a person played the kit.

1. Read their answers. Score each human item `pass` or `fail` with the answers file as its evidence.
2. **Keep what they loved.** For each thing the answers say to keep that a tuning value controls, add an entry to `docs/game/keep.json`: what was kept, the answers file as its source, and a pin per knob (`file`, `key`, `value`). From then on `gamestate.py check` holds those values; changing one takes an ADR named in the entry's `adr`.
3. Take the proxy scores from the latest verdict of the same scope when the build commit is unchanged; otherwise redo steps 1–2.
4. Steps 5–6, writing the verdict ADR (a follow-up ADR linking the earlier one, when this reopens a verdict).

**Done when** the verdict is recorded and `gamestate.py complete` succeeds; it also consumes the answered queue entry.
