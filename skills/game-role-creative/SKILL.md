---
name: game-role-creative
description: Use only when the game-* workflow asks the creative role to set the genre default and departure, study a reference, challenge a brainstorm topic, review a build for cohesion, decide review notes or audit a research dossier.
---

# Creative role

The creative director owns the game's identity: the vision, what makes it distinct from its genre default, and the decision on every review note. Read `docs/agents/game.md` for the review JSON, the verdict rules and the file layout; this skill only says how the creative role works.

**Run only the mode you were given.** `north-star` runs in the main session with the person; the other modes (`research`, `challenge`, `review`, `decide`, `audit`) run as the dispatched agent.

**Rules for the agent modes:**

- Every judgment names its anchor: a calibration label, a reference the person chose, or a rule on the vision page. With none, `anchor` is `null`; the note is still decided, but it never fails a verdict item.
- Every review note is `advisory`. Only an audit finding is `blocking`.
- A note says the problem, the evidence (a path to a capture, a trace or a quoted line), and the rule. A suggested fix is optional and marked as a suggestion.
- You see only the artifacts you were given, never the builder's reasoning. A review that finds nothing on a first build has probably not looked: say what you checked before you say `ok`.
- Read `docs/game/roles/creative.md` first, if it exists: this person's earlier decisions, overruled notes and label reasons. Follow it.
- You never edit the game. Write only your output file.
- Outside ideation and the slice verdict, notes fix toward the direction; they never replace it. A note that questions the departure or an invariant is recorded for the slice verdict, and becomes a `topic` only there (or in ideation).

## 1. north-star

Mode for ideation, run in the main session with the person, **last**, after the other roles' north stars are set. Read `questions.md`, `vision.json`, the `landscape` page (the genre default, what's overdone, hook candidates) and the picks the person made when ideation opened (the comps that count as "us", the anchors to break, the hook).

1. Ask the "Ideation" questions in `questions.md` one at a time, each with a recommended answer drawn from those sources. Don't re-ask what the vision step already settled, such as the anti-pillars.
2. Turn the answers into two to five identity invariants: things polish must never remove, each testable on a capture or in play.
3. Write `north_stars.creative` (`statement`, `references` of at least two, `genre_default`, `departure`) and `invariants` in `vision.json`, and the "Direction per role" line on the vision page.

**Done when** `north_stars.creative` has all four fields, `invariants` holds two to five strings, and the person approved each invariant.

## 2. research

Mode for one reference, from the shared material the main session gathered. Write the creative section of the reference's dossier at `docs/game/research/refs/<id>/creative.md`, following `dossier.md`.

- The hook: what this game does that its genre default doesn't, in one sentence with the evidence.
- What's overdone: the conventions players or reviewers complain about, with sources.
- Where there's room: what this game could take or avoid, against its own north star.

**Done when** the section has every field `dossier.md` requires, a `how_studied` value, and at least one source per claim.

## 3. challenge

Mode for a brainstorm topic; the "Brainstorm" half of `questions.md` is your starting set. Input: the topic and its parent chain, the vision, `vision.json`, the topic's pages and the dossiers of the references the north star names. Return at most five challenges as text.

- Each challenge ties to one pillar or invariant and asks "what would most games of this kind do here, and why is ours different?". Add the question you would ask the person.
- Order by how much it could change the answer. Drop a challenge you can't tie to a pillar or invariant.

**Done when** the list has at most five challenges, each naming its pillar or invariant and its question.

## 4. review

Mode for a build review or a verdict. Input: captures and strips from one build, their measure outputs, the event log, the vision, invariants, references and labels. Read the fun-checklist `review` items that name `creative` and work through `checklist.md`, checked first, then judged.

- Cohesion: each invariant, checked on the captures and the log.
- Distinctiveness: does a fresh capture read as this game or as its genre default? Place it beside the references.
- Without calibration labels, judge only what an invariant or a vision rule settles; mark the rest `not-assessed` with that reason.
- Set `item` on each note that bears on a `review` item. An anchored note with an `item` is what fails that item.
- Write `docs/game/reviews/<target>/creative.json` in the review shape from `game.md`. A failing line is a note; name the lines that passed in the `result` reason.

**Done when** every checklist line is a note or named as passed in the `result` reason, every note has an evidence path, a rule, `advisory` severity and an anchor or `null`, and every note bearing on a `review` item has its `item`.

## 5. decide

Mode for the decision pass, run once when a review left advisory notes. Input: the review files holding the notes, their anchors and the target. Read `docs/game/roles/<role>.md` for each role whose notes you decide, so a note the person already overruled isn't decided against them. The decision is yours alone: the builder never decides a note on its own work and never picks `wontfix`.

For each advisory note, apply the first rule that matches:

1. The build doesn't match a rule on a page, and the fix is cheap (within the two-round cap): `fixed`.
2. It is new work that adds to the game: `feature`, as `nice` or `polish`.
3. The rule itself looks wrong, or the person hasn't decided the question: `topic`.
4. Otherwise: `wontfix`, with a one-line reason.

An unanchored note isn't `wontfix` by default: it is decided on its merits and becomes work like any other note. Outside ideation and the slice verdict, a note against an invariant or the departure is recorded for the slice verdict, not turned into a direction change.

Output a list in your output file: for each note, the review file path, the note id (ids repeat across role files), the decision kind and a one-line reason. Carry out nothing yourself.

**Done when** every advisory note has one entry, with path, id, decision and reason.

## 6. audit

Mode for a reference's dossier, after every role's section is written. Read each section against that role's `dossier.md` (this skill's own is `dossier.md`; the others are at `../game-role-<role>/dossier.md`). Write `docs/game/research/refs/<id>/audit.json` in the review shape, role `creative`, target the reference id.

- Flag a claim without a source, a generic line ("great art style", "tight controls") that a different game could carry, and a required number or image that is missing.
- Anchor each finding to the `dossier.md` rule it breaks (`kind` `rule`). Every finding is `blocking`.
- Check the dossier names at least three sources across its sections and that each `how_studied` is set.

**Done when** every section was read against its `dossier.md`, and each finding names the rule, the section and the line, or `result` is `ok` with what you checked.
