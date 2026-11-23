---
name: game-review
description: Review the game by its roles (creative, design, feel, art, audio, narrative, ux) as parallel agents working from captures, frame strips, measurements and logs prepared once from one build, then have every note decided by the creative director, carry the decisions out and record them. Called by game-build for a visible feature, game-polish for a polish feature, game-verdict for a verdict scope and game-brainstorm for a topic's challenges; also run directly.
disable-model-invocation: true
---

# Game Review

Every aspect of the game has an owner with taste, and no builder grades its own visible work. This skill runs those owners: it prepares what they look at once, dispatches one agent per role in parallel, checks they touched nothing but their own output, has every note decided, carries the decisions out and records them. It runs inside the session that called it (build, polish, verdict or brainstorm) and shares that session's base commit. Read `docs/agents/game.md` first: its session rules, the review record, the decision grammar and role memory.

| Task | Target folder `docs/game/reviews/<target>/` | Roles | Mode | Notes may block |
| --- | --- | --- | --- | --- |
| `game-review feature <id>` | `<id>` | the feature's `roles` | `review` | only a measured failure of its frozen acceptance |
| `game-review polish <id>` | `<id>` | the feature's `roles`, plus `creative` against the invariants | `review` | no |
| `game-review <scope>` (`core-loop`, `slice`, `full`, `final`) | `verdict-<scope>` | every active role | `review` | no |
| `game-review topic <id>` | `<id>` (inputs only) | the topic's `roles`, plus `creative` on a `core` topic | `challenge` | no notes: challenges come back as text |

**Rounds.** A feature or polish review is at most two rounds of steps 2–7 per feature per session; round 2 re-runs the whole review on the commit that fixed round 1's notes. A verdict or a topic is one round.

**Paths for the agents.** This skill's base directory (shown when it loads) gives the absolute paths every dispatch carries: the role skill at `../game-role-<role>/SKILL.md` beside it, the role's stance at `../../agents/<role>.md`, and `scripts/measure.py` inside it. Resolve each to an absolute path.

## What each role is given

