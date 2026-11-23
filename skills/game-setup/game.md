# Game workflow

Config for the game-* skills. Every game-* session reads this file first. Edit it freely; it is the project's, not the skills'. `game-setup upgrade` refreshes the sections the skills own and shows you what it replaces.

## The goal

A game that is **fun, playable, rich, working, testable and tested**, described by an up-to-date wiki and GDD. Publishing it is out of scope. The run is complete when:

| Quality | Checked by |
| --- | --- |
| Playable | the packaged build launches without dev tools and plays from title screen to the end of a session, on every target platform this machine can build for |
| Working | every `must` feature passes; a long crash and softlock fuzz run is clean |
| Tested | tests, replays and bot runs cover the core rules and every feature, green on the final build |
| Testable | the simulation core is deterministic and the adapter commands re-run every check |
| Rich | every richness target passes on the final build |
| Fun | every fun proxy passes on the final build, and the playtest kit is ready; people's answers can still reopen the verdict |

The game is made in two **stages**:

- **slice** (pre-production): setup → scan (the landscape) → ideation (vision, the roles' north stars and the vertical slice) → research (the references ideation chose) → brainstorm (only the slice's topics) → consolidate → plan → build the core loop → verdict (core-loop, on bots) → build the rest of the slice to its quality bar → verdict (slice: the gate into production, after a person's playtest).
- **production**: brainstorm (the remaining topics) → consolidate → plan → build systems and content → verdict (full) → polish → verdict (final) → done.

`state.json` `phase` is one of `setup`, `scan`, `ideation`, `research`, `brainstorm`, `consolidate`, `plan`, `build`, `verdict`, `polish`, `awaiting-human` or `done`. The game-research skill runs both `scan` and `research`; every other phase runs its own `game-<phase>` skill. A restart goes back to `scan`.

Brainstorming doesn't end with its phase: any later phase opens a topic when it meets a question the wiki doesn't answer.

The game is made over **many sessions, one step per session**. A person starts a session and runs `/game-next`; `gamestate.py status` names the step, the session does it, checks it and stops. Steps that need no person can also run back to back unattended (the game-next skill's `unattended.md`).

## Autonomy

Mode: {{autonomous | interactive}}

Setup, ideation, research homework and brainstorm topics are always conversations with a person (`with-user:` steps), whatever the mode. A person also has three short moments the run waits for, whatever the mode: **calibration** (labelling captures once the visual target exists), the **slice playtest**, and **A/B picks** in polish (see Human queue). The mode decides the rest:

- **autonomous**: other steps decide on their own. At each judgement call, take the recommended answer and record it in an ADR as an assumption a human can overturn. Work only a person can do goes to the **human queue**.
- **interactive**: the user also approves the fun checklist and richness targets (game-consolidate), the ticket breakdown (game-plan) and each verdict's outcome and review notes (game-verdict), when they are in the session.

## Session rules

Every game-* session is a **fresh session** doing **one task**:

1. Start: note your base commit (`git rev-parse HEAD`) and run `python3 docs/game/gamestate.py status`. Read only the files your task names; reach for more only when the work demands it.
2. Hand reading-heavy exploration to a subagent or the `research` skill, which returns a summary or writes notes to a file.
3. When the step outgrows the session (a second unplanned subsystem appears, or you are past roughly half your context), split: write the remainder as new tickets, features or topics, commit what is green with your page drafts, stop. The next dispatch of the same task resumes from what is on disk.
4. Leave the repo green: commit only work whose tests pass.
5. **Keep the wiki true.** When your work changes what the game is or how it plays, change the page that describes your change, as the last step; see The wiki. When you meet a design question no page answers, open a topic for it rather than deciding silently.
6. **Page drafts.** Every page text you write is first a **draft**: the page's full new text in `docs/game/drafts/<page-id>.md`. Drafts go into your state commit (and into any earlier commit, when the step splits). The pages commit then writes each draft to the docs place, records the page's `version` and `updated` in `wiki.json`, and deletes the draft (see "Pages are written last"). So a draft on disk is a page not yet written, and nothing drafted is lost when a session ends early:
   - To change a page that has a draft, change the draft: it is newer than the docs place.
   - A session that resumes a task picks up that task's drafts instead of redoing the work behind them. A topic's drafts belong to its brainstorm while the topic is `open` with a `resolution`; that session finishes them (game-brainstorm's step 1).
   - Any other drafts outlived their step (a build whose feature now passes, a GDD sync): the next game-gdd session writes them first.
7. End: `gamestate.py check --since <base>` passing; a commit; a progress entry of at most 10 lines appended to `docs/game/progress.md`; when the task is the phase's own (status shows `task:`) and every step is done, `gamestate.py complete`; and a short report: what changed, the **evidence**, what is left.

**Asking the user.** Ask the person in the session directly, one question at a time, each with your recommended answer. In an unattended session (`--unattended`), take the recommended answer and record it in an ADR as an assumption.

**The bar only rises.** Outside the plan phase a feature is never deleted and its `acceptance`, `verify` and `milestone` never change; a `must` feature leaves `must` only as `tier: "cut"` with `cut_reason: "replaced by F0xx[, F0yy]"` naming live must features. After consolidate, fun checklist items and richness targets can be added but not changed or removed. Set `passes: true` only with evidence from a run in this session. `gamestate.py check` enforces all of this against your base commit. The wiki, by contrast, changes freely: it describes the game, it doesn't judge it.

## The wiki

The wiki is the living description of the game: precise enough to plan, build and test from. It holds the **current truth** only; why something changed lives in an ADR the page links to. Its pages live in the docs place next to the tasks, which `docs/agents/docs.md` names with how to read, write and comment there. A user who chose local files gets `docs/game/wiki/` instead; that is the only case where the wiki is in the repo.

`docs/game/wiki.json` indexes the pages, one entry each:

```json
{"pages": [
  {"id": "weapons", "title": "Weapons", "area": "Systems",
   "link": "https://example.com/docs/weapons", "version": 3, "updated": "2026-11-22: stealing needs a free hand",
   "flagged": {"topic": "T031", "note": "edited by hand; check against the page"}}
]}
```

- `id`: unique and stable; topics and features name pages by it.
- `title`: the page's title.
- `area`: Vision, Mechanics, Controls, Systems, Content, Modes and sessions, Screens and onboarding, Feel, Art, Audio, Narrative and world. Each area is a section of the wiki's home page, listing its pages with one line each. An area whose role is switched off (Art, Audio, or Narrative and world; see Roles) needs no page.
- `link`: the page's URL, or its repo-relative path for local files.
- `version`: the page's version as the session that wrote it read it back, the way `docs/agents/docs.md` says (the docs tool's version number, else its last-modified time, else a hash of the text; for local files, a git hash of the page above its comments). A page whose version moved without a session recording it was edited by hand.
- `updated`: the date and a one-line reason, e.g. `"2026-11-22: stealing needs a free hand"`.
- `flagged`: set when a direct edit was detected. It names the open topic that reviews the edit, and clears when that topic is resolved or deferred.
- `index` is the wiki's home page (area Vision), created by setup from the game-ideation skill's `index-template.md`. Its sections are the areas; a session that adds a page adds the page's line under its area.
- After the scan, the `landscape` page (area Vision) exists: comps, the genre's anchors and default, player complaints, the player, hook candidates and candidate references. After research, the `research` page (area Vision): what the studied references teach, per aspect, and what is still unknown. The game-research skill writes both.
- Once ideation is done, the pages `vision`, `slice` and `concepts` always exist: `vision` (pitch, audience and platforms, comps and hook, pillars, anti-pillars, core loop, target feeling, direction per role with the identity invariants, references, scope, kill condition), `slice` (what the vertical slice proves, what is in and out, its quality bar, its playtest) and `concepts` (the directions compared and the choice).
- Every other page has one subject (a system, a content type, a mode, a screen flow, a role's rules), is written by brainstorm topics and kept true by every phase. Each role keeps its own pages (see Roles), laid out by its role skill's `page-template.md`. A page starts with:

  ```markdown
  # <Title>

  Topics: T004, T019 · Decisions: ADR-0007 · Last changed: <date>, <what and why in one line>
  ```

- Link instead of repeating; split a page that passes about 200 lines; use the terms in `CONTEXT.md`.

**Comments only.** People comment on wiki pages; sessions edit them. A person's comment becomes a topic or a note, never a silent change. game-gdd compares each page's version in the docs tool with the `version` in `wiki.json`. A mismatch, including a missing page, becomes a topic to review it plus a `flagged` entry. `gamestate.py` only validates `flagged`.

**Pages are written last.** A session finishes its work, runs `check --since <base>` and commits its state and code with its page drafts (session rule 6). Only then does it write the pages in the docs place from those drafts; a second commit, the **pages commit**, records each page's new `version` and `updated` in `wiki.json` and deletes the drafts. A session that ends between the two commits leaves its drafts committed, and session rule 6 says who writes them. When the docs place can't be reached, the session stops with `stop: <tracker> docs unreachable` (naming the tracker from `issue-tracker.md`) rather than writing the pages elsewhere. Local files are used only when the user chose them in setup.

**Setup is always `with-user:`.** Setup can't complete until `docs/agents/docs.md` exists and `state.json` has `docs_verified: {"place": "...", "date": "YYYY-MM-DD"}`, recording that the user's chosen place passed its smoke test, plus `intent` and `research_sources` (see Research).

### vision.json

`docs/game/vision.json` holds the vision's facts as data, so that checks and the verdict read them without parsing prose. The `vision` and `slice` pages explain them. The example shows two of the north stars.

```json
{
  "pillars": [{"id": "P1", "statement": "Every fight is a negotiation"}],
  "anti_pillars": ["We will not add stat grinding, because it would compromise P1"],
  "kill_condition": "Fewer than half of testers start a second match",
  "slice": {
    "test_question": "Is one match fun enough to repeat?",
    "quality_bar": {"code": "production", "feel": "production", "art": "production",
                    "audio": "representative", "ui": "representative", "onboarding": "representative"}
  },
  "directions": {"count": 3, "choice": "C2"},
  "north_stars": {
    "creative": {"statement": "A duel you retell afterwards",
                 "references": ["Samurai Gunn: one hit decides", "Okami: ink as identity"],
                 "genre_default": "health bars, item spam, four-player chaos", "departure": "one-hit duels drawn in ink"},
    "art": {"statement": "Ink on paper", "references": ["Okami: brush strokes", "Sumi-e: negative space"],
            "directions": 3, "choice": "Ink wash", "rules": ["Two values per layer: rules out gradients"],
            "reserved": ["self: vermilion"], "lost": ["Neon arcade: fights the duel's quiet"]}
  },
  "invariants": ["Every hit reads as one ink stroke", "One button dashes"],
  "roles_off": {}
}
```

- **Quality bars** are `placeholder`, `representative`, `production` or `final`, one per aspect. The roles read their bar here: `art` → `art`, `feel` → `feel`, `audio` → `audio`, `ux` → `ui` (HUD, contrast, text, settings) and `onboarding` (the first minute), `narrative` → `ui`. Production features use the slice's bar. Reviewers read only these values. When the `slice` page's Means column narrows a bar to an area (the art bar to the visual target's area, the rest of the slice a step lower), game-plan's acceptance per feature carries the narrowing.
- `north_stars`: one object per active role, set with the person in ideation by the role skill's `north-star` mode. Each has a `statement` and at least two `references` ("title: what we take"). Beyond those:
  - `creative`: `genre_default`, `departure`;
  - `design`: `variety` (what makes runs or matches differ);
  - `feel`: `never` (what it must never feel like) and `actions`, at least one: `{"<action>": {"words": [one or two adjectives], "references": [one to three timestamped clips]}}`;
  - `art`: `directions` (2 or 3: how many were compared), `choice`, `rules`, `reserved` (reserved colour roles), `lost` (each other direction and why it lost);
  - `audio`: `by_ear`, `anti_references`, `voice` (`full`, `barks`, `gibberish` or `none`), `muted`;
  - `narrative`: `setting`, `tone_words` (three), `anti_words` (three), `ui_voice`, `story_light`;
  - `ux`: `player`, `input`, `session`, `access`.
- `invariants`: two to five identity invariants, what polish must never remove, set by `creative` last in ideation. They are the same strings as the vision page's "Identity invariants"; only the person changes them.
- `roles_off`: `{"<role>": "<the reason the person accepted>"}`, for example `{"audio": "the game is played muted in class"}`; `{}` when every role is on.

Of these, the ideation gate checks the pillars, anti-pillars, kill condition, directions, the slice's test question and bars, each active role's `statement` and `references`, art's `directions` and `choice`, feel's `actions`, and the invariants. The other north-star fields are their role skills' to fill.

## Topics

`docs/game/topics.json` holds the brainstorm tree: every design question, open or answered. Each topic is brainstormed with a person, one per session, and mirrored as a `ready-for-human` ticket in the tracker.

```json
{"id": "T014", "title": "Weapon stealing", "parent": "T003",
 "question": "How does a player take an opponent's weapon, and what stops it from dominating?",
 "priority": "core", "stage": "slice", "status": "open", "roles": ["design", "feel", "creative"],
 "pages": ["weapons"], "unblocks": ["F021"], "ticket": "#88",
 "resolution": ""}
```

- `priority`: `core` (the core loop depends on it), `support` (needed before planning is complete), `later` (depth that can wait).
- `stage`: `slice` when the vertical slice needs it answered, otherwise `production`. Production topics wait until the slice ships.
- `status`: `open`, `resolved` (its `pages` were written or updated and `resolution` gives the answer in a line) or `deferred` (`resolution` says why it waits). Any session may reopen a topic when the game changes under it: `status` back to `open`, and `resolution` cleared to `""` (an open topic with a `resolution` is a brainstorm between its two commits).
- `roles`: the roles in charge (see Roles). An open topic needs at least one; brainstorm runs their challenges before asking the person anything.
- `unblocks`: features that can't be built until it is answered; the status tool brainstorms those topics before building them.

## Roles

Every taste aspect of the game has an owner, its **role**. A role sets a north star with the person in ideation, keeps its pages, brings its challenges to the brainstorm topics it is on, and reviews the running game. Its process lives in the role skill `game-role-<role>`; an agent named by its role id (`agents/<role>.md`) runs it in parallel for game-review and game-research. Roles sharpen the person's questions and challenge their answers; they never answer for the person.

| Role | Owns | Its pages |
| --- | --- | --- |
| `creative` | the vision, identity and distinctiveness; decides every review note | `vision` (its "Direction per role" section), and the invariants in `vision.json` |
| `design` | rules, systems, levels, opposition, economy | the Mechanics, Systems and Content pages |
| `feel` | how core actions feel: response, feedback layers, camera | `feel` (area Feel): one feel sheet per core action |
| `art` | the look: identity, palette, values, silhouettes, UI visual language, motion, VFX | `art-bible` (area Art) |
| `audio` | sonic identity, feedback by ear, music, mix priority | `audio` (area Audio) |
| `narrative` | fantasy, tone, world, characters, every player-facing word | `tone-and-world` (area Narrative and world) |
| `ux` | understanding and access: screens, HUD, onboarding, input, accessibility | `screens` and `onboarding` (area Screens and onboarding) |

The **active roles** are these seven minus `vision.json` `roles_off`. Ideation switches a role off only with a reason the person accepts; a story-light game keeps `narrative` with its minimum kit. A switched-off role is on no topic, feature or fun item.

### Which roles are in charge

Topics and features get a `roles` list of role ids, set by whoever creates them: **ideation** for the first topics, **brainstorm** for follow-up topics, **plan** for features, **consolidate** for the gap topics it opens, and **build and verdict** for the topics and features their review notes create. This default table maps the wiki areas to roles:

| Area | Roles |
| --- | --- |
| Mechanics | design and feel |
| Controls | feel and ux |
| Systems | design |
| Content | design plus the roles its pieces touch (art, audio, narrative) |
| Modes and sessions | design and ux |
| Screens and onboarding | ux and art |
| Feel | feel, audio and art |
| Art | art |
| Audio | audio |
| Narrative and world | narrative |

- The session starts from the table and adds or removes roles by judgment.
- A reviewer may add a role it finds missing. The review records that, and that role reviews too.
- `creative` is on every `core` topic, every verdict review and every polish review. On features it is the decider, not a reviewer.
- **Features get roles only when they are visible:** when they change what the player sees, hears or does with their hands. A rules-only feature (sim logic, saves, netcode) has `roles: []` and no build-time review.
  - `design` is never a feature reviewer. Its checks (completability, difficulty curve, decisions per minute, source/sink balance) need whole-game bot runs, so it judges at verdicts.
  - The rest of the table applies to visible features as written.
- `check` rejects an unknown role id, a role in `roles_off`, an open topic with no roles, `design` on a feature, and a feature with empty `roles` whose `pages` include a page in Screens and onboarding, Feel, Art, Audio, or Narrative and world, or whose verify kind is `capture`.

### Role memory

`docs/game/roles/<role>.md` holds what this person taught the role, so its judgment converges on their taste across sessions. Every role agent reads its file first and follows it. game-review appends one line per lesson:

```markdown
- <date> <target> <kind>: <what> (why: <their reason>)
```

Kinds: `overruled` (the person set aside one of the role's notes, or changed a decision of creative's), `pick` (an A/B pick), `label` (a calibration label's reason, for `art`, `ux` and `creative` from stills, `feel` from strips). In ideation, `narrative`'s north-star mode also records there which sample strings the person picked, and why.

## Research

Market numbers never come from memory. Before ideation, the **scan** maps the landscape; after it, the **deep study** reads the references ideation chose, one per session, each role from its own angle. What the agent can't do becomes the person's **homework**. The game-research skill says how; these are its facts.

- `state.json` `intent`: `sell` or `hobby`, asked in setup. `hobby` drops sales numbers and saturation, and keeps comps, anchors, the player, references and complaints.
- `state.json` `research_sources`: `{"checked": "<date>", "reachable": [hosts], "unreachable": [hosts]}`, set in setup, plus `"public_repo_ok": true` when the person accepted reference images in a public repo. An unreachable source's work becomes homework.
- `docs/game/research/references.json`: `{"scanned_for": null, "refs": [...]}`. `scanned_for` is the restart ADR the last scan ran for. Each ref: `id` (`R1`…, never reused), `title`, `why` (`comp` or `aspect`), `roles`, `sources` (links, or `person: <homework id>, <date>`), `status`, `how_studied` (per role, `{"how": "played" | "watched" | "read" | "not-assessed", "reason": "..."}`) and `homework` (what a person does to fill a gap the agent couldn't, one string each). `status` moves `candidate` (the scan proposes it) → `open` (ideation: the vision or a north star names it) → `studied` (its dossier passed). A candidate nobody named is never studied.
- `docs/game/research/refs/<id>/`: `material/` (the sources, with `index.md`), one dossier section `<role>.md` per role of the reference, its images in `art/`, `ux/` and `feel/`, and `audit.json` (a review record by `creative`, target `<id>`, whose findings block). Images are always committed, downscaled to at most 1280 px on the longest side (`measure.py shrink`).
- `docs/game/research/homework.json`: `{"reason": "", "page": "<link>", "items": [...]}`, at most ten items in rank order, or none with a `reason`. Each item: `id` (`H1`…), `what`, `why`, `questions`, `minutes`, `roles`, `status` (`open`, `answered` or `skip`), `answer`, `ticket`. `page` is the homework page beside the wiki where people answer; `ticket` is the item's `ready-for-human` ticket.
- `docs/game/references/`: images the person gives as references in ideation.

**Gates.**

- **scan**: the `landscape` page is in `wiki.json`; for `sell`, `references.json` has at least three comps; after a restart, `scanned_for` names its ADR.
- **ideation** (besides the vision): every active role is covered by an `open` or `studied` reference, one whose `roles` name it.
- **research**: every active role is still covered; every opened reference is `studied`, with a dossier section and a `how_studied` per role, images for `art`, `ux` and `feel` (or `not-assessed` with a reason), three sources (or a `homework` entry naming the gap), and an audit with no open finding; the `research` page is in `wiki.json`; `homework.json` exists.

**Brainstorm waits** while a homework item is `open`: the next step is `with-user: game-research homework`, and an unattended run stops there. Homework is not copied into the human queue.

## Reviews

A visible feature isn't done until its roles have reviewed it, and no builder grades its own visible work. The game-review skill runs every review: inputs prepared once from one build, the roles dispatched in parallel, every note decided by `creative`, the decisions carried out and recorded. Callers: game-build (a feature with `roles`, a polish feature), game-verdict (a scope), game-brainstorm (a topic's challenges, which come back as text).

A review lives in `docs/game/reviews/<target>/`, where `<target>` is a feature id (a polish feature's too), a topic id, or `verdict-<scope>`. Each role's record is `<role>.json`:

```json
{"role": "art", "target": "F012", "commit": "3f2a9c1", "independent": true,
 "inputs": ["docs/game/reviews/F012/inputs/captures/beauty.png"],
 "result": "notes", "reason": "passed: values, contrast, silhouettes",
 "notes": [{"id": "N1", "what": "An enemy's dash trail is vermilion, the player's reserved colour",
            "evidence": "docs/game/reviews/F012/inputs/measure/dash.json",
            "rule": "art-bible, Colour roles: vermilion is the player's alone",
            "severity": "advisory", "anchor": {"kind": "rule", "ref": "art-bible#colour-roles"},
            "item": "FC7", "suggestion": "suggestion: the threat colour", "decision": "fixed 9b1e0c4"}],
 "requests": [{"capture": "hud-dark", "why": "the HUD over the darkest area"}]}
```

- `result`: `ok`, `notes` or `not-assessed`; `not-assessed` needs a `reason`. `reason` also names what passed.
- `independent`: `true` when the role ran as its own agent; `false` when the session ran it itself (no subagent tool), and verdicts then score its review items `not-assessed`.
- A note: `id`, `what` and `evidence` (a path), the `rule`, `severity`, `anchor` (what the person set that the build contradicts: `{"kind": "label" | "reference" | "rule", "ref": "..."}`, or `null`), `item` (the fun checklist item it bears on, if any), an optional `suggestion`, the `decision`, and `reraises` (`"<path>#<id>"` when it repeats an earlier decided note).
- `requests`: `{"capture": "<state or strip>", "why": "..."}` asks for one more capture; `{"role": "<id>", "why": "..."}` adds a missing role, which reviews too.

**Severity.** A note is `blocking` only for a measured failure of a feature's frozen acceptance, in a feature or polish-feature review; its `rule` quotes that acceptance line. Everything else is `advisory`: every judgment, a measured check against a page rule added after plan, every note in a verdict-scope review, and every note of `creative`'s. A research audit's findings are the exception: anchored to the dossier rules, they block.

**Decisions.** Every note gets one, in this grammar:

- `fixed <commit>`: fixed in that commit. A blocking note is always fixed, never decided.
- `feature F0xx`: new work, a `nice` or a polish feature.
- `topic T0xx`: the rule itself looks wrong, so it goes to the person; the target can still pass.
- `wontfix: <reason>`.

`creative` decides the advisory notes in its `decide` mode, writing `decisions-<n>.md` per round beside the records; in interactive mode the person decides a verdict review's notes. The session carries the decisions out. The builder never decides a note on its own work and never picks `wontfix`. `check` rejects a decision outside the grammar, and one naming a feature or topic that doesn't exist.

**A feature passes** only when every role in its `roles` has a record in its `reviews` map, made on this session's work (its `commit` descends from the session's base), with a decision on every note and every blocking note `fixed`.

**Inputs.** Reviewers read files; they never build or run the game. `inputs/` under the target holds what they read, made once from one build at the review's commit: `captures/` and `strips/` (shrunk to at most 1280 px), `derived/<capture>/` (grayscale, thumbnail and colour-blindness copies), `measure/<capture>.json`, `events/`, `bot/`, `dumps/` (with `strings.json`), `pages/<page-id>.md` (page copies), `decided.md` (one line per earlier decided note) and `index.md` (one line per input with the command and commit that made it, or `<input>: n/a: <reason>`). Full-size captures go in `inputs/full/`, which `inputs/.gitignore` keeps out of git. game-review commits its own work, subjects starting `game-review: <target> round <n>` (the skill lists them); a feature or polish feature gets at most two rounds per session.

**Anchored to the person.** A role's judgment can fail a verdict item only through an anchor: a calibration label, a reference the person chose, or a page rule. Taste judgments by `creative`, `art`, `feel` and `ux` are `not-assessed` until calibration labels exist. `audio` is never judged by taste, since the model can't hear: its items are measured, and its taste is the person's. `narrative` judges text against the tone page; `design` judges bot traces at verdicts.

## The GDD

A game design document for people, kept next to the tasks in the docs place `docs/agents/docs.md` names. game-gdd writes it from the wiki in plain language and updates the pages whose wiki sources changed. The status tool makes it the next step before every phase or milestone change while `wiki.json` or `own-calls.md` has changed since the last `gdd-synced`. People read and comment there; their edits and comments come back as topics, never as silent changes to the wiki.

## Files

| Path | What | Written by |
| --- | --- | --- |
| `docs/game/seed.md` | the user's original prompt, verbatim | game-setup |
| `docs/game/wiki.json` | index of the wiki pages (the pages live in the docs place) | ideation, research, brainstorm, consolidate; every phase keeps it true |
| `docs/game/vision.json` | pillars, anti-pillars, kill condition, slice test question and quality bars, directions, north stars, invariants, roles switched off | ideation; brainstorm, consolidate, plan adjust and verdict when they change the vision or slice page |
| `docs/game/drafts/` | page drafts: page text committed but not yet written in the docs place (session rule 6) | any session that writes pages |
| `docs/game/topics.json` | the brainstorm tree | ideation, brainstorm; any phase opens topics |
| `docs/game/research/` | `references.json`, `homework.json`, and per reference `refs/<id>/` (see Research) | game-research; ideation opens references |
| `docs/game/references/` | images the person gives as references | ideation |
| `docs/game/reviews/<target>/` | the roles' review records, their inputs and the decisions (see Reviews) | game-review |
| `docs/game/roles/<role>.md` | role memory: what the person taught each role | game-review; `narrative`'s north-star mode |
| `docs/game/calibration/labels.json` | the person's calibration labels | the person, through a `calibrate` entry |
| `docs/game/fun-checklist.json` | fun checklist | game-consolidate |
| `docs/game/keep.json` | what playtests and people said to keep, with pinned tuning values | game-verdict, game-gdd |
| `docs/game/own-calls.md` | player-visible choices agents made that no page specified | game-build, any session |
| `docs/game/richness.json` | richness targets | game-consolidate |
| `docs/game/features.json` | definition of done | game-plan, game-polish add items; game-build sets `passes` |
| `docs/game/state.json` | `version` (of the state tool that wrote it), phase, milestone, task, counters, limits, attempts, verdicts, human queue, GDD sync point, `adapter_verified`, `docs_verified`, `intent`, `research_sources` | `gamestate.py`; skills append verdicts and queue entries; game-setup sets `docs_verified`, `adapter_verified`, `intent` and `research_sources` |
| `docs/game/progress.md` | append-only session log | every session |
| `docs/game/assets.md` | every asset's source and license | whoever adds an asset |
| `docs/game/engine-notes.md` | engine CLI, headless, test and export facts; the named capture states and frame strips | game-plan |
| `docs/game/playtests/` | verdict evidence, captures, human playtest kits and answers | game-verdict, game-build |
| `docs/game/archive/restart-N/` | the definition of done, human queue and research homework from before restart N | `gamestate.py` |
| `docs/agents/docs.md` | where the wiki and GDD live and how to read, write and comment there | game-setup; game-gdd records new GDD pages |
| `docs/game/gamestate.py` | reads, checks and advances state; commits its own state changes | game-setup installs it |

Decisions are ADRs and game terms live in `CONTEXT.md`, both where `docs/agents/domain.md` says. Tickets live in the tracker `docs/agents/issue-tracker.md` describes, labelled with the roles in `docs/agents/triage-labels.md`. The wiki and GDD live where `docs/agents/docs.md` says.

## Vocabulary

- **Pillars**: 3–4 statements of the feelings or features the game delivers, in `vision.json`. Every feature serves one; a feature with no pillar is not in the game. **Anti-pillars** say what the game will never do and which pillar each protects. A page quotes a pillar in `vision.json`'s exact words.
- **Kill condition**: the playtest result, stated in `vision.json`, that would stop the game as conceived. The slice verdict checks it.
- **North star**: a role's direction for its aspect, chosen by the person in ideation (`vision.json` `north_stars`). **Identity invariants**: two to five things polish must never remove.
- **Vertical slice**: the small part of the game built first (`slice` page and `vision.json`): one complete start → challenge → resolution delivering the target feeling, at the quality bar the user chose per aspect (`placeholder`, `representative`, `production` or `final`). Its verdict, after a person's playtest, is the gate into production, and the sessions it took set the production budget.
- **Visual target** and **feel target**: the slice's first features (`target: visual` in milestone `slice`, `target: feel` in milestone `core-loop`): one in-game scene built to the slice's art bar, and the core action at its feel sheet's targets. Everything later is reviewed against them.
- **Core loop**: the action the player repeats minute to minute, in one sentence.
- **Design-ready**: a topic's question is answered on a page precisely enough to plan features and write tests from. Brainstorming aims here, not at exhaustiveness.
- **Fun checklist**: statements that are true when the game is fun, each observable in one play session, with a `scope`: `core-loop`, `slice` or `full`, and a `kind`:
  - **proxy**: a metric, threshold and method a bot run or replay can measure;
  - **human**: needs a person;
  - **review**: judged by the named `roles` from this build's review records, with `taste: true` when calibration labels anchor its judgment (a look, a feel, identity, the first minute), else `false`, as for every `audio`, `narrative` and `design` item, whose judgments a page rule or a measurement settles. It `fail`s when a role's review has an anchored note whose `item` is this one; it is `not-assessed` when a review wasn't independent or was not assessed, or when it is a taste item for `creative`, `art`, `feel` or `ux` and no calibration labels exist yet; otherwise it `pass`es. Unanchored notes never change its score.

  The checklist's 10-item cap counts only proxy and human items.
- **Richness targets**: `richness.json` targets `{id, aspect, scope, statement, metric, threshold, how}` with `scope` `slice` or `full`; the full game needs at least one per aspect: **depth** (systems that change each other), **breadth** (distinct content), **variety** (playthroughs that differ).
- **Scope tiers**: `must`, `nice`, `cut`. Nice features are built after their milestone's must features, while the budget has room.
- **Tuning knobs**: per-system values and an on/off toggle, loaded from data so they change without code edits.
- **Simulation core / presentation shell**: game rules live in a deterministic core (fixed tick or turn, seeded RNG, input as data, serializable state) that runs headless. Rendering, audio and input devices live in a thin shell around it. Tests, bots and replays drive the core.
- **Tick**: one step of the simulation core: a fixed-timestep frame in a real-time game, one turn or action in a turn-based one.
- **Definition of done**: `features.json`. With the final verdict, it is how the goal above is checked.
- **Evidence**: the command run, its result (numbers, hash, artifact path) and the commit.
- **Task**: what the current phase still owes (`state.json` `task`, shown by status). Phase skills clear it with `gamestate.py complete` as their last step.
- **Gate**: a phase's completion criterion, checked by `gamestate.py gate`.
- **Verdict**: the scored judgement of a green build against the fun checklist and richness targets: `ship`, `adjust`, `restart` or `kill`. Scopes: `core-loop` (on bots, before the slice is polished), `slice` (the gate into production; waits for calibration labels and a person's playtest), `full` (before polish), `final` (after polish; shipping it completes the run). It runs again when playtest answers arrive. Each score is `pass` or `fail` with an evidence file, `not-assessed` with the reason it couldn't be measured, or `pending-human`; a ship needs every item to pass. A review item's score also lists its records in `reviews` (paths), and `gate` recomputes its result from them.
- **Kept values**: `keep.json` entries `{id, what, source, pins: [{file, key, value}], adr}` for what a playtest or a person said to keep. `gamestate.py check` holds each pinned tuning value (a dotted key in JSON, or a `key = value` / `key: value` line); changing or dropping one needs a new ADR in the entry's `adr`.
- **Own calls**: player-visible choices an agent made that no page specified, logged in `own-calls.md` and shown in the GDD for people to keep or change.
- **Durable assets**: seed.md, the wiki, `vision.json`, the fun checklist, richness targets, kept values, ADRs, CONTEXT.md, final art, the research dossiers and role memory. They survive a restart. Code is disposable.
- **Human queue**: `state.json` `human_queue` entries `{id, what, why, how, unblocks: [feature ids]}` for work only a person can do, each mirrored as a `ready-for-human` ticket. The run moves past queued features and stops at the end for the queue; open playtest entries don't stop it. A person finishing an entry deletes it, and for a `human`-verified feature sets `passes: true` with evidence starting `human:`; the next `/game-next` session goes back to anything still failing. Three kinds carry `kind`, `how` (the kit) and `answers` (a file path the person writes):
  - `playtest`, plus `scope`: the person plays and writes their answers, and leaves the entry; the next session reopens the verdict with them.
  - `calibrate`, queued when the visual target passes: 8–12 captures from this build, the person's references, two or three "not our game" examples, and strips of core actions beside their reference clips. The person labels each into `docs/game/calibration/labels.json` (`answers`): `{"labels": [{"capture": "<path>", "ours": true, "why": "<one line>"}]}`. Builds go on meanwhile; the slice verdict waits for the labels. Calibration repeats when the art direction changes.
  - `compare`, plus `unblocks`: a polish feature whose acceptance is a taste call (a grade, a feel retune, a mix) is verify `human`, and its kit is two to four before-and-after pairs. The person picks one of each; the picks go into `keep.json` pins and role memory, and the feature passes on the pick.

### features.json item

```json
{
  "id": "F012", "title": "Dash with an ink trail",
  "pillar": "P1", "tier": "must", "milestone": "core-loop", "target": "feel",
  "acceptance": ["The dash responds within 2 frames of its input in the event log",
                 "The dash fires visual, sound and camera feedback in the event log"],
  "verify": {"kind": "replay", "how": "replay tests/replays/dash.json --events out/dash.jsonl; check the dash lines"},
  "pages": ["feel", "mechanics"], "measures": [], "tickets": ["#41"],
  "roles": ["feel", "audio", "art"],
  "reviews": {"feel": "docs/game/reviews/F012/feel.json", "audio": "docs/game/reviews/F012/audio.json",
              "art": "docs/game/reviews/F012/art.json"},
  "passes": false, "evidence": "", "blocked": "", "cut_reason": ""
}
```

`milestone` is one of `core-loop`, `slice` (the vertical slice), `systems`, `content`, `verdict-build` (production), `polish`. `verify.kind` is one of `test`, `sim`, `replay`, `bot`, `capture`, `check` (any scripted or recorded inspection) or `human`. `pages` lists the ids of the wiki pages the feature implements. `measures` lists the fun proxy and richness target ids whose metric this feature produces. `roles` follows "Which roles are in charge" (`[]` for a rules-only feature); `reviews` maps each of them to its review record; `target` (`visual` or `feel`) marks the visual or feel target. Ids are never reused, including ids in `docs/game/archive/`. Build attempts are counted by `gamestate.py` in `state.json` `attempts`.

## Limits

In `docs/game/state.json` `limits`:

| Limit | Default | When reached |
| --- | --- | --- |
| `budget_sessions` | 150 sessions, re-estimated by game-plan and game-polish | the run stops |
| `brainstorm_share` | 0.2 of the budget for brainstorm sessions | support topics wait; consolidate defers what is left |
| `max_adjusts` | 2 | the run stops for a human decision |
| `max_restarts` | 1 | the run stops for a human decision |
| `max_attempts` | 3 build sessions per feature since it last passed | the feature counts as blocked and goes to game-plan's unblock mode |
| `max_repeats` | 5 sessions in a row on the same step | the run stops as stalled |

## Commands

The adapter: how this project builds, runs and proves itself. Contract: the game-setup skill's `adapter-contract.md`. Empty until game-plan picks the engine.

| Name | Command | Verified |
| --- | --- | --- |
| bootstrap | | |
| build | | |
| test | | |
| run | | |
| sim | | |
| replay | | |
| bot | | |
| capture | | |
| dump | | |
| loudness | | |
| package | | |

## Companion skills

The game-* skills lean on these. When one isn't installed, do what its "If missing" column says.

| Skill | Used for | If missing |
| --- | --- | --- |
| `grilling` | walking a design tree | ask, or answer, one question at a time until every branch is resolved |
| `domain-modeling` | CONTEXT.md terms and ADRs | ADR = context, decision, consequences, in the ADR folder, numbered |
| `codebase-design` | the simulation core / presentation shell seam, deep modules | small interfaces over large implementations; test at the seam |
| `prototype` | a clickable demo of a mechanic or UI for a person to judge (interactive mode only) | skip the demo; build the feature and let the verdict judge it |
| `tdd` | building game rules test-first in the simulation core | red, green, refactor, one behaviour at a time |
| `code-review` | reviewing each session's diff | review the diff against the ticket, the wiki pages it implements and the repo's standards |
| `diagnosing-bugs` | a red verify or a regression | reproduce, minimise, hypothesise, fix, add the regression test |
| `research` | reference games, engine and platform facts from primary sources | read primary sources; save the facts with links to a notes file |
| `wizard` | a walkthrough for a multi-step human queue entry | a numbered checklist with exact URLs, clicks and where each value goes |
