# Role reviews: every aspect of the game has an owner with taste

Status: draft for approval · Date: 2026-11-23 · Branch: `design/role-reviews` (from `design/multi-repo`, release 0.6.0)

Research behind it: [docs/research/2026-11-23-game-development-roles.md](../../research/2026-11-23-game-development-roles.md) (what each studio role owns, produces and reviews; how studios review builds; what AI reviewers can and can't judge). Read its last section, "Wiring the roles into GameDirector's phases", before this one.

## Why

The user ran GameDirector on a simple idea with no human input, including brainstorming. On paper the flow was organized and every check passed, but the game looked bad and wasn't fun. Nothing in the skills owns taste:

- the verdict looks at captures but "records findings as notes; they inform the decision but score nothing";
- "feels good" is a checklist line about response time, and nothing ever asks whether the game is special or unique;
- art and feel only reach their final bar in polish, judged again by checklists.

Studios avoid this with roles: a creative director, a game designer, an art director, audio, narrative, UX and a feel owner. Each one sets a direction early, keeps rules that a build can visibly fail, and reviews the actual game. The research also gives a warning. Claude-Code-Game-Studios (CCGS), the closest prior art, measured that its 30-document, role-gated path cost several times more and ranked **last** with blind reviewers and a human playtest. Its creative roles can't launch the game, so they judge documents. What helped instead was a better brief and the rule that anything visible is launched and screenshotted before it counts. AI reviewers reliably catch broken things and rarely catch good ones. Fun, beauty and sound stay provisional until a person plays.

## What the user decided

1. **The roles.** Each real studio role takes part in ideation, brainstorming and the implementation phases. It follows its own process with its own deliverables (the art director's references, palette and art bible, for example).
2. **Ideation and brainstorming always wait for a person** (option A). The roles sharpen the questions and challenge the person's answers. They never answer in the person's place, and unattended runs stop at these steps as they do today.
3. **Only the relevant roles review.** The session decides which roles are in charge of each topic and feature, and only those prepare challenges or review.
4. **Reviews run in parallel as subagents.**
5. **The person gets two more short moments** besides the slice playtest:
   - **calibration:** labelling about ten screenshots "our game / not our game" once the first in-game visual target exists;
   - **A/B picks in polish:** choosing between before-and-after captures.
6. **Structure: one skill per role, one agent per role, and one review skill.**
   - The **role skill** holds the role's process for every phase and its page template. The main session uses it with the person.
   - The **role agent** is thin: limited tools, its own model, and its role skill preloaded. It runs challenges and reviews in parallel.
   - The **`game-review`** skill runs a review: it chooses the roles, gathers the inputs, dispatches the agents and has the creative director decide each note.
   - Tying the skill set to Claude Code for this is accepted.

## Goals

- Every taste aspect has an owner: identity, play, feel, look, sound, story and tone, and the player's understanding.
- Each owner sets a north star with the person in ideation, keeps one living page of rules a capture or build can fail, brings its challenges to each relevant brainstorm topic, and reviews the running game.
- A visible feature is not done until its roles have reviewed captures of it and every note has a recorded decision. The state tool enforces this, so agents can't skip it.
- Reviews are independent:
  - a fresh context per role;
  - artifacts in, notes out;
  - no reviewer edits the game;
  - one decider per note.
- Measured facts block. Judgments are advisory and decided on, and taste judgments are marked "not assessed" until the person has calibrated them.
- The person's few minutes go where the research says they matter: choosing directions and references, labelling calibration captures, playing the slice, and A/B choices in polish.

## Non-goals

- Replacing the person's playtest or pretending an AI score means "fun".
- New roles for producer, technical director and QA. Their work already lives in game-plan (scope, budgets, tech ADRs), game-build (tests) and game-verdict (stability, packaging). This design leaves it there.
- Role sign-offs on documents. Brainstorm challenges are the one place roles read text, because there is no build yet, and the person answers them.
- Multi-repo plans 2–4. They come after this (see Calls I made).

## Anti-goals (failure even if it works)

- **Document volume grows.** Each role keeps at most one page per subject, under the wiki's existing ~200-line split rule. If role pages turn into a document pile, this design has reproduced the CCGS result.
- **Reviewers rubber-stamp.** Agents "skew positive when grading their own work". A review that never finds anything, or approves with open notes, has failed.
- **A house formula.** A central reviewer applying generic genre criteria makes games alike (Ubisoft's editorial team, restructured in 2020). Every role judges against *this* game's north stars, references, rules and calibration labels, and weights distinctiveness explicitly.
- **Late wholesale rework.** The creative director can overturn direction only at ideation and at the slice verdict. Later phases fix toward the direction; they don't replace it.

## Constraints

- **Agnostic as before:** genre, engine, platform and tracker. Per-game numbers (palette, loudness, contrast, budgets) come from the game's own pages and plan, never from the plugin.
- **One step per session; `game-next` schedules; no orchestrator.** Subagents inside a session are fine; they don't talk to the person.
- **Subagents can't ask the person anything** (Claude Code removes AskUserQuestion from subagents). Every conversation with the person happens in the main session.
- **Phase skills keep `disable-model-invocation: true`.** Role skills must drop it, because Claude Code doesn't preload a skill with that flag into a subagent. Their descriptions must be narrow enough that Claude never invokes them on its own.
- **The plugin can't set an agent's permission mode or hooks.** Supported agent fields include name, description, model, effort, maxTurns, tools, disallowedTools, skills, memory, isolation and color.
- **`gamestate.py` stays stdlib-only, Python 3.8+, test-first.** Any new script follows the same rule.
- **Writing rules:** skills follow `writing-for-agents`, and every numbered step ends in a `**Done when**`. `tests/test_skills.py` checks the structure.
- **State changes go through a versioned upgrade:** `CURRENT_VERSION` becomes 7.

## Approaches considered

1. **A shared review skill that runs inside the phase sessions.** Role files plus `game-review`, with reviewers as subagents. Reviews sit next to the work they judge, the state tool enforces them, and nothing is tied to one tool.
2. **Reviews as their own sessions.** The state tool schedules `game-review F012 art,feel` after a visible feature passes. Each review gets a whole fresh session, but this roughly doubles the sessions for visible features, and features pass and then get reopened a session later. Rejected.
3. **Roles as Claude Code agents.** These bring harness-enforced tool limits, a model per role, the role always loaded, and parallel dispatch. But agents can't talk to the person, so the role's ideation and brainstorm parts can't live only in an agent.

**Chosen: 1 and 3 together.**
- A role skill per role carries the process, used with the person.
- A thin role agent per role preloads that skill and runs challenges and reviews.
- `game-review` orchestrates.

The user picked this after weighing what agents add over skills, and accepted tying the skill set to Claude Code.

## The design

### The seven roles

| Role id | Owns | Its page (wiki area) | North star set in ideation | Measures (code) | Judges (agent, on captures) | Needs the person |
|---|---|---|---|---|---|---|
| `creative` | the vision, identity and distinctiveness; decides every review note | `vision` (Vision), plus the identity invariants in `vision.json` | the genre default and this game's departure; the identity invariants polish must not remove | n/a | cohesion across the whole game against the invariants; whether it reads as generic | at ideation and the slice verdict |
| `design` | rules, systems, levels, opposition, economy | the Mechanics, Systems and Content pages (it already writes these) | the core loop's decisions, what makes runs or matches differ | bot completability, difficulty curve, decisions per minute, source/sink balance | dominant strategies and boring stretches in bot traces; enemy or content role clarity | whether it's fun to replay |
| `feel` | how core actions feel: response, feedback layers, camera | `feel`: one feel sheet per core action (Feel) | one or two adjectives and one to three reference clips per core action | input-to-response frames, buffer and forgiveness windows, feedback channels fired per action | frame strips around each action beside its references | feel on real hardware |
| `art` | the look: identity, palette, values, silhouettes, UI visual language, motion, VFX | `art-bible` (Art) | a slogan, 3–5 rules, a reference board, a chosen direction of 2–3 | palette match against the art bible's colour table, value histogram, contrast, colour-blindness simulation, silhouette overlap | cohesion with the visual target, read order, placeholder or stock-asset look | beauty, and the calibration labels |
| `audio` | sonic identity, feedback by ear, music, mix priority | `audio` (Audio) | what the player must be able to do by ear; one or two pillars; references and anti-references | every gameplay event mapped to a sound, variation counts, back-to-back repeats, loudness where the adapter can measure it | the sound list against the pillars (from logs and descriptions: the model can't hear) | listening |
| `narrative` | fantasy, tone, world, characters, every player-facing word | `tone-and-world` (Narrative and world) | a fantasy line, tone words and words to avoid, the setting in one sentence | glossary and naming consistency, string length, subtitle coverage | UI text and barks against the tone page, mismatches between story and play | whether players can restate the premise |
| `ux` | understanding and access: screens, HUD, onboarding, input, accessibility | `screens` and `onboarding` (Screens and onboarding) | the target player, input device, session context, access needs | launch-to-control time, text size, overlaps, contrast ratios, settings present | the first minute against the onboarding page, using Hodent-style usability heuristics | comprehension |

The table fixes each role's ownership, page and the kind of checks it runs. The questions, page templates and checklists inside each role skill are the builder's to write from the research report, following its "Wiring the roles" table. A **story-light game** keeps the `narrative` role with the report's minimum kit (fantasy line, setting sentence, tone words, UI voice, naming). A role can be switched off in ideation only with a reason the person accepts, recorded in `vision.json` (`roles_off: {"audio": "the game is played muted in class"}`).

### Which roles are in charge

- Topics and features get a `roles` list of role ids, set by whoever creates them:
  - **ideation** for the first topics;
  - **brainstorm** for follow-up topics;
  - **plan** for features;
  - **consolidate** for the gap topics it opens;
  - **build and verdict** for the topics and features their review notes create.
- A **default table in `game.md`** maps the wiki areas to roles:
  - Mechanics: design and feel
  - Controls: feel and ux
  - Systems: design
  - Content: design plus the roles its pieces touch (art, audio, narrative)
  - Modes and sessions: design and ux
  - Screens and onboarding: ux and art
  - Feel: feel, audio and art
  - Art: art
  - Audio: audio
  - Narrative and world: narrative
- The session starts from the table and adds or removes roles by judgment.
- A reviewer may add a role it finds missing. The review records that, and that role reviews too.
- `creative` is on every `core` topic, every verdict review and every polish review. On features it is the decider, not a reviewer.
- `check` rejects these:
  - an unknown role id;
  - an open topic with no roles;
  - a feature with empty `roles` whose `pages` include a page in Feel, Art, Audio, Narrative and world, or Screens and onboarding, or whose verify kind is `capture`. Plan can't dodge reviews by leaving roles empty on visible work.

### Wiki areas

**"Tone, art and world" splits into Art, Audio, and Narrative and world:**

| | Areas |
|---|---|
| Before | Vision, Mechanics, Controls, Systems, Content, Modes and sessions, Screens and onboarding, Feel, Tone, art and world |
| After | Vision, Mechanics, Controls, Systems, Content, Modes and sessions, Screens and onboarding, Feel, Art, Audio, Narrative and world |

- The home page template gets the new sections.
- Consolidate's "one page per area this stage needs" gate skips areas whose role is in `roles_off`.

### Ideation: north stars with the person

A new step goes between "Write the vision" and "Define the vertical slice", called **Set the roles' north stars**. For each active role, in the main session:

1. Read the role skill's `north-star` mode.
2. Ask the person its questions, one at a time, with a recommended answer as always.
3. Where the role compares options (art's 2–3 visual directions, each with a slogan, rules and references), present them and let the person choose. References are titles of games, films and artworks with what to take from each. When the person has images, save them under `docs/game/references/`.
4. `creative` asks last: "What would most games of this kind do, and where does ours depart?" It turns the answer into **identity invariants**: two to five things polish must never remove.

`vision.json` gains `north_stars` (one object per active role, each with at least a `statement` and two `references`; `art` also has `directions` and `choice`; `feel` has an entry per core action), `invariants` and `roles_off`. The ideation gate requires these. The `vision` page gets a short "Direction per role" section. The roles' full pages are **not** written in ideation: each becomes a seeded slice topic (for example `T-art`, "the art bible for the slice") with that role in charge, brainstormed with the person like any topic.

The slice quality-bar step recommends this default, still the person's call:
- feel at `production`;
- the visual target area at `production`, the rest `representative`;
- audio `representative`, with signature sounds near final.

The research found slices that leave art and audio at placeholder can't show whether the game will look and sound right.

### Brainstorm: the topic's roles prepare the challenges

Step 1 (Prepare) gains a parallel dispatch, before anything is asked:
1. One agent for each role in the topic's `roles` gets the topic and its parent chain, the vision and `vision.json`, the topic's pages and its own role page, and runs its role skill's `challenge` mode.
2. Each returns at most five challenges and the questions it would ask, as text, in its own fresh context.

The main session merges and orders them, then grills the person as today, attributing each challenge to its role ("the art role asks…"). The role pages the topic touches are drafted from the person's answers. The rest of brainstorm is unchanged, including that only the person answers.

### Plan: captures, the visual target first, roles on features

- **Capture protocol.** Plan defines named capture states for this game, recorded in `docs/game/engine-notes.md`: a beauty view, a typical play moment, peak effects load, each main menu, and the HUD over the brightest and darkest areas. It also defines frame strips: N frames after a scripted input, stitched into one contact-sheet image.
  - The adapter contract's `capture` gains `--state NAME` and `--strip INPUT --frames N --every K`.
  - `sim`, `replay` and `bot` gain an **event log**: each player action, its input-to-response frames, and the feedback channels it fired (visual effect, sound event, camera, haptic).
  - Where the engine can't do these, the adapter marks them `n/a` as today, and the affected checks become `not-assessed` or `human`.
- **The visual target and the feel target come first.** The slice milestone's first features are:
  - one in-game scene built to the slice's art bar (the visual target);
  - the core action at its feel sheet's targets.

  Everything later is reviewed against them. Calibration (below) is scheduled when the visual target passes.
- **Every feature gets `roles`** (see "Which roles are in charge"). Its acceptance includes the measured checks its roles' pages imply: palette within the art bible's table, response frames, feedback channels, sound coverage.
- **Measuring tool.** The plugin ships `skills/game-review/scripts/measure.py`: stdlib-only, PNG in, JSON and PNG out. It does:
  - palette match against a hex table;
  - value histogram;
  - contrast between given regions;
  - grayscale, thumbnail and colour-blindness-simulated copies, so reviewers can look at them;
  - contact sheets from frames.

  It works the same for any engine because it only reads captures.

### Build: a visible feature is done when its roles have reviewed it

After step 3 (Verify), for a feature with `roles`:

1. Capture the feature's states and frame strips from the built game in this session, and run its measured checks.
2. Run `game-review feature <id>`. It dispatches the feature's role agents in parallel on those artifacts.
3. A **measured failure blocks**: fix it and repeat from 1, at most two review rounds per session.
4. Judgment notes go to the `creative` decision:
   - **`fixed`:** the build doesn't match a page's rule and it's cheap. Fix it now, inside the same two-round cap.
   - **`feature`:** a new feature, `nice` or `polish`.
   - **`topic`:** the rule itself looks wrong. It goes back to the person, and the feature can still pass.
   - **`wontfix`:** a one-line reason.
5. Record the review in the feature's `reviews` before setting `passes`. A feature that can't clear its blocking notes in two rounds stays failing and counts an attempt, as today.

The builder never grades its own visible work.

### game-review: how a review runs

Task forms (also callable by the user directly):

| Task | What it reviews |
|---|---|
| `game-review feature <id>` | one feature, by its `roles` |
| `game-review topic <id>` | a topic's `challenge` mode (used by brainstorm) |
| `game-review <scope>` | the whole build, by every active role, for a verdict scope |
| `game-review polish <id>` | a polish feature, by its roles plus `creative` against the invariants |

Steps:

1. **Choose the roles.** Take the target's `roles` (or every active role for a scope), add `creative` where the table says, and add any role a previous review added.
2. **Prepare the inputs, once, in the main session.**
   - **Captures and strips** from one build at one commit, with their `measure.py` outputs.
   - **The event log and bot metrics.**
   - **The anchors:** the role's page, `vision.json` north stars and invariants, the references, the calibration labels (when they exist), and past decided notes for that role.

   Reviewers read these artifacts. They don't build or run the game themselves, which avoids parallel builds fighting over one checkout. A reviewer that needs another capture asks for it in its notes, and game-review makes one extra capture round.
3. **Dispatch** one role agent per role, in parallel, each with the paths above and its output path.
   - Each agent runs its role skill's `review` mode: it **measures first**, then **judges**. A judgment needs a rule from its page, a reference, or a calibration label it can point to.
   - Notes state the problem, its evidence and the rule. A suggested fix is optional and marked as a suggestion.
   - Taste judgments made before calibration labels exist are `not-assessed` with that reason.
4. **Check independence.** After the agents return, the working tree may differ only in the review files. Anything else is discarded and noted.
5. **Decide each note:** the `creative` decision above. In interactive mode, the person decides the notes a verdict review raises; they already approve verdict outcomes.
6. **Record and commit.** Each role's review is `docs/game/reviews/<target>/<role>.json`:
   - role, target, commit;
   - inputs (paths);
   - result: `ok`, `notes` or `not-assessed`, with a reason;
   - notes, each with: `id`, `what`, `evidence`, `rule`, `severity` (`blocking` for a measured failure, `advisory` otherwise), `suggestion` and `decision` (`fixed <commit>`, `feature F0xx`, `topic T0xx`, `wontfix: <reason>`).
7. **Append to the role's memory.** Each decided note and each of the person's choices that taught the role something go into `docs/game/roles/<role>.md`:
   - a note the person overruled;
   - an A/B pick;
   - a calibration label's reason.

   The agent reads that file on every run, so the role builds up calibration to this person's taste across sessions.

**`check` enforces:**
- the review JSON shape;
- that a feature can't go `passes: true` while any of its roles lacks a review at or after the feature's last code change;
- that every note has a decision whose `F`/`T` id exists;
- that no `blocking` note is open.

**Without a subagent tool** (another agent runtime), game-review runs the roles one at a time in the session, reading each role skill. The record says `"independent": false`, and verdicts treat such taste scores as `not-assessed`.

### The role agents

`agents/<role>.md` in the plugin, named `game-director:<role>`. Each has:

- **Model:** the most capable model for `creative`, `art` and `design`, and the standard model for the rest. The builder confirms against current model names.
- **Tools:** Read, Glob, Grep, Write (its review file and nothing else, checked in step 4), and Bash (only for `measure.py`). `Edit`, `NotebookEdit` and `Agent` are disallowed.
- **Skills:** its role skill (`game-role-<id>`), preloaded.
- **maxTurns:** a cap the builder sets from a trial review.
- **Body:** the role's stance in a few lines. Skeptical by design: "a review that finds nothing on a first build has probably not looked", and "you never see the builder's reasoning, only the artifacts".

If preloading plugin skills by name doesn't work, `game-review` passes the role skill's absolute path in the dispatch prompt (it knows its own base directory), and the agent reads it first.

### Verdicts: a review of the whole build, decided per note

Verdict step 3 ("Look at it", today unscored) becomes `game-review <scope>`. Every active role reviews the whole build's captures, strips, bot traces and event logs. `creative` judges cohesion and invariants. Every note gets a decision. The fun checklist gains a third kind:

- **`review`:** an item judged by named roles (`"roles": ["art"]`), scored from the review files.
  - A `review` item that depends on taste is `not-assessed` until calibration labels exist, so **the slice can't ship until the person has calibrated**. It already can't ship until they have played it.
  - Consolidate adds at least one `review` item each for `creative`, `art` and `feel` at slice scope, for example:
    - "a fresh capture reads as this game, not its genre default";
    - "captures match the visual target";
    - "every core action meets its feel sheet".
  - It adds one per active role at full scope.

The verdict ADR records every role's notes and their decisions next to the score table.

### The person's two new moments

- **Calibration** (human queue kind `calibrate`, added when the visual target feature passes):
  - **The kit:** 8–12 captures from this build, the person's references, and two or three "not our game" examples (the engine's default scene, a stock-asset scene, a capture with the palette broken on purpose).
  - **The ask:** "ours" or "not ours", with one line why. The answers go to `docs/game/calibration/labels.json`.
  - **Who uses them:** the art and feel reviewers read the labels as anchors; their taste judgments are `not-assessed` until then. Builds don't stop meanwhile; measured checks still block.
  - **Redo:** calibration repeats when the art direction changes (an adjust or restart that changes `north_stars.art`).
- **A/B picks in polish** (human queue kind `compare`):
  - Polish features whose acceptance is a taste judgment (a colour grade, a feel retune, a mix) use verify kind `human` with a `compare` entry: two to four pairs of before-and-after captures or strips. The person picks one of each pair.
  - The picks go into `keep.json` pins when a knob controls them, and into the role's memory file.
  - The feature passes on the pick.

Both wait in unattended runs exactly as the playtest does.

### Polish: one pass per role, guarded by the invariants

game-polish's checklist sections become role-owned:
- feel: one pass per core action, tuned one parameter at a time against reference strips;
- art: a cohesion pass (normalise outliers, unify outline and density), lighting or grade per area, and noise reduction in the play layer;
- audio: a mix in the worst-case scene, a variation and repetition pass, a missing-sound sweep, and loudness compliance;
- narrative: tone, continuity and localisation readiness;
- ux: accessibility settings and onboarding timing.

Every polish feature names its role and is reviewed by it plus `creative` against the identity invariants, so polish can't sand off what makes the game recognisable.

### State tool changes (version 7)

- `ROLES = ["creative", "design", "feel", "art", "audio", "narrative", "ux"]`.
- The new `AREAS`, with `SLICE_AREAS` excluding Modes and sessions as before.
- `roles` on topics and features, validated as above.
- `reviews` on features, and the review JSON shape with its pass rule.
- Fun item kind `review`, with `roles`, scoring and the `not-assessed` rule.
- Human queue kinds `calibrate` and `compare`, and their scheduling.
- `vision.json` `north_stars`, `invariants` and `roles_off` in the ideation gate.
- `CURRENT_VERSION = 7`. Upgrade handles setup-phase games as in 0.6.0; mid-run games are still refused.

### Skills and files touched

**New:**
- `skills/game-review/`: SKILL.md and `scripts/measure.py`;
- `skills/game-role-{creative,design,feel,art,audio,narrative,ux}/`: SKILL.md with `north-star`, `challenge` and `review` modes, plus reference files for its questions, page template and checklist;
- `agents/{creative,design,feel,art,audio,narrative,ux}.md`.

**Changed:**
- `game.md`: roles, the area table, schema, reviews and the person's moments;
- `adapter-contract.md`: capture states, strips and the event log;
- game-ideation, game-brainstorm, game-consolidate, game-plan, game-build, game-verdict and game-polish, as above;
- game-gdd: a "Direction" page from the north stars, and the review decisions in Status;
- `index-template.md`, `gdd-structure.md`, `gamestate.py`, the tests, README and `plugin.json` (skills list; agents are discovered from `agents/`).

**Tests:**
- `test_skills.py` learns that `game-role-*` skills must *not* have `disable-model-invocation` and must have a narrow "Use only when…" description;
- agents need name, description, model, tools, disallowedTools including Edit and Agent, and a `skills` entry naming an existing role skill.

## What's left to the builder

- Each role skill's question bank, page template and review checklist, written from the research report's role sections, short and failable.
- The exact `measure.py` operations and outputs, and the `vision.json` and review JSON field details beyond those named here.
- How capture states and strips map to each adapter, the `maxTurns` caps, and the agent prompt wording.
- Wording of the GDD "Direction" page.

## Calls I made (check these)

1. **Role memory is an explicit file, `docs/game/roles/<role>.md`, not the agents' `memory` field.** The docs say `memory` does nothing when auto memory is off and don't describe it for plugin agents. A committed file gives the same build-up of taste, works in unattended loops, and the state tool can see it.
2. **Reviewers read artifacts made once by `game-review`; they don't run the game themselves.** Parallel builds in one checkout would collide, and worktree isolation would rebuild the game per reviewer. A reviewer can ask for one extra capture round.
3. **The roles' full pages are seeded as slice topics, not written in ideation.** Ideation stays a short conversation, and each page gets a full brainstorm with the person.
4. **The creative director decides notes; reviewers never decide.** In interactive mode the person decides verdict notes.
5. **Producer, technical director and QA stay inside plan, build and verdict.**
6. **Two review rounds per feature per session.** Past that, the feature stays failing and the attempt counts, as the build skill already does for red verifies.
7. **Calibration gates the slice ship but not builds.**
8. **Mid-run upgrade to version 7 stays unsupported.** No mid-run game on 0.6.0 exists yet; EveLikeBrawl is still at setup.
9. **Order:** this ships as 0.7.0 before multi-repo plans 2–4, because the user's current problem is quality.
10. **The research report is committed** at `docs/research/` so the role skills can cite it.