Every reviewer gets the target (a feature's acceptance and verify, or the scope), `docs/game/vision.json` (north stars, invariants, `slice.quality_bar`), `docs/game/calibration/labels.json`, its memory `docs/game/roles/<role>.md`, the fun checklist's `review` items that name it, copies of the target's pages (a feature's or topic's `pages`), and `inputs/index.md`. Then its row:

| Role | From the build (under `inputs/`) | Its anchors |
| --- | --- | --- |
| `creative` | every capture and strip, their measure outputs and derived copies, the event log | the `vision` page, the `landscape` page (the genre default), the references `north_stars.creative` names, the visual target's captures |
| `design` (verdicts only) | bot metrics and traces from whole-game runs | the pages in the Mechanics, Systems and Content areas, the references `north_stars.design` names |
| `feel` | a strip per core action, the event log with the window inputs | the `feel` page, the reference strips (the feel sections' strips under `docs/game/research/refs/`, the calibration kit's), the feel target's strips |
| `art` | the named states' captures, their `palette` and `values` outputs, their derived copies | the `art-bible` page, the visual target's captures, the reference images (`docs/game/references/`, the art sections under `docs/game/research/refs/`) |
| `audio` | the event log's sound events, the game's event list, the sound list or manifest, loudness | the `audio` page, the references `north_stars.audio` names |
| `narrative` | the string tables, the strings dump and `strings.json`, the captures, the event log | the `tone-and-world` page, the references `north_stars.narrative` names |
| `ux` | captures of the menus, the first minute and the HUD over the brightest and darkest areas, their derived copies, the event log with launch-to-control events, the UI dump, the settings list | the `screens` and `onboarding` pages, the references `north_stars.ux` names |

A challenge needs no build: the topic and its parent chain, the `vision` page and `vision.json`, the topic's pages, the role's own pages (its anchors above), the dossiers of the references its north star names (`docs/game/research/refs/<id>/<role>.md`) and its memory.

## 1. Choose the roles

Start from the task's row above. The active roles are the state tool's roles minus `vision.json` `roles_off`; leave out a switched-off role. Then:

- Add each role an earlier review of this target asked for (a `requests` entry naming a role), and write it into the feature's or topic's `roles` so `check` holds the target to it.
- Keep `design` off features and polish features: its checks need whole-game bot runs, so it reviews at verdicts.

Count this session's rounds for a feature or polish target: the commits since base whose subject starts `game-review: <target> round` and ends `inputs`. After two, there is no third: report the feature still failing to the caller and stop.

**Done when** you have the role list and this round's number, or the target has no roles (a rules-only feature) and the review ends with nothing to record.

## 2. Prepare the inputs, once

Reviewers read files; they never build or run the game, so parallel agents never fight over one checkout. Put everything the chosen roles' rows name in `docs/game/reviews/<target>/inputs/`:

1. **One build at one commit.** Commit what the caller has open, then note `git rev-parse HEAD`: the review's `commit`. Remove an earlier review's `inputs/` for this target (git keeps it). Run the adapter's `build`; a red build ends the review, reported to the caller.
2. **Captures and strips**, through the adapter (Commands in `docs/agents/game.md`, capture states in `docs/game/engine-notes.md`): `capture --state NAME` into `captures/` for each named state that shows the target (a scope: every state); `capture --strip INPUT --frames N --every K` into `strips/` for each core action it touches, stitched with `measure.py sheet` when the adapter writes separate frames.
3. **Measurements**, with `measure.py`: `derive` on every capture into `derived/<capture>/`; at an `art` bar above `placeholder`, `palette` against the art bible's hex table and `values` on every capture, into `measure/<capture>.json`. Everything that writes files happens here; agents run only the commands that print (`palette`, `values`, `contrast`).
4. **Logs**, from `sim`, `replay` or `bot` runs of this build, into `events/`: per action, input-to-response frames and the feedback channels fired; sound events with sample ids and voice counts; scripted inputs just inside and just outside each buffer and forgiveness window the feel sheets state; launch-to-control events (launch to the first accepted input). For a scope, also the verdict's bot metrics and traces from this build into `bot/` (its `notes.md` names them), or run `bot` for them.
5. **Dumps**, into `dumps/`, where the adapter gives them: the UI dump (text boxes and sizes), the settings list, loudness, and the strings dump. From the strings dump, compute with a short script, never by eye, into `strings.json`: each string's length and its place (button, title, tooltip, subtitle); each glossary term's hits in its exact spelling and in any other spelling or case; each anti-word's and banned word's hits. Index the string tables, the game's event list and its sound list or manifest by their paths in the repo.
6. **Anchors.** Copy each page a reviewer needs into `pages/<page-id>.md`: from its draft in `docs/game/drafts/` when one exists, else from the docs place as `docs/agents/docs.md` says (agents can't reach the docs place). The visual target's captures and the feel target's strips are the inputs of the latest review of the passed feature with that `target`. Index in-repo anchors (`vision.json`, labels, references, dossiers, role memory, `fun-checklist.json`) by path.
7. **The index**, `inputs/index.md`: one line per input with its path and the command and commit that made it. An input the adapter marks `n/a`, a command that fails, a page not written yet, labels not given yet: a line `<input>: n/a: <reason>`. An input is made from this build or listed `n/a`, never stood in for by a hand-made or remembered substitute; the reviewer marks the checks that need it `not-assessed` with that reason.

A topic needs only items 6 and 7: the page copies, and the topic's parent chain in the index.

Commit the inputs: `game-review: <target> round <n> inputs`.

**Done when** every input the chosen roles' rows name is a file under `inputs/`, an in-repo path in the index, or an index line with `n/a` and its reason; everything from the build came from the one build at the review commit; and the inputs are committed with `git status` clean.

## 3. Dispatch the role agents in parallel

One Agent call per role, all in one message so they run in parallel, `subagent_type` `game-director:<role>`, with the model set at dispatch: the most capable model available for `creative`, `art` and `design`, a standard model for `feel`, `audio`, `narrative` and `ux`. Each prompt gives:

- the mode (`review`, or `challenge` for a topic) and the role skill's absolute path, to read first when the skill isn't preloaded;
- the target: the feature's id, acceptance and verify, the scope, or the topic's id; and the kind (`feature`, `polish` or `verdict`), which sets the role's severity rule;
- its quality bar in `vision.json` `slice.quality_bar`: `art`, `feel` and `audio` by name, `ui` for narrative, `ui` and `onboarding` for ux;
- the index and the paths its row names (for a challenge, the challenge inputs above), and that an `n/a` input makes each check needing it `not-assessed` with the index's reason;
- `measure.py`'s absolute path, for `palette`, `values` and `contrast` only;
- for a review: the output path `docs/game/reviews/<target>/<role>.json`; the record's `role`, `target`, `commit` and `"independent": true`; and how to ask for more: a top-level `requests` list of `{"capture": "<state or strip>", "why": "..."}` or `{"role": "<id>", "why": "..."}`, with the lines waiting on it `not-assessed` meanwhile;
- for a challenge: return at most five challenges as text, and write nothing.

**Without a subagent tool** (another agent runtime), run the roles yourself, one at a time: read the role skill and its stance, run the mode on the same inputs, and write the file with `"independent": false`. Verdicts score review items from such files `not-assessed`.

**Done when** every agent has returned: each reviewer's file is at its output path, and each challenger's list is in hand.

## 4. Check independence

`git status --porcelain --untracked-files=all` may list only this dispatch's output files: `docs/game/reviews/<target>/<role>.json` for the roles dispatched, or `decisions.md` after the decide pass, and nothing after a challenge. Restore any other tracked path with `git checkout -- <path>`, delete any other untracked one with `git clean -f -- <path>`, and note each discarded path in the `reason` of every review file from that dispatch (parallel writers can't be told apart).

Then set each review file's facts yourself (`role`, `target`, `commit`, `independent`, and `inputs` as its row's paths) and run `gamestate.py check --since <base>`. A reviewer whose file is missing or malformed (a reason from `check`, or a `blocking` note outside a feature review) is dispatched once more with the reasons; if it still is, write its file as `not-assessed` with that reason. Every note, `result` and judgment in a review file is the reviewer's alone.

