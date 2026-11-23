# Audio: review checklist

Unheard: say so in the `result` reason. Mark each line passed, a note, or `not-assessed` with the reason. In a feature review a note is `blocking` only when a measured check written into the feature's frozen acceptance fails at its milestone's quality bar; every other note is `advisory`, and in a verdict or polish-scope review all are. An anchor (a chosen reference or a page rule) decides whether a note can fail an item through its `item`, never its severity. A `placeholder` bar gets no judgment of how a sound is made, and no loudness check. Read the `review` items that name `audio` first.

## Checked first (from the event list, the log and the sound list)

- Event coverage: every gameplay event in the event list maps to a sound; list the unmapped ones.
- Variation counts: each repeated event has at least the page's minimum variations.
- Back-to-back repeats: the log shows no event firing the same sample twice in a row beyond the page's limit.
- Priority: each event's sound sits in the tier the page assigns it, and per-tier voice limits hold in the log.
- Loudness, only where the adapter measures it: integrated level and true peak against the page's target. Otherwise `not-assessed`: no measurement.

## Judged (from the sound list and descriptions; unheard)

- The signature sounds exist in the sound list and each is mapped to the events the page names.
- The palette per category: the sources and processing the list names match the page's rows and its "never" rules.
- Every event the player must catch by ear (the `by_ear` list) has a distinct sound, not shared with another event of the same tier.
- The UI sounds belong to one family: shared key, timbre and envelope as the page states them.
- Each sound that carries critical information has a visual cue too (the accessibility line).
- Only what a page rule or a chosen reference settles; the rest is `not-assessed` with that reason.

## Needs the person

- Listening: whether it sounds right, the mix balance, the music: never a note.
- Taste: audio is not calibrated by labels; the person's playtest and A/B picks decide it.
