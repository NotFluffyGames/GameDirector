---
name: game-brainstorm
description: Turn a raw game idea into 3-5 distinct concepts, prototype the most promising core loops with bots to find the fun, and choose one on evidence. Phase 1 of the game-* workflow; also re-runs after a restart verdict.
disable-model-invocation: true
---

# Game Brainstorm

**Diverge, test, converge.** The raw idea becomes several real options; the strongest core loops get played by bots in throwaway prototypes; one concept is chosen on evidence. Read `docs/agents/game.md` first and follow its session rules.

Everything this phase decides goes in `docs/game/concepts.md`, laid out as [concepts-template.md](concepts-template.md). When the phase spans sessions, resume at the first step whose result concepts.md doesn't hold yet.

## 1. Read the seed

Read `docs/game/seed.md`. On a `restart <adr>` task, also read that ADR's lessons and the old concepts.md: runner-up concepts are candidates again; the failed concept is one only if the lessons name a fix.

**Done when** you can say what the seed fixes (what must stay true of the game) and what it leaves open.

## 2. Diverge

Write 3–5 concepts that differ in their core loop, not only in theme. Ways to get real distance from the seed:

- change the core verb, or the player count and mode;
- change time: real-time against turn-based, short sessions against long runs;
- cross the seed with a reference game from a different genre;
- invert one of the seed's assumptions.

Each concept gets a hook, core verb, core loop, target feeling, reference games, its richness sources and its biggest risk (the template's fields). In interactive mode, the user may add or veto concepts, through the questions protocol when you can't reach them.

**Done when** 3–5 concepts are written and no two share a core loop.

## 3. Score

Score each concept 1–5, with a one-line reason per score:

- **Fun potential**: does the loop pose a real decision or skill test every few seconds or turns?
- **Richness potential**: depth from systems that change each other, breadth from content built from reusable parts, variety between runs.
- **Fit to the seed**.
- **Agent-buildable**: can its rules run headless and deterministically, so bots and tests can judge it?
- **Risk** (5 = least risky).

**Done when** every concept has every score.

## 4. Prototype the top loops

Prototype the top two concepts (three when scores are close). For each, with the `prototype` skill, build a throwaway **rules simulation** of the core loop: rules only, no art, in whatever language is quickest on this machine, outside the game's source tree (for example `.scratch/prototypes/<concept>/`). Give it at least two bot policies (random and greedy) and run at least 30 seeded games. Measure:

- decision density: decisions per minute or turn with more than one viable option;
- skill: greedy's win or score rate against random;
- dominance: how often the single most-used action is the best one;
- endings: how sessions end and how long they last.

Rules simulations can't show real-time feel; record that as an open risk for the core-loop verdict. Record the numbers under `## Prototypes`, then delete the prototype code: the numbers are what lasts.

**Done when** each prototyped concept has a number for every measure.

## 5. Choose

Pick the concept with the best evidence: prototype numbers first, scores second. In interactive mode the user chooses, given your recommendation. Under `## Choice`, write the concept id, why it won, what the prototype showed, what is still unproven, and any ideas worth borrowing from the others.

**Done when** Choice names one concept and its evidence.

## 6. Close

`gamestate.py check --since <base>`, commit, progress entry, `gamestate.py complete`. Reply with the chosen concept's hook and core loop, its prototype headline numbers, and the runner-up.
