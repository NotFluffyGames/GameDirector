---
name: game-director
description: Take a raw game idea to a fun, playable, rich, working and tested game in one run, by driving the game-* phase skills one fresh session per task until the final verdict ships or only human work remains.
disable-model-invocation: true
argument-hint: "[game idea] [--interactive] [--step]"
---

# Game Director

You are the **director**: a thin loop. Read state, dispatch **one task** to a **fresh session**, check the result, advance, repeat. You never do phase work yourself; that keeps your context small enough to last the whole game.

State lives on disk, not in your conversation: `docs/agents/game.md` (project config), `docs/game/` (seed, design, definition of done, state, progress log) and `docs/game/gamestate.py`, which reads, advances and commits that state. Run the tool instead of reading the JSON yourself.

## Dispatching

A dispatch starts a fresh session (a subagent; [loop-modes.md](loop-modes.md) covers harnesses without them) with only this prompt:

> Read `<skills-dir>/game-<phase>/SKILL.md` and follow it. Task: `<the next: action>`. Project config: `docs/agents/game.md`. Reply in at most 150 words: what changed, the evidence, what is left; start with `needs-user` if you wrote questions for the user.

`<skills-dir>` is the parent of this skill's directory; pass the absolute path. If the phase skills aren't beside this one, name the skill instead (`use the game-build skill`). A `fix: …` action goes to a session without a phase skill: "Fix these `gamestate.py check` violations without weakening the definition of done, then make check pass: …".

## Steps

### 1. Orient

If `docs/agents/game.md` is missing, dispatch `game-setup` with the user's whole prompt; it saves the idea to `docs/game/seed.md`. Then run `python3 docs/game/gamestate.py status`.

**Done when** status prints a `next:` line.

### 2. Act on `next:`

- `game-…` or `fix: …`: run `gamestate.py tick "<the action>"`, record the base commit (`git rev-parse HEAD`), dispatch.
- `advance`: run `gamestate.py advance`.
- `stop: …`: go to step 4.

A reply starting `needs-user`: put the questions in `docs/game/questions.md` to the user, write their answers under each question, commit, and go back to step 2 (the same task comes up again). In `--step` mode, or with no user to ask, answer with the recommended answers and mark them as assumptions.

**Done when** the dispatch has replied, or advance has printed the new phase.

### 3. Check

Treat a reply as a claim; the tool decides.

1. After a dispatch, run `gamestate.py check --since <base>`. On violations, dispatch one `fix:` session naming them (tick it first). If check still fails, `git reset --hard <base>` (the base already holds the tick, so the session still counts) and note why in `docs/game/progress.md`.
2. When advance printed `milestone complete`, run the adapter's `test` command and a short `bot` run from `docs/agents/game.md`. Red: dispatch `game-build` with the task `regression: <failing output, trimmed>` (tick it first).
3. Run `gamestate.py status` and return to step 2.

In `--step` mode, stop after one pass through steps 2–3. If your own context passes half despite all this, append a handoff note to progress.md and stop; running `/game-director` again resumes from disk.

**Done when** status prints `next: stop: …`.

### 4. Report

Tell the user:

- where the game stands against the goal in `docs/agents/game.md` (fun, playable, rich, working, testable, tested): phase, definition-of-done counts per milestone, the verdicts passed and the last verdict's scores;
- how to play it: the packaged builds and the adapter's `run` command, and target platforms this machine couldn't build for;
- the playtest kit: where it is, and that writing its answers file and running `/game-director` re-judges the game with them;
- the rest of the human queue, with the walkthrough each entry points to;
- sessions used against the budget, adjusts and restarts used;
- what to do next: play it and answer the kit, work the queue and run `/game-director` to resume, or raise the limit the stop names.
