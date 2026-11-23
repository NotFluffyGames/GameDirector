---
name: game-ideation
description: With the user, turn a raw, high-level game idea into a vision (pitch, pillars, anti-pillars, core loop, target feeling, scope, kill condition), each role's north star and a vertical slice definition - going through the landscape scan with them, grilling them, comparing distinct directions and letting them choose; then seed the wiki pages and the brainstorm topic tree, and open the references the research phase studies. Runs after the landscape scan in the game-* workflow; also re-runs after a restart.
disable-model-invocation: true
---

# Game Ideation

Formulates the **vision** with the user (what the game is, who it is for, why it will be fun, what it will never be), sets each role's **north star** with them, and defines the **vertical slice**: the small part of the game built first, to the quality bar the user sets, to prove the game before production. Nothing is designed in detail yet. This is a conversation, whatever the autonomy mode: it runs in the session the user started, never in a subagent or an unattended loop. The roles sharpen your questions and challenge the user's answers; the user answers.

It writes the first wiki pages (in the docs place, see "The wiki" in `docs/agents/game.md`), `docs/game/vision.json` and the topics, and opens in `docs/game/research/references.json` the references the research phase studies; game-gdd then turns the pages into the human GDD. Draft each page in `docs/game/drafts/` as the user settles it (session rule 6 in `docs/agents/game.md`), and commit the drafts with `vision.json` and `references.json` whenever the session splits; the pages are written in the docs place at the last step, after the state is committed. A session that resumes ideation reads the committed drafts, `vision.json` and `references.json` and goes on at the first step whose **Done when** doesn't hold. Read `docs/agents/game.md` first, its Roles and Research sections included, and follow its session rules.

**Paths.** This skill's base directory is the folder this SKILL.md was read from. Each role's skill is `../game-role-<role>/SKILL.md`, with its `questions.md` beside it.

## 1. Read the seed and the landscape

Read `docs/game/seed.md`, the `landscape` page (through the docs place) and `docs/game/research/references.json`. On a `restart <adr>` task, also read that ADR's lessons, `vision.json` and the current wiki pages: they tell you which parts of the vision failed. The scan has been redone for the restart, and studied references keep their dossiers.

**Done when** you can say what the seed fixes (what must stay true of the game), what it leaves open, and what the landscape offers: the comps, the genre's anchors and default, the hook candidates and the candidate references per role.

## 2. Go through the landscape

With the user, one question at a time, each with your recommendation drawn from the `landscape` page:

- **Comps that count as "us"**: the games this one will be compared with.
- **Anchors**: which of the genre's anchors the game keeps, and which it breaks and why.
- **The hook**: one of the hook candidates or the user's own, as the anchor genre plus this game's departure, in one phrase.
- **References**: the candidates the roles' north stars start from, per aspect (play, look, feel, sound, tone, first minute, identity), and any the user adds: a game, a film, an artwork. An added one becomes a `references.json` entry with the next id (never reused: the next after the highest in the file's git history), `title`, `why` (`comp` or `aspect`), the `roles` it serves, `sources` (a link when there is one), `status` `candidate` and `how_studied` `{}`. Images the user gives go under `docs/game/references/`.

Offer, never choose: every pick is the user's. Every reference opened at step 9 costs a research session, so recommend references that serve several roles. Record the picks in the vision draft's "Comps and hook" and "References" sections ([vision-template.md](vision-template.md)).

**Done when** the user has picked the comps, the anchors to break, the hook and the starting references, and the vision draft records each pick.

## 3. Grill the vision

With the `grilling` skill, interview the user one question at a time down the vision's design tree: audience, platforms and input, player count, session length, the feeling a session should leave, must-haves, no-gos, scope. Give your recommended answer with each question. Be **ruthless**: push on vague answers until they are concrete, name contradictions between answers, and ask what the game gives up for each thing it wants.

**Done when** every branch has a concrete answer from the user and none is "TBD".

## 4. Compare directions

Draft 3–5 **directions** for the `concepts` page, laid out as [concepts-template.md](concepts-template.md). They differ in the core loop, not only in theme. Ways to get distance from the seed:

- change the core verb, or the player count and mode;
- change time: real-time against turn-based, short sessions against long runs;
- cross the seed with a reference game from a different genre;
- invert one of the seed's assumptions.

Score each on fun potential, richness potential, fit to the user's answers and their hook, how well an agent can build and test it, and risk. Present them with your recommendation and challenge the user's favourite as hard as the others. The user chooses. Record the choice, its reasons and the ideas worth borrowing from the others under `## Choice`, and `directions` in `docs/game/vision.json`: `count`, and `choice`, the chosen direction's id (e.g. `C2`).

**Done when** the concepts draft has 3–5 scored directions and the user's choice, and `vision.json` records both.

## 5. Write the vision

Draft the `vision` page from [vision-template.md](vision-template.md), and write its facts into `docs/game/vision.json` (`pillars`, `anti_pillars`, `kill_condition`; schema in `docs/agents/game.md`). Grill the user for the **anti-pillars** (what the game will never do, and which pillar each protects) and the **kill condition** (the playtest result that would stop the game as conceived). Read the pitch, hook, pillars, anti-pillars and core loop back to the user and fix what they correct.

**Done when** the user accepts the vision, and the page draft and `vision.json` agree: a one-page pitch, a one-sentence core loop, 3–4 pillars each able to reject a feature, at least one anti-pillar, and a kill condition a playtest can meet or not.

## 6. Set the roles' north stars

Each active role sets its direction with the user, in this session: `design`, `feel`, `art`, `audio`, `narrative`, `ux`, then `creative` last. For each:

