# Feel: review checklist

Mark each line passed, a note, or `not-assessed` with the reason. In a feature review a note is `blocking` only when a measured check written into the feature's frozen acceptance fails; every other note is `advisory`, and in a verdict-scope review all are (a polish feature's review is a feature review). An anchor (a label, a chosen clip or a sheet rule) decides whether a note can fail an item through its `item`, never its severity. Read the `review` items that name `feel` first.

## Checked first (from the event log)

- Input-to-response frames for each action, against the sheet.
- Buffer and forgiveness windows, against the sheet, from scripted early and late inputs.
- Feedback channels fired per action, against the sheet's layers; a layer on the sheet that never fires is a note.
- Scaling: the large event fires at least as many channels as the small one.

## Judged (from strips beside reference clips)

- Does the first response frame land where the reference's does? Name the frames compared.
- Does a layer read as noise when the action repeats quickly, or does the signal layer stay clear?
- Camera: shake or movement proportionate to the event, with no sustained shake.
- Only what a sheet rule or a label settles; the rest is `not-assessed` with that reason.

## Needs the person

- Feel on real hardware, and whether the action satisfies: never a note.
- Taste: `not-assessed` until strip labels exist.
