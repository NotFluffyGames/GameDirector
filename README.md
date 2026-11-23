# GameDirector

Agent skills that take a raw game idea to a **fun, playable, rich, working, testable and tested game**, over many sessions:

```
/game-next a two-player couch brawler where you steal each other's weapons
```

Every session does **one step** and stops: run `/game-next` in a fresh session and it asks the state tool what comes next, does that step with you or on its own, checks it, and tells you what the next session will do. Shaping the idea is always a conversation with you; scanning, studying, building, judging and polishing can run unattended. Seven studio roles (creative, design, feel, art, audio, narrative and ux) own every taste aspect and review the running game, and a research phase studies comparable games before anything is designed. Nothing in the skills names an engine, genre, platform, repo or task manager: each project records those once, in config the skills read. Publishing is out of scope: the run ends with a game you can play, backed by evidence, and documents that describe it.

## The goal

| Quality | Checked by |
| --- | --- |
| Playable | the packaged build launches without dev tools and plays from title screen to the end of a session, on every target platform the machine can build for |
| Working | every `must` feature passes; a long crash and softlock fuzz run is clean |
| Tested | tests, replays and bot runs cover the core rules and every feature, green on the final build |
| Testable | a deterministic simulation core, and adapter commands that re-run every check |
| Rich | richness targets for depth (systems that change each other), breadth (distinct content) and variety (playthroughs that differ) pass on the final build |
| Fun | every fun proxy passes on the final build, and a playtest kit is ready; people's answers can still reopen the verdict |
| Reviewed | every visible feature, verdict and polish feature is reviewed by its roles, every note decided by the creative director and carried out |

## How it works

```
slice:       setup → scan (the landscape, unattended) → ideation (vision, north stars + vertical slice)
             → research (the references ideation chose; homework for you) → brainstorm (the slice's topics, one per session)
             → consolidate → plan → build the core loop → verdict: core-loop (bots) → build the slice to its quality bar
             → verdict: slice (after your calibration and playtest; the gate into production)
production:  brainstorm (the remaining topics) → consolidate → plan → build systems and content → verdict: full
             → polish (a pass per role; your A/B picks) → verdict: final → done

any verdict: adjust → plan     restart → scan → ideation     kill (slice) → you decide
any phase:   an unanswered design question → a brainstorm topic, with you
```

`state.json` `phase` is one of setup, scan, ideation, research, brainstorm, consolidate, plan, build, verdict, polish, done, plus `awaiting-human` stops.

The **vertical slice** comes first: a small part of the game, one complete start → challenge → resolution that delivers the target feeling, at the quality bar you choose per aspect (code, feel, art, audio, UI, onboarding). Brainstorming designs only what the slice needs, so something playable and representative arrives early; the slice verdict waits for a person's playtest and checks the vision's kill condition; and the sessions the slice took set the production budget.

