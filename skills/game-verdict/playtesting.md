# Playtesting

How an agent measures a game, and how it hands the rest to people.

## Contents

- Bot policies
- Runs and sample sizes
- Metrics format
- Fuzzing
- Captures and visual review
- Human playtest kit

## Bot policies

A bot reads core state and returns input actions each tick, through the same action interface the presentation shell uses. Build the cheapest policy that answers the question:

| Policy | How | Answers |
| --- | --- | --- |
| random | uniform over legal actions | crashes, softlocks, degenerate wins ("does mashing win?") |
| scripted | a fixed action sequence or recorded replay | onboarding time, regression checks |
| greedy / heuristic | pick the action with the best immediate evaluation | baseline competence, balance between options |
| search | lookahead (minimax, MCTS, beam) on a copied core state | skill ceiling, dominant strategies, meaningful-choice counts |
| fixed-skill | heuristic with noise or limited lookahead | difficulty curve, progress pacing |
| model-driven | a language model choosing actions from a text rendering of state | turn-based or slow games where heuristics are hard to write; expensive, so few runs |

Comparing two policies (stronger vs weaker, option A vs option B) is how skill, balance and luck items get measured. Bots ship as code in the repo, exposed through the adapter's `bot` command.

## Runs and sample sizes

- Seed every run; record seed, knob-file hash and build commit with the metrics.
- At least 30 runs per measured configuration; 100+ when comparing win rates that should differ by under 10 points.
- Report median, p10 and p90, plus the pass/fail against the threshold. A rate near its threshold (within its sampling error) counts as inconclusive: run more.

## Metrics format

The core's metrics hook emits one JSON object per run:

```json
{"seed": 17, "build": "abc1234", "knobs": "sha1:…", "policy": "greedy-vs-search",
 "ticks": 5400, "winner": 1, "lead_changes": 3, "final_gap": 1, "events": {"core_verb": 212}}
```

The `bot` command writes one line per run plus a summary; verdict evidence is the raw file plus the summary.

## Fuzzing

Random-policy runs with random knob perturbation within each knob's declared range: 30 minutes of game time for a real-time game, or 2,000 turns for a turn-based one, or more. Fail on: crash, exception in logs, NaN or out-of-range state, or a softlock (state hash unchanged for 10 seconds of game time, or 20 consecutive turns, while legal inputs arrive and the game is not paused or over). Save the replay of every failure.

## Captures and visual review

Capture through the adapter's `capture` command at fixed seeds and ticks so captures are comparable across builds. Review each against the art pages in the wiki: palette, silhouettes readable at the smallest target screen size, UI text legible, the player's focus obvious. A vision-capable model can do this review; record it as notes, never as a score for a human item.

## Human playtest kit

Write into the verdict's evidence folder:

1. **How to play**: the adapter's `run` command or a packaged build, controls, and what a session is.
2. **Script**: play N sessions without help; think aloud or note moments of confusion, tension, boredom and delight.
3. **Score sheet** (`score-sheet.md`): each human fun-checklist item as a yes/no question with a "what happened" field, plus: "Would you play another round right now? Why?" and "What would you change first?"
4. **Return path**: "Copy the score sheet to `answers.md` in this folder, fill it in, commit, and run `/game-next`." The file's existence is the signal: the run reopens the verdict with it.
