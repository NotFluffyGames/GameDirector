# GameDirector

Agent skills that take a raw game idea to a **fun, playable, rich, working, testable and tested game**, over many sessions:

```
/game-next a two-player couch brawler where you steal each other's weapons
```

Every session does **one step** and stops: run `/game-next` in a fresh session and it asks the state tool what comes next, does that step with you or on its own, checks it, and tells you what the next session will do. Shaping the idea is always a conversation with you; building, judging and polishing can run unattended. Nothing in the skills names an engine, genre, platform, repo or task manager: each project records those once, in config the skills read. Publishing is out of scope: the run ends with a game you can play, backed by evidence, and documents that describe it.

## The goal

| Quality | Checked by |
| --- | --- |
| Playable | the packaged build launches without dev tools and plays from title screen to the end of a session, on every target platform the machine can build for |
| Working | every `must` feature passes; a long crash and softlock fuzz run is clean |
| Tested | tests, replays and bot runs cover the core rules and every feature, green on the final build |
| Testable | a deterministic simulation core, and adapter commands that re-run every check |
| Rich | richness targets for depth (systems that change each other), breadth (distinct content) and variety (playthroughs that differ) pass on the final build |
| Fun | every fun proxy passes on the final build, and a playtest kit is ready; people's answers can still reopen the verdict |

## How it works

```
setup → ideation → brainstorm (one topic per session) → consolidate → plan → build: core-loop
      → verdict: core-loop → build: systems, content, verdict-build → verdict: full → polish → verdict: final → done

any verdict: adjust → plan     restart → ideation
any phase:   an unanswered design question → a brainstorm topic, with you
```

| Skill | Step | Produces | With you? | Leans on |
| --- | --- | --- | --- | --- |
| `game-next` | every session | runs the next step, checks it, reports what's next | — | — |
| `game-setup` | first session | `docs/agents/game.md` and `human-docs.md` config, state files, verified engine commands | decisions | `research` |
| `game-ideation` | vision | vision and directions considered in the wiki, the first topics | always | `grilling`, `domain-modeling` |
| `game-brainstorm` | one topic | the topic's wiki pages, follow-up topics | always | `grilling`, `research` |
| `game-consolidate` | after brainstorm | a complete, consistent wiki; the fun checklist and richness targets | interactive mode | — |
| `game-gdd` | whenever the wiki changed | the human GDD, next to your tasks, in sync with the wiki | — | — |
| `game-plan` | plan | tech ADRs, walking skeleton, `features.json`, tickets | interactive mode | `codebase-design`, `domain-modeling`, `research` |
| `game-build` | one feature | built, verified, reviewed and committed | — | `tdd`, `diagnosing-bugs`, `code-review` |
| `game-verdict` | three gates | fun and richness scores from bots and replays, playtest kit, ship/adjust/restart ADR | interactive mode | — |
| `game-polish` | polish | feel, final art and audio, balance, performance, accessibility and packaged-build features | — | — |

**Ideation and brainstorming, with you.** Ideation grills you on the raw idea, compares 3–5 directions that play differently, lets you choose, and writes the vision. It then breaks "the game" into first-level topics. Each brainstorm session takes one topic, grills you on it, and challenges every answer hard against the vision, the rest of the wiki, how it plays and what it costs. It then writes or updates the topic's pages and opens the follow-up topics the conversation raised. The tree grows until every topic is answered precisely enough to plan features and write tests from.

**Living documents.** The **wiki** (`docs/game/wiki/`) is for agents: the current truth about the game, precise enough to build and test from, with ADRs for why things changed. Every session that changes what the game is updates its page in the same commit, and any design question a later phase hits becomes a topic. The **GDD** is for people and lives next to your tasks (for example a ClickUp Doc beside the task list). `game-gdd` rewrites it from the wiki before each phase or milestone moves on. Your comments and edits there come back as topics.

**The state tool decides.** `docs/game/gamestate.py` owns every transition:
- It re-plans after an adjust and re-ideates after a restart.
- It rebuilds regressions before anything is judged, and brainstorms the topics a feature waits on before building it.
- It syncs the GDD when the wiki changed, reopens a verdict when playtest answers arrive, and commits its own bookkeeping.

**Context per session.** Each session does one step, reads only what that step names, splits work that outgrows it, and ends with a commit and a short report. All state is on disk, so nothing depends on an earlier conversation.

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

## Use

| You want | Run |
| --- | --- |
| to start a game | `/game-next <idea>` (add `--interactive` to approve tickets and decide verdicts too) |
| the next step | `/game-next`, in a fresh session |
| steps that need no person to run back to back | `AGENT_CMD='claude -p' skills/game-next/scripts/loop.sh` (see `skills/game-next/unattended.md`) |
| a specific phase by hand | `/game-ideation`, `/game-brainstorm T014`, `/game-consolidate`, `/game-gdd`, `/game-plan`, `/game-build F012`, `/game-verdict full`, `/game-polish` |

The game repo ends up with:
- `docs/agents/game.md`: config, session rules, vocabulary, adapter commands, companion-skill fallbacks.
- `docs/agents/human-docs.md`: where the GDD lives.
- `docs/game/`: the seed idea, the wiki, the topic tree, fun checklist, richness targets, definition of done, state, progress log, assets and playtests.
- ADRs.

Edit any of them; the skills read them fresh every session.

## Why it is built this way

- **Long-running agent work**: one step per fresh session, a JSON feature list as the definition of done, progress log plus git as memory ([Anthropic: effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents); [Ralph](https://github.com/snarktank/ralph)).
- **Engineering discipline**: alignment by grilling, decisions broken into a tree of one-session questions, tracer-bullet tickets with blocking edges, TDD, code review, per-repo tracker config ([mattpocock/skills](https://github.com/mattpocock/skills)).
- **Game production**: playable prototypes over long design docs (Lee Perry, *Prototyping Based Design*, GDC); a vertical-slice gate before production (Greg Donovan, *The Vertical Slice Challenge*, GDC); functional-but-ugly modular content (Burgess and Purkeypile, *Modular Level Design for Skyrim*, GDC 2013); tech and netcode decided early (Kratochvil, *Rebuilding Your Engine During Development*, GDC 2018); a vision locked early so pre-production converges (Kotaku's reporting on Anthem and Destiny).
- **Building blocks over ceremony**: headless capture and engine knowledge kept behind per-project adapters ([Godogen](https://github.com/htdt/godogen)).

## Known limits

- Proxy metrics catch a game that clearly isn't fun; they don't prove one is. Playtest answers reopen the verdict, which can still send the game back to adjust or restart.
- Ideation and brainstorming need you in the session; an unattended loop stops at them.
- Engines whose gameplay can't leave the editor give weaker determinism; the adapter contract's fallbacks trade exact hashes for tolerances.
- Platforms the machine can't build for (consoles, signed mobile builds) are reported, not built.
- Nothing has been measured yet: these skills have not been run end to end on a real game.

## Develop

```
python3 -m unittest discover tests
```

Edit skills following the `writing-for-agents` skill. The state schemas (`features.json`, `fun-checklist.json`, `richness.json`, `topics.json`, the vision, directions and index headings) live in two places that must agree: `skills/game-setup/game.md` plus the templates, and `skills/game-setup/scripts/gamestate.py`.
