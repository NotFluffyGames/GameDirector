# GameDirector

Agent skills that take a raw game idea to a **fun, playable, rich, working, testable and tested game** in one prompt:

```
/game-director a two-player couch brawler where you steal each other's weapons
```

A thin **director** drives seven phase skills, one fresh session per task, until the final verdict ships or only work a person must do remains. Nothing in the skills names an engine, genre, platform, repo or task manager: each project records those once, in config the skills read. Publishing is out of scope: the run ends with a game you can play, backed by evidence.

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
setup → brainstorm → design → plan → build: core-loop → verdict: core-loop → build: systems, content, verdict-build
      → verdict: full → polish → verdict: final → done

any verdict: adjust → plan (then back through build and the verdicts not yet passed)
             restart → brainstorm (old definition of done archived)
```

| Skill | Phase | Produces | Leans on |
| --- | --- | --- | --- |
| `game-director` | all | runs the loop below | — |
| `game-setup` | setup | `docs/agents/game.md` config, state files, verified adapter commands | `research` |
| `game-brainstorm` | brainstorm | 3–5 concepts, scored, the top loops prototyped with bots, one chosen | `prototype`, `grilling` |
| `game-design` | design | the game definition (mechanics, controls, systems, content, modes, screens, feel, art), fun checklist, richness targets | `grilling`, `domain-modeling` |
| `game-plan` | plan | tech ADRs, walking skeleton, `features.json`, tickets | `domain-modeling`, `codebase-design`, `research` |
| `game-build` | build | one feature built, verified, reviewed and committed | `tdd`, `prototype`, `diagnosing-bugs`, `code-review` |
| `game-verdict` | verdict | fun and richness scores from bots and replays, playtest kit, ship/adjust/restart ADR | — |
| `game-polish` | polish | feel, final art and audio, balance, performance, accessibility and packaged-build features | — |

**The loop.** `docs/game/gamestate.py status` prints the next action. The director dispatches it to a fresh subagent, checks the result with the tool, and advances. Phase work never happens in the director, so its context grows by one short reply per task. The tool owns every transition: it re-plans after an adjust, re-brainstorms after a restart, sends regressions in earlier milestones back to build before anything is judged, reopens a verdict when playtest answers arrive, and commits its own bookkeeping so a reset never loses it.

**Context per session.** Each session does one task (one feature, one verdict, one planning step), reads only what that task names, splits work that outgrows it into new tickets, and ends with a commit, a progress entry and a 150-word reply. All state is on disk, so any session, and the director itself, can stop and resume.

**Definition of done.** `docs/game/features.json` lists every feature with a pillar, scope tier, milestone, acceptance criteria and a verify method. A feature passes only with evidence from a run. Outside planning, items can be cut but not deleted, and acceptance can't be edited; `gamestate.py check` enforces this against the session's starting commit. Gates and phase transitions are code, not judgement.

**From raw idea to definition.** Brainstorm widens the idea into 3–5 concepts that differ in their core loop, scores them, and plays the top loops with bots in throwaway rules prototypes before choosing one. Design then writes the complete game definition, so planning turns design into features instead of inventing it.

**Testing a game without a person.** Projects separate a deterministic **simulation core** (fixed tick, seeded RNG, input as data) from a thin **presentation shell**. Tests, headless `sim` runs, input `replay`s and `bot` policies drive the core; `capture` renders screenshots for visual checks. The fun checklist turns "is it fun?" into proxy metrics (lead changes, dominant-strategy win rates, decisions per minute) plus items left for human playtesters; richness targets measure depth by toggling each system off and watching outcomes shift.

**People stay in the loop where it counts.** Work only a person can do goes to a human queue; the run carries on past it and stops at the end. Playtest kits don't stop it: the run ends with the kit ready, and your answers reopen the verdict. `--interactive` also asks you to pick the concept, and at the design tree, the ticket breakdown and each verdict. Limits on budget, adjusts, restarts, per-feature attempts and repeated identical dispatches stop the run for a human instead of letting it loop.

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
| to pick the concept and be consulted on design, tickets and verdicts | `/game-director <idea> --interactive` |
| to resume after clearing the human queue or raising a limit | `/game-director` |
| one step at a time | `/game-director --step` |
| a single phase by hand | `/game-setup`, `/game-brainstorm`, `/game-design`, `/game-plan`, `/game-build F012`, `/game-verdict full`, `/game-polish` |

The game repo ends up with `docs/agents/game.md` (config: autonomy, session rules, vocabulary, adapter commands, companion-skill fallbacks), `docs/game/` (seed, concepts, game definition, fun checklist, richness targets, definition of done, state, progress log, assets, playtests) and ADRs. Edit any of them; the skills read them fresh every session.

## Why it is built this way

- **Long-running agent work**: one feature per fresh session, a JSON feature list as the definition of done, progress log plus git as memory ([Anthropic: effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents); [Ralph](https://github.com/snarktank/ralph)).
- **Engineering discipline**: alignment by grilling, tracer-bullet tickets with blocking edges, TDD, two-axis code review, per-repo tracker config ([mattpocock/skills](https://github.com/mattpocock/skills)).
- **Game production**: playable prototypes over long design docs (Lee Perry, *Prototyping Based Design*, GDC); a vertical-slice gate before production (Greg Donovan, *The Vertical Slice Challenge*, GDC); functional-but-ugly modular content (Burgess and Purkeypile, *Modular Level Design for Skyrim*, GDC 2013); tech and netcode decided early (Kratochvil, *Rebuilding Your Engine During Development*, GDC 2018); pillars locked early to avoid pre-production that never converges (Kotaku's reporting on Anthem and Destiny).
- **Building blocks over ceremony**: headless capture and engine knowledge kept behind per-project adapters ([Godogen](https://github.com/htdt/godogen)).

## Known limits

- Proxy metrics catch a game that clearly isn't fun; they don't prove one is. In an autonomous run, human playtest answers arrive after the run has moved on; they reopen the verdict, which can still send the game back to adjust or restart.
- Engines whose gameplay can't leave the editor give weaker determinism; the adapter contract's fallbacks trade exact hashes for tolerances.
- Platforms the machine can't build for (consoles, signed mobile builds) are reported, not built.
- `--interactive` needs the director running in a live conversation; the external loop runs autonomous.
- Nothing has been measured yet: these skills have not been run end to end on a real game.

## Develop

```
python3 -m unittest discover tests
```

Edit skills following the `writing-for-agents` skill. The state schemas (`features.json`, `fun-checklist.json`, `richness.json`, the design and concepts headings) live in two places that must agree: `skills/game-setup/game.md` plus the templates, and `skills/game-setup/scripts/gamestate.py`.
