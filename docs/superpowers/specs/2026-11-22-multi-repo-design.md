# Games that span several repos

Design for making the game-* skills work for a game whose code lives in several repos (a client and a backend, a repo per platform, a repo per region), without making single-repo games any harder.

## Intent

The user is making a multiplayer game, which means at least a client and server-side code. More generally, real games are often split across repos by team, stack or platform. The skill set promised from the start to be repo-agnostic, the same way it is engine-, genre- and tracker-agnostic. Today it isn't: everything assumes one repo.

How it works today:

- All game state lives in one repo's `docs/game/`: the wiki, the topic tree, the fun checklist and richness targets, the definition of done (`features.json`), verdicts and `state.json`.
- One set of adapter commands (build, test, run, sim, replay, bot, capture, package) lives in `docs/agents/game.md`.
- `gamestate.py` checks are git-based against one repo: the edit guard compares against the session's base commit, the tool commits its own state, and a bad session is reset to its base.
- The tracker and the human GDD already live outside the repo.

## Goals

- **Any layout.** A game is a set of **components**: clients, a game server, backend services, shared libraries, platform shells, region builds. Each component lives in the home repo, in a folder of a monorepo, or in its own repo. The skills assume none of these; each game records its own layout once.
- **One game, one truth.** Game-level things stay one per game: vision, wiki, topics, fun checklist, richness targets, verdicts, GDD, definition of done.
- **Shared by every team.** The design docs live where every team already works: next to the tasks.
- **An explicit, verified tasks home.** The tasks home holds every team's tasks and both layers of docs, so it is chosen or created explicitly with the user, and proven to support docs before anything is written there.
- **Checks cover every repo.** No repo can quietly break what the game counts as done: evidence, clean state, rollback and regressions all span every component a session touches.
- **Work outside the workflow is checked too.** Each component repo runs a CI check against the game's state, so a hand-made fix in the server repo can't break a passing feature unnoticed.
- **Parallel sessions.** Several people (or several unattended loops) can run `/game-next` at once, on different steps, without corrupting the game's state.
- **Several components tested together.** Bots that join a running server, several clients, simulated network conditions, and a server people can join for a human playtest.

## Non-goals

