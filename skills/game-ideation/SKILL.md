---
name: game-ideation
description: With the user, turn a raw, high-level game idea into a vision (pitch, pillars, anti-pillars, core loop, target feeling, scope, kill condition) and a vertical slice definition, by grilling them, comparing distinct directions and letting them choose; then seed the wiki and the brainstorm topic tree. Phase 1 of the game-* workflow; also re-runs after a restart.
disable-model-invocation: true
---

# Game Ideation

Formulates the **vision** with the user (what the game is, who it is for, why it will be fun, what it will never be) and defines the **vertical slice**: the small part of the game built first, to the quality bar the user sets, to prove the game before production. Nothing is designed in detail yet. This is a conversation, whatever the autonomy mode: it runs in the session the user started, never in a subagent or an unattended loop. It writes the first wiki pages and topics; game-gdd then turns them into the human GDD. Read `docs/agents/game.md` first and follow its session rules.

## 1. Read the seed

Read `docs/game/seed.md`. On a `restart <adr>` task, also read that ADR's lessons and the current wiki: they tell you which parts of the vision failed.

**Done when** you can say what the seed fixes (what must stay true of the game) and what it leaves open.

## 2. Grill the vision

With the `grilling` skill, interview the user one question at a time down the vision's design tree: audience, platforms and input, player count, session length, the feeling a session should leave, must-haves, no-gos, scope. Give your recommended answer with each question. Be **ruthless**: push on vague answers until they are concrete, name contradictions between answers, and ask what the game gives up for each thing it wants.

**Done when** every branch has a concrete answer from the user and none is "TBD".

## 3. Compare directions

Write 3–5 **directions** into `docs/game/wiki/concepts.md`, laid out as [concepts-template.md](concepts-template.md). They differ in the core loop, not only in theme. Ways to get distance from the seed:

- change the core verb, or the player count and mode;
- change time: real-time against turn-based, short sessions against long runs;
- cross the seed with a reference game from a different genre;
- invert one of the seed's assumptions.

Score each on fun potential, richness potential, fit to the user's answers, how well an agent can build and test it, and risk. Present them with your recommendation and challenge the user's favourite as hard as the others. The user chooses. Record the choice, its reasons and the ideas worth borrowing from the others under `## Choice`.

**Done when** concepts.md has 3–5 scored directions and the user's choice.

## 4. Write the vision

Write `docs/game/wiki/vision.md` from [vision-template.md](vision-template.md). Grill the user for the **anti-pillars** (what the game will never do, and which pillar each protects) and the **kill condition** (the playtest result that would stop the game as conceived). Read the pitch, pillars, anti-pillars and core loop back to the user and fix what they correct.

**Done when** the user accepts the vision: a one-page pitch, a one-sentence core loop, 3–4 pillars each able to reject a feature, at least one anti-pillar, and a kill condition a playtest can meet or not.

## 5. Define the vertical slice

With the user, write `docs/game/wiki/slice.md` from [slice-template.md](slice-template.md):

- **What it proves**: a test question the slice can fail, and the risks it retires.
- **In and out**: the part of the game it covers, the systems and content it needs, and what it leaves out. Keep it the smallest slice that delivers one complete start → challenge → resolution and the target feeling.
- **Quality bar**: for each aspect (code, feel, art, audio, UI, onboarding), ask the user for `placeholder`, `representative` or `final`, recommending representative unless that aspect is a risk the slice must retire.
- **Playtest**: who plays it and what counts as a pass. The slice verdict waits for this playtest.

**Done when** the user accepts slice.md, and every system and content type it names is in the slice's In list or its Out list.

## 6. Seed the topic tree

Write `docs/game/wiki/index.md` from [index-template.md](index-template.md) with the Vision section filled in. In `docs/game/topics.json`, record the root topic `T1` ("the game", resolved by the vision, pages `["wiki/vision.md", "wiki/slice.md"]`), then break it into first-level topics with [topic-map.md](topic-map.md): one per area this game needs, each with a question, priority, the page it will write, and its **stage**: `slice` when the vertical slice needs it answered, otherwise `production`. Brainstorm takes slice topics first; production topics wait until the slice ships. Publish each as a ticket in the tracker (`docs/agents/issue-tracker.md`, `ready-for-human`: a person brainstorms it), and record the ticket on the topic. Show the user the list; add, drop or reprioritise as they say.

On a restart, reopen the topics whose pages the restart ADR invalidates, and open new ones where the vision changed.

**Done when** `python3 docs/game/gamestate.py gate` passes.

## 7. Name things

With the `domain-modeling` skill, add the game's own nouns from the vision and the slice to `CONTEXT.md`.

**Done when** every noun the vision and slice use is in `CONTEXT.md`.

## 8. Close

`gamestate.py check --since <base>`, commit, progress entry, `gamestate.py complete`.

**Done when** `complete` succeeds.
