---
name: game-director
description: Take a game from an idea to a release candidate in one run by driving the game-* phase skills, one fresh session per task, until the definition of done passes or only human work remains.
disable-model-invocation: true
argument-hint: "[game idea] [--interactive] [--step]"
---

# Game Director

You are the **director**: a thin loop. Read state, dispatch **one task** to a **fresh session**, check the result, advance, repeat. You never do phase work yourself; that keeps your context small enough to last the whole game.

State lives on disk, not in your conversation: `docs/agents/game.md` (project config), `docs/game/` (design, definition of done, state, progress log) and `docs/game/gamestate.py`, which reads and advances that state. Run the tool instead of reading the JSON yourself.

## Dispatching

A dispatch starts a fresh session (a subagent; see [loop-modes.md](loop-modes.md) for harnesses without them) with only this prompt:

> Read `<skills-dir>/game-<phase>/SKILL.md` and follow it. Task: `<the next: line>`. Project config: `docs/agents/game.md`. Reply in at most 150 words: what changed, the evidence, the gate status.

`<skills-dir>` is the parent of this skill's directory; pass the absolute path. If the phase skills aren't beside this one, name the skill instead (`use the game-build skill`). Pass the user's idea and flags on the first `game-setup` and `game-ideate` dispatches.

## Steps

### 1. Orient

If `docs/agents/game.md` is missing, dispatch `game-setup`. Then run `python3 docs/game/gamestate.py status`.

**Done when** status prints a `next:` line.

### 2. Act on `next:`

Record the base commit (`git rev-parse HEAD`), then:

- `game-…`: dispatch it, then run `gamestate.py tick`.
- `advance`: run `gamestate.py advance`.
- `stop: …`: go to step 4.

**Done when** the dispatch has replied or advance has printed the new phase.

### 3. Check

Treat a reply as a claim; the tools decide.

1. `gamestate.py check --since <base>`. On violations, dispatch one fix session naming them. If check still fails, `git reset --hard <base>`, note why in `docs/game/progress.md`, and continue.
2. When advance printed `milestone complete`, run the adapter's `test` command and a short `bot` run from `docs/agents/game.md`. Red: dispatch `game-build` with the task `regression: <failing output, trimmed>`.
3. Run `gamestate.py status` and return to step 2.

In `--step` mode, stop after one pass through steps 2–3. If your own context passes half despite all this, append a handoff note to progress.md and stop; running `/game-director` again resumes from disk.

**Done when** status prints `next: stop: …`.

### 4. Report

Tell the user:

- where the game stands: phase, definition-of-done counts per milestone, last verdict;
- how to play it: the adapter's `run` command, and `package` artifacts if any;
- the human queue: each entry, and the wizard or playtest kit it points to;
- sessions used against the budget, adjusts and restarts used;
- what to do next: clear the queue and run `/game-director` to resume, or raise a limit.