- Deploying to production, live operations, or scaling the backend. The goal stays a fun, playable, tested game, not a launched service.
- Choosing the repo layout for the team. The skills record the layout a game has; they recommend one only when a new game has none yet (game-plan's tech decisions).
- Supporting every CI system with prewritten config. The CI check is described once; game-setup writes it for whichever CI a component uses.

## Anti-goals

- **A single-repo game pays for this.** One component, the home repo itself, must need no extra setup, files the user has to think about, or steps.
- **Two sources of truth.** No component repo holds its own copy of the definition of done or the design.
- **Tracker-specific state code.** `gamestate.py` stays tracker-agnostic; it never calls a tracker's API.

## Constraints

- One step per session, via `/game-next`; no orchestrator conversation. Many sessions may run at once.
- Ideation and brainstorming happen with a person; the slice verdict waits for a person's playtest.
- `gamestate.py`: Python 3.8+, standard library only, git-based checks.
- Claude Code sessions: locally the working directory is one repo, but sibling checkouts are reachable by path. Cloud sessions can attach several repos.
- Agents reach docs next to the tasks through the tracker's connector (MCP or CLI), which can be unavailable; this session saw several connectors fail.

## Approaches considered

1. **A home repo plus a component map** (picked). One repo is the game's home for checked state and the component map; components live anywhere; features name the components they touch. It is one source of truth, changes the state tool least, and costs a single-repo game nothing (a map with one row). Its costs are that a session touching a component needs two checkouts, and a cross-repo feature has one commit per repo, not one in all.
2. **Each repo runs its own state**, with a game-level layer combining them for verdicts. Rejected: two state machines to keep in agreement, and complicated cross-repo gates, to support layouts approach 1 already handles.
3. **A meta repo that includes the others** (git submodules or a manifest), so the skills see one tree. Rejected as the model: submodules are painful day to day, teams often won't accept them, and separate permissions per region or platform fit badly. It still works inside approach 1: a team that wants submodules points the map at submodule folders.

**The user's refinement:** prose docs, both the agent-facing wiki and the human-facing GDD, live **next to the tasks**, because the tasks' home is shared by every team. Only the **checked state** stays in the home repo, because its checks need git history and `gamestate.py` must stay tracker-agnostic.

## Decisions (made with the user)

1. Components, each in any repo, recorded in a per-game map. A single-repo game has one component.
2. The home repo holds the checked state and the component map: `state.json`, `features.json`, `topics.json`, `fun-checklist.json`, `richness.json`, `keep.json`, `own-calls.md`, `progress.md`, `gamestate.py`, and the config in `docs/agents/`.
3. The wiki (agent-facing) and the GDD (human-facing) live next to the tasks, in the tracker's docs tool, as two layers.
4. Checks cover every repo a session touches: evidence commits, a clean state at session end, rollback per repo, and regressions at milestone boundaries.
5. A CI check runs in each component repo against the game's state.
6. Testing several components together (the "stack") is part of the adapter.
7. Platform and region variants are declared per game: separate components, or variants of one component's build.
8. The tasks home is chosen or created explicitly with the user, never defaulted, and setup proves it supports docs before going further. Setup is therefore always a conversation with the user (`with-user:`).
9. How work lands is chosen per component: **direct push** (the default) or **pull requests**. Either way, sessions work in their own copy of each repo, never in a developer's checkout.
10. **Parallel sessions are supported**: several sessions run at once, each on its own step.
11. **People only comment on wiki pages.** Their comments become topics, as with the GDD; a direct edit is detected and becomes a topic too.

## Design

### Components and the map

The map lives in two forms in the home repo: `docs/game/components.json`, which `gamestate.py` reads, and a Components table in `docs/agents/game.md` for people.

```json
{"components": [
  {"name": "client", "role": "Bevy game client", "repo": ".", "path": ".", "branch": "main",
   "commands": {"build": "cargo build -p client", "test": "cargo test -p client"},
   "variants": []},
  {"name": "server", "role": "authoritative game server", "repo": "NotFluffyGames/eve-server",
   "path": "../eve-server", "branch": "main",
   "commands": {"build": "...", "test": "...", "run": "..."}, "variants": []}
]}
```

- `repo`: `.` for the home repo, otherwise the remote (`owner/name` or a git URL). `path`: where a session finds the checkout, relative to the home repo root. A monorepo folder is `repo: "."` with `path` set to the folder.
- `commands`: the per-component rows of today's adapter contract. The game-level rows move to the stack (below).
- `variants`: build variants of this component (platforms, regions) that `package` and playtests can take, for example `{"name": "eu", "package": "... --region eu"}`. A variant that needs its own codebase is a separate component instead.
- `init` writes a one-component map for the home repo; a single-repo game never edits it. *(My call.)*

### Features across components

- `features.json` items gain `components` (default: the home's component).
- Evidence names the commit in each component: `evidence: {"text": "...", "commits": {"client": "<sha>", "server": "<sha>"}}`. The tool also accepts today's plain-string evidence for single-component features. *(My call: the string form stays valid, so existing games keep working.)*
- Tickets carry the component names (a label or a field in the tracker, per `issue-tracker.md`).

### Docs next to the tasks

- `docs/agents/human-docs.md` becomes `docs/agents/docs.md`: where both layers live, and how to read, write and comment there. *(My call on the name.)* Setup asks the user to confirm the place.
- **The wiki index stays in the home repo** as `docs/game/wiki.json`: every page's id, title, area (the index sections), link, and `updated` (date and one-line reason). Topics and features refer to pages by id. `gamestate.py` checks references against this index, instead of against files, and checks each area for consolidate's gate. A session that changes a page updates its `updated` entry in the same commit as the code or state change it goes with.
- **GDD staleness** becomes `git diff gdd_synced..HEAD -- docs/game/wiki.json docs/game/own-calls.md`: any page updated since the last sync. The rest of today's mechanism stays.
- **Vision facts the gates need** move to `docs/game/vision.json`: pillars (id and statement), anti-pillars, whether a kill condition is set, the slice's quality bar and test question. The vision and slice pages are the prose; `vision.json` is their checked summary, written by ideation and updated by any session that changes them. Gates read the JSON, not the pages.
- **Files in the repo only by the user's choice.** When the user explicitly chooses local files (a solo or offline game), the pages are markdown under `docs/game/wiki/` in the home repo, indexed by the same `wiki.json`: one mechanism, two storage places. Setup never falls back to this on its own.
- **People comment; agents edit.** Wiki pages are written only by sessions. People comment, and game-gdd turns comments into topics, as for the GDD. Setup protects the wiki pages (agent-edit, everyone-comment) where the docs tool supports page permissions, and says so where it doesn't.
- **Direct edits are detected.** `wiki.json` records each page's version or last-modified time from the docs tool, as the session last wrote it. A page whose version moved without a session recording it was edited by hand: game-gdd opens a topic quoting the change (from the tool's history, where it has one), and the page is marked "edited outside a session; under review in T0xx" until the topic resolves. The next brainstorm then rewrites it. *(My call: keep the edit visible rather than revert it, since not every docs tool can restore old versions.)*
- **Pages are written last.** A session writes tracker pages only after `check` passes and its state transaction lands, so a rolled-back session never leaves a page changed. Parallel sessions claim the pages they will write.
- **When the connector is unavailable**: every session that needs the docs checks the connection first (a cheap read of the index page) and stops with `stop: <tracker> docs unreachable` rather than working around it. Unattended loops need the connector set up too.

### Sessions across repos

- `/game-next` always starts in the home repo.
- **Session-owned copies.** A session works in its own copy of every repo it touches: a git worktree of a local checkout, or a fresh clone (in a cloud session, an attached repo). It never commits in, resets or switches a developer's own checkout. *(My call: protects people's uncommitted work, and is what makes parallel sessions possible.)*
- `gamestate.py tick` (now `claim`, below) records the base commit of every copy in `docs/game/.session.json`, which is gitignored and per copy. `check` reads it by default.
- **Rollback** resets the session's own copies to their bases. Nothing pushed is ever rolled back: pushing happens only after `check` passes.

