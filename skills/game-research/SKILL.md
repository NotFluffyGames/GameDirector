---
name: game-research
description: Research the game's market and references. Before ideation, alone, a landscape scan of comparable games, the genre's anchors and defaults, player complaints and candidate references; after ideation, one session per reference opened for study, writing per-role dossiers, then a brief and the person's homework, which brainstorm waits on. Handles the scan and research phases of the game-* workflow; also re-scans after a restart.
disable-model-invocation: true
---

# Game Research

Keeps the game from being designed from memory. The **scan** maps the landscape before ideation, so the person chooses a direction that isn't generic; the **deep study** reads the references ideation opened, one per session, so brainstorm grills topics with evidence. What the agent can't do itself becomes the person's homework, and brainstorm waits for it. Read `docs/agents/game.md` first and follow its session rules.

| Task | When | Mode |
| --- | --- | --- |
| `game-research scan` | phase scan, the agent alone | [Scan](#scan): the `landscape` page and the candidate references |
| `game-research ref <id>` | phase research, the agent alone | [Ref](#ref): one open reference studied into a dossier per role, then audited |
| `game-research brief` | phase research, the agent alone | [Brief](#brief): the `research` page from the dossiers, and the homework |
| `game-research homework` | with a person, before brainstorm's topics | [Homework](#homework): each open homework item answered or skipped |
| `game-research restart <adr>` | phase scan, after a verdict's restart | [Restart](#restart): the scan again in light of the ADR, studied dossiers kept |

**Paths.** This skill's base directory is the folder this SKILL.md was read from. Resolved from it: [sources.md](sources.md) (the sources, their terms, the review-count multipliers and the methods), each role's skill `../game-role-<role>/SKILL.md` and section rules `../game-role-<role>/dossier.md`, its stance `../../agents/<role>.md`, game-review's `../game-review/SKILL.md` (dispatch mechanics) and `../game-review/scripts/measure.py`.

## Rules for every mode

- **Market lines.** Every number (reviews, prices, playtimes, units, shares) carries its source link and retrieval date, or reads `not researched: <why>`. None comes from memory; a fact read only in a search engine's summary is marked as such. Units are a range from the review count and the launch-year multiplier in `sources.md`, never a point.
- **Sources.** Fetch only on the terms in `sources.md`; SteamDB never. `state.json` `research_sources` lists the hosts setup found unreachable: probe one again before giving up on it. Work an unreachable source would have done becomes a homework candidate.
- **Images** are the evidence for the art, ux and feel sections, committed with the dossier, always downscaled.
  - Save each in `docs/game/research/refs/<id>/<role>/` for the role that uses it (`art`, `ux`, `feel`; in both folders when two use it), named by what it shows (`hud.png`, `dash-strip.png`), with its source in `material/index.md`.
  - Shrink it: `python3 <measure.py> shrink IN.png --out OUT.png` (longest side at most 1280 px). `measure.py` reads only 8-bit, non-interlaced PNG: convert anything else (JPEG, WebP, a 16-bit or interlaced PNG) first with what this machine has (`magick` or `convert`, `ffmpeg`, Python's Pillow, macOS `sips`). With no converter, keep an original PNG, JPEG or WebP as is only when it is at most 1280 px on its longest side and at most 500 KB (`file` prints its dimensions; Steam's `path_thumbnail` qualifies); otherwise save nothing, and the image is `not-assessed: no converter`.
- **Homework candidates.** What the agent can't do goes on a list as it arises: a game it can't play (a person playing it is the strongest evidence for feel, ux and audio), sound it can't hear, an unreachable source, an image no source gives, an audit finding it couldn't fix. In a ref session, into the reference's `homework` list in `references.json`, one line each: what a person does and the gap it fills ("play R3 for 20 minutes and time the dash's recovery: feel"); the gate accepts a reference short of sources whose gap is named there. In a scan, into the landscape page's "Not researched" section. The brief ranks them.
- **Pages last.** Every page is drafted in `docs/game/drafts/<page-id>.md` and written in the docs place after the state commit, as "Pages are written last" in `docs/agents/game.md` says. A new wiki page gets a `wiki.json` entry (`id`, `title`, area `Vision`, `link`, `version` read back as `docs/agents/docs.md` says, `updated`) and a line under Vision on the home page, whose `index` entry gets its new `version` and `updated` in the same pages commit.
- **Offer, never choose.** Which comps count as "us", which anchors to break, the hook, the references and the price are the person's picks in ideation. A weak number states the odds; it never drops a direction.

## The research files

`gamestate.py check` validates their shapes; `gamestate.py gate` reads them.

- `docs/game/research/references.json`: `{"scanned_for": null, "refs": [...]}`. `scanned_for` is the restart ADR the last scan ran for, `null` before any restart. Each ref:
  - `id` (`R1`, `R2`… in order, never reused: a new one is the next after the highest any version of the file held, found with `git log -p -- docs/game/research/references.json`, not only in the current file), `title`;
  - `why`: `comp` (a comparable game) or `aspect` (a reference for play, look, feel, sound, tone or identity);
  - `roles`: the role ids it informs; `sources`: links, or `person: <homework id>, <date>`;
  - `status`: `candidate` (from the scan), `open` (ideation picked it), `studied` (its dossier is done);
  - `how_studied`: per role, `{"how": "played" | "watched" | "read" | "not-assessed", "reason": "..."}`;
  - `homework`: its candidates (above), non-empty strings.
- `docs/game/research/refs/<id>/`: `material/` (the gathered sources, `index.md`, page copies in `pages/`), one dossier section `<role>.md` per role, the image folders `art/`, `ux/` and `feel/`, and `audit.json` (the review record from `docs/agents/game.md`: role `creative`, target `<id>`).
- `docs/game/research/homework.json`: `{"reason": "", "page": "<link>", "items": [...]}`, at most ten items in rank order, or none with a `reason`. Each item: `id` (`H1`…), `what`, `why`, `questions` (a list), `minutes`, `roles`, `status` (`open`, `answered` or `skip`), `answer`, `ticket`.
- Wiki pages `landscape` (the scan) and `research` (the brief), both area Vision.

## Scan

Task `game-research scan`. One session, the agent alone, from the seed. It writes the `landscape` page and starts `references.json`; ideation then goes through both with the person.

### 1. Read the seed

Read `docs/game/seed.md`, `state.json` `intent` and `research_sources`, and [sources.md](sources.md). A scan that resumes goes on from its committed `references.json` and `landscape` draft.

**Done when** you can name the one to three genres or tags the seed sits in, the intent, and which hosts this machine reaches.

### 2. Find the comps

Gather comparable games by proximity, as `sources.md` describes.

- **`sell`**: three to five; the gate needs at least three. For each: launch year, price, top tags, review count across all languages and score with the date read, the units range from that count and the launch year's multiplier, median playtime at review, each with its source. SteamSpy owners only as a cross-check.
- **`hobby`**: the three to five closest games, from itch.io as readily as Steam, without sales numbers.

Write each comp to `references.json`: the next `id`, `title`, `why` `comp`, `roles` (the roles it is evidence for: `creative` for the genre default, `design` for the loop, others where it is also a look, feel, sound, tone or UI reference), `sources`, `status` `candidate`, `how_studied` `{}`.

**Done when** every comp has its entry and its values, each sourced and dated or `not researched: <why>`, and a `sell` game has at least three comps.

### 3. Read the complaints

For each comp, pull its negative reviews in all languages with playtime at review, then a sample of positive ones (itch.io comps: their comments and ratings). Read past the rants, cluster the complaints into themes, and count them. The complaints are the richest design input here: most negative reviews are about design.

**Done when** each comp's reviews were read, or it is marked `not researched: <why>`, and every theme has its count, the comps it appears in and one quoted line with its review id and link.

### 4. Map the genre and the player

From the comps' store data, reviews and achievements, and the methods in `sources.md`:

- **anchors**: what players of the genre expect, each with the comps that show it;
- **the genre default**, in a paragraph, and what's overdone; the creative role asks the person to depart from it;
- **the player**: two or three Quantic Foundry motivations the comps and the seed's loop serve, those not served, who it isn't for, the games they already play ("plays X, Y and Z; wants A and B; leaves at C"), and the SDT and PENS needs the loop must meet;
- **norms**: platform, input and session length the comps set, and price for `sell`;
- **hook candidates**: two or three departures from the default, each a phrase pairing the anchor genre with its hook; none chosen;
- **risks**: for `sell`, saturation and the odds, stated plainly; for both, the design risks the complaints show.

**Done when** every item is written with its sources, and none of them makes a choice that is the person's.

### 5. Propose references

Offer candidate references per aspect, each with what it offers this seed and what to avoid: play (`design`), look (`art`, `ux`), feel (`feel`), sound (`audio`), tone and world (`narrative`), identity (`creative`). Games mostly; films, books and artworks where the aspect calls for them. Each is a `references.json` entry with `why` `aspect`, its roles, `sources` and `status` `candidate`; a comp that also serves an aspect gains that role instead of a second entry.

**Done when** every role has at least two candidates (comps included), and every entry has a `title`, `why`, `roles`, a source and status `candidate`.

### 6. Write the landscape and close

Draft `docs/game/drafts/landscape.md` (title "Landscape"):

- a header line: the intent, the retrieval dates, the hosts reached and not;
- the genre frame; the comps as a table; the anchors; the genre default and what's overdone; the complaint themes; the player; the norms; the hook candidates;
- the candidate references per aspect: id, title, what to take, what to avoid;
- the risks;
- **Not researched**: each gap with its reason, for the brief's homework.

Draft the home page with the landscape's line under Vision. Run `gamestate.py check --since <base>`, commit `references.json` with the drafts, and append a progress entry. Then the pages commit (Pages last), and `gamestate.py complete`.

**Done when** the landscape page and its `wiki.json` entry are committed, no scan draft remains, and `complete` succeeds.

## Ref

Task `game-research ref <id>`. Phase research, the agent alone, one reference per session: the state tool hands out each `open` reference in turn, then a `studied` one whose dossier falls short. Each role studies the reference against this game's vision and its own north star: what to take, what to avoid.

### 1. Prepare

Read the reference's entry, `vision.json` (its roles' north stars, the invariants, `roles_off`), and whatever `docs/game/research/refs/<id>/` already holds. Copy the `vision` and `landscape` pages into `material/pages/`, from their drafts when they exist, else from the docs place (the role agents can't reach it). Remove from the entry's `roles` every role in `roles_off`.

- **Status `open`**: the whole study, steps 2–7, skipping a step whose **Done when** already holds (an earlier session split).
- **Status `studied`** (handed out again): run `gamestate.py gate` and do only what clears its lines starting `<id>:`, then audit again (step 6) when a section changed.

**Done when** you know which steps this session runs, and the page copies are in `material/pages/`.

### 2. Gather the material, once

Into `material/`, once for every role:

- the store page: description, price, release date, genres, tags, platforms;
- reviews in all languages, negative first, then positive: up to 100 negative and 50 positive, spread across playtime, each with its language, playtime at review, date and `recommendationid`, a non-English one followed by its English translation;
- wikis, guides, manuals and patch notes: the numbers (timings, costs, counts) and the UI;
- for a reference that isn't a game (a film, a book, an artwork), its pages and published stills;
- `material/index.md`: one line per source with its URL, retrieval date, what it gave and the file that holds it; a source that failed: `<source>: n/a: <reason>`.

**Done when** every source is a file under `material/` with its index line, or an `n/a` line with its reason, and at least three are gathered, or each gap has a candidate in the entry's `homework` saying what a person does to fill it (the failed hosts go in the progress entry).

### 3. Play and capture

The reference's image roles need: `art/` a play moment and the UI (at least two); `ux/` a first-minute moment and the HUD; `feel/` a frame strip per core action the reference shares with this game (`north_stars.feel` names them).

- **Playable in a browser** (an itch.io HTML5 build, a web game): play it with Playwright (the Python or Node package, installed or installable, or a browser tool this session has). Screenshot the first minute and the HUD; for each core action, N frames every K ms after the scripted input, stitched with `measure.py sheet`. Note what you played and for how long: the roles' `how_studied` is `played`.
- **Otherwise**: the store's screenshots, and where `ffmpeg` exists, frames from its trailer around each core action, stitched into strips: `watched`.

Shrink and index every image (Images), then run `measure.py derive` on each PNG art shot into `art/derived/<shot>/`: the art role reads its palette from them, and the role agents write nothing but their sections. A JPEG or WebP original kept without a converter gets no derived copies: its index line says so, and the art role reads that shot as it is.

**Done when** every image role of the reference has its images in its folder, shrunk and indexed, or a reason it has none, which is its section's `not-assessed` reason and a homework candidate.

### 4. Dispatch the roles in parallel

Commit the material: `game-research: <id> material`. Then dispatch one agent per role in the reference's `roles`, all at once, with the agent type, model tier, absolute paths and no-subagent fallback of game-review's step 3. Each prompt gives:

- mode `research`, and the reference's entry;
- `material/index.md`, the page copies, `docs/game/vision.json`, the role's image folder, its memory `docs/game/roles/<role>.md` and its `dossier.md`;
- how the material was got (played, frames, text), so its `how_studied` is true to it; an image role with no images is `not-assessed` with step 3's reason;
- its output, its only file: `docs/game/research/refs/<id>/<role>.md`.

Check independence as item 1 of game-review's step 4 does, the dispatch's outputs being these sections. A section missing, or without a `how_studied`: dispatch that role once more; still missing, write it yourself as `not-assessed` with that reason. Commit: `game-research: <id> dossiers`.

**Done when** every role of the reference has its section committed and the tree is clean.

### 5. Record

In the reference's entry: `how_studied` per role, from its section (`how`, and the reason it gives); `sources`, the distinct sources the sections cite; `status` `studied`. Commit, then run `gamestate.py gate`.

**Done when** every role of the reference has a `how_studied` entry, and `gate`'s lines for `<id>` name only the audit and, at most, the source count (the audit takes that up).

### 6. Audit, at most two rounds

1. Dispatch `creative` in `audit` mode, with the most capable model available, as in step 4: the reference's `references.json` entry with its `homework` list, the section paths, each role's `dossier.md`, `material/index.md`, and the output `docs/game/research/refs/<id>/audit.json`. A gap the entry's `homework` names (fewer than three sources, a missing number, image or sample) is the person's to fill, so it is no finding. Check independence as in step 4, then set the record's facts yourself: role `creative`, target `<id>`, `commit` (HEAD at dispatch), `independent: true` (`false` without a subagent tool), `inputs` (the section paths). Its findings are all `blocking` by the audit mode's rule, unlike a review's. Run `check --since <base>` and commit: `game-research: <id> audit round <n>`.
2. `result` `ok`: the audit is done. Otherwise fix every finding:
   - a missing image, number or source: gather it (steps 2–3);
   - send each role with findings back to its section as in step 4, with the audit's path and its note ids, to rewrite what they name;
   - a finding that can't be fixed in this session: remove the line (a sourceless claim, a generic line) or mark the field `not-assessed: <reason>` in its section, and add a homework candidate;
   - update the entry as step 5 does, and commit: `game-research: <id> fix round <n>`. Set each note's `decision` to `fixed <that commit>` and commit the audit.
3. After round 1's fixes, audit once more (round 2, overwriting `audit.json`; round 1's stays in git history) and fix its findings the same way. There is no third audit.

**Done when** `audit.json` is committed with `result` `ok` or every note `fixed <commit>`, and `gamestate.py gate` names nothing for `<id>`.

### 7. Close

Run `gamestate.py check --since <base>`, commit the entry's homework candidates and anything left, and append a progress entry. A ref session writes no page and runs no `complete`: the brief completes the phase.

**Done when** the tree is committed, `check --since <base>` passes, and `gate` names nothing for `<id>`.

## Brief

Task `game-research brief`, once every opened reference is studied. Phase research, the agent alone. It synthesizes what the studied references teach the chosen direction, and turns what's still unknown into the person's homework.

### 1. Read

Read every studied reference's sections and entry (its homework candidates included), the `landscape` page (complaint themes, risks, "Not researched"), `vision.json` (north stars, invariants, the chosen direction), the `vision` page, and `state.json` `research_sources`. A brief that resumes picks up its drafts and `homework.json`.

**Done when** you can list, per aspect, the references studied for it, and every homework candidate with where it came from.

### 2. Draft the brief

Draft `docs/game/drafts/research.md` (title "Research"):

- **per aspect** (play, look, feel, sound, tone and world, first minute and HUD, identity): what to take and what to avoid, each line tied to the north star it serves and pointing to its dossier section;
- the complaint themes that matter for the chosen direction;
- the risks;
- **unknowns**: what nobody could find out, each pointing to its homework item or saying why it isn't pursued.

**Done when** every studied reference appears under an aspect, every take or avoid line points to a dossier section, and every unknown points to a homework item or a reason.

### 3. Rank the homework

From every studied reference's `homework` candidates, the unknowns and the unreachable sources whose work still matters, merge duplicates and rank by how much each answer could change a decision: a north star, a slice topic, a risk. Keep at most ten; the rest go under the brief's unknowns as "not pursued: ranked below ten". A candidate that an item in `docs/game/archive/*/homework.json` already answered or skipped isn't asked again. The entries' `homework` lists stay as they are: the gate reads them.

Write `docs/game/research/homework.json` in rank order. Each item:

- `id`: `H1`…, continuing after the highest id in `docs/game/archive/*/homework.json`;
- `what`: a task a person can do, with its subject ("play R3 for 20 minutes", "find three screenshots of how R2 shows damage", "check the R1 community for what players miss");
- `why`: the decision or role it feeds; `questions`: what to answer; `minutes`: the time it takes; `roles`;
- `status` `open`, `answer` `""`.

With no item, `items` is `[]` and `reason` says why. Draft the homework page, `docs/game/drafts/homework.md` (title "Research homework"): brainstorm waits until each item is answered or skipped, and skipping is fine (a game they don't own); answers go in a comment on the page or on the item's ticket, or to a `/game-next` session; then the items in rank order, each with what, minutes, why, questions and an empty answer.

**Done when** `homework.json` passes `check` with at most ten complete items in rank order, or none with a reason, and the homework draft lists the same items.

### 4. Close

Run `gamestate.py check --since <base>`, commit `homework.json` and `references.json` with the drafts, and append a progress entry. Then the pages:

- the `research` page and the home page, as Pages last says. After a restart the `research` page and its `wiki.json` entry already exist: rewrite the page and update the entry's `version` and `updated`, never adding a second entry;
- the homework page in the docs place beside the wiki (after a restart, rewrite the one the latest `docs/game/archive/*/homework.json` links). It isn't a wiki page, since people write answers on it: record its link as `homework.json` `page`;
- each item as a `ready-for-human` ticket (`docs/agents/issue-tracker.md`) titled `<id>: <what>`, linking the homework page, recorded as the item's `ticket`.

Delete the drafts and commit: the pages commit. Then `gamestate.py gate` and `gamestate.py complete`.

**Done when** the `research` page and its `wiki.json` entry, the homework page's link and the tickets are committed, no brief draft remains, and `complete` succeeds.

## Homework

Task `with-user: game-research homework`. Phase brainstorm, with a person, before any topic: brainstorm waits until every item is `answered` or `skip`.

### 1. Read

Read the open items in `homework.json`, the comments on the homework page and on each item's ticket (answers people left there), the `research` page and the dossier sections each item feeds.

**Done when** you know, for each open item, any answer already left and where.

### 2. Go through the items

One item at a time, in rank order: its what, why, questions and minutes, with an answer already left read back for the person to confirm. The person answers (from having done it, or doing it now), skips it with a reason (`skip`, the reason in `answer`), or keeps it for later (it stays `open`, and brainstorm keeps waiting). Record `status` and `answer` in their words, dated. Where an answer describes something visual, ask for screenshots and save them (Images).

**Done when** every open item was put to the person, and each is answered, skipped, or kept open by their choice.

### 3. Fold the answers in

- **The dossiers.** Each answer goes into the sections of its references and roles under "From the person (`<id>`, `<date>`)". A person who played the reference sets that role's `how_studied` to `played`, reason the item id, and adds `person: <id>, <date>` to the entry's `sources`; an image role keeps `not-assessed` while its folder has no image.
- **The brief.** Draft the `research` page with what the answers change: take and avoid lines, unknowns resolved.
- **Contradictions.** An answer that contradicts a decided north star, an invariant or a written page becomes an open topic with the fields `docs/agents/game.md` lists, its parent the topic that wrote the page (`T1` for a north star), the item's roles in `roles`, and a `ready-for-human` ticket. The north star or page stays as it is until that topic is brainstormed.

**Done when** every answer is in its dossier sections and the research draft, and every contradiction is a topic with a ticket.

### 4. Close

Close the tickets of answered and skipped items, with the answer or the reason. Draft the homework page with the answers. Run `gamestate.py check --since <base>`, commit `homework.json`, `references.json`, the dossiers, any images and `topics.json` with the drafts, and append a progress entry. Then the pages commit: the `research` page (its new `version` and `updated` in `wiki.json`) and the homework page. Brainstorm has no task to complete: its topics follow.

**Done when** the pages commit is in, no draft from this session remains, and `check --since <base>` passes.

## Restart

Task `game-research restart <adr>`. Phase scan, after a verdict's restart. A changed direction changes which games are comparable, so the landscape is redone; studied dossiers are kept, ideation picks again, and research studies only the newly opened references.

### 1. Read the restart

Read the ADR (what failed and what changes), the seed, the current `landscape` page, `references.json` and `vision.json`.

**Done when** you can say which parts of the landscape the ADR changes: the comps, anchors, player, norms, hooks, references.

### 2. Re-scan

Redo the scan's steps 2–5 for the parts the ADR changes:

- keep the comps that still fit and add new ones; a `sell` game has at least three that fit;
- a `candidate` that no longer fits is deleted, and its id isn't reused: a new reference takes the next id after the highest in the file's git history (`git log -p -- docs/game/research/references.json`), which still holds the ids of deleted entries;
- a `studied` entry and its dossier stay as they are.

Draft the landscape page from the current one, rewritten wherever the ADR changes it. Set `references.json` `scanned_for` to the ADR's path exactly as `state.json` `restart_adr` holds it.

**Done when** the landscape draft and `references.json` answer the ADR, every studied entry is unchanged, and `scanned_for` equals `restart_adr`.

### 3. Close

As the scan's step 6, updating the `landscape` page and its `wiki.json` entry rather than adding one, then `gamestate.py complete`.

**Done when** the landscape page's new `version` and `updated` are committed, no draft remains, and `complete` succeeds.
