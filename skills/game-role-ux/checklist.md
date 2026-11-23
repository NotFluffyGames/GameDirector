# UX: review checklist

Mark each line passed, a note, or `not-assessed` with the reason. In a feature review a note is `blocking` only when a measured check written into the feature's frozen acceptance fails at the quality bar in `vision.json` `slice.quality_bar`; every other note is `advisory`, and in a verdict-scope review all are (a polish feature's review is a feature review). An anchor (a label, a chosen reference or a page rule) decides whether a note can fail an item through its `item`, never its severity. A `placeholder` bar gets no judgment of a screen's finish. Read the `review` items that name `ux` first.

## Checked first

- Launch-to-control time, from the event log: launch to the first input accepted, against the `onboarding` page's target.
- Contrast: `measure.py contrast` between each HUD text region and its backdrop, against the ratios the `screens` page states.
- Text size and overlaps, from the UI dump where the adapter gives one: no text under the page's minimum size, no two elements overlapping, nothing off-screen. Otherwise `not-assessed`: no dump.
- Settings present, from the settings list against the `screens` page's Accessibility minimum section: list each entry it names that is missing.
- `derive` run on each capture, so the judged lines below have their copies.

## Judged (on captures, against the pages)

- No critical information by colour alone: on the colour-blindness copies, the critical elements stay distinguishable.
- Flow: the captures follow the flow map, with a way back and out at each step; a dead end is a note.
- HUD: the critical information is the most visible, per the hierarchy; nothing situational competes with it.
- First minute: what the page says is taught is taught by doing, in the page's order, and a failed attempt shows what went wrong.
- Input: each verb maps to the input the map gives, with no conflict.
- Heuristics: perception (can it be seen and read), attention (what competes), memory (what must be remembered rather than shown). Name the heuristic on each note.
- Only what a page rule or a label settles; the rest is `not-assessed` with that reason.

## Needs the person

- Comprehension: whether a player understands: never a note.
- Taste: `not-assessed` until still labels exist.
