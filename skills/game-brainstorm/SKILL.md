---
name: game-brainstorm
description: With the user, take one open design topic from the game's topic tree, gather the challenges of the roles in charge of it, grill the user on it, ruthlessly challenge the idea against the vision, then write or update its wiki pages in the docs place and open the follow-up topics it raises. Runs after research in the game-* workflow, one topic per session; any later phase reopens it when it meets an unanswered design question.
disable-model-invocation: true
---

# Game Brainstorm

One topic, one conversation. The topic tree in `docs/game/topics.json` breaks the game down one question at a time; each session takes a topic, works it through with the user, and leaves the wiki truer and the tree one step deeper. This is a conversation, whatever the autonomy mode: it runs in the session the user started, never in a subagent or an unattended loop. The topic's roles (see Roles in `docs/agents/game.md`) prepare challenges before anything is asked; they sharpen the questions and challenge the answers, and only the user answers. Topics wait while research homework is open: `gamestate.py status` sends the session to the game-research skill's homework mode first. Read `docs/agents/game.md` first and follow its session rules.

**Paths.** This skill's base directory is the folder this SKILL.md was read from: the game-review skill is `../game-review/SKILL.md`, and each role's page template `../game-role-<role>/page-template.md`.

## 1. Prepare

Take the topic the task names (`game-brainstorm T014 …`), or with none, the first open topic `gamestate.py status` would pick. Read:

- the topic, its `roles`, and its parent chain up to `T1`;
- the `vision` page, and `docs/game/vision.json`: the pillars, anti-pillars, core loop and target feeling everything is judged against, and the roles' north stars and the identity invariants;
- the `slice` page: while the stage is `slice` (status shows it), design only what the slice's In list needs;
- the pages the topic writes, and the pages the wiki's home page links them to (ids and links in `docs/game/wiki.json`, read through the docs place);
- `CONTEXT.md`, and the ADRs those pages link.

**Recovery.** When the topic is `open` with a `resolution`, an earlier session ended between step 5's two commits. Look for its committed drafts: `docs/game/drafts/<page-id>.md` for the topic's `pages`.

- Drafts there: the conversation is already in them. Do step 5's second half from those drafts, with no new conversation, and end the session.
- No drafts: the answers were lost. Clear the `resolution` and go on below: the challenges are gathered and the conversation runs again with the person.

A draft of one of the topic's pages while it has no `resolution` belongs to another step (session rule 6): start your draft of that page from it.

Then gather the roles' challenges, before asking anything: read the game-review skill and run its task `game-review topic <id>`. It dispatches one agent per role in the topic's `roles` (with `creative` on a `core` topic) in parallel, each in its role skill's `challenge` mode, reading the topic, the vision, its own pages and the research dossiers of the references its north star names; you get back at most five challenges per role, merged, ordered and attributed to their roles. Add your own: where could this idea contradict the vision or another page, what could make it dominant, boring, confusing or too big, and how do the studied references (the `research` page and the dossiers) handle the same question.

**Done when** you can state the topic's question, what the wiki already says about it, each role's challenges with its role, and your three strongest challenges; on the recovery path with drafts, when step 5 is done instead.

## 2. Grill and challenge

With the `grilling` skill, interview the user one question at a time down the topic's design tree, giving your recommended answer with each. Be **ruthless** with every answer:

- **Against the vision**: which pillar does it serve, and does it break an anti-pillar? Does it strengthen the core loop or compete with it? Does it deliver the target feeling?
- **Against the wiki**: does it contradict another page? Does it duplicate something that already exists?
- **Against play**: what is the dominant strategy, the degenerate case, the boring case, the confusing first minute?
- **Against scope**: what does it cost, and what would the game lose without it? In the slice stage: does the slice need it, or can it wait for production?

Put the roles' challenges to the user as part of this, each attributed to its role ("the art role asks…"), with your recommended answer; a challenge never becomes an answer the user didn't give. Push vague answers until they are concrete enough to test. When an answer fails a challenge, say so plainly and help the user find a better one; when the user overrules you or a role, record their reason.

**Done when** every branch of the topic is answered concretely enough to plan features and write tests from (design-ready), and every challenge raised, yours and the roles', is resolved or recorded as an accepted risk.

## 3. Write it down

- Draft the wiki pages the topic covers in `docs/game/drafts/<page-id>.md` (session rule 6), in the page format from "The wiki" in `docs/agents/game.md`: current truth only, precise rules and numbers, links instead of repetition. A role's page is drafted from the user's answers, laid out by its role skill's `page-template.md`, each rule stated so a capture, a log or a string could fail it. A change to the vision, a north star or the slice also changes `docs/game/vision.json`.
- A homework item the user answers mid-topic is folded in as the game-research skill's homework mode does it (its steps 3 and 4), for that item: its `status` and dated `answer` in `docs/game/research/homework.json`; the dossier sections it feeds, and their references' entries in `references.json` (`how_studied` `played` when the user played it, a `person: <id>, <date>` source); drafts of the `research` page and the homework page with the answer; an answer that contradicts a north star, an invariant or a page as a follow-up topic (step 4). Step 5 closes its ticket.
- A decision the user made against a challenge, or that reverses an earlier page, gets an ADR (with `domain-modeling`) linked from the page.
- Draft an update for every other page the answers change, and the home page's line under its area for each new page.
- Add new terms to `CONTEXT.md`.

**Done when** someone who never saw this conversation could design features from the drafts alone, and every homework answer given is recorded.

## 4. Open the follow-ups

For each question the conversation raised but didn't settle, open a child topic: `parent` this topic, a question, a priority (`core`, `support`, `later`), a `stage` (`slice` only when the slice needs it answered, otherwise `production`), the page id it will write, and its `roles`: the area's roles from the table in `docs/agents/game.md`, `creative` on a `core` topic, and any role whose challenge raised the question. Open only questions that planning can't do without, or that you mark `later`; merge with an existing open topic instead of duplicating it. Publish each as a `ready-for-human` ticket.

**Done when** every unsettled question is a topic with `roles` or a recorded accepted risk.

## 5. Close

Set the topic's `pages` (ids, every page it drafted) and a one-line `resolution`, leaving its `status` `open` for now. `gamestate.py check --since <base>`, commit the state (topics, vision.json, ADRs, `CONTEXT.md`, and `homework.json`, `references.json` and the dossiers when a homework answer changed them) with the drafts, progress entry.

Then write the pages, last: create or update each drafted page in the docs place from its draft (the home page included), and record each page's `version` (read back as `docs/agents/docs.md` says) and `updated` in `docs/game/wiki.json` (a new page gets an entry with `id`, `title`, `area`, `link`), including the `index` entry's new `version` and `updated` when you changed the home page. When the topic was a review of a flagged page, remove that page's `flagged` entry, and its draft is the text without the note. A homework answer's drafts go the same way: the `research` page (its `version` and `updated` in `wiki.json`) and the homework page beside the wiki, as game-research's homework mode writes them; close the answered item's ticket with the answer. Delete the drafts, set the topic `resolved`, close its ticket, run `check --since <base>` again, and commit that: the pages commit.

**Done when** the topic is resolved, its pages are written with their `wiki.json` entries committed, its drafts are gone, and check passes.