### How work lands

Each component's map entry has `integration: "push"` (the default) or `"pr"`.

- **push:** after `check` passes, the session rebases onto the latest `branch` of each component it changed, re-runs that component's `test`, and pushes, components first and the home last. A rebase conflict is resolved in the session (the `resolving-merge-conflicts` skill), or the session stops and leaves its claim to expire. If a push fails after a component already landed, the home's next state transaction records what landed; the following session finishes the rest. *(My call.)*
- **pr:** the session pushes its own branch and opens a pull request in each component it changed, linking the feature and the ticket, and the feature becomes `awaiting-merge` with the pull request recorded. The pull request is merged by the component's own rules: automatically once its CI check passes, or by a person. A short **confirm** step (`game-build confirm F012`) then checks out the component's `branch`, re-runs the feature's verify there, and records the evidence commit on `branch`. Squash and rebase merges therefore work: evidence always names a commit on `branch`. Awaiting-merge features don't block other work, but they do block the gates (a verdict judges merged code only). *(My call on the confirm step.)*
- The home repo always uses push for state (below), because state transactions must land immediately.

### Parallel sessions

The home repo's `branch` is the single place sessions coordinate. Git provides the lock: a push that isn't a fast-forward fails, and the session fetches and retries.

- **Claims.** `gamestate.py claim` replaces `tick`. It fetches the home, computes the frontier of steps that can run now, picks the first one no live claim holds, and adds a claim `{id, step, components, pages, session, started, expires}` to `docs/game/claims.json`. Then it commits and pushes; a rejected push means fetch and retry. `/game-next` takes the step it claimed. *(My call on the mechanism.)*
- **The frontier.** Steps that can run side by side: features in the current milestone whose tickets aren't blocked and whose components and pages no live claim holds; brainstorm topics whose pages no claim holds; a GDD sync when nothing else is editing pages. **Exclusive steps** run alone: ideation, consolidate, plan (except checkpoint and unblock on unclaimed features), verdicts, and every phase transition (`advance` waits until no claims remain for the phase).
- **State transactions.** Sessions no longer hand-edit shared state files during build and brainstorm. Small changes go through tool commands that fetch, apply, commit and push with retry:
  - `gamestate.py record F012 --passes --evidence ...`
  - `gamestate.py topic T014 --resolve ...`
  - `gamestate.py queue ...`
  - `gamestate.py release`, which drops the claim.

  Exclusive steps (plan, consolidate, verdicts) may still edit files directly, since nothing runs beside them.
