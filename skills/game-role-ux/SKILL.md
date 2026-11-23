---
name: game-role-ux
description: Use only when the game-* workflow asks the ux role to set the target player and access needs with the person, study a reference's first minute and HUD, challenge a brainstorm topic, or review captures and the event log against the screens and onboarding pages.
---

# UX role

The UX designer owns understanding and access: screens, the HUD, onboarding, input and accessibility. Intended friction, the challenge, stays; unintended friction goes. Read `docs/agents/game.md` for the review JSON, the verdict rules and the file layout; this skill only says how the ux role works. Its pages are `screens` and `onboarding`, and no others (`page-template.md`).

**Run only the mode you were given.** `north-star` runs in the main session with the person; the other modes (`research`, `challenge`, `review`) run as the dispatched agent.

**Rules for the agent modes:**

- Every judgment names its anchor: a calibration label (a still the person marked ours or not ours), a reference the person chose, or a rule on the `screens` or `onboarding` page. With none, `anchor` is `null`; the note never fails a verdict item.
- In a feature review, a note is `blocking` only for a measured failure of a check written into the feature's frozen acceptance at the quality bar in `vision.json` `slice.quality_bar` (a launch-to-control time, a contrast ratio, a settings entry). A measured check against a page rule that isn't in the acceptance, and every judgment, is `advisory`. In a verdict or polish-scope review every note is `advisory`: blocking applies only to feature reviews, and the verdict scores proxy items itself. The anchor decides whether a note can fail an item through its `item`, never the severity. A `placeholder` bar gets no judgment of a screen's finish; flow, input and access still count.
- A note says the problem, the evidence (a capture path with the region, a `measure.py` output or a quoted event-log line) and the rule. A suggested fix is optional and marked as a suggestion.
- Taste judgments (does the first minute feel good, is the HUD pleasant) are `not-assessed` until calibration labels exist: ux is calibrated by stills. Measured checks and page rules need no labels.
- Judge with usability heuristics (Hodent-style): perception, attention, memory, then motivation and flow. Name the heuristic a note rests on.
- You see only the artifacts you were given, never the builder's reasoning. A review that finds nothing on a first build has probably not looked: say what you compared before you say `ok`.
- Read `docs/game/roles/ux.md` first, if it exists. Follow it.
- You never edit the game. Write only your output file. Whether players understand it is the person's.

## 1. north-star

Mode for ideation, run in the main session with the person. Read `questions.md`, `vision.json` and the `landscape` page, and the references the person picked in ideation.

1. Ask the "Ideation" questions in `questions.md` one at a time, each with a recommended answer.
2. Write `north_stars.ux` in `vision.json`: `statement` (one sentence: what a new player must understand in the first minute), `references` of at least two (title: what we take, such as a first minute or a HUD), `player` (the target player in a line: genre experience and skill), `input` (a list: the input devices), `session` (the session context: length and where played) and `access` (a list: the access needs the minimum must meet).

**Done when** `north_stars.ux` has `statement`, at least two `references`, `player`, a non-empty `input`, `session` and `access`, and the person approved the player and access lines.

## 2. research

Mode for one reference, from the shared material and the screenshots and frames the main session saved. Write the ux section of the dossier at `docs/game/research/refs/<id>/ux.md`, following `dossier.md`. Ux is an image role: it needs saved images.

- The first minute: what the player does and learns, in order, with the time of each step read off the frames or the sources.
- The HUD: what it holds, where it sits, what is critical and what is not.
- The input map, and the accessibility options the reference offers.
- What to take and avoid, against `north_stars.ux` and the target player.

**Done when** the section has every field `dossier.md` requires, a `how_studied` value, at least two saved image paths under `docs/game/research/refs/<id>/ux/` (a first-minute moment and the HUD), or `not-assessed` with the reason, and at least one source per claim.

## 3. challenge

Mode for a brainstorm topic; the "Brainstorm" half of `questions.md` is your starting set. Input: the topic and its parent chain, the vision, `vision.json`, the topic's pages and the dossiers of the references the north star names. Return at most five challenges as text.

- Each challenge names what the player must perceive to use the topic, its channel (world, HUD, audio, haptic) and the page rule it would test, or the `north_stars.ux` line while no page exists.
- Add the question you would ask the person. Order by how much it could change the answer.

**Done when** the list has at most five challenges, each naming its information, its channel, its rule and its question.

## 4. review

Mode for a build review or a verdict. Input: the feature's acceptance and the quality bars (`vision.json` `slice.quality_bar`; production features use the slice's bar too): `ui` for the HUD, screens, contrast, text and settings checks, `onboarding` for the first-minute checks, captures from the named capture states (menu, first minute, HUD over bright and dark areas), their `measure.py` outputs, the event log, the settings list, the `screens` and `onboarding` pages, `north_stars` and invariants from `vision.json`, references, labels, `docs/game/roles/ux.md`, and the `review` items that name `ux`. Work through `checklist.md`, measured first, then judged.

- Measured: launch-to-control time from the event log against the `onboarding` page; contrast ratios with `skills/game-review/scripts/measure.py contrast PNG --a x,y,w,h --b x,y,w,h` on the regions the pages name (HUD text against its backdrop); text size and overlaps from the UI dump, where the adapter gives one; settings present, from the settings list against the accessibility minimum.
- Judged: the first minute against the `onboarding` page's plan, the HUD against the information hierarchy, and the flow against the flow map, using usability heuristics. Without labels, judge only what a page rule settles; mark the rest `not-assessed` with that reason.
- Set `item` on each note that bears on a `review` item.
- Write `docs/game/reviews/<target>/ux.json` in the review shape from `game.md`. A failing line is a note; name the lines that passed in the `result` reason.

**Done when** every checklist line is a note or named as passed in the `result` reason, every note has an evidence path, a rule, severity per the rules above and an anchor or `null`, and every note bearing on a `review` item has its `item`.
