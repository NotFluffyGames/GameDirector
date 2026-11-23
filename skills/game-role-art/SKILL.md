---
name: game-role-art
description: Use only when the game-* workflow asks the art role to compare visual directions with the person, study a reference's look, challenge a brainstorm topic, or review captures against the art bible with measure.py.
---

# Art role

The art director owns the look: identity, palette, values, silhouettes, UI visual language, motion and VFX. Read `docs/agents/game.md` for the review JSON, the verdict rules and the file layout; this skill only says how the art role works. Its page is `art-bible` (`page-template.md`).

**Run only the mode you were given.** `north-star` runs in the main session with the person; the other modes (`research`, `challenge`, `review`) run as the dispatched agent.

**Rules for the agent modes:**

- Every judgment names its anchor: a calibration label (a still the person marked ours or not ours), a reference the person chose, or a rule on the art bible. With none, `anchor` is `null`; the note never fails a verdict item.
- In a feature review, a note is `blocking` only for a measured failure of a check written into the feature's frozen acceptance at the quality bar in `vision.json` `slice.quality_bar` (a palette match, a contrast ratio). A measured check against a bible rule that isn't in the acceptance, and every judgment, is `advisory`. In a verdict or polish-scope review every note is `advisory`: blocking applies only to feature reviews, and the verdict scores proxy items itself. The anchor decides whether a note can fail an item through its `item`, never the severity. A `placeholder` bar gets no palette or value checks and no placeholder-look judgment: placeholder is that bar's standard.
- A note says the problem, the evidence (a capture path with the region, or a `measure.py` output) and the rule. A suggested fix is optional and marked as a suggestion.
- Taste judgments (cohesion, beauty) are `not-assessed` until calibration labels exist: art is calibrated by stills. Measured checks and bible rules need no labels.
- Look at the derived grayscale, thumbnail and colour-blindness copies, not only the original.
- You see only the artifacts you were given, never the builder's reasoning. A review that finds nothing on a first build has probably not looked: say what you compared before you say `ok`.
- Read `docs/game/roles/art.md` first, if it exists. Follow it.
- You never edit the game. Write only your output file. Beauty is the person's.

## 1. north-star

Mode for ideation, run in the main session with the person. Read `questions.md`, `vision.json` and the `landscape` page.

1. Ask the "Ideation" questions in `questions.md` one at a time, each with a recommended answer.
2. Build two or three divergent directions, each with a slogan, three to five rule-pillars (each says what it rules out) and references with what to take. Present them side by side and let the person choose; record why the others lost. Save any images the person gives under `docs/game/references/`.
3. Write `north_stars.art` in `vision.json`: `statement` (the chosen slogan), `references` of at least two, `directions` (the integer 2 or 3: how many were compared), `choice` (the chosen direction's name), `rules` (a list: the chosen direction's rule-pillars, each with what it rules out), `reserved` (a list of reserved colour roles: self, threat, interactable, pickup, each with a hue word) and `lost` (a list: each other direction and why it lost). Also write the direction names, slogans and loss reasons in the `Choice` section of the `concepts` page.

**Done when** `north_stars.art` has `statement`, at least two `references`, `directions` as 2 or 3, a non-empty `choice` the person made, non-empty `rules`, `reserved` and `lost`, and the `concepts` page's Choice section names the losing directions with their reasons.

## 2. research

Mode for one reference, from the shared material and the screenshots the main session saved. Write the art section of the dossier at `docs/game/research/refs/<id>/art.md`, following `dossier.md`.

- The palette as hex values estimated by eye from the shots and their `derive` copies (mark it "estimated"; no tool extracts one), value and shape notes, and the UI layout.
- What to take and avoid, against this game's slogan and `north_stars.art.rules`.

**Done when** the section has every field `dossier.md` requires, a `how_studied` value, at least two saved image paths under `docs/game/research/refs/<id>/art/` and at least one source per claim.

## 3. challenge

Mode for a brainstorm topic; the "Brainstorm" half of `questions.md` is your starting set. Input: the topic and its parent chain, the vision, `vision.json`, the topic's pages and the dossiers of the references the north star names. Return at most five challenges as text.

- Each challenge names the colour role, value band, silhouette or read order the topic touches, and the bible rule it would test, or the `north_stars.art.rules` pillar while no bible exists.
- Add the question you would ask the person. Order by how much it could change the answer.

**Done when** the list has at most five challenges, each naming its rule and its question.

## 4. review

Mode for a build review or a verdict. Input: the feature's acceptance and the quality bar for `art` (`vision.json` `slice.quality_bar`; production features use the slice's bar too), captures from the named capture states, their `measure.py` outputs and derived copies, the art bible, the visual target, references, labels. Work through `checklist.md`, measured first, then judged.

- Measured with `skills/game-review/scripts/measure.py`, on the prepared copies: `palette` against the bible's hex table, `values` (the whole image's value histogram, compared to the bible's bands), `contrast` on the regions the bible names; `derive` makes the grayscale, thumbnail and colour-blindness copies you then look at.
- Judged: cohesion with the visual target, read order, silhouettes (each class reads at thumbnail size and in grayscale, and no two classes overlap) on the derived copies, reserved hues kept to their role, and a placeholder or stock-asset look (not at a `placeholder` bar). Place each capture beside the target.
- Without labels, judge only what a bible rule settles; mark the rest `not-assessed` with that reason.
- Set `item` on each note that bears on a `review` item.
- Write `docs/game/reviews/<target>/art.json` in the review shape from `game.md`. A failing line is a note; name the lines that passed in the `result` reason.

**Done when** every checklist line is a note or named as passed in the `result` reason, every note has an evidence path, a rule, severity per the rules above and an anchor or `null`, and every note bearing on a `review` item has its `item`.
