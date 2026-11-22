---
name: game-next
description: Do the next step of making a game with the game-* skills, in this session - the state tool picks the step (setup, ideation, a brainstorm topic, a feature, a verdict, ...), this session does it, checks it and tells the user what comes next. Run it in a fresh session each time.
disable-model-invocation: true
argument-hint: "[game idea] [--interactive] [--unattended]"
---

# Game Next

The game is made over many sessions, **one step per session**. This skill finds the step, does it here, checks it, and ends by telling the user what the next session will do. State lives on disk (`docs/agents/game.md`, `docs/game/`), so every session starts fresh and nothing depends on an earlier conversation.

`--unattended` means nobody is in this session (an external loop started it): steps that need a person are skipped, and questions are answered with recommended answers recorded as assumptions.

## 1. Orient

- No `docs/agents/game.md`: this session's step is **setup**. Read the `game-setup` skill's SKILL.md (beside this skill) and follow it in project mode, passing the user's whole prompt as the idea; then go to step 4.
- Otherwise run `python3 docs/game/gamestate.py status` (`status --no-user` when unattended). While its `next:` line is `advance`, run `gamestate.py advance`.

**Done when** `next:` is a step or a stop.

## 2. Do the step

The `next:` line names it:

| `next:` | Do |
| --- | --- |
| `with-user: game-<phase> …` | A conversation with the user. Unattended, this never comes up. |
| `game-<phase> …` | Work the agent does; the user may watch. |
| `fix: …` | Fix the listed `gamestate.py check` violations without weakening the definition of done. |
| `stop: …` | Nothing to do: go to step 4 and report the stop. |

Run `gamestate.py tick "<the next: line>"`, note the base commit (`git rev-parse HEAD`), then read the phase skill's SKILL.md (`../game-<phase>/SKILL.md` beside this skill, or the installed `game-<phase>` skill) and follow it, with the rest of the `next:` line as its task.

**Done when** the phase skill's own steps are done, or it stopped at a session boundary it names.

## 3. Check

Run `gamestate.py check --since <base>`. Fix what it reports in this session. If a violation can't be fixed without weakening the definition of done, `git reset --hard <base>` (the base holds the tick), note why in `docs/game/progress.md`, and say so in the report.

**Done when** check passes.

## 4. Report and stop

While `next:` is `advance`, run `gamestate.py advance`. Then tell the user, briefly:

- what this session did, with its evidence;
- where the game stands: phase, open topics, definition-of-done counts, the last verdict;
- the next step from `next:`, and whether it needs them (`with-user:`) or could run unattended ([unattended.md](unattended.md));
- for a stop: what it needs from them (playtest answers, the human queue, a raised limit, a person for a conversation step).

End with: **start a new session and run `/game-next`**. Do not start the next step here: each step gets a fresh session.