A topic's review ends here: hand the caller the challenges merged, ordered by how much each could change the answer, and attributed to their role ("the art role asks…").

**Done when** `git status` lists only this dispatch's output files, each dispatched reviewer has a file with the right facts that `check` names no reason for, or the challenges are with the caller and the tree is clean.

## 5. One extra capture round

When a review lists `requests`, make the captures asked for from the same build (the review commit), add them with their measurements to `inputs/` and the index, and commit (`game-review: <target> round <n> extra captures`). Dispatch again only the roles that asked and the roles asked for (added to the target's `roles` as in step 1), with the new paths, then check independence again. One extra round per review round: a request made after it stays unanswered, and its lines stay `not-assessed`.

**Done when** every request has had its one extra round, or there were none.

## 6. Decide every note

- **Blocking notes** (feature reviews only) are measured failures of the frozen acceptance. Fixing them is building, not deciding: fix each, commit, and set its decision to `fixed <commit>`; round 2 measures it again. In round 2 no round is left to measure a fix, so a blocking note stays open and the feature stays failing.
- **Advisory notes.** When any review file of this round has one, dispatch one more agent: `creative` in `decide` mode, with the most capable model available. Give it the review files' paths, the index, the target, and the fix rounds left (two minus this round for a feature or polish feature; none for a verdict, which scores one build). Its output path is `docs/game/reviews/<target>/decisions.md`: per note, the review file, the note id, the decision and a one-line reason. Run step 4's `git status` check for this dispatch. An advisory note with no entry goes back to the decide pass once more. With no advisory notes, nothing is dispatched.
- **Interactive mode, verdict reviews:** when the person is in the session, they decide the advisory notes. Show them one at a time (role, what, evidence path, rule, anchor), with creative's decision as your recommendation; theirs stands. In a verdict the choices are `feature`, `topic` and `wontfix`.
- **Carry each decision out**, then write it into its note in the decision grammar from `docs/agents/game.md`:
  - `fixed`: make the fix and commit it: `fixed <commit>`. A fix that can't land within this round becomes a `feature` instead.
  - `feature`: add a feature to `features.json` with the fields `docs/agents/game.md` lists, the next unused id, tier `nice` (milestone `polish` when the decision says polish), the note's role in `roles` unless it is `design`, the note's rule as its acceptance, and a ticket: `feature <id>`.
  - `topic`: open a topic asking whether the rule is right, with the fields `docs/agents/game.md` lists and the note's role in `roles`, published as a `ready-for-human` ticket: `topic <id>`. The target can still pass.
  - `wontfix`: `wontfix: <the decider's reason>`.

You carry the decisions out; the decider makes them. The builder never decides a note on its own work and never picks `wontfix`: when the decide pass ran in-session (no subagent tool), a `wontfix` on your own work becomes a `topic`, so a person sees it.

**Done when** every note has a decision in the grammar whose commit, feature or topic exists, except a blocking note left open in round 2.

## 7. Record and commit

- The review files hold this round's notes with their decisions; `decisions.md` sits beside them.
- For a feature or polish feature, set its `reviews` in `features.json`: `{role: path}` for every role in its `roles`.
- **Role memory.** Append to `docs/game/roles/<role>.md` (create it if missing) one line per lesson the person taught: `- <date> <target> <kind>: <what> (why: <their reason>)`. Kinds: `overruled`, in the memory of the role whose call the person overruled (a reviewer's note they set aside with `wontfix`, or a decision of creative's they changed); `pick`, each A/B pick in this target's compare answers; `label`, each calibration label's reason that memory doesn't hold yet, for `art`, `ux` and `creative` (stills) and `feel` (strips).
- Run `gamestate.py check --since <base>`, then commit `game-review: <target> round <n> reviews`.
- Report to the caller: the round; per role, the result and each note with its decision; the blocking notes still open; the review file paths. A verdict puts the paths in its review items' `reviews` and lists every note and decision in its ADR.

When round 1 of a feature or polish feature fixed anything, run round 2 from step 2 on the new commit. After round 2, an open blocking note keeps the feature failing, and the caller counts the attempt.

**Done when** the round's review files, `decisions.md`, the `reviews` map and the memory lines are committed and `check --since <base>` names none of them; then either round 2 has begun or the caller has the report.
