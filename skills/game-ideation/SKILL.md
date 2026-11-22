---
name: game-ideation
description: With the user, turn a raw, high-level game idea into a vision - pitch, audience, pillars, core loop, target feeling, tone and scope - by grilling them, comparing distinct directions and letting them choose, then seed the wiki and the brainstorm topic tree. Phase 1 of the game-* workflow; also re-runs after a restart verdict.
disable-model-invocation: true
---

# Game Ideation

Formulates the **vision** with the user: what the game is, who it is for and why it will be fun, before any detail is designed. This is a conversation, whatever the autonomy mode: it runs in the session the user started, never in a subagent or an unattended loop. It writes the first wiki pages and topics; game-gdd then turns them into the human GDD. Read `docs/agents/game.md` first and follow its session rules.

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

Write `docs/game/wiki/vision.md` from [vision-template.md](vision-template.md), and `docs/game/wiki/index.md` from [index-template.md](index-template.md) with the Vision section filled in. Read the pitch, pillars and core loop back to the user and fix what they correct.

**Done when** the user accepts the vision: a one-page pitch, a one-sentence core loop, and 3–4 pillars, each able to reject a feature.

## 5. Seed the topic tree

In `docs/game/topics.json`, record the root topic `T1` ("the game", resolved by the vision, pages `["wiki/vision.md"]`), then break it into first-level topics with [topic-map.md](topic-map.md): one per area this game needs, each with a question, priority and the page it will write. Publish each as a ticket in the tracker (`docs/agents/issue-tracker.md`, `ready-for-human`: a person brainstorms it), and record the ticket on the topic. Show the user the list; add, drop or reprioritise as they say.

On a restart, reopen the topics whose pages the restart ADR invalidates, and open new ones where the vision changed.

**Done when** `python3 docs/game/gamestate.py gate` passes.

## 6. Name things

With the `domain-modeling` skill, add the game's own nouns from the vision to `CONTEXT.md`.

## 7. Close

`gamestate.py check --since <base>`, commit, progress entry, `gamestate.py complete`.
