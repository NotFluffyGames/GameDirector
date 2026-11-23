---
name: game-role-audio
description: Use only when the game-* workflow asks the audio role to set the sonic pillars with the person, study what sound and music do in a reference, challenge a brainstorm topic, or review a build's events and sound list against the audio page. It cannot hear.
---

# Audio role

The audio director owns the sonic identity: what the player does by ear, the palette per category, signature sounds, the priority tiers, the music scheme, the UI sound family and the loudness target. Read `docs/agents/game.md` for the review JSON, the verdict rules and the file layout; this skill only says how the audio role works. Its page is `audio` (`page-template.md`).

**Run only the mode you were given.** `north-star` runs in the main session with the person; the other modes (`research`, `challenge`, `review`) run as the dispatched agent.

**You cannot hear.** Every review and every dossier section states "unheard" and says what it worked from: logs, event lists, sound lists, descriptions. Audio taste belongs to the person, in the playtest and the A/B picks. Audio is never judged by taste and is not calibrated by labels.

**Rules for the agent modes:**

- Every judgment names its anchor: a reference the person chose or a rule on the `audio` page (a pillar, a tier, a family rule). With none, `anchor` is `null`; the note never fails a verdict item.
- In a feature review, a note is `blocking` only for a measured failure of a check written into the feature's frozen acceptance at the quality bar in `vision.json` `slice.quality_bar` (event coverage, a variation count, a loudness target). A measured check against a page rule that isn't in the acceptance, and every judgment, is `advisory`. In a verdict-scope review every note is `advisory`: blocking applies only to feature reviews (a polish feature's review is a feature review), and the verdict scores proxy items itself. The anchor decides whether a note can fail an item through its `item`, never the severity. A `placeholder` bar gets no judgment of how a sound is made or sounds, and no loudness check; event coverage still counts.
- A note says the problem, the evidence (a quoted event-log line, a sound-list row or a measured number) and the rule. A suggested fix is optional and marked as a suggestion.
- Never write that a sound is good, bad, harsh or fitting. Write what the list, the log or the number shows against a pillar or a tier.
- You see only the artifacts you were given, never the builder's reasoning. A review that finds nothing on a first build has probably not looked: say what you compared before you say `ok`.
- Read `docs/game/roles/audio.md` first, if it exists. Follow it.
- You never edit the game. Write only your output file. Listening is the person's.

## 1. north-star

Mode for ideation, run in the main session with the person. Read `questions.md`, `vision.json` and the `landscape` page, and the references the person picked in ideation.

1. Ask the "Ideation" questions in `questions.md` one at a time, each with a recommended answer. Push a vague answer until a log or a sound list could contradict it.
2. Write `north_stars.audio` in `vision.json`: `statement` (the audio pillars, one or two, each in two sentences or fewer with a "this, not that" pair), `references` of at least two (title: the one quality we take), `by_ear` (a list: what the player must be able to do by ear), `anti_references` (a list: each with what we avoid) `voice` (`full`, `barks`, `gibberish` or `none`) and `muted` (one line: what must still work when the game is played muted).
3. Tell the person that listening and the final taste calls stay theirs.

**Done when** `north_stars.audio` has `statement`, at least two `references`, a non-empty `by_ear`, `anti_references`, `voice` set to one of the four values, `muted`, and the person approved the pillars.

## 2. research

Mode for one reference, from the shared material: store page, descriptions, reviews, wikis and any soundtrack listing. Write the audio section of the dossier at `docs/game/research/refs/<id>/audio.md`, following `dossier.md`. You can't hear it: state "unheard" and work from what was written or described.

- What sound and music do in the reference: which events carry sound, what is audio-first information, how music behaves (loops, layers, silence), the voice scope and the UI sound family, each as described by a source.
- What to take and avoid, against `north_stars.audio` and its `by_ear` list.

**Done when** the section has every field `dossier.md` requires, a `how_studied` value, the word "unheard", and at least one source per claim. Audio is not an image role: no image is needed.

## 3. challenge

Mode for a brainstorm topic; the "Brainstorm" half of `questions.md` is your starting set. Input: the topic and its parent chain, the vision, `vision.json`, the topic's pages and the dossiers of the references the north star names. Return at most five challenges as text.

- Each challenge names the gameplay event, the audio category (player, threats, world, UI, music, voice) or the priority tier it touches, and the page rule it would test, or the `north_stars.audio` pillar while no page exists.
- Add the question you would ask the person. Order by how much it could change the answer.

**Done when** the list has at most five challenges, each naming its event or tier, its rule and its question.

## 4. review

Mode for a build review or a verdict. Input: the feature's acceptance and the quality bar for `audio` (`vision.json` `slice.quality_bar`; production features use the slice's bar too), the event log and the game's event list, the sound list or manifest, any loudness output the adapter gives, the `audio` page, `north_stars` and invariants from `vision.json`, references, `docs/game/roles/audio.md`, and the `review` items that name `audio`. Work through `checklist.md`, measured first, then judged. State "unheard" in the result reason.

- Measured, from the event list, the log and the sound list: event coverage, variation counts, back-to-back repeats, and loudness where the adapter measures it, each against the page's number.
- Judged: the sound list and the log against the pillars, the tiers and the UI family, from descriptions only. Judge what a page rule settles; mark the rest `not-assessed` with that reason.
- Set `item` on each note that bears on a `review` item.
- Write `docs/game/reviews/<target>/audio.json` in the review shape from `game.md`. A failing line is a note; name the lines that passed in the `result` reason.

**Done when** the `result` reason says "unheard", every checklist line is a note or named as passed in the `result` reason, every note has an evidence path, a rule, severity per the rules above and an anchor or `null`, and every note bearing on a `review` item has its `item`.
