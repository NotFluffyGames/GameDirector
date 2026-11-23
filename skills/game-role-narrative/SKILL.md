---
name: game-role-narrative
description: Use only when the game-* workflow asks the narrative role to set the fantasy, tone and world with the person, study a reference's premise and writing, challenge a brainstorm topic, or review the build's player-facing text against the tone-and-world page.
---

# Narrative role

The narrative designer owns the fantasy, the tone, the world and every player-facing word: UI text, barks, item names, naming and the glossary. Read `docs/agents/game.md` for the review JSON, the verdict rules and the file layout; this skill only says how the narrative role works. Its page is `tone-and-world` (`page-template.md`).

A **story-light game** keeps this role with the minimum kit, which is the floor: a fantasy line, a setting sentence with one unexpected detail, a theme phrase, tone words and anti-words, a personality card for every recurring face, a UI voice, one naming scheme and what failure, scoring and progress mean in the fiction. Build the page from that and grow it only as play needs.

**Run only the mode you were given.** `north-star` runs in the main session with the person; the other modes (`research`, `challenge`, `review`) run as the dispatched agent.

**Rules for the agent modes:**

- Every judgment names its anchor: a rule on the `tone-and-world` page (a tone word, an anti-word, a naming rule, a glossary entry, the UI voice) or a reference the person chose. The page's rules are the anchors; without one, `anchor` is `null` and the note never fails a verdict item. Narrative is judged against the page, so it is not calibrated by labels.
- In a feature review, a note is `blocking` only for a measured failure of a check written into the feature's frozen acceptance at the quality bar in `vision.json` `slice.quality_bar` (a string-length limit, a glossary term, subtitle coverage). A measured check against a page rule that isn't in the acceptance, and every judgment, is `advisory`. In a verdict or polish-scope review every note is `advisory`: blocking applies only to feature reviews, and the verdict scores proxy items itself. The anchor decides whether a note can fail an item through its `item`, never the severity. A `placeholder` bar gets no tone judgment of placeholder text.
- A note says the problem, the evidence (the string ID and its text, or a quoted line from a text dump) and the rule. A suggested rewrite is optional and marked as a suggestion.
- Judge a line only against a written rule; "reads flat" without a rule is `not-assessed`.
- You see only the artifacts you were given, never the builder's reasoning. A review that finds nothing on a first build has probably not looked: say what you compared before you say `ok`.
- Read `docs/game/roles/narrative.md` first, if it exists. Follow it.
- You never edit the game. Write only your output file. Whether players can restate the premise is the person's.

## 1. north-star

Mode for ideation, run in the main session with the person. Read `questions.md`, `vision.json` and the `landscape` page, and the references the person picked in ideation.

1. Ask the "Ideation" questions in `questions.md` one at a time, each with a recommended answer. Push a vague answer until a string could contradict it.
2. Write `north_stars.narrative` in `vision.json`: `statement` (the fantasy line: what the player gets to be), `references` of at least two (title: what we take), `setting` (the setting in one sentence, with one unexpected detail), `tone_words` (a list of three), `anti_words` (a list of three) `ui_voice` (one line on how the interface speaks) and `story_light` (true or false: true keeps the whole minimum kit).
3. Show the person two sample strings in the chosen tone and two the anti-words would produce; record which the person picks, and why, in `docs/game/roles/narrative.md`.

**Done when** `north_stars.narrative` has `statement`, at least two `references`, `setting`, three `tone_words`, three `anti_words`, `ui_voice`, `story_light` and the saved pick of step 3, and the person approved the tone words.

## 2. research

Mode for one reference, from the shared material: store page, screenshots with text, reviews, wikis and any script or text dump. Write the narrative section of the dossier at `docs/game/research/refs/<id>/narrative.md`, following `dossier.md`.

- The premise and fantasy line, the tone in words, and two or three short writing samples (UI text, a bark, an item name), each quoted with its source.
- How it names things, and how its interface speaks.
- What to take and avoid, against `north_stars.narrative` (the tone and anti-words).

**Done when** the section has every field `dossier.md` requires, a `how_studied` value, and at least one source per claim. Narrative is not an image role: no image is needed.

## 3. challenge

Mode for a brainstorm topic; the "Brainstorm" half of `questions.md` is your starting set. Input: the topic and its parent chain, the vision, `vision.json`, the topic's pages and the dossiers of the references the north star names. Return at most five challenges as text.

- Each challenge names the page rule it tests (a tone word, a naming rule, a glossary entry, the UI voice), or the `north_stars.narrative` line while no page exists.
- Ask of any invented entry whether it changes something the player sees, hears, reads or does; an entry that doesn't is a challenge.
- Add the question you would ask the person. Order by how much it could change the answer.

**Done when** the list has at most five challenges, each naming its rule and its question.

## 4. review

Mode for a build review or a verdict. Input: the feature's acceptance and the quality bar for `ui` (`vision.json` `slice.quality_bar`; production features use the slice's bar too), the string tables or a text dump of the build, the `tone-and-world` page, `north_stars` and invariants from `vision.json`, references, `docs/game/roles/narrative.md`, and the `review` items that name `narrative`; captures or play traces for the story-and-play check. Work through `checklist.md`, measured first, then judged.

- Measured from the string tables: glossary and naming consistency (each term spelled and cased as the glossary says; names follow the naming rules), string length against the limits, subtitle coverage where voiced lines exist.
- Judged: UI text, barks and item names against the tone words, the anti-words and the UI voice, and mismatches between what the fiction says and what play does. Judge only what a page rule settles; mark the rest `not-assessed` with that reason.
- Set `item` on each note that bears on a `review` item.
- Write `docs/game/reviews/<target>/narrative.json` in the review shape from `game.md`. A failing line is a note; name the lines that passed in the `result` reason.

**Done when** every checklist line is a note or named as passed in the `result` reason, every note has an evidence path or string ID, a rule, severity per the rules above and an anchor or `null`, and every note bearing on a `review` item has its `item`.
