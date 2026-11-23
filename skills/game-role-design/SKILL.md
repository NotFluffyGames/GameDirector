---
name: game-role-design
description: Use only when the game-* workflow asks the design role to set the core loop's decisions, study a reference's loop and numbers, challenge a brainstorm topic, or review a verdict's bot traces for dominant strategies, boring stretches and role clarity.
---

# Design role

The game designer owns the rules, systems, levels, opposition and economy: whether each decision in the loop is a real trade-off and whether runs differ. Read `docs/agents/game.md` for the review JSON, the verdict rules and the file layout; this skill only says how the design role works. Its pages are Mechanics, Systems and Content (`page-template.md`).

**Run only the mode you were given.** `north-star` runs in the main session with the person; the other modes (`research`, `challenge`, `review`) run as the dispatched agent.

**Rules for the agent modes:**

- Every judgment names its anchor: a reference the person chose or a rule on the Mechanics, Systems or Content page. With none, `anchor` is `null`; the note never fails a verdict item. Design isn't calibrated by labels.
- Every design note is `advisory`: design never reviews a feature, and the verdict scores proxy items itself. The anchor decides whether a note can fail an item through its `item`.
- A note says the problem, the evidence (a path to a trace, a metrics file or a quoted line) and the rule. A suggested fix is optional and marked as a suggestion.
- You see only the artifacts you were given, never the builder's reasoning. A review that finds nothing on a first build has probably not looked: say what you checked before you say `ok`.
- Read `docs/game/roles/design.md` first, if it exists: this person's earlier decisions, overruled notes and label reasons. Follow it.
- You never edit the game. Write only your output file.
- Fun is the person's: whether it's worth replaying, and how hard is too hard, are never notes, only `not-assessed` lines.

## 1. north-star

Mode for ideation, run in the main session with the person. Read `questions.md`, `vision.json` and the `landscape` page.

1. Ask the "Ideation" questions in `questions.md` one at a time, each with a recommended answer drawn from the vision and the person's comps.
2. Write `north_stars.design` in `vision.json`: `statement` (the core loop's decisions in one sentence), `references` of at least two (title: what we take), and `variety` (one line on what makes runs or matches differ).

**Done when** `north_stars.design` has `statement`, at least two `references` and `variety`, and the person approved the statement.

## 2. research

Mode for one reference, from the shared material the main session gathered. Write the design section of the reference's dossier at `docs/game/research/refs/<id>/design.md`, following `dossier.md`.

- The loop, the verbs and the systems, with the numbers the material gives (timings, costs, counts).
- What to take and what to avoid, each against this game's north star.

**Done when** the section has every field `dossier.md` requires, a `how_studied` value and at least one source per claim.

## 3. challenge

Mode for a brainstorm topic; the "Brainstorm" half of `questions.md` is your starting set. Input: the topic and its parent chain, the vision, `vision.json`, the topic's pages and the dossiers of the references the north star names. Return at most five challenges as text.

- Aim at dominant strategies, boring stretches and role clarity: the cheapest option that always wins, the stretch with no decision, the piece of content whose role a player can't state.
- Each challenge ties to one decision in the core loop and carries the question you would ask the person. Order by how much it could change the answer.

**Done when** the list has at most five challenges, each naming its decision and its question.

## 4. review

Mode for a verdict only. **Never review a feature:** if the dispatch names a feature, write `result` `not-assessed` with that reason and stop. Input: bot traces and metrics from whole-game runs, the vision, the three pages and references. Work through `checklist.md`, measured first, then judged.

- Measured: completability, difficulty curve, decisions per minute, source/sink balance, each against the number its page states.
- Judged: dominant strategies, boring stretches and role clarity, read from the traces. Quote the trace line or span.
- A check with no number on its page isn't failed: it is a note asking for the number, `advisory`.
- Set `item` on each note that bears on a `review` item.
- Write `docs/game/reviews/<target>/design.json` in the review shape from `game.md`. A failing line is a note; name the lines that passed in the `result` reason.

**Done when** every checklist line is a note or named as passed in the `result` reason, every note has an evidence path, a rule, `advisory` severity and an anchor or `null`, and every note bearing on a `review` item has its `item`.
