---
name: game-setup
description: Configure a repo for the game-* skills (autonomy, limits, tracker, state files, the user's seed idea), and later fill and smoke-test the engine adapter commands. Run first; game-plan calls it again once the engine is chosen.
disable-model-invocation: true
---

# Game Setup

Writes the per-repo config every game-* session reads, so no skill hardcodes an engine, platform or tracker. Two modes:

- **project**: the first run, before any engine is chosen.
- **adapter**: once an engine exists, fill and smoke-test the build, run and verify commands.

Take the mode from the task. With no task: project mode when `docs/agents/game.md` is missing, otherwise adapter mode.

## Project mode

### 1. Explore

Read what exists before deciding anything:

- Is this a git repository? `git remote -v`; `CLAUDE.md` / `AGENTS.md` and any `## Agent skills` block in them.
- `docs/agents/` (written by `setup-matt-pocock-skills` when installed), `CONTEXT.md`, the ADR folder.
- `docs/game/`: an earlier run of this workflow.
- An engine project: engine project files, build scripts, package manifests, an existing source tree.
- The user's prompt: the idea, platforms, budget, and whether they asked to be consulted (`--interactive`).

**Done when** you can state: git or not, tracker configured or not, engine present or not, earlier game state present or not.

### 2. Decide

- **Autonomy**: `interactive` when the user passed `--interactive` or asked to be consulted; otherwise `autonomous`.
- **Tracker**: an existing `docs/agents/issue-tracker.md` wins. Without one: interactive → ask the user (the questions protocol in [game.md](game.md)) whether to run `/setup-matt-pocock-skills` first or use local files; autonomous → local files: write [issue-tracker-local.md](issue-tracker-local.md) as `docs/agents/issue-tracker.md`, plus a default `docs/agents/triage-labels.md` (the roles `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`, each label equal to its role).
- **Domain docs**: an existing `docs/agents/domain.md` wins. Without one: single context, `CONTEXT.md` plus `docs/adr/` at the root, written into `docs/agents/domain.md`.
- **Limits**: the defaults in [game.md](game.md), overridden by anything the user's prompt says about time or budget.

**Done when** each decision has a value.

### 3. Write

1. No git repository: `git init` and an initial commit.
2. `docs/agents/game.md` from [game.md](game.md), with the autonomy mode filled in.
3. Copy [scripts/gamestate.py](scripts/gamestate.py) to `docs/game/gamestate.py` and run `python3 docs/game/gamestate.py init` (`python` where `python3` doesn't exist). Apply limit overrides to `docs/game/state.json`. Without any Python 3, tell the user the gates become manual and stop.
4. `docs/game/seed.md`: the user's prompt, verbatim, with any flags. Every later brainstorm and design run reads it.
5. In `CLAUDE.md` or `AGENTS.md` (whichever exists; if neither, the one your harness reads), add under `## Agent skills`:

   ```markdown
   ### Game workflow

   [autonomous | interactive] game-* workflow; state in `docs/game/`. See `docs/agents/game.md`.
   ```

6. When an engine project already exists, do adapter mode now.
7. Commit, then `python3 docs/game/gamestate.py complete`.

**Done when** `complete` succeeds.

## Adapter mode

### 1. Gather

Read [adapter-contract.md](adapter-contract.md), the engine ADR and `docs/game/engine-notes.md`. Missing facts about the engine's CLI, headless, test or export support: get them from official docs with the `research` skill, into engine-notes.md.

**Done when** you know a candidate command for every row of the contract.

### 2. Fill and smoke-test

For each row: write the command (or wrapper script) into the Commands table of `docs/agents/game.md`, run it, and record the smoke-test result in the Verified column. A row the engine can't support follows the contract's "When the engine resists" fallback, with the reason recorded.

**Done when** every required command passed its smoke test in this session, or is `n/a` under a fallback.

### 3. Close

Set `adapter_verified: true` in `docs/game/state.json`, commit, append a progress entry.
