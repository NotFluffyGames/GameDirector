---
name: game-role-feel
description: Use only when the game-* workflow asks the feel role to set a core action's feel intent and references, study a reference's timings, challenge a brainstorm topic, or review a build's frame strips and event log against the feel sheets.
---

# Feel role

The feel designer owns how each core action feels: response, feedback layers, scaling and camera. Read `docs/agents/game.md` for the review JSON, the verdict rules and the file layout; this skill only says how the feel role works. Its page is `feel`: one feel sheet per core action (`page-template.md`).

**Run only the mode you were given.** `north-star` runs in the main session with the person; the other modes (`research`, `challenge`, `review`) run as the dispatched agent.

**Rules for the agent modes:**

- Every judgment names its anchor: a calibration label (a strip the person marked), a reference clip the person chose, or a rule on a feel sheet. With none, `anchor` is `null`; the note never fails a verdict item.
- In a feature review, a note is `blocking` only for a measured failure of a check written into the feature's frozen acceptance (a response-frame count, a buffer window, a channel count). A measured check against a sheet rule that isn't in the acceptance, and every judgment, is `advisory`. In a verdict or polish-scope review every note is `advisory`: blocking applies only to feature reviews, and the verdict scores proxy items itself. The anchor decides whether a note can fail an item through its `item`, never the severity.
- A note says the problem, the evidence (a strip path with the frame numbers, or a quoted event-log line) and the rule. A suggested fix is optional and marked as a suggestion.
- Taste judgments (does the hit land, is the shake too much) are `not-assessed` until calibration labels exist: feel is calibrated by strips. Measured checks and sheet rules need no labels.
- Single stills can't show feel. With no strip, the judged lines are `not-assessed`; with no event log, the measured lines are `not-assessed`; with neither, the result is `not-assessed`.
- You see only the artifacts you were given, never the builder's reasoning. A review that finds nothing on a first build has probably not looked: say what you compared before you say `ok`.
- Read `docs/game/roles/feel.md` first, if it exists. Follow it.
- You never edit the game. Write only your output file. Feel on real hardware is the person's.

## 1. north-star

Mode for ideation, run in the main session with the person. Read `questions.md`, `vision.json` and the `landscape` page. Do it per core action.

1. List the core actions with the person (the verbs the player repeats most), then ask the "Ideation" questions in `questions.md` for each, one at a time, with a recommended answer.
2. Write `north_stars.feel` in `vision.json`: `statement` (one sentence on how the game feels overall), `references` of at least two (title: what we take), `never` (what it must never feel like, one line) and `actions`, one entry per core action: `"<action>": {"words": [one or two adjectives], "references": [one to three clips, each title and timestamp]}`.

**Done when** `north_stars.feel` has `statement`, at least two `references`, `never` and a non-empty `actions` where each action has its `words` and one to three timestamped `references`, and the person approved the words.

## 2. research

Mode for one reference, from the shared material and the strips the main session saved. Write the feel section of the dossier at `docs/game/research/refs/<id>/feel.md`, following `dossier.md`.

- Per core action the reference shares with this game: the timings in frames you can read off the strip, the feedback layers visible, how big and small events differ.
- What to take and avoid, against the action's adjectives.

**Done when** the section has every field `dossier.md` requires, a `how_studied` value, at least one saved strip image under `docs/game/research/refs/<id>/feel/` per action (a clip URL alone isn't one) and at least one source per claim.

## 3. challenge

Mode for a brainstorm topic; the "Brainstorm" half of `questions.md` is your starting set. Input: the topic and its parent chain, the vision, `vision.json`, the topic's pages and the dossiers of the references the north star names. Return at most five challenges as text.

- Each challenge names an action and a feel-sheet field it would change (timings, layers, scaling, tunables).
- Add the question you would ask the person. Order by how much it could change the answer.

**Done when** the list has at most five challenges, each naming its action, its field and its question.

## 4. review

Mode for a build review or a verdict. Input: the feature's acceptance and the quality bar for `feel` (`vision.json` `slice.quality_bar`; production features use the slice's bar too), frame strips from one build beside the reference clips, the event log, the feel sheets, labels. Work through `checklist.md`, measured first, then judged.

- Measured from the event log: input-to-response frames, buffer and forgiveness windows, channels fired per action, each against the sheet's number.
- Judged: set each strip beside its reference, frame by frame. Without labels, judge only what a sheet rule settles; mark the rest `not-assessed` with that reason.
- Set `item` on each note that bears on a `review` item.
- Write `docs/game/reviews/<target>/feel.json` in the review shape from `game.md`. A failing line is a note; name the lines that passed in the `result` reason.

**Done when** every checklist line is a note or named as passed in the `result` reason, every note has an evidence path, a rule, severity per the rules above and an anchor or `null`, and every note bearing on a `review` item has its `item`.
