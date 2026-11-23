# Art: review checklist

Mark each line passed, a note, or `not-assessed` with the reason. In a feature review a note is `blocking` only when a measured check written into the feature's frozen acceptance fails at the quality bar in `vision.json` `slice.quality_bar`; every other note is `advisory`, and in a verdict-scope review all are (a polish feature's review is a feature review). An anchor (a label, a chosen reference or a bible rule) decides whether a note can fail an item through its `item`, never its severity. A `placeholder` bar gets no palette or value checks. Read the `review` items that name `art` first.

## Checked first (with `measure.py`)

- `palette` of each capture against the bible's hex table: the share of pixels outside the table.
- `values`: the whole capture's value histogram against the bible's overall range (it can't split layers).
- `contrast` between the regions the bible names (player against ground, HUD text against its backdrop).
- Each capture's derived copies are in `inputs/derived/<capture>/` (game-review makes them; you never run `derive`), so the judged lines below have them; a line whose copy is missing is `not-assessed`.

## Judged (beside the visual target and references)

- Cohesion: does this capture belong beside the visual target? Name what differs.
- Read order: what does the eye see first, second, third; is it the order the bible gives?
- Layer values: on the grayscale copy, do UI, characters, VFX and environment sit in their bands?
- Silhouettes: on the thumbnail and grayscale copies, each class reads, and no two classes overlap.
- Colour roles: on the colour-blindness copy, roles stay distinguishable; reserved hues appear only in their role.
- Placeholder or stock look (not at a `placeholder` bar): default-engine shapes, untextured primitives, mismatched asset styles.
- Only what a bible rule or a label settles; the rest is `not-assessed` with that reason.

## Needs the person

- Beauty and final taste: never a note.
- Calibration labels: until they exist, taste judgments here are `not-assessed`.