| Skill | Step | Produces | With you? | Leans on |
| --- | --- | --- | --- | --- |
| `game-next` | every session | runs the next step, checks it, reports what's next | — | — |
| `game-setup` | first session | `docs/agents/game.md` and `docs.md` config, state files, the tasks home and docs place (chosen or created, then smoke-tested), the research hosts this machine reaches, wiki and GDD skeletons, verified engine commands | always | `research` |
| `game-research` | scan, then one reference per session | the landscape page (comps, anchors, complaints, candidate references); per-role dossiers of each reference; a brief; your homework | homework only | — |
| `game-ideation` | vision | vision (with anti-pillars and a kill condition), each role's north star, the vertical slice definition, directions considered, the references to study, the first topics | always | `grilling`, `domain-modeling` |
| `game-brainstorm` | one topic | the topic's wiki pages (in your docs place), follow-up topics; the roles' challenges come first | always | `grilling`, `research` |
| `game-consolidate` | after each brainstorm pass | a complete, consistent wiki (with a whole-design review, the roles' pages against each other); the fun checklist with the roles' review items, and richness targets | interactive mode | — |
| `game-gdd` | whenever the wiki changed | the human GDD, next to your tasks, in sync with the wiki, including the AI's own calls for you to keep or change | — | — |
| `game-plan` | plan | tech ADRs, a walking skeleton that captures and logs itself, the capture protocol (named states and strips, the event log), `features.json` opening with a `feel` target in core-loop and a `visual` target in the slice, tickets | interactive mode | `codebase-design`, `domain-modeling`, `research` |
| `game-build` | one feature | built, verified, reviewed by its roles and committed; queues your calibration when the visual target passes; applies your A/B picks | — | `tdd`, `diagnosing-bugs`, `code-review` |
| `game-verdict` | core loop, slice, full, final | fun and richness scores with evidence, a review by every role, playtest kits, kept values, a ship/adjust/restart/kill ADR | the calibration and slice playtest; interactive mode | — |
| `game-polish` | polish | one pass per role (feel, art, audio, narrative, ux), balance, performance, accessibility and packaged-build features, each reviewed; A/B pairs for taste calls | your A/B picks | — |
| `game-review` | called by build, verdict, brainstorm | the roles' review records, every note decided and carried out | — | — |
| `game-role-<id>` | called by the above | one skill per role (creative, design, feel, art, audio, narrative, ux); its agent is `agents/<id>.md` | — | — |

**Ideation and brainstorming, with you.** Ideation grills you on the raw idea, compares 3–5 directions that play differently, lets you choose, writes the vision (with anti-pillars and a kill condition), and defines the vertical slice with you. It then breaks "the game" into first-level topics. Each brainstorm session takes one topic, grills you on it, and challenges every answer hard against the vision, the rest of the wiki, how it plays and what it costs. It then writes or updates the topic's pages and opens the follow-up topics the conversation raised. The tree grows until every topic is answered precisely enough to plan features and write tests from.

**Roles and reviews.** Every taste aspect has an owner. `creative` guards the vision and decides every review note; `design` owns rules and systems; `feel` how actions feel; `art` the look; `audio` sound; `narrative` tone, world and every player-facing word; `ux` understanding and access. Ideation sets each role's north star with you (a role is switched off only with a reason you accept). A role challenges the brainstorm topics it is on before you are asked anything, and it reviews the running game. `game-review` prepares captures, frame strips, measurements and logs once from one build, runs the roles as parallel agents that read those files (they never run the game), has `creative` decide every note, carries the decisions out and records them under `docs/game/reviews/`. A visible feature passes only when its roles reviewed it, and no builder grades its own visible work. A judgment fails a verdict item only through an anchor you set: a calibration label, a reference you chose, or a page rule. Each role keeps what you taught it in `docs/game/roles/<role>.md`.

**Research.** Market numbers never come from memory. A landscape scan before ideation finds comparable games, the genre's anchors and defaults, player complaints and candidate references. After ideation, one session per reference studies it, each role from its own angle, into dossiers that `creative` audits. What the agent can't do (play a game, watch a stream, see a store page it can't reach) becomes a short, ranked homework list for you, and brainstorm waits for your answers. Every number carries its link and retrieval date; one nobody fetched reads `not researched`.

**The person's moments.** Conversations: setup, ideation, research homework and brainstorm topics. Three short waits, in either mode: **calibration** (you label 8-12 captures "ours" or "not ours" with a reason, once the visual target exists; builds go on meanwhile, and the slice, full and final verdicts wait), the **slice playtest**, and **A/B picks** in polish (the run waits for them before the final verdict). Calibration is what lets the roles' taste judgments count.

**Living documents.** The **wiki** is for agents: the current truth about the game, precise enough to build and test from, with ADRs for why things changed. Its pages live in a docs place next to your tasks (for example ClickUp Docs beside the task list), so you can read and comment on them there; `docs/game/wiki.json` in the repo indexes them, and `docs/game/vision.json` holds the vision's facts. If you chose local files instead, the pages are in `docs/game/wiki/`. Every session that changes what the game is updates its page in the same step, and any design question a later phase hits becomes a topic. People comment on wiki pages and sessions edit them; if you edit a page by hand, `game-gdd` flags it and the next session checks it. The **GDD** is for people and lives in the same place. `game-gdd` rewrites it from the wiki before each phase or milestone moves on. Your comments and edits there come back as topics.

**Setup is a conversation.** `game-setup` asks where your tasks live, choosing an existing home or creating one, picks the docs place, and runs a smoke test that writes and reads back a page. It creates the wiki and GDD skeletons, and it can't finish until that test passes (`docs_verified` in `state.json`).

**The state tool decides.** `docs/game/gamestate.py` owns every transition:
- It re-plans after an adjust and re-ideates after a restart.
- It rebuilds regressions before anything is judged, and brainstorms the topics a feature waits on before building it.
- It syncs the GDD when the wiki changed, reopens a verdict when playtest answers arrive, and commits its own bookkeeping.

**Context per session.** Each session does one step, reads only what that step names, splits work that outgrows it, and ends with a commit and a short report. All state is on disk, so nothing depends on an earlier conversation.

**Honest evidence.** Every verdict score is pass or fail with an evidence file, "not assessed" with the reason it couldn't be measured, or waiting for a person; the state tool refuses a ship otherwise. What a playtest or a comment says to keep is pinned in `keep.json`, and the check holds those tuning values unless an ADR changes them. Every player-visible choice an agent makes that no page specified goes on the AI's own-calls list in the GDD.

**The definition of done.** `docs/game/features.json` lists every feature with its pillar, tier, milestone, the wiki pages it implements, acceptance criteria and a verify method. A feature passes only with evidence from a run. Once planning is over, features can be cut but not deleted, and acceptance can't be edited. After consolidate, the fun checklist and richness targets can rise but not drop. `gamestate.py check` enforces all of this.

**Testing a game without a person.** Projects separate a deterministic **simulation core** (fixed tick, seeded RNG, input as data) from a thin **presentation shell**. Tests, headless `sim` runs, input `replay`s and `bot` policies drive the core; `capture` renders screenshots. Fun proxies (lead changes, dominant-strategy win rates, decisions per minute) and richness targets (each system toggled off must shift outcomes) turn "fun and rich" into numbers. Human playtest kits cover what numbers can't.

**Limits.** Budget, brainstorm share, adjusts, restarts, per-feature attempts and repeated steps stop the run for you instead of letting it loop.

## Install

### Claude Code

```
/plugin marketplace add NotFluffyGames/GameDirector
/plugin install game-director@notfluffygames
```

Recommended companions, which the skills call when present:

```
/plugin marketplace add mattpocock/skills
/plugin install mattpocock-skills@mattpocock
```

### Other agents

Copy the folders under `skills/` into your agent's skills directory, keeping them side by side. Each skill also carries `agents/openai.yaml` metadata.

### Requirements

- git, and Python 3.8+ for `gamestate.py` (standard library only)
- an agent harness that can run shell commands
- whatever the chosen engine needs, installed by the adapter's `bootstrap` command
- for research, these hosts (setup probes them and records `research_sources`; any HTTP status counts as reachable, only no response or a proxy refusal as unreachable, and what research loses without one becomes homework): `store.steampowered.com`, `api.steampowered.com`, `steamspy.com`, `itch.io`
- Claude Code, for the role agents: without them no slice, full or final verdict can ship (see Known limits)

## Use

| You want | Run |
| --- | --- |
| to start a game | `/game-next <idea>` (add `--interactive` to approve tickets and decide verdicts too) |
| the next step | `/game-next`, in a fresh session |
| steps that need no person to run back to back | `AGENT_CMD='claude -p' <plugin folder>/skills/game-next/scripts/loop.sh`, from the game repo (see `skills/game-next/unattended.md`) |
| to bring a game set up with an older version up to date | `/game-next` notices and runs `game-setup upgrade` with you while the game is still at setup (updates `gamestate.py` and state to schema version 7, and sets up the docs place if the game has none); a game mid-run on an older version stops instead, since mid-run upgrades aren't supported. An upgraded game keeps its old Commands table until `game-setup` adapter mode runs at plan's walking skeleton, so it has no `dump` or `loudness` rows until then |
| a specific phase by hand | `/game-research ref R1`, `/game-ideation`, `/game-brainstorm T014`, `/game-consolidate`, `/game-gdd`, `/game-plan`, `/game-build F012`, `/game-review feature F012`, `/game-verdict full`, `/game-polish` |

The game repo ends up with:
- `docs/agents/game.md`: config, session rules, vocabulary, adapter commands, companion-skill fallbacks.
- `docs/agents/docs.md`: where the wiki and GDD live, and how to read, write and comment there.
- `docs/game/`: the seed idea, the research (`research/`) and role memory (`roles/`), the reviews (`reviews/`), your calibration labels (`calibration/`), the wiki index (`wiki.json`), the vision facts (`vision.json`), the topic tree, fun checklist, richness targets, definition of done, state, progress log, assets and playtests.
- ADRs.

Edit any of them; the skills read them fresh every session.

## Why it is built this way

- **Long-running agent work**: one step per fresh session, a JSON feature list as the definition of done, progress log plus git as memory ([Anthropic: effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents); [Ralph](https://github.com/snarktank/ralph)).
- **Engineering discipline**: alignment by grilling, decisions broken into a tree of one-session questions, tracer-bullet tickets with blocking edges, TDD, code review, per-repo tracker config ([mattpocock/skills](https://github.com/mattpocock/skills)).
- **Game production**: playable prototypes over long design docs (Lee Perry, *Prototyping Based Design*, GDC); a vertical-slice gate before production (Greg Donovan, *The Vertical Slice Challenge*, GDC); functional-but-ugly modular content (Burgess and Purkeypile, *Modular Level Design for Skyrim*, GDC 2013); tech and netcode decided early (Kratochvil, *Rebuilding Your Engine During Development*, GDC 2018); a vision locked early so pre-production converges (Kotaku's reporting on Anthem and Destiny).
- **Building blocks over ceremony**: headless capture and engine knowledge kept behind per-project adapters ([Godogen](https://github.com/htdt/godogen)).

## Known limits

- Proxy metrics catch a game that clearly isn't fun; they don't prove one is. Playtest answers reopen the verdict, which can still send the game back to adjust or restart.
- Every step that needs you stops an unattended loop: ideation, research homework, brainstorm topics, calibration, the slice playtest and A/B picks. The scan runs unattended right after setup.
- Audio is never heard. The audio role judges the event log and loudness numbers against the audio page; how it sounds is your call.
- Taste judgments (creative, art, feel, ux) stay provisional, scored not-assessed, until your calibration labels exist.
- The role agents are Claude Code-only: outside Claude Code they can't run. The session then runs each role itself, from the role skill's path, and marks its reviews not independent, so verdicts score every review item not-assessed. No review item can pass, so the slice, full and final verdicts can't ship (nor the core-loop verdict, when the checklist gives it a review item).
- Research needs the hosts above; a source this machine can't reach becomes homework, not a guess.
- Engines whose gameplay can't leave the editor give weaker determinism; the adapter contract's fallbacks trade exact hashes for tolerances.
- Platforms the machine can't build for (consoles, signed mobile builds) are reported, not built.
- Every session that reads wiki pages needs the tracker's docs connector (for example ClickUp's) connected; without it, choose local files at setup.
- Nothing has been measured yet: these skills have not been run end to end on a real game.

## Develop

```
python3 tests/run.py
```

That runs all tests in parallel (`-j N` sets the bucket count, extra arguments filter test ids by substring); `python3 -m unittest discover tests` runs them serially.

Both must pass.

`tests/test_skills.py` checks the skills themselves: packaging, links, a completion criterion on every step, real tool commands, and a skill for every step and mode the state tool can schedule. Edit skills following the `writing-for-agents` skill. The state schemas (`state.json`, `features.json`, `fun-checklist.json`, `richness.json`, `topics.json`, `keep.json`, `wiki.json`, `vision.json`, `research/references.json`, `research/homework.json`, the review records under `reviews/` and `calibration/labels.json`) live in two places that must agree: `skills/game-setup/game.md` plus the templates, and `skills/game-setup/scripts/gamestate.py`.