- **Leases.** A claim expires (default 4 hours, a limit in `state.json`). A crashed session's step returns to the frontier, and its unpushed work is lost with its copy.
- **Counters.** `sessions`, `attempts` and `last_dispatch` become per-claim records, so parallel ticks don't collide. Stall detection counts claims of the same step in a row.
- **Code conflicts.** Two sessions on the same component work on different features, in different copies. They meet at rebase (push) or merge (pr), as people do.

### Checks across repos

`gamestate.py check`, run from the home, adds per component:

- the checkout exists, is on its `branch`, and has no uncommitted changes (at session end; the start-of-session check only warns);
- every passing feature's evidence commit for this component exists, and is an ancestor of the component's `branch` head (after a fetch); otherwise "F012: server commit abc123 is not on main (history rewritten?)";
- the component repo has its pointer block (below).

**Regressions:** when `advance` prints `milestone complete`, `/game-next` runs every component's `test` and the stack's smoke test before reporting. A feature whose test now fails gets `passes: false`, and the state tool sends it back to build, whatever repo broke it. *(Replaces today's single-repo regression step.)*

### The stack (several components together)

Game-level adapter commands in `docs/agents/game.md`, empty for a single-process game:

| Name | Does |
| --- | --- |
| `stack-up` / `stack-down` | start and stop the server and services locally, at chosen commits |
| `stack-bots` | run N bot clients against the running stack: `--clients N --policy P --runs R --net <profile>` (latency, jitter, loss) |
| `stack-smoke` | the short regression run for milestone boundaries |
| `playtest-server` | make a server people can join for a human playtest (local, LAN or a deployed instance), printing how to connect |

`sim`, `replay` and `bot` stay per component. Proxies and features that need several components use `stack-bots`, with a new verify kind, `stack`. A `playtest-server` that needs cloud credentials is a human-queue entry with a wizard.

### Component repos

- **Pointer block** in each component's `CLAUDE.md` or `AGENTS.md`: the component's name, the game, where the home repo is, the docs location, and how to run the check. A session that starts there reads it.
- **CI check**, written by game-setup for each component, in whatever CI the component uses. On pushes and pull requests to the component's branch, the job:
  1. checks out the home repo read-only (a read token is a human-queue entry with a wizard);
  2. runs `gamestate.py check --component <name> --path .`: evidence commits still reachable, and no history rewritten under a passing feature;
  3. runs the component's `test` command.

  It fails the job when any of these fail. It never writes to the home repo: failures reach the game as red CI, and as the next milestone's regression run. A component with no CI gets a human-queue entry saying so.

### Setup and upgrade

Setup is now always a conversation with the user (`with-user: game-setup`): it makes choices only the user can make, with their accounts.

1. **The tasks home, chosen or created explicitly.** Show the user what exists: the tracker this repo already uses (`docs/agents/issue-tracker.md`), and the spaces, lists or projects the connected tracker offers. The user picks one, or asks for a new one, which setup creates with their go-ahead. Local files only when the user explicitly chooses them.
2. **Prove it supports docs.** A smoke test, like the adapter's:
   1. create a page, read it back and edit it;
   2. add a comment and read comments back;
   3. link the page from a task;
   4. delete the test page.

   Each result is recorded in `docs/agents/docs.md`. If the tracker can't host docs, the user chooses a docs tool beside it (reachable from the same sessions), which gets the same test.
3. **Create the skeletons.** The wiki and the GDD, created empty in the docs place with their page lists, and their ids recorded in `wiki.json` and `docs.md`.
4. **The layout.** One repo (the default; no questions beyond that), or the list of components. Setup writes the map, the pointer blocks, the CI checks (through adapter mode, per component), and the stack rows when there is more than one process.

The setup gate (in `gamestate.py`) gains `docs_verified`: set only when the smoke test passed, with the date and the docs place. Setup can't complete without it, the same way plan can't complete without `adapter_verified`.

- **Layout decided later.** game-plan's tech decisions recommend a layout for a new multiplayer game and record it in an ADR. When the layout has more than one component, plan runs game-setup's new **components mode**, a sub-step like adapter mode: map rows, pointer blocks, adapters, CI. *(My call.)*
- **Agents never create repos on their own.** A component that needs a new repo becomes a human-queue entry with a wizard; in a session with the user present, the agent may create it with their go-ahead. *(My call.)*
- **The plan gate covers every component:** each has verified adapter commands, its pointer block, and a CI check written or queued for a person (when it needs a credential). *(My call.)*
- **A new upgrade mode in game-setup** refreshes a game repo's copies (`gamestate.py`, the `game.md` template sections the skills own, new state files, the docs move) while keeping project choices: autonomy, commands, tracker, docs location. When an existing game's tasks home was never verified for docs, upgrade runs steps 1–3 with the user. **Migrations are versioned:** each release that changes the game files ships a migration step, and upgrade applies them in order from the game's recorded version. *(My call.)* The first supports EveLikeBrawl's case: a game set up with 0.3.0, still at setup. Games partway through a run on an older version aren't supported, since none exist.

## What the skills change

| Skill | Change |
| --- | --- |
| game-setup | always with the user; tasks home chosen or created explicitly; docs smoke test; wiki and GDD skeletons; layout question, component map, pointer blocks, CI checks, stack rows; upgrade mode |
| gamestate.py | setup as a `with-user:` step gated on `docs_verified`; components.json, wiki.json and vision.json checks; per-component evidence and checks; `.session.json`; `--component` mode; `stack` verify kind; claims, leases and the parallel frontier; state transactions (`record`, `topic`, `queue`, `release`); `awaiting-merge` and confirm steps; versioned migrations |
| game-next | home-repo rule; `claim` instead of `tick`; session-owned copies; a docs connection check before steps that need docs; push or pull request per component; per-copy rollback; milestone regression run across components |
| ideation, brainstorm, consolidate | pages via the docs tool; keep wiki.json and vision.json in step |
| game-plan | features name components; layout recommendation; stack features |
| game-build | work in session-owned copies; push or pull request per component; confirm mode for merged pull requests; `record` for results; per-component evidence; pages last, via the docs tool |
| game-verdict | stack bots and `playtest-server` for multiplayer scopes |
| game-gdd | both layers in the same docs tool; staleness from wiki.json; comments become topics; direct wiki edits detected and flagged |

## Calls I made (for the user to check)

- Sessions work in session-owned copies (worktrees or clones), never in a developer's checkout.
- Push order components first, home last; a partial push is finished by the next session.
- Pull-request integration uses a confirm step that re-verifies on the component's branch after the merge.
- Claims in `claims.json` on the home's branch, with git's fast-forward rule as the lock, and 4-hour leases.
- During build and brainstorm, shared state changes only through tool commands that retry on conflict.
- A direct wiki edit is kept, flagged, and turned into a topic, not reverted.
- The layout's components are set up through a components mode that plan calls.
- Agents never create repos on their own.
- The plan gate requires every component's adapter, pointer and CI.
- Upgrade migrations are versioned; mid-run games on old versions aren't migrated.
- `human-docs.md` is renamed `docs.md`.
- The string form of feature evidence stays valid for single-component games.

## Left to the builder

- The exact JSON field names beyond those above, and the CLI shape of `--component`.
- The order of the work. Suggested: upgrade mode and docs move first (EveLikeBrawl needs it), then components and checks, then the stack and CI.
- Test design. `gamestate.py` stays test-first, with temporary multi-repo fixtures (a home and two component repos); `tests/test_skills.py` grows checks for the new references.

## Risks

- **Connector dependence.** Every session that reads pages needs the tracker's docs connector. Mitigation: a clear stop, and the markdown fallback for local-files trackers.
- **Cross-repo cost.** Sessions with several checkouts are slower; fetching each component for the ancestor check costs time. Mitigation: fetch only components the session touched, and every component only at milestone boundaries.
- **CI credentials.** Each component's CI needs read access to the home repo, which needs a person to set it up.
- **Parallel complexity.** Claims, leases and state transactions are the biggest change to the state machine. Mitigation: single-session use stays the default path; one session simply claims everything in order.
- **Claim contention.** Many sessions on a small frontier retry often. Mitigation: a session that can't claim anything stops with `stop: nothing to claim (N sessions running)` instead of spinning.