1. Read the role skill's `north-star` mode and its `questions.md`.
2. Run the mode with the user: its questions one at a time, each with a recommended answer. The role sharpens the question and challenges the answer; the user answers. `art` builds two or three directions and the user chooses one; `creative`, last, names the genre default and the departure and turns them into the identity invariants.
3. The mode writes `north_stars.<role>` in `vision.json` (and `creative` the `invariants`). Its references are titles with what to take from each, from step 2's picks or added now as step 2 adds them.
4. Add the role's line to the vision draft's "Direction per role".

On a restart, run the mode again for each role whose north star the ADR's lessons or the new direction touch, and read the others back to the user to keep or change.

Recommend keeping every role; a story-light game keeps `narrative` with its minimum kit. A role the user wants off (a game played muted: `audio`) goes off only with a reason they accept, in `vision.json` `roles_off`, and its line in "Direction per role" says so. The roles' full pages aren't written here: each becomes a slice topic at step 8.

**Done when** every active role's `north-star` mode has met its own **Done when**, `gamestate.py gate` lists no `north_stars` or `invariants` line, and "Direction per role" has a line per role, a switched-off one with its reason.

## 7. Define the vertical slice

With the user, draft the `slice` page from [slice-template.md](slice-template.md), and write the `slice` block of `docs/game/vision.json` (`test_question`, `quality_bar`):

- **What it proves**: a test question the slice can fail, and the risks it retires.
- **In and out**: the part of the game it covers, the systems and content it needs, and what it leaves out. Keep it the smallest slice that delivers one complete start → challenge → resolution and the target feeling.
- **Quality bar**: for each aspect (code, feel, art, audio, UI, onboarding), ask the user for `placeholder`, `representative`, `production` or `final`. Recommend, as the user's call: feel at `production`; art at `production` in `quality_bar.art`, the bar the visual target needs, with the slice page's Means column naming the visual target's area (the scene built first) and narrowing the rest of the slice to `representative`, which game-plan's acceptance per feature carries; audio `representative`, with the signature sounds (name them) near final; code `production`; UI and onboarding `representative` unless one is a risk the slice must retire. A slice that leaves art or audio at placeholder can't show whether the game will look and sound right: say so when the user picks it.
- **Playtest**: who plays it and what counts as a pass. The slice verdict waits for this playtest.

**Done when** the user accepts the slice page, the `vision.json` slice block matches it, and every system and content type it names is in the slice's In list or its Out list.

## 8. Seed the topic tree

In `docs/game/topics.json`, record the root topic `T1` ("the game", answered by the vision, priority `core`, roles `["creative"]`, pages `["vision", "slice"]`, still `open` until its pages are in `wiki.json` at step 11), then break it into first-level topics with [topic-map.md](topic-map.md): one per area this game needs, each with a question, priority, the page id it will write, its **stage** (`slice` when the vertical slice needs it answered, otherwise `production`) and its **roles**: the area's roles from the table in `docs/agents/game.md` (Roles), `creative` on every `core` topic, adjusted by judgment. Seed a slice topic for each active role's page, with that role in `roles`: the map's role rows. Brainstorm takes slice topics first; production topics wait until the slice ships. Publish each as a ticket in the tracker (`docs/agents/issue-tracker.md`, `ready-for-human`: a person brainstorms it), and record the ticket on the topic. Show the user the list; add, drop or reprioritise as they say.

On a restart, reopen the topics whose pages the restart ADR invalidates (clearing their `resolution`, checking their `roles`), and open new ones where the vision or a north star changed.

**Done when** `topics.json` has `T1` and the first-level topics, each with `roles` and a ticket, `gamestate.py gate` lists no line about topics, and the user has seen the list.

## 9. Open the references to study

In `docs/game/research/references.json`, set `status` `open` on every reference the vision and the north stars name: the comps that count as "us", and each title in a north star's `references` and in `feel`'s action clips. Each one's `roles` gains every role whose north star names it; a title with no entry gets one as step 2 adds it. A `studied` reference (a restart) stays `studied`; a candidate nobody named stays `candidate` and is never studied. Then bring the vision draft's "References" section to exactly this set, each with its id and what the game takes from it.

**Done when** every reference the vision and the north stars name is `open` or `studied` with the roles that name it, the vision draft lists the same set, and `gamestate.py gate` lists no `references.json` line.

## 10. Name things

With the `domain-modeling` skill, add the game's own nouns from the vision, the north stars and the slice to `CONTEXT.md`.

**Done when** every noun the vision, the north stars and the slice use is in `CONTEXT.md`.

## 11. Close

Draft the home page too, with its Vision section filled ([index-template.md](index-template.md) lists the pages). `gamestate.py check --since <base>`, commit the state (`vision.json`, `topics.json`, `references.json`, `CONTEXT.md`, any images under `docs/game/references/`) with the drafts, progress entry. Then write the pages in the docs place, last, from the drafts: `vision`, `slice`, `concepts` and the home page. In the pages commit, add a `wiki.json` entry for each of `vision`, `slice` and `concepts` (`id`, `title`, area Vision, `link`, `version` read back as `docs/agents/docs.md` says, `updated`), update the `index` entry's `version` and `updated`, set `T1` to `resolved` with a one-line `resolution` (the vision and slice answer it), and delete the drafts. On a restart, update the existing pages and entries instead. Then run `python3 docs/game/gamestate.py gate`, and `gamestate.py complete`.

**Done when** the pages and their `wiki.json` entries are committed, no ideation draft remains, `gate` passes and `complete` succeeds.
