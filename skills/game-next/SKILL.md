---
name: game-next
description: Do the next step of making a game with the game-* skills, in this session - the state tool picks the step (setup, the landscape scan, ideation, the research of references, a brainstorm topic, a feature, a verdict, ...), this session does it, checks it and tells the user what comes next. Run it in a fresh session each time.
disable-model-invocation: true
argument-hint: "[game idea] [--interactive] [--unattended]"
---

# Game Next

The game is made over many sessions, **one step per session**. This skill finds the step, does it here, checks it, and ends by telling the user what the next session will do. State lives on disk (`docs/agents/game.md`, `docs/game/`), so every session starts fresh and nothing depends on an earlier conversation.

`--unattended` means nobody is in this session (an external loop started it): steps that need a person are skipped, and questions are answered with recommended answers recorded as assumptions. Every **stop** this session reaches, whether from `next:` or from the steps below, is printed in the report on a line of its own that starts with `stop:`; the unattended loop ends on that line.

## 1. Orient

1. No `docs/game/state.json` (a new game, or a setup that ended before writing it): this session's step is **setup**. Read the `game-setup` skill's SKILL.md (beside this skill) and follow it in project mode, passing the user's whole prompt as the idea; then go to step 4. Unattended, it is the stop `stop: setup needs a person: start a session with someone present and run /game-next <idea>`.
2. Compare versions before anything runs the game's tool: the game's is `version` in `docs/game/state.json` (missing counts as 1), the plugin's is `CURRENT_VERSION` in the game-setup skill's `scripts/gamestate.py` beside this skill.
   - Older, and `phase` is `setup`: this session's step is `with-user: game-setup upgrade`; go to step 2 with it. Unattended, it is the stop `stop: this game is at version <n> and the plugin at <m>: run /game-next with a person to upgrade it`.
   - Older, past setup: the stop `stop: this game is at version <n> and the plugin at <m>; upgrading a game mid-run isn't supported: finish it with the plugin release it was made with`.
   - Newer: the stop `stop: this game is at version <n>, newer than the plugin (<m>): update the plugin`.
   - A version that isn't a whole number: the stop `stop: docs/game/state.json version <value> is not a whole number`.
3. Equal: run `python3 docs/game/gamestate.py status` (`status --no-user` when unattended). While its `next:` line is `advance`, run `gamestate.py advance`.

**Done when** this session has a step or a stop.

## 2. Do the step

The `next:` line names it:

| `next:` | Do |
| --- | --- |
| `with-user: game-<phase> …` | A conversation with the user. Unattended, this never comes up. |
| `game-<phase> …` | Work the agent does; the user may watch. |
| `fix: …` | Fix the listed `gamestate.py check` violations without weakening the definition of done. |
| `stop: …` | Nothing to do: go to step 4 and report the stop. |

Before a `with-user:` or `game-<phase>` step other than `game-setup` (setup and `game-setup upgrade` create the home page, so they run without it; `fix:` and `stop:` need none), read the wiki's home page (the `index` entry in `docs/game/wiki.json`) through the docs place, as `docs/agents/docs.md` describes. If it can't be read, the stop is `stop: <tracker> docs unreachable` (naming the tracker from `docs/agents/issue-tracker.md`): go to step 4 without starting the step.

Run `gamestate.py tick "<the next: line>"` (skip it for an upgrade step 1 found: the game's tool is still the old copy), note the base commit (`git rev-parse HEAD`), then read the SKILL.md of the skill the `next:` line names (`../game-<name>/SKILL.md` beside this skill, or the installed `game-<name>` skill; `game-research` runs both the `scan` and the `research` phase) and follow it, with the rest of the `next:` line as its task.

**Done when** the home page was read (for the steps that read it) and the phase skill's own steps are done, or it stopped at a session boundary it names, or the docs stop was reached.

## 3. Check

Run `gamestate.py check --since <base>`. Fix what it reports in this session. If a violation can't be fixed without weakening the definition of done, `git reset --hard <base>` (the base holds the tick), note why in `docs/game/progress.md`, and say so in the report.

**Done when** check passes.

## 4. Report and stop

While `next:` is `advance`, run `gamestate.py advance`. Then tell the user, briefly:

- what this session did, with its evidence;
- where the game stands: stage (slice or production) and phase, open topics, definition-of-done counts, the last verdict;
- the next step from `next:`, and whether it needs them (`with-user:`) or could run unattended ([unattended.md](unattended.md));
- for a stop: the stop line itself, on a line of its own starting with `stop:` (for example `stop: ClickUp docs unreachable`), then what it needs from them (answering or skipping the research homework, labelling the calibration kit, playing the slice and writing its answers, making the A/B picks, other playtest answers, the human queue, a raised limit, a person for a conversation step, a decision after a kill, an upgrade).

End with: **start a new session and run `/game-next`**. Do not start the next step here: each step gets a fresh session.

**Done when** the user has the report and the next step, and any stop is on its own `stop:` line.
