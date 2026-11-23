# Kits for a person

game-build makes two kits a person works through: the **calibration kit** when the slice's look first passes, and the **compare kit** for a polish feature verified by A/B picks. Their human queue entries are kinds `calibrate` and `compare` ("Human queue" in `docs/agents/game.md` gives their fields and what the person writes). For both:

- every capture and strip comes from this session's build through the adapter (Commands in `docs/agents/game.md`; the named states and strips are the capture protocol in `docs/game/engine-notes.md`);
- every image is committed shrunk to at most 1280 px on its longest side with game-review's `measure.py` (`../game-review/scripts/measure.py` beside this skill): `python3 <measure.py> shrink IN.png --out OUT.png`; separate frames are stitched into one sheet with `measure.py sheet`;
- an item the adapter marks `n/a` is left out, with its reason in the kit's `index.md`;
- the entry is mirrored as a `ready-for-human` ticket.

## Calibration kit

The person marks what is "ours" and what is "not ours", which gives the roles' taste judgments their anchors ("Anchored to the person" in `docs/agents/game.md`). Queue a kit when its trigger passes:

- the visual target;
- with `art` in `vision.json` `roles_off`, the feel target;
- with `feel` off too, the first feature in milestone `slice` with `roles`;

and either:

- no `docs/game/calibration/labels.json` exists and no `calibrate` entry is queued; or
- the art direction changed since the latest kit: `north_stars.art` in `docs/game/vision.json` differs from that kit's `art.json` (an adjust or a restart changed it).

Make it in `docs/game/calibration/kit-<n>/`, `n` one past the latest kit:

1. **8–12 captures from this build**: each named state that renders, then `capture --seed N --tick T` shots across the slice to make up the count.
2. **The person's references**: the images in `docs/game/references/`, or with none there, the images in the `art/` folders under `docs/game/research/refs/` of the references `north_stars.art` names; listed by path.
3. **Two or three "not our game" examples**: the engine's default scene (its default sky, lighting and primitives, or a framework's bare shapes), a scene in stock assets, and a capture of this build (the beauty view, while `art` is on) with its palette broken on purpose. Render them from test states outside the shipped game, as the adapter contract's test fixture is.
4. **Feel strips**: for each action in `north_stars.feel` `actions`, its strip from this build (`capture --strip`), beside its reference clips: their links and timestamps, and any strip of that action in the feel sections under `docs/game/research/refs/`.
5. **`art.json`**: `north_stars.art` as `vision.json` holds it now (`null` with `art` off).
6. **`index.md`**: the items numbered in mixed order under neutral names, so the person judges each by eye without being told which are the decoys; the ask, per item "ours" or "not ours" with one line why, into `docs/game/calibration/labels.json` in the shape "Human queue" gives (`capture` is the item's path); and the return path: commit the labels and run `/game-next`.

When an older `labels.json` exists, move it into the previous kit's folder (`kit-<n-1>/labels.json`): the person's new labels replace it. Until they arrive, the taste judgments of `creative`, `feel`, `art` and `ux` are `not-assessed` and the slice verdict waits; builds go on.

Queue the entry: `kind` `calibrate`, `how` the kit's `index.md`, `answers` `docs/game/calibration/labels.json`, `unblocks` `[]`.

## Compare kit

A polish feature whose acceptance is a taste call (a grade, a feel retune, a mix) is verify `human`, and its verify `how` names what its two to four pairs show (game-polish writes it). It takes two sessions. The first makes the kit and queues its `compare` entry; the person writes the picks into the entry's `answers` file and leaves the entry; then the state tool schedules the **picks session**, `game-build <id> "<title>" picks <answers>`. Meanwhile the run builds whatever else it can, and the final verdict waits for the picks.

**First session.** Build each candidate behind tuning knobs, each within the pages' rules, the feature's measured checks and the identity invariants (`vision.json` `invariants`), and run the full suite. Make the kit in `docs/game/playtests/evidence/<id>/compare/`:

- the pairs: each the same named state or strip rendered before and after the change, with each side's values in the knob file while it renders and the current values restored after; for a mix, which the person must hear, the knob file of each side to run the build with;
- `index.md`: per pair, what changes (the knob and its two values); and the return path: one pick per pair, with one line why, in `picks.md` beside it; leave the queue entry, commit, and run `/game-next`.

Queue the entry: `kind` `compare`, `how` the kit's `index.md`, `answers` its `picks.md`, `unblocks` `["<id>"]`. Then do step 4's code review and step 5 without `passes`, the ticket left open as `ready-for-human`. The roles review the picked build in the picks session.

**The picks session** (the task ends `picks <answers>`). Set each picked value in its knob file, and pin the picks: a `docs/game/keep.json` entry with `what`, `source` the picks file and a pin per knob ("Kept values" in `docs/agents/game.md`). Run the verify's measured checks and the full suite, then steps 4 and 5 as for any feature: game-review writes each pick in `picks.md` to its role's memory (its step 7), `evidence` starts `human:` and names the picks file, and step 5's commit removes the `compare` entry from the human queue.
