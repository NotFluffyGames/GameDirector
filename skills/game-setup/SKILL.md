---
name: game-setup
description: Configure a repo for the game-* skills with the user (autonomy, limits, whether the game is meant to sell, the tasks home and the docs place beside it, smoke-tested, the research sources this machine reaches, wiki and GDD skeletons, state files, the seed idea); fill and smoke-test the engine adapter commands once an engine exists; upgrade a game set up with an older version. The first /game-next session runs it, game-plan runs adapter mode, and /game-next runs upgrade mode for an older game still at setup.
disable-model-invocation: true
---

# Game Setup

Writes the per-repo config every game-* session reads, so no skill hardcodes an engine, platform or tracker. Three modes, taken from the task, or with no task from the game:

- **upgrade**: the task `game-setup upgrade`: an older game's files brought up to this version.
- **project**: the task `game-setup`; with no task, a game with no `docs/game/state.json` yet, or one whose `phase` is still `setup`. The first run, before any engine is chosen; a session that resumes it skips the steps whose **Done when** already holds.
- **adapter**: game-plan's step 2 sends you here, or the user asks once an engine exists: fill and smoke-test the build, run and verify commands.

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
- **Intent**: one question: is the game meant to **sell**, or is it a **hobby** (a jam, a learning project, a game for friends)? Recommend `sell` when the prompt mentions selling, a store or a price, otherwise `hobby`. It sizes research: `hobby` drops sales numbers and saturation, and keeps comps, anchors, the player, references and complaints.
- **Tracker**: an existing `docs/agents/issue-tracker.md` wins. Without one, ask the user whether to run `/setup-matt-pocock-skills` first or use local files: write [issue-tracker-local.md](issue-tracker-local.md) as `docs/agents/issue-tracker.md`, plus a default `docs/agents/triage-labels.md` (the roles `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`, each label equal to its role).
- **Tasks home**: show the user the tracker's existing spaces, lists and projects. They pick one, or you create one with their go-ahead.
- **Domain docs**: an existing `docs/agents/domain.md` wins. Without one: single context, `CONTEXT.md` plus `docs/adr/` at the root, written into `docs/agents/domain.md`.
- **Limits**: the defaults in [game.md](game.md), overridden by anything the user's prompt says about time or budget.

**Done when** the user has confirmed the tasks home and each other decision has a value.

### 3. Smoke-test the docs place

The docs place is the tracker's docs feature at the tasks home. When the tracker can't host docs, the user picks a docs tool beside it; local files only when they choose them.

Fill [docs.md](docs.md) as `docs/agents/docs.md`: the tasks home, the docs place, how to read, write and comment there, and which **version** a page has there. Run every step of its Smoke test table in the docs place, remove what the test created, and record each result and date. Protect the wiki's container (the folder, space or doc that holds its pages) so people comment and sessions edit, and pages created later inherit it; where the tool has no page permissions, tell the user and record `not supported (user told)`.

**Done when** every Smoke test row holds a pass and a date (`protect the wiki` may hold `not supported (user told)`), or the user has picked another place and `docs/agents/docs.md` is refilled for it (its Docs place section and its Smoke test table) with every row passing.

### 4. Check the research sources

Research reads other games' store pages and reviews from this machine. Probe each host in the Reachability table of the game-research skill's [sources.md](../game-research/sources.md) once, as it says, and note each reachable or not, with what a failure printed.

- **Unreachable hosts** (no response at all; any HTTP status counts as reached): tell the user which failed and what research loses (its column there); in research, their work becomes homework for a person. Allowing a host in this machine's or environment's network settings fixes it: probe again once they have.
- **A public repo**: when the remote is public (`gh repo view --json visibility`, or ask the user), tell them that research commits downscaled screenshots of other games under `docs/game/research/refs/`, and ask them to make the repo private or accept that. Accepted: `public_repo_ok` is `true`. Made private: check the visibility again.

Step 6 records `research_sources` in `docs/game/state.json`: `{"checked": "<today>", "reachable": [...], "unreachable": [...]}`, the hosts by name, plus `"public_repo_ok": true` when the person accepted a public repo.

**Done when** every host in the table has today's result, the user has heard which failed, and the repo is private or the person accepted committing reference images to a public one.

### 5. Create the skeletons

