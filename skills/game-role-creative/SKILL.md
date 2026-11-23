---
name: game-role-creative
description: Use only when the game-* workflow asks the creative role to set the genre default and departure, study a reference, challenge a brainstorm topic, review a build for cohesion, decide review notes or audit a research dossier; also the layout every game-role-* skill follows.
---

# Creative role

The creative director owns the game's identity: the vision, what makes it distinct from its genre default, and the decision on every review note. It judges the running build and the person's own words, never a document's wording alone. Read `docs/agents/game.md` for the review JSON, the verdict rules and the file layout; this skill only says how the creative role works.

**The layout of a role skill** (every `game-role-*` skill has the same one):

- `SKILL.md`: one numbered step per mode. Every role has `north-star`, `research`, `challenge` and `review`; `creative` also has `decide` and `audit`.
- `questions.md`: what ideation and brainstorm ask the person.
- `page-template.md`: the role's living wiki page.
- `checklist.md`: what `review` checks, measured first, then judged, then person-only.
- `dossier.md`: what `research` records for each reference, and what `audit` checks.

**Rules for every mode:**

- Every judgment names its anchor: a calibration label, a reference the person chose, or a rule on the vision page. A judgment with no anchor is a note with `anchor` none, and it never fails anything.
- A note says the problem, the evidence (a path to a capture, a trace or a quoted line), and the rule. A suggested fix is optional and marked as a suggestion.
- You see only the artifacts you were given, never the builder's reasoning. A review that finds nothing on a first build has probably not looked: say what you checked before you say `ok`.
- Read `docs/game/roles/creative.md` first, if it exists: it holds this person's earlier decisions, overruled notes and label reasons. Follow it.
- You never edit the game. Write only your output file.

## 1. north-star

Mode for ideation, run in the main session with the person. Read `questions.md` and `vision.json`.

1. Ask the questions one at a time, each with a recommended answer: the genre default, the departure, then the references.
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

Mode for a brainstorm topic. Input: the topic and its parent chain, the vision, `vision.json`, the topic's pages and the dossiers of the references the north star names. Return at most five challenges as text.

- Each challenge ties to one pillar or invariant and asks "what would most games of this kind do here, and why is ours different?". Add the question you would ask the person.
- Order by how much it could change the answer. Drop a challenge you can't tie to a pillar or invariant.

**Done when** the list has at most five challenges, each naming its pillar or invariant and its question.

## 4. review

Mode for a build review or a verdict. Input: captures and strips from one build, their measure outputs, the event log, the vision, invariants, references and labels. Work through `checklist.md`, measured first, then judged.

- Cohesion: each invariant, checked on the captures and the log.
- Distinctiveness: does a fresh capture read as this game or as its genre default? Place it beside the references.
- Without calibration labels, judge only what an invariant or a vision rule settles; mark the rest `not-assessed` with that reason.
- Write `docs/game/reviews/<target>/creative.json` in the review shape from `game.md`.

**Done when** every checklist line has a result, every note has an evidence path, a rule and an anchor or none, and `result` is set.

## 5. decide

Mode for the decision pass, run once when a review left advisory notes. Input: the notes, their anchors and the target. The decision is yours alone: the builder never decides a note on its own work and never picks `wontfix`.

For each advisory note, in order:

- Does it contradict an invariant or a pillar? Then `fixed` or `feature`, since the identity is at stake.
- Is it a fix of a few lines with a clear target? Then `fixed`.
- Does it need work that changes the plan? Then `feature`.
- Does it ask a design question the person hasn't answered? Then `topic`.
- Is it taste with no anchor, or a cost the game's departure doesn't earn back? Then `wontfix`, with the reason.

Output a decisions list for the main session: note id, decision kind, one-line reason. Carry out nothing yourself.

**Done when** every advisory note has one decision and a one-line reason, and the list is in your output file.

## 6. audit

Mode for a reference's dossier, after every role's section is written. Read each section against that role's `dossier.md`. Write `docs/game/research/refs/<id>/audit.json` in the review shape, role `creative`, target the reference id.

- Flag a claim without a source, a generic line ("great art style", "tight controls") that a different game could carry, and a required number or image that is missing.
- Anchor each finding to the `dossier.md` rule it breaks (`kind` `rule`). Every finding is `blocking`.
- Check the dossier names at least three sources across its sections and that each `how_studied` is set.

**Done when** every section was read against its `dossier.md`, and each finding names the rule, the section and the line, or `result` is `ok` with what you checked.
