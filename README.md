# GameDirector

Agent skills that take a game from an idea to a release candidate in one prompt:

```
/game-director a two-player couch brawler where you steal each other's weapons
```

A thin **director** drives six phase skills, one fresh session per task, until a machine-checked definition of done passes or only work a person must do remains. Nothing in the skills names an engine, genre, platform, repo or task manager: each project records those once, in config the skills read.

## How it works

```
setup ──► ideate ──► plan ──► build: core-loop ──► verdict (core-loop) ──► build: systems, content, verdict-build ──► verdict (full) ──► release: polish, release ──► done
              ▲         ▲                                 │                                                         │
              │         └──────── adjust ─────────────────┴─────────────────────────────────────────────────────────┤
              └────────────────── restart ──────────────────────────────────────────────────────────────────────────┘
```

| Skill | Phase | Produces | Leans on |
| --- | --- | --- | --- |
| `game-director` | all | runs the loop below | — |
| `game-setup` | setup | `docs/agents/game.md` config, state files, verified adapter commands | `research` |
| `game-ideate` | ideate | pitch, pillars, core loop, tone/art/world, fun checklist | `grilling`, `domain-modeling` |
| `game-plan` | plan | tech ADRs, walking skeleton, `features.json`, tickets | `domain-modeling`, `codebase-design`, `research` |
| `game-build` | build | one feature built, verified, reviewed and committed | `tdd`, `prototype`, `diagnosing-bugs`, `code-review` |
| `game-verdict` | verdict | bot/replay scores, playtest kit, ship/adjust/restart ADR | — |
| `game-release` | release | polish and release features, release wizard | `wizard` |

**The loop.** `docs/game/gamestate.py status` prints the next action. The director dispatches it to a fresh subagent, checks the result with the tool, and advances. Phase work never happens in the director, so its context grows by one short reply per task. The tool owns every transition: it re-plans after an adjust, re-ideates after a restart, sends regressions in earlier milestones back to build before anything is judged, reopens a verdict when playtest answers arrive, and commits its own bookkeeping so a reset never loses it.

**Context per session.** Each session does one task (one feature, one verdict, one planning step), reads only what that task names, splits work that outgrows it into new tickets, and ends with a commit, a progress entry and a 150-word reply. All state is on disk, so any session, and the director itself, can stop and resume.

**Definition of done.** `docs/game/features.json` lists every feature with a pillar, scope tier, milestone, acceptance criteria and a verify method. A feature passes only with evidence from a run. Outside planning, items can be cut but not deleted, and acceptance can't be edited; `gamestate.py check` enforces this against the session's starting commit. Gates and phase transitions are code, not judgement.

**Testing a game without a person.** Projects separate a deterministic **simulation core** (fixed tick, seeded RNG, input as data) from a thin **presentation shell**. Tests, headless `sim` runs, input `replay`s and `bot` policies drive the core; `capture` renders screenshots for visual checks. The fun checklist turns "is it fun?" into proxy metrics (lead changes, dominant-strategy win rates, decisions per minute) plus items left for human playtesters.

**People stay in the loop where it counts.** Work only a person can do (playtests, store accounts, signing keys, submissions) goes to a human queue, with a playtest kit or a step-by-step wizard. The run carries on past it and stops at the end. `--interactive` also asks you at the design tree, the ticket breakdown and each verdict. Limits on budget, adjusts, restarts, per-feature attempts and repeated identical dispatches stop the run for a human instead of letting it loop.

## Install

### Claude Code

```
/plugin marketplace add NotFluffyGames/GameDirector
/plugin install game-director@notfluffygames
```

Recommended companions, which the phase skills call when present:

```
/plugin marketplace add mattpocock/skills
/plugin install mattpocock-skills@mattpocock
```

### Other agents

Copy the folders under `skills/` into your agent's skills directory, keeping them side by side. Each skill also carries `agents/openai.yaml` metadata. Without subagents, run the director one step per process with `skills/game-director/scripts/loop.sh` (see `skills/game-director/loop-modes.md`).

### Requirements

- git, and Python 3.8+ for `gamestate.py` (standard library only)
- an agent harness that can run shell commands; subagents recommended
- whatever the chosen engine needs, installed by the adapter's `bootstrap` command

## Use

| You want | Run |
| --- | --- |
| a whole game, hands off | `/game-director <idea>` |
| to be consulted on design, tickets and verdicts | `/game-director <idea> --interactive` |
| to resume after clearing the human queue or raising a limit | `/game-director` |
| one step at a time | `/game-director --step` |
| a single phase by hand | `/game-setup`, `/game-ideate`, `/game-plan`, `/game-build F012`, `/game-verdict full`, `/game-release` |

The game repo ends up with `docs/agents/game.md` (config: autonomy, session rules, vocabulary, adapter commands, companion-skill fallbacks), `docs/game/` (design, fun checklist, definition of done, state, progress log, assets, playtests) and ADRs. Edit any of them; the skills read them fresh every session.

## Why it is built this way

- **Long-running agent work**: one feature per fresh session, a JSON feature list as the definition of done, progress log plus git as memory ([Anthropic: effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents); [Ralph](https://github.com/snarktank/ralph)).
- **Engineering discipline**: alignment by grilling, tracer-bullet tickets with blocking edges, TDD, two-axis code review, per-repo tracker config ([mattpocock/skills](https://github.com/mattpocock/skills)).
- **Game production**: playable prototypes over long design docs (Lee Perry, *Prototyping Based Design*, GDC); a vertical-slice gate before production (Greg Donovan, *The Vertical Slice Challenge*, GDC); functional-but-ugly modular content (Burgess and Purkeypile, *Modular Level Design for Skyrim*, GDC 2013); tech and netcode decided early (Kratochvil, *Rebuilding Your Engine During Development*, GDC 2018); pillars locked early to avoid pre-production that never converges (Kotaku's reporting on Anthem and Destiny).
- **Building blocks over ceremony**: headless capture and engine knowledge kept behind per-project adapters ([Godogen](https://github.com/htdt/godogen)).

## Known limits

- Proxy metrics catch a game that clearly isn't fun; they don't prove one is. In an autonomous run, human playtest answers arrive after the run has moved on; they reopen the verdict, which can still send the game back to adjust or restart.
- Engines whose gameplay can't leave the editor give weaker determinism; the adapter contract's fallbacks trade exact hashes for tolerances.
- Store submission, certification and anything needing your accounts always ends in the human queue.
- `--interactive` needs the director running in a live conversation; the external loop runs autonomous.
- Nothing has been measured yet: these skills have not been run end to end on a real game.

## Develop

```
python3 -m unittest discover tests
```

Edit skills following the `writing-for-agents` skill. The `features.json` schema lives in two places that must agree: `skills/game-setup/game.md` and `skills/game-setup/scripts/gamestate.py`.
