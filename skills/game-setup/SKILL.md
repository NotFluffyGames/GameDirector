---
name: game-setup
description: Configure a repo for the game-* skills (autonomy, limits, tracker, where human-facing docs live, state files, the user's seed idea), and later fill and smoke-test the engine adapter commands. The first /game-next session runs it; game-plan runs it again once the engine is chosen.
disable-model-invocation: true
---

# Game Setup

Writes the per-repo config every game-* session reads, so no skill hardcodes an engine, platform or tracker. Two modes:

- **project**: the first run, before any engine is chosen.
- **adapter**: once an engine exists, fill and smoke-test the build, run and verify commands.

Take the mode from the task. With no task: project mode when `docs/agents/game.md` is missing, otherwise adapter mode.

## Project mode

Setup is always a conversation with the user. Ask where a choice is theirs; never settle the tasks home or the docs place on your own.

### 1. Explore

Read what exists before deciding anything:

- Is this a git repository? `git remote -v`; `CLAUDE.md` / `AGENTS.md` and any `## Agent skills` block in them.
- `docs/agents/` (written by `setup-matt-pocock-skills` when installed), `CONTEXT.md`, the ADR folder.
- `docs/game/`: an earlier run of this workflow.
- An engine project: engine project files, build scripts, package manifests, an existing source tree.
- The tracker, when one is configured: its existing spaces, lists and projects, through its tools.
- The user's prompt: the idea, platforms, budget, and whether they asked to be consulted (`--interactive`).

**Done when** you can state: git or not, tracker configured or not and what spaces, lists and projects it holds, engine present or not, earlier game state present or not.

### 2. Choose the tasks home

- **Autonomy**: `interactive` when the user passed `--interactive` or asked to be consulted; otherwise `autonomous`.
- **Tracker**: an existing `docs/agents/issue-tracker.md` wins. Without one, ask the user whether to run `/setup-matt-pocock-skills` first or use local files: write [issue-tracker-local.md](issue-tracker-local.md) as `docs/agents/issue-tracker.md`, plus a default `docs/agents/triage-labels.md` (the roles `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`, each label equal to its role).
- **Tasks home**: show the user the tracker's existing spaces, lists and projects. They pick one, or you create one with their go-ahead.
- **Domain docs**: an existing `docs/agents/domain.md` wins. Without one: single context, `CONTEXT.md` plus `docs/adr/` at the root, written into `docs/agents/domain.md`.
- **Limits**: the defaults in [game.md](game.md), overridden by anything the user's prompt says about time or budget.

**Done when** the user has confirmed the tasks home and each other decision has a value.

### 3. Smoke-test the docs place

The docs place is the tracker's docs feature at the tasks home. When the tracker can't host docs, the user picks a docs tool beside it; local files only when they choose them.

Fill [docs.md](docs.md) as `docs/agents/docs.md`: the tasks home, the docs place, and how to read, write and comment there. Run every step of its Smoke test table in the docs place, remove what the test created, and record each result and date. Set page protection where the tool supports it, so people comment and sessions edit.

**Done when** every Smoke test row holds a pass and a date, or the user has picked another place and its table passes.

### 4. Create the skeletons

1. The wiki home page, from [index-template.md](../game-ideation/index-template.md), in the docs place.
2. An empty GDD with the pages of [gdd-structure.md](../game-gdd/gdd-structure.md), each holding only its title.
3. Record the GDD page ids and links in the GDD pages table of `docs/agents/docs.md`, and the home page's id, link and today's date in its Wiki pages table. Step 5 writes the home page into `wiki.json`.

**Done when** each skeleton page exists in the docs place and its id and link are recorded.

### 5. Write

1. No git repository: `git init` and an initial commit.
2. `docs/agents/game.md` from [game.md](game.md), with the autonomy mode filled in.
3. Copy [scripts/gamestate.py](scripts/gamestate.py) to `docs/game/gamestate.py` and run `python3 docs/game/gamestate.py init` (`python` where `python3` doesn't exist). Apply limit overrides to `docs/game/state.json`, and set `docs_verified` to `{"place": "<docs place>", "date": "<today>"}`. Without any Python 3, tell the user the gates become manual and stop.
4. `docs/game/wiki.json` with the home page as its one page (`id` `index`, `area` Vision, `version` 1).
5. `docs/game/seed.md`: the user's prompt, verbatim, with any flags. Ideation reads it, and every restart.
6. In `CLAUDE.md` or `AGENTS.md` (whichever exists; if neither, the one your harness reads), add under `## Agent skills`:

   ```markdown
   ### Game workflow

   [autonomous | interactive] game-* workflow, one step per session: run `/game-next`. Agent-facing wiki and state in `docs/game/`; human-facing GDD where `docs/agents/docs.md` says. See `docs/agents/game.md`.
   ```

7. When an engine project already exists, do adapter mode now.

**Done when** `docs/agents/game.md`, `docs/agents/docs.md`, `docs/game/state.json` with `docs_verified`, `wiki.json` and `seed.md` exist.

### 6. Close

Commit, then `python3 docs/game/gamestate.py complete`.

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

**Done when** the commit holds the verified Commands table and `adapter_verified: true`.

## Upgrade mode

Task `game-setup upgrade`: bring an older game's files up to this version, with the user.

### 1. Upgrade the state

Copy [scripts/gamestate.py](scripts/gamestate.py) over `docs/game/gamestate.py`, then run `python3 docs/game/gamestate.py upgrade`.

**Done when** `upgrade` reports the current version.

### 2. Refresh the shared files

Replace every section of `docs/agents/game.md` with the one in [game.md](game.md), except the autonomy mode and the Commands table, which keep their values. Rename `docs/agents/human-docs.md` to `docs.md` when it exists, and follow its renamed path wherever the repo mentions it.

**Done when** `docs/agents/game.md` matches [game.md](game.md) apart from those two, and no `human-docs.md` remains.

### 3. Verify the docs place

When `docs_verified` in `docs/game/state.json` is set, skip this step. Otherwise run project mode's steps 2 to 4 with the user, then set `docs_verified` as step 5 does.

**Done when** `docs_verified` is set, or was set already.

### 4. Close

Commit, then `python3 docs/game/gamestate.py complete`.

**Done when** `complete` succeeds.
