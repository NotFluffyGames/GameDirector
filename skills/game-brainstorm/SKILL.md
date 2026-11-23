---
name: game-brainstorm
description: With the user, take one open design topic from the game's topic tree, grill them on it, ruthlessly challenge the idea against the vision, then write or update its wiki pages in the docs place and open the follow-up topics it raises. Phase 2 of the game-* workflow, one topic per session; any later phase reopens it when it meets an unanswered design question.
disable-model-invocation: true
---

# Game Brainstorm

One topic, one conversation. The topic tree in `docs/game/topics.json` breaks the game down one question at a time; each session takes a topic, works it through with the user, and leaves the wiki truer and the tree one step deeper. This is a conversation, whatever the autonomy mode: it runs in the session the user started, never in a subagent or an unattended loop. Read `docs/agents/game.md` first and follow its session rules.

## 1. Prepare

Take the topic the task names (`game-brainstorm T014 …`), or with none, the first open topic `gamestate.py status` would pick. Read:

- the topic, and its parent chain up to `T1`;
- the `vision` page, and `docs/game/vision.json`: the pillars, anti-pillars, core loop and target feeling everything is judged against;
- the `slice` page: while the stage is `slice` (status shows it), design only what the slice's In list needs;
- the pages the topic writes, and the pages the wiki's home page links them to (ids and links in `docs/game/wiki.json`, read through the docs place);
- `CONTEXT.md`, and the ADRs those pages link.

Then prepare your challenges before asking anything: where could this idea contradict the vision or another page, what could make it dominant, boring, confusing or too big, and how do two or three reference games handle the same question (the `research` skill, if you need facts).

**Done when** you can state the topic's question, what the wiki already says about it, and your three strongest challenges.

## 2. Grill and challenge

With the `grilling` skill, interview the user one question at a time down the topic's design tree, giving your recommended answer with each. Be **ruthless** with every answer:

- **Against the vision**: which pillar does it serve, and does it break an anti-pillar? Does it strengthen the core loop or compete with it? Does it deliver the target feeling?
- **Against the wiki**: does it contradict another page? Does it duplicate something that already exists?
- **Against play**: what is the dominant strategy, the degenerate case, the boring case, the confusing first minute?
- **Against scope**: what does it cost, and what would the game lose without it? In the slice stage: does the slice need it, or can it wait for production?

Push vague answers until they are concrete enough to test. When an answer fails a challenge, say so plainly and help the user find a better one; when the user overrules you, record their reason.

**Done when** every branch of the topic is answered concretely enough to plan features and write tests from (design-ready), and every challenge you raised is resolved or recorded as an accepted risk.

## 3. Write it down

- Draft the wiki pages the topic covers, in the page format from "The wiki" in `docs/agents/game.md`: current truth only, precise rules and numbers, links instead of repetition. A change to the vision or slice also changes `docs/game/vision.json`.
- A decision the user made against a challenge, or that reverses an earlier page, gets an ADR (with `domain-modeling`) linked from the page.
- Draft an update for every other page the answers change.
- Add new terms to `CONTEXT.md`.

**Done when** someone who never saw this conversation could design features from the drafts alone.

## 4. Open the follow-ups

For each question the conversation raised but didn't settle, open a child topic: `parent` this topic, a question, a priority (`core`, `support`, `later`), a `stage` (`slice` only when the slice needs it answered, otherwise `production`) and the page id it will write. Open only questions that planning can't do without, or that you mark `later`; merge with an existing open topic instead of duplicating it. Publish each as a `ready-for-human` ticket.

**Done when** every unsettled question is a topic or a recorded accepted risk.

## 5. Close

Set the topic's `pages` (ids) and a one-line `resolution`, leaving its `status` `open` for now. `gamestate.py check --since <base>`, commit the state (topics, vision.json, ADRs, `CONTEXT.md`), progress entry.

Then write the pages, last: create or update each drafted page in the docs place, add the home page line for each new one under its area, and record each page's `version` (from the docs tool) and `updated` in `docs/game/wiki.json` (a new page gets an entry with `id`, `title`, `area`, `link`). Set the topic `resolved`, close its ticket, run `check --since <base>` again, and commit that.

**Done when** the topic is resolved, its pages are written with their `wiki.json` entries committed, and check passes.