1. The wiki home page, from [index-template.md](../game-ideation/index-template.md), in the docs place.
2. An empty GDD with the pages of [gdd-structure.md](../game-gdd/gdd-structure.md), each holding only its title.
3. Record the GDD page ids and links in the GDD pages table of `docs/agents/docs.md`, and an `index` row (the home page's link) in its Wiki pages table. Step 6 writes the home page into `wiki.json`.

**Done when** each skeleton page exists in the docs place and its id and link are recorded.

### 6. Write

1. No git repository: `git init` and an initial commit.
2. `docs/agents/game.md` from [game.md](game.md), with the autonomy mode filled in.
3. Copy [scripts/gamestate.py](scripts/gamestate.py) to `docs/game/gamestate.py` and run `python3 docs/game/gamestate.py init` (`python` where `python3` doesn't exist). Apply limit overrides to `docs/game/state.json`, and set `docs_verified` to `{"place": "<docs place>", "date": "<today>"}`, `intent` to the step 2 answer and `research_sources` to step 4's record. Without any Python 3, tell the user the gates become manual and stop.
4. `docs/game/wiki.json` with the home page as its one page: `id` `index`, `title`, `area` Vision, `link` (from step 5), `version` (the page's version, read back as `docs/agents/docs.md` says) and `updated` (today's date and a reason, e.g. `2026-11-23: created by setup`).
5. `docs/game/seed.md`: the user's prompt, verbatim, with any flags. Ideation reads it, and every restart.
6. In `CLAUDE.md` or `AGENTS.md` (whichever exists; if neither, the one your harness reads), add under `## Agent skills`:

   ```markdown
   ### Game workflow

   [autonomous | interactive] game-* workflow, one step per session: run `/game-next`. State in `docs/game/`; the wiki (for agents) and the GDD (for people) live where `docs/agents/docs.md` says. See `docs/agents/game.md`.
   ```

7. When an engine project already exists, do adapter mode now.

**Done when** `docs/agents/game.md`, `docs/agents/docs.md`, `docs/game/state.json` with `docs_verified`, `intent` and `research_sources`, `wiki.json` and `seed.md` exist, the `index` entry in `wiki.json` has a link, and `python3 docs/game/gamestate.py check` passes.

### 7. Close

Commit, then `python3 docs/game/gamestate.py complete`.

**Done when** `complete` succeeds.

## Adapter mode

### 1. Gather

Read [adapter-contract.md](adapter-contract.md), the engine ADR and `docs/game/engine-notes.md`. Missing facts about the engine's CLI, headless, test or export support: get them from official docs with the `research` skill, into engine-notes.md.

**Done when** you know a candidate command for every row of the contract.

### 2. Fill and smoke-test

For each row: write the command (or wrapper script) into the Commands table of `docs/agents/game.md`, run it, and record the smoke-test result in the Verified column. A row the engine can't support follows the contract's "When the engine resists" fallback, with the reason recorded.

**Done when** every required command passed its smoke test in this session or is `n/a` under a fallback, and every optional output passed its smoke test (on the contract's test fixture while the game has nothing of its own to show) or is `n/a` because the engine can't give it.

### 3. Close

Set `adapter_verified: true` in `docs/game/state.json`, commit, append a progress entry.

**Done when** the commit holds the verified Commands table and `adapter_verified: true`.

## Upgrade mode

Task `game-setup upgrade`: bring an older game's files up to this version, with the user.

### 1. Upgrade the state

Run this skill's copy of the tool against the repo, before replacing the repo's copy: `python3 <this skill's folder>/scripts/gamestate.py upgrade --root .` (the file is [scripts/gamestate.py](scripts/gamestate.py)). It commits what it changed. A game still at setup gets a fresh state that keeps its limits, counters, human queue, `adapter_verified` and `docs_verified`, so step 3 doesn't choose the tasks home or smoke-test the docs place again. When it refuses (no game state here, a game newer than this plugin, a version that isn't a whole number, or a game past setup), it has changed nothing: tell the user what it said and stop. Otherwise copy [scripts/gamestate.py](scripts/gamestate.py) over `docs/game/gamestate.py` and commit it.

**Done when** `upgrade` reports the current version (or that it was already there) and `docs/game/gamestate.py` is this skill's copy, committed; or it refused and the user has its message.

### 2. Refresh the shared files

1. Replace every section of `docs/agents/game.md` with the one in [game.md](game.md), except the autonomy mode and the Commands table, which keep their values.
2. Show the user `git diff docs/agents/game.md` and ask which removed lines were their own edits; put back each one they keep, in the section it belongs to. The old text stays in git history.
3. Rename `docs/agents/human-docs.md` to `docs.md` when it exists, and follow its renamed path wherever the repo mentions it.
4. Replace the `### Game workflow` block in `CLAUDE.md` or `AGENTS.md` with project step 6.6's, keeping its autonomy mode.

**Done when** `docs/agents/game.md` matches [game.md](game.md) apart from the autonomy mode, the Commands table and the edits the user kept, no `human-docs.md` remains, and the `### Game workflow` block says to run `/game-next`.

### 3. Verify the docs place

Skip this step when `docs_verified`, `intent` and `research_sources` in `docs/game/state.json` are set and `docs/game/wiki.json` has an `index` entry with a link. Otherwise, with the user: project mode's steps 2 and 3 when `docs_verified` is unset, its intent question (step 2) and step 4 when `intent` or `research_sources` is unset, and its step 5 for each skeleton page the docs place lacks. Then register the home page's `index` entry in `wiki.json` as project step 6.4 does (when it has none) and set what you settled in `state.json` as step 6.3 does.

**Done when** `docs_verified`, `intent` and `research_sources` are set and `wiki.json` has an `index` entry with a link.

### 4. Close

Commit, then `python3 docs/game/gamestate.py complete`.

**Done when** `complete` succeeds.
