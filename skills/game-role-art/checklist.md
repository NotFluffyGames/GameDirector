# Art: review checklist

Mark each line passed, a note, or `not-assessed` with the reason. A note is `blocking` only when a measured check written into the feature's frozen acceptance fails at its milestone's quality bar; every other note is `advisory`. An anchor (a label, a chosen reference or a bible rule) decides whether a note can fail an item through its `item`, never its severity. A `placeholder` bar gets no palette or value checks. Read the `review` items that name `art` first.

## Checked first (with `measure.py`)

- `palette` of each capture against the bible's hex table: the share of pixels outside the table.
- `values` per layer against the bible's bands; the grayscale copy keeps layers apart.
- `contrast` between the regions the bible names (player against ground, HUD text against its backdrop).
- `derive` copies looked at: thumbnail and colour-blindness copies keep roles distinguishable.
- Reserved hues appear only in their role.

## Judged (beside the visual target and references)

- Cohesion: does this capture belong beside the visual target? Name what differs.
- Read order: what does the eye see first, second, third; is it the order the bible gives?
- Placeholder or stock look: default-engine shapes, untextured primitives, mismatched asset styles.
- Only what a bible rule or a label settles; the rest is `not-assessed` with that reason.

## Needs the person

- Beauty and final taste: never a note.
- Calibration labels: until they exist, taste judgments here are `not-assessed`.
