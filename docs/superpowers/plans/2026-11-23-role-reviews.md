# Role Reviews and Research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every taste aspect of a game an owner: seven role skills and agents. They set north stars with the person, study references in a new research phase, challenge brainstorm topics, and review the running build. A visible feature isn't done until its roles have reviewed it, and a role can fail a verdict only when its judgment is anchored to the person.

**Architecture:**
- **The state tool** (`gamestate.py`) learns roles, reviews, review-kind fun items, the research phase, calibration and the new `vision.json` fields, all enforced by `check`, the gates and the routing.
- **New skills:**
  - seven `game-role-*` skills, each preloaded into a thin plugin agent in `agents/`;
  - `game-review`, which runs reviews in parallel;
  - `game-research`, the new phase.
- **The existing phase skills** call these.
- **`measure.py`** (stdlib-only) turns captures into facts.

**Tech Stack:** Python 3.8+ standard library only (`gamestate.py`, `measure.py`, tests with `unittest`); Markdown skills in the Agent Skills format; Claude Code plugin agents (`agents/*.md`).

**Spec:** `docs/superpowers/specs/2026-11-23-role-reviews-design.md`. Research it cites: `docs/research/2026-11-23-game-development-roles.md` and `docs/research/2026-11-23-game-market-research.md`. Implementers of skill-writing tasks read the parts of these their task names.

## Global Constraints

- **Code:** `gamestate.py` and `measure.py` use the Python 3.8+ standard library only. Change them test-first: write the failing test, see it fail, then implement. `python3 -m unittest discover tests` must be green at the end of every task.
- **Skills follow the `writing-for-agents` skill.** Every numbered step (`## N.` / `### N.`) ends in a `**Done when**` line, and reference material sits behind pointers. Skills point to `docs/agents/game.md` instead of repeating it.
- **`disable-model-invocation`:**
  - Phase skills, `game-review` and `game-research` keep `disable-model-invocation: true`.
  - `game-role-*` skills must **not** have it, and their description starts `Use only when` (Claude Code won't preload a skill with that flag into a subagent).
- **Exact values:**
  - Role ids, in this order: `creative`, `design`, `feel`, `art`, `audio`, `narrative`, `ux`.
  - Wiki areas, in this order: `Vision`, `Mechanics`, `Controls`, `Systems`, `Content`, `Modes and sessions`, `Screens and onboarding`, `Feel`, `Art`, `Audio`, `Narrative and world`.
- **State versions:** `CURRENT_VERSION` becomes `7`. Mid-run upgrades stay unsupported; setup-phase games are reset as in 0.6.0.
- **The plugin version** becomes `0.7.0`, in Task 15 only.
- **Commits** end with exactly these two lines. No model identifier appears in commit messages, code comments or docs. An agent's `model:` field uses the aliases `opus` or `sonnet` as configuration.

  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01N8DsbmJZ8SGtg9yYL18gm8
  ```

  Don't push; the controller pushes.
- **Don't touch** `research_notes/`, `reports/` or `.superpowers/` (git-ignored scratch).

## Review Focus

1. **A role in `vision.json` `roles_off` that is still named somewhere.** Topic, feature or fun item `roles` that name it should give a `check` reason naming `roles_off`, not silently pass. The test is in Task 1.
2. **Malformed new files** (`references.json`, `homework.json`, a review JSON, `labels.json` that is a list or has non-dict entries) give reasons, not tracebacks. Tests are in Tasks 2 and 5.
3. **A note decision that names a feature or topic that doesn't exist** (`feature F099`) is a `check` reason. The test is in Task 2.
4. **A taste `review` item scored `pass` before `docs/game/calibration/labels.json` exists** is refused by the verdict gate. The test is in Task 3.
5. **A `hobby` game doesn't need comps; a `sell` game needs three.** Setup refuses a missing `intent`. Tests are in Task 5.
6. **`measure.py` on a PNG it can't decode** (16-bit, interlaced, not a PNG) exits 2 with a message, not a traceback. The test is in Task 7.

---

## File structure

| Path | Responsibility | Task |
|---|---|---|
| `skills/game-setup/scripts/gamestate.py` | roles, reviews, review items, research phase, calibration, vision fields, v7 | 1–6 |
| `tests/test_gamestate.py` | end-to-end tests of the above (fixtures updated) | 1–6 |
| `skills/game-review/scripts/measure.py` | captures → facts and derived images | 7 |
| `tests/test_measure.py` | measure.py tests | 7 |
| `tests/test_skills.py` | role-skill and agent packaging rules | 8 |
| `skills/game-role-<id>/` (×7) | the role's process per mode, plus `questions.md`, `page-template.md`, `checklist.md`, `dossier.md` | 8–10 |
| `agents/<id>.md` (×7) | thin plugin agents preloading their role skill | 8–10 |
| `skills/game-review/SKILL.md` | how a review runs | 11 |
| `skills/game-research/SKILL.md` | the research phase | 5 (stub), 12 |
| `skills/game-setup/*` | intent, research sources, roles in `game.md`, capture contract | 12, 13 |
| `skills/game-{ideation,brainstorm,consolidate}/*` | north stars, role challenges, review items | 13 |
| `skills/game-{plan,build,verdict,polish,gdd,next}/*` | capture protocol, targets, reviews, role passes, GDD pages | 14 |
| `README.md`, `.claude-plugin/plugin.json` | release 0.7.0 | 15 |

---

### Task 1: Roles on topics and features; the new wiki areas

**Files:**
- Modify: `skills/game-setup/scripts/gamestate.py` (constants near line 37–68, `_check_topics`, `_check_features`, `_consolidate_gate` via `SLICE_AREAS`)
- Modify: `skills/game-ideation/index-template.md` (one `## <area>` section per new area)
- Modify: `skills/game-setup/game.md` (the `area` list under "The wiki" only; the rest is Task 13)
- Test: `tests/test_gamestate.py`

**Interfaces:**
- Produces:
  - constants `ROLES`, `TASTE_AREAS = ["Screens and onboarding", "Feel", "Art", "Audio", "Narrative and world"]`, and the new `AREAS`;
  - `Game.active_roles() -> list` (ROLES minus the keys of `vision.json` `roles_off`, in ROLES order);
  - `Game._check_roles(owner: str, roles, on_feature: bool = False) -> list` (reason strings).

  Topics and features gain `"roles": [...]`.

- [ ] **Step 1: Update fixtures, then write the failing tests**

  **Fixtures:**
  - `AREAS` and `PAGE_IDS` replace `"Tone, art and world": ["art"]` with `"Art": ["art"]`, `"Audio": ["audio"]` and `"Narrative and world": ["tone"]`.
  - `topic(...)` takes `roles=("design",)` and stores `list(roles)`.
  - `feature(...)` takes `roles=()`.

  **Tests:**

```python
def test_topics_and_features_name_known_roles(self):
    self.to_plan()
    self.edit("topics.json", lambda d: d["topics"][1].update(roles=["lighting"]))
    self.assertIn("topic T2: role 'lighting' is not one of", self.tool("check", ok=False))
    self.edit("topics.json", lambda d: d["topics"][1].update(roles=[]))
    self.assertIn("topic T2: open without roles", self.tool("check", ok=False))

def test_visible_features_need_roles_and_design_reviews_only_at_verdicts(self):
    self.to_plan()
    self.edit("features.json", lambda d: d.update(features=[feature("F1", "core-loop", kind="capture")]))
    self.assertIn("F1: visible work needs roles", self.tool("check", ok=False))
    self.edit("features.json", lambda d: d["features"][0].update(roles=["design"]))
    self.assertIn("F1: design judges at verdicts, not on features", self.tool("check", ok=False))
    self.edit("features.json", lambda d: d["features"][0].update(roles=["art"]))
    self.tool("check")  # passes

def test_a_role_switched_off_cannot_be_named(self):
    self.to_plan()
    self.edit("vision.json", lambda v: v.update(roles_off={"audio": "played muted in class"}))
    self.edit("topics.json", lambda d: d["topics"][1].update(roles=["audio"]))
    self.assertIn("topic T2: role 'audio' is switched off in vision.json roles_off", self.tool("check", ok=False))
```

  Also:
  - a page `{"pages": ["art"]}` (area Art) on a `test`-verified feature with `roles: []` gives the same "visible work needs roles" reason;
  - `test_consolidate_gate_skips_areas_of_roles_switched_off`: with `roles_off: {"audio": "muted"}` and no Audio page, the slice consolidate gate doesn't ask for one.

- [ ] **Step 2: Run them to see them fail**

  Run: `python3 -m unittest tests.test_gamestate -k roles -k visible -k switched`

  Expected: FAIL (AREAS mismatch and the missing reasons).

- [ ] **Step 3: Implement**

  **Constants and helpers:**
  - Constants `ROLES`, `TASTE_AREAS` and the new `AREAS`; `SLICE_AREAS` keeps its definition.
  - `active_roles()` reads `self.vision().get("roles_off")`, ignoring it when it's not a dict.

  **`_check_roles` returns these reasons:**
  - `"<owner>: role '<r>' is not one of [...]"`;
  - `"<owner>: role '<r>' is switched off in vision.json roles_off"`;
  - `"<owner>: design judges at verdicts, not on features"` (only with `on_feature`);
  - `"<owner>: roles must be a list"` when it isn't one.

  **Topics:** `_check_topics` calls `_check_roles(f"topic {tid}", t.get("roles", []))` and adds `"topic <tid>: open without roles (who prepares its challenges?)"` for an open topic with none.

  **Features:** `_check_features` calls `_check_roles(fid, ..., on_feature=True)`. It adds `"<fid>: visible work needs roles (pages in <areas> or verify kind capture)"` when `roles` is empty and either verify kind is `capture` or one of its `pages` has an area in `TASTE_AREAS`.

  **Consolidate:** `_consolidate_gate` skips Art, Audio, and Narrative and world when `art`, `audio` or `narrative` is not in `active_roles()`.

  **Templates:** update `index-template.md` sections and the `game.md` area list.

- [ ] **Step 4: Run the whole suite**

  Run: `python3 -m unittest discover tests`

  Expected: OK (including `test_index_template_has_a_section_per_area`).

- [ ] **Step 5: Commit** `gamestate: roles on topics and features; Art, Audio, and Narrative and world areas`

---

### Task 2: Feature reviews and the review record

**Files:**
- Modify: `skills/game-setup/scripts/gamestate.py`
- Test: `tests/test_gamestate.py`

**Interfaces:**
- Consumes: `ROLES`, `_check_roles` (Task 1).
- Produces:
  - **Constants:**
    - `REVIEW_RESULTS = ["ok", "notes", "not-assessed"]`
    - `SEVERITIES = ["blocking", "advisory"]`
    - `ANCHOR_KINDS = ["label", "reference", "rule"]`
    - `DECISION_RE = r"^(fixed [0-9a-f]{7,40}|feature F\d+|topic T\d+|wontfix: \S.*)$"`
  - **Methods:**
    - `Game.review(path: str) -> dict | None` (the parsed JSON, None when missing or not an object);
    - `Game._review_shape(path: str) -> list`;
    - `Game._check_reviews() -> list`;
    - `Game._review_guard(since: str) -> list`.
  - **Feature field:** `"reviews": {role: "docs/game/reviews/<target>/<role>.json"}`.
  - **Review JSON shape** (`docs/game/reviews/<target>/<role>.json`):

```json
{"role": "art", "target": "F012", "commit": "abc1234", "independent": true,
 "inputs": ["docs/game/reviews/F012/inputs/beauty.png"], "result": "notes", "reason": "",
 "notes": [{"id": "N1", "what": "HUD text sinks into the sky", "evidence": "inputs/hud-bright.png contrast 2.1:1",
            "rule": "art-bible: HUD contrast >= 4.5:1", "severity": "advisory",
            "anchor": {"kind": "rule", "ref": "art-bible#hud"}, "item": "FC7",
            "suggestion": "outline the text", "decision": "feature F031"}]}
```

- [ ] **Step 1: Write the failing tests**

```python
def test_a_visible_feature_passes_only_after_its_roles_reviewed_it(self):
    self.to_plan()
    self.plan(extra=[feature("F4", "slice", kind="capture", roles=("art", "feel"))])
    self.set_passes("F1", "F2")
    base = self.git("rev-parse", "HEAD").strip()
    self.set_passes("F4")
    out = self.tool("check", "--since", base, ok=False)
    self.assertIn("F4: passes without a review by art", out)
    self.write_review("F4", "art", base)
    self.write_review("F4", "feel", base, notes=[self.note(severity="blocking", decision="")])
    out = self.tool("check", "--since", base, ok=False)
    self.assertIn("F4: feel review note N1 is blocking and not fixed", out)

def test_review_notes_need_decisions_that_point_somewhere(self):
    self.to_plan()
    self.write_review("F1", "art", "HEAD", notes=[self.note(decision="feature F099")])
    self.assertIn("docs/game/reviews/F1/art.json: note N1 decision names F099, which does not exist",
                  self.tool("check", ok=False))
    self.write_review("F1", "art", "HEAD", notes=[self.note(decision="maybe later")])
    self.assertIn("note N1 decision 'maybe later' is not", self.tool("check", ok=False))

def test_malformed_reviews_are_reasons_not_crashes(self):
    self.to_plan()
    self.write("docs/game/reviews/F1/art.json", "[]")
    self.assertIn("docs/game/reviews/F1/art.json: not a JSON object", self.tool("check", ok=False))
```

  Helpers on `GameRun`:
  - `write_review(target, role, commit, notes=(), result=None)` writes a valid review JSON (result defaults to `"notes"` when notes exist, else `"ok"`; commit `"HEAD"` resolves to `git rev-parse HEAD`). When `target` is a feature id, it sets that feature's `reviews[role]`, then commits.
  - `note(**overrides)` returns the example note above, with overrides applied.

- [ ] **Step 2: Run them to see them fail.**

  Run: `python3 -m unittest tests.test_gamestate -k review`

  Expected: FAIL.

- [ ] **Step 3: Implement**

  **`_review_shape(path)` checks**, each failure a reason prefixed with `path`:
  - the file is an object;
  - `role` is in ROLES;
  - `target` and `commit` are non-empty;
  - `result` is in REVIEW_RESULTS, and `not-assessed` has a `reason`;
  - `notes` is a list of objects, each with `id`, `what`, `evidence`, and `severity` in SEVERITIES;
  - an `anchor`, if present, has `kind` in ANCHOR_KINDS and a `ref`;
  - every `decision` matches DECISION_RE (`note <id> decision '<d>' is not one of fixed <commit> | feature F.. | topic T.. | wontfix: <reason>`);
  - `feature F..` and `topic T..` decisions name existing ids.

  **`_check_reviews()` runs `_review_shape`:**
  - over every `docs/game/reviews/**/*.json`;
  - for each feature with `passes: true` and non-empty `roles`, it adds:
    - `"<fid>: passes without a review by <role>"` when `reviews[role]` is missing or the file doesn't exist;
    - `"<fid>: <role> review note <id> is blocking and not fixed"` for a blocking note whose decision doesn't start `fixed`;
    - `"<fid>: <role> review note <id> has no decision"`.

  **`_review_guard(since)`:** for each feature whose `passes` went from false (at `since`) to true, each role's review `commit` must satisfy `git merge-base --is-ancestor <since> <commit>`. Otherwise the reason is `"<fid>: the <role> review predates this session's work; review again"`.

  **Wiring:** `check()` calls `_check_reviews()`, and `_review_guard(since)` alongside `_feature_guard`.

- [ ] **Step 4: Run the whole suite.** Expected: OK.

- [ ] **Step 5: Commit** `gamestate: a visible feature passes only with decided reviews by its roles`

---

### Task 3: Review items in the fun checklist, scored from anchored notes

**Files:**
- Modify: `skills/game-setup/scripts/gamestate.py` (`_check_targets`, `_consolidate_gate`, `_verdict_gate`, `kinds`)
- Test: `tests/test_gamestate.py`

**Interfaces:**
- Consumes: `review()` (Task 2), `active_roles()` (Task 1).
- Produces:
  - **Constants:** `FUN_KINDS = ["proxy", "human", "review"]`, `CALIBRATED_ROLES = ["creative", "feel", "art", "ux"]`, `LABELS = "docs/game/calibration/labels.json"`.
  - **Method:** `Game.review_result(item: dict, paths: list) -> str` (one of pass, fail, not-assessed).
  - **A review item:** `{"id", "statement", "scope", "kind": "review", "roles": [...], "taste": bool}`.
  - **Its verdict score:** `{"result", "evidence": <first review path>, "reviews": [paths]}`.

- [ ] **Step 1: Update the fixture and write the failing tests**

  **Fixture:** `FUN` gains these items:
  - `FC5` review, scope slice, roles `["art"]`, taste true;
  - `FC6` review, scope slice, roles `["feel"]`, taste true;
  - `FC7` review, scope slice, roles `["creative"]`, taste true;
  - `FC8` review, scope full, roles `["audio"]`, taste false.

  `record_verdict` writes review files for review items: one per role, under `docs/game/reviews/verdict-<scope>/<role>.json`, with no notes, and `reviews` in the score.

```python
def test_slice_consolidate_needs_review_items_for_creative_art_and_feel(self):
    ...  # remove FC6, complete fails with "fun checklist has no slice review item for feel"

def test_review_items_fail_only_on_anchored_notes(self):
    self.to_slice_verdict()
    self.calibrate()
    unanchored = self.note(anchor=None, item="FC5", decision="feature F3")
    self.record_verdict("adjust", reviews={"art": [unanchored]}, complete=False)
    self.tool("complete")  # FC5 scored pass: an unanchored note doesn't change the score
    anchored = self.note(item="FC5", decision="feature F3")  # the example note carries a rule anchor
    self.record_verdict("adjust", reviews={"art": [anchored]}, complete=False)
    self.assertIn("FC5: scored pass but its reviews say fail", self.tool("complete", ok=False))

def test_taste_items_are_not_assessed_until_calibration(self):
    self.to_slice_verdict()  # no labels.json
    self.record_verdict("ship", complete=False)
    self.assertIn("FC5: scored pass but its reviews say not-assessed", self.tool("complete", ok=False))

def test_review_items_do_not_count_toward_the_ten_item_cap(self):
    ...  # 10 proxy/human items + 7 review items pass the production consolidate gate
```

  Write these as complete tests. `calibrate()` writes `LABELS` as `{"labels": [{"capture": "x.png", "ours": true, "why": "palette"}]}` and commits. `record_verdict(..., reviews={role: [notes]})` puts those notes into that role's review file.

- [ ] **Step 2: Run them to see them fail.** Expected: FAIL.

- [ ] **Step 3: Implement**

  **`_check_targets`:**
  - `kind` must be in FUN_KINDS;
  - a review item needs non-empty `roles`, checked with `_check_roles(f"fun {iid}", ...)`;
  - `taste` must be a bool;
  - review items need no metric, threshold or how.

  **`_consolidate_gate`:**
  - **Slice stage:** add `"fun checklist has no slice review item for <role>"` for each of `creative`, `art` and `feel` that is in `active_roles()`. Those review items are excluded from the 3–6 count.
  - **Production:** add `"fun checklist has no full review item for <role>"` for each active role. The 10-item cap counts only proxy and human items.

  **`review_result(item, paths)`** decides in this order:
  1. any note in those reviews with `item == item["id"]` and a valid anchor → `fail`;
  2. the item has `taste`, one of its roles is in CALIBRATED_ROLES, and LABELS doesn't exist → `not-assessed`;
  3. any of the reviews has result `not-assessed` or `independent` false → `not-assessed`;
  4. otherwise → `pass`.

  **`_verdict_gate`, for review items:**
  - the score needs `reviews`: one existing, valid review per role on the item (`"<iid>: needs a review by <role>"`);
  - the recorded result must equal `review_result` (`"<iid>: scored <x> but its reviews say <y>"`);
  - the existing ship rules then apply unchanged;
  - `pending-human` stays human-only.

- [ ] **Step 4: Run the whole suite.** Expected: OK.

- [ ] **Step 5: Commit** `gamestate: review items fail only on anchored notes; taste waits for calibration`

---

### Task 4: North stars, invariants and role topics in ideation

**Files:**
- Modify: `skills/game-setup/scripts/gamestate.py` (`_vision_shape`, `_ideation_gate`)
- Test: `tests/test_gamestate.py`

**Interfaces:**
- Consumes: `active_roles()`.
- Produces: `vision.json` keys `north_stars`, `invariants` and `roles_off`:

```json
"north_stars": {
  "creative": {"statement": "...", "references": ["...", "..."], "genre_default": "...", "departure": "..."},
  "design":   {"statement": "...", "references": ["...", "..."]},
  "feel":     {"statement": "...", "references": ["...", "..."], "actions": {"dash": {"words": ["snappy"], "references": ["..."]}}},
  "art":      {"statement": "...", "references": ["...", "..."], "directions": 3, "choice": "A2"},
  "audio":    {"statement": "...", "references": ["...", "..."]},
  "narrative":{"statement": "...", "references": ["...", "..."]},
  "ux":       {"statement": "...", "references": ["...", "..."]}
},
"invariants": ["the ink-wash palette", "one-button dash"],
"roles_off": {}
```

- [ ] **Step 1: Update the fixture and write the failing tests**

  **Fixtures:**
  - `VISION_JSON` gains the block above, with real strings.
  - `SEED_TOPICS` gains slice topics `T7`–`T11` with roles `feel`, `art`, `audio`, `narrative` and `ux` respectively (pages empty, open, priority support).

```python
def test_ideation_needs_a_north_star_per_active_role_and_invariants(self):
    self.to_ideation()
    v = json.loads(json.dumps(VISION_JSON)); del v["north_stars"]["art"]; v["invariants"] = ["one"]
    (self.game / "vision.json").write_text(json.dumps(v))
    out = self.tool("complete", ok=False)
    self.assertIn("vision.json north_stars: art missing", out)
    self.assertIn("vision.json invariants: 1; needs 2-5", out)

def test_art_direction_and_feel_actions_are_required(self):
    ...  # art "directions": 1 -> "north_stars.art: directions 1; needs 2-3"; no choice -> "...: no choice";
         # feel "actions": {} -> "north_stars.feel: no core action"

def test_each_role_with_a_page_has_a_slice_topic(self):
    ...  # drop T8 (art) -> "no slice topic for role art (its page)"; with roles_off {"art": "..."} it passes
```

- [ ] **Step 2: Run them to see them fail.** Expected: FAIL.

- [ ] **Step 3: Implement**

  **`_vision_shape`** reports non-dict `north_stars`, a non-list `invariants`, and a non-dict `roles_off` or blank reasons, as reasons.

  **`_ideation_gate`** adds, for each active role:
  - `"vision.json north_stars: <r> missing"`;
  - `"north_stars.<r>: no statement"`;
  - `"north_stars.<r>: <n> references; needs 2"`;
  - for art: directions an int from 2 to 3, and a non-empty `choice`;
  - for feel: a non-empty `actions` dict.

  It also adds:
  - `"vision.json invariants: <n>; needs 2-5"`;
  - for each active role in `feel`, `art`, `audio`, `narrative`, `ux`: a seeded topic with `stage: slice` whose `roles` contains it, else `"no slice topic for role <r> (its page)"`.

- [ ] **Step 4: Run the whole suite.** Expected: OK.

- [ ] **Step 5: Commit** `gamestate: ideation sets each role's north star and the identity invariants`

---

### Task 5: The research phase

**Files:**
- Modify: `skills/game-setup/scripts/gamestate.py` (PHASES, DESIGN_PHASES, DEFAULT_STATE, setup gate, `advance`, `_restart`, `_work`, `gate`, docstring Commands untouched)
- Create: `skills/game-research/SKILL.md` (**stub**: frontmatter, a one-paragraph purpose, and a `## Modes` table naming `game-research`, `ref`, `brief`, `homework` and `restart`, each with one line; no numbered steps yet. Task 12 writes the skill.) and `skills/game-research/agents/openai.yaml`
- Modify: `.claude-plugin/plugin.json` (list `./skills/game-research`)
- Test: `tests/test_gamestate.py`

**Interfaces:**
- Produces:
  - **Constants:**
    - `PHASES` with `"research"` between `"setup"` and `"ideation"`; `DESIGN_PHASES` includes it;
    - `INTENTS = ["sell", "hobby"]`, `REF_WHY = ["comp", "aspect"]`, `HOW_STUDIED = ["played", "watched", "read", "not-assessed"]`;
    - `MAX_HOMEWORK = 10`, `MIN_COMPS = 3`, `MIN_SOURCES = 3`, `IMAGE_ROLES = ["art", "ux", "feel"]`.
  - **`DEFAULT_STATE`** gains `"intent": None` and `"research_sources": None`.
  - **Methods:**
    - `Game.references() -> list`;
    - `Game.homework() -> list`;
    - `Game.homework_open() -> list` (items whose `status` is `open`);
    - `Game._check_research() -> list` (shapes);
    - `Game._research_gate() -> list`;
    - `Game._research_action() -> str | None`.
  - **Files:**
    - `docs/game/research/references.json` — `{"scanned_for": null|"<adr>", "refs": [{"id": "R1", "title", "why", "roles": [...], "sources": [...], "status": "open"|"studied", "how_studied": {role: {"how": ..., "reason": ...}}}]}`;
    - dossiers at `docs/game/research/refs/<id>/<role>.md`;
    - the audit at `docs/game/research/refs/<id>/audit.json` (review JSON shape, role `creative`, target `<id>`);
    - `docs/game/research/homework.json` — `{"reason": "", "items": [{"id": "H1", "what", "why", "questions": [...], "minutes", "roles": [...], "status": "open"|"answered"|"skip", "answer": ""}]}`.

- [ ] **Step 1: Update helpers and write the failing tests**

  **Helpers:**
  - `to_ideation()` sets `intent: "sell"` and `research_sources: {"checked": "2026-11-23", "reachable": [], "unreachable": []}`, completes setup, advances to research, calls a new helper `research()`, then advances to ideation.
  - `research()` writes:
    - 3 comps plus one aspect reference per role not covered, all studied;
    - dossier files for each role;
    - one `.png` per IMAGE_ROLES dossier directory;
    - 3 sources each;
    - an audit with no notes;
    - the `research` wiki page (area Vision);
    - `homework.json` with one `answered` item.

    Then it commits and runs `complete`.

```python
def test_setup_needs_intent_and_checked_research_sources(self):
    ...  # missing intent -> "state.intent must be one of ['sell', 'hobby']"; missing sources -> "research sources not checked"

def test_research_runs_scan_then_one_session_per_reference_then_the_brief(self):
    ...  # next() == "game-research" (no refs); after refs R1..R3 open -> "game-research ref R1";
         # all studied, no research page -> "game-research brief"; gate passes -> "advance"; never "with-user:"

def test_research_gate_checks_evidence_per_reference(self):
    ...  # R1 with 2 sources -> "R1: 2 sources; needs 3"; art dossier without an image ->
         # "R1: no image for the art section"; how_studied art {"how": "not-assessed"} without reason ->
         # "R1: art not-assessed needs a reason"; an open audit note -> "R1: audit note N1 is open"

def test_hobby_needs_no_comps_but_sell_needs_three(self):
    ...

def test_ideation_waits_on_open_homework(self):
    ...  # homework H1 open -> next() == "with-user: game-research homework";
         # --no-user -> "stop: waiting for research homework"; status "skip" -> "with-user: game-ideation"

def test_malformed_research_files_are_reasons_not_crashes(self):
    ...  # references.json "[]" and homework.json {"items": "x"} -> reasons

def test_restart_rescans_then_returns_to_ideation(self):
    ...  # replaces test_restart_goes_back_to_ideation_and_archives_features_and_queue's first next():
         # "game-research restart docs/adr/0001-v.md"; after references.json scanned_for == adr and gate
         # passes -> advance -> "with-user: game-ideation restart docs/adr/0001-v.md"; dossiers untouched
```

  Write each `...` as a complete test with these exact reason strings. Update `test_setup_and_ideation_without_a_task_are_conversations` and every helper so the existing suite passes through research.

- [ ] **Step 2: Run them to see them fail.** Expected: FAIL.

- [ ] **Step 3: Implement**

  **Setup gate:** add `"state.intent must be one of ['sell', 'hobby']"` and `"research sources not checked (game-setup records research_sources)"`.

  **Advancing:**
  - setup → research sets `task="game-research"`;
  - research → ideation sets `task=f"game-ideation restart {adr}"` when `restart_adr` is set, else `"game-ideation"`;
  - `_restart` now sets `phase="research"` and `task=f"game-research restart {adr}"`; everything else is unchanged, and the dossiers stay.

  **`_check_research()`** reports shape problems as reasons:
  - references and homework that aren't objects or lists;
  - unknown `why`, `status`, `how_studied` values and roles;
  - duplicate ids;
  - more than MAX_HOMEWORK items;
  - an empty `items` list without a `reason`.

  It runs inside `check()` and validates each audit with `_review_shape`.

  **`_research_gate()`:**
  - intent minimums: `sell` needs at least MIN_COMPS refs with `why: comp`, and every active role in some aspect ref's `roles`; `hobby` needs only the latter;
  - every ref is `studied`, and for each of its roles has the dossier file plus a `how_studied` entry; `not-assessed` needs a `reason`;
  - at least MIN_SOURCES sources;
  - an image file (`.png`, `.jpg`, `.jpeg` or `.webp`) in the ref's directory for each IMAGE_ROLES role unless its how is `not-assessed`;
  - no audit note without a decision, or with a blocking note not `fixed`;
  - a wiki page with id `research`;
  - `homework.json` exists.

  `gate()` calls it in phase research.

  **`_research_action()`**, in this order:
  1. a restart task while `scanned_for != restart_adr` → that task;
  2. no refs → `"game-research"`;
  3. the first open ref → `f"game-research ref {id}"`;
  4. no `research` page or no `homework.json` → `"game-research brief"`;
  5. else `None`.

  In `_work`, phase research returns `_research_action()` or falls through to the gate and `advance`. It is never `with-user:`.

  **Ideation:** in `_work`, phase ideation with `homework_open()` returns `"with-user: game-research homework"`. With `no_user` it returns `"stop: waiting for research homework: a person answers or skips each open item in docs/game/research/homework.json (or the homework page), then run /game-next"`. Only after that does the existing ideation task logic run.

  **`write_missing_files`** does not create research files. The research skill does.

  **Homework lives only in `homework.json`.** The spec also mentions human-queue entries of kind `homework`; they're dropped. Ideation's start waits on the homework, not the awaiting-human phase, so a second copy in `human_queue` would only drift. Record this as a ruling in the ledger.

- [ ] **Step 4: Run the whole suite.** Expected: OK (`test_every_phase_has_a_skill` finds the stub; the mode words appear in the stub's table).

- [ ] **Step 5: Commit** `gamestate: a research phase before ideation, thorough by structure`

---

### Task 6: Calibration, A/B entries, the visual and feel targets, and version 7

**Files:**
- Modify: `skills/game-setup/scripts/gamestate.py` (queue checks, `_plan_gate`, `_work` verdict branch, `CURRENT_VERSION`, docstring)
- Test: `tests/test_gamestate.py`

**Interfaces:**
- Consumes: `LABELS` (Task 3), `active_roles()`.
- Produces:
  - **Constants:** `QUEUE_KINDS = ["playtest", "calibrate", "compare"]`, `TARGETS = ["visual", "feel"]`, `CURRENT_VERSION = 7`.
  - **Feature field:** optional `"target": "visual" | "feel"`.
  - **Queue entries:**
    - `calibrate`: `{"id", "what", "kind": "calibrate", "how": <kit path>, "answers": LABELS}`;
    - `compare`: `{"id", "what", "kind": "compare", "how": <kit path>, "answers": <path>, "unblocks": ["F0xx"]}`.

- [ ] **Step 1: Write the failing tests**

```python
def test_slice_plan_needs_a_visual_target_and_a_feel_target(self):
    ...  # plan without them -> "no must feature with target visual in milestone slice",
         # "no must feature with target feel in milestone core-loop"; roles_off art drops the first

def test_a_passing_visual_target_queues_calibration(self):
    ...  # F with target visual passes, no labels, no calibrate entry ->
         # "the visual target passes: queue a calibrate entry for a person (kind calibrate)"

def test_the_slice_verdict_waits_for_calibration(self):
    ...  # calibrate entry open, labels missing, scope slice -> next() starts
         # "stop: waiting for calibration: a person labels the kit"; labels written -> verdict proceeds

def test_queue_entries_of_known_kinds_are_complete(self):
    ...  # calibrate without answers, compare without unblocks -> reasons

def test_labels_file_shape_is_checked(self):
    ...  # LABELS as "[]" or {"labels": [{"ours": "yes"}]} -> "calibration labels: ..." reasons, not crashes

def test_upgrade_brings_a_version_6_game_at_setup_to_7(self):
    ...  # state version 6 at setup -> upgrade notes "version 6 -> 7"; intent None, research_sources None
```

  Fixture: `plan()` gains `target="feel"` on F1 and a feature `F5` ("slice", kind capture, roles `("art",)`, `target="visual"`). `feature()` takes `target=None` and omits the key when None.

- [ ] **Step 2: Run them to see them fail.** Expected: FAIL.

- [ ] **Step 3: Implement**

  **Queue checks:** in `check()`, an entry whose `kind` is `calibrate` needs `how` and `answers`; `compare` needs `how`, `answers` and non-empty `unblocks`.

  **Features:**
  - `_check_features` validates `target` in TARGETS when present.
  - It adds the calibration reason when a passing `target: visual` feature exists, LABELS is missing, and no `calibrate` entry is queued.

  **`_plan_gate`** (slice stage) adds the two target reasons: the visual one when `art` is active, the feel one when `feel` is active.

  **`_work`:** in phase verdict, scope slice, before the playtest wait, an open `calibrate` entry with no LABELS file returns `f"stop: waiting for calibration: a person labels the kit ({entry['how']}) into {LABELS}; then run /game-next"`. Calibrate entries are removed from the queue by `complete` once LABELS exists, the same way answered playtests are consumed.

  **Labels:** `check()` validates LABELS when it exists: an object whose `labels` is a list of objects, each with `capture`, a bool `ours` and a non-empty `why`.

  **Version 7:** set `CURRENT_VERSION = 7` and update the docstring's upgrade line.

- [ ] **Step 4: Run the whole suite.** Expected: OK.

- [ ] **Step 5: Commit** `gamestate: calibration and A/B entries, visual and feel targets, version 7`

---

### Task 7: measure.py

**Files:**
- Create: `skills/game-review/scripts/measure.py`
- Test: `tests/test_measure.py`
- Modify: `tests/test_skills.py` (`skill_dirs`, see Step 5)

**Interfaces:**
- Produces the CLI `python3 measure.py <command> ...`. Each command prints JSON to stdout and exits 0, or exits 2 with `measure: <reason>` on stderr for bad input:

| Command | Does | Prints |
|---|---|---|
| `palette PNG --hex "#rrggbb,..." [--tolerance 24]` | share of opaque pixels within `tolerance` (Euclidean RGB) of any listed colour | `{"match_share": float, "per_colour": {hex: float}, "off_palette_share": float}` |
| `values PNG` | luma histogram (Rec. 709), 10 bins | `{"bins": [10 floats], "midtone_share": float}` (bins 3–6) |
| `contrast PNG --a x,y,w,h --b x,y,w,h` | WCAG contrast ratio between the two regions' mean relative luminance | `{"ratio": float}` |
| `derive PNG --out DIR` | writes `grayscale.png`, `thumb.png` (longest side 160 px, box filter) and `cvd-protan.png`, `cvd-deutan.png`, `cvd-tritan.png` (Machado et al. 2009 severity-1.0 matrices on linear RGB) | `{"written": [paths]}` |
| `sheet PNG... --out PNG [--cols 4]` | a contact sheet of equal-size frames in row-major order | `{"written": path, "frames": n}` |

  It decodes PNGs with bit depth 8, colour types 0, 2, 3, 4 and 6, and no interlace. Anything else exits 2 with `measure: unsupported PNG (<detail>)`. Encoding writes 8-bit RGB or RGBA. Internally it uses `read_png(path) -> (width, height, rows)`, where `rows` is a list of lists of `(r, g, b, a)` tuples, and `write_png(path, width, height, rows)`.

- [ ] **Step 1: Write the failing tests** in `tests/test_measure.py`:
  - `test_palette_share_of_a_two_colour_image`: a 4×1 image with three `#112233` pixels and one `#ffffff` gives `match_share` 0.75 for `--hex "#112233"`.
  - `test_values_put_mid_grey_in_the_midtones`: an all-`#808080` image gives `midtone_share` 1.0.
  - `test_contrast_black_on_white_is_21`: `ratio` 21.0 ± 0.05.
  - `test_derive_writes_five_images_that_round_trip`: the output files decode, and the thumbnail's longest side is ≤ 160.
  - `test_sheet_tiles_frames`: four 2×2 frames with `--cols 2` give a 4×4 image whose top-right pixel is frame 2's.
  - `test_unsupported_png_exits_2`: a 16-bit PNG, and a text file named `.png`, both give exit 2 with `measure:`.

  The tests build PNGs with `measure.write_png`, imported from the script path the way `test_skills.load_tool` does. The 16-bit file is built by hand (signature plus an IHDR with bit depth 16).

- [ ] **Step 2: Run them to see them fail.**

  Run: `python3 -m unittest tests.test_measure`

  Expected: FAIL (file missing).

- [ ] **Step 3: Implement** with `zlib`, `struct`, `json`, `argparse` and `math`. PNG filter types 0–4 are unfiltered per scanline (Paeth as in the PNG spec).

- [ ] **Step 4: Run the whole suite.** Expected: OK.

- [ ] **Step 5: Commit** `game-review: measure.py turns captures into facts and derived images`

  The `game-review` folder has no SKILL.md yet. Add `skills/game-review/` to plugin.json only in Task 11, and keep `test_plugin_lists_exactly_the_skill_folders` green by having that test ignore folders without a SKILL.md. Change that test now:

  ```python
  def skill_dirs(): return sorted(p for p in SKILLS.iterdir() if (p / "SKILL.md").is_file())
  ```

---

### Task 8: Role-skill packaging rules, and the `creative` role

**Files:**
- Modify: `tests/test_skills.py`
- Create: `skills/game-role-creative/SKILL.md`, `questions.md`, `page-template.md`, `checklist.md`, `dossier.md`, `agents/openai.yaml`
- Create: `agents/creative.md`
- Modify: `.claude-plugin/plugin.json` (list the skill)

**Interfaces:**
- Produces:
  - **The role-skill layout** Tasks 9–10 copy:
    - SKILL.md modes: `north-star`, `research`, `challenge`, `review`; `creative` also has `decide` and `audit`;
    - reference files: `questions.md` (ideation and brainstorm questions), `page-template.md` (its living page), `checklist.md` (review: measured first, then judged, then person-only), `dossier.md` (research requirements per reference).
  - **The agent file format:**

```markdown
---
name: creative
description: Use only when game-review dispatches the creative director to review, challenge, research, audit or decide notes for a game made with the game-* skills.
model: opus
tools: Read, Glob, Grep, Write, Bash
disallowedTools: Edit, NotebookEdit, Agent
skills: game-role-creative
maxTurns: 40
---
<stance, 10-20 lines>
```

- [ ] **Step 1: Write the failing tests** in `tests/test_skills.py`:
  - `test_role_skills_can_be_preloaded`: for each `skills/game-role-*`:
    - frontmatter without `disable-model-invocation`;
    - a description starting `Use only when`;
    - the four reference files present;
    - a SKILL.md mentioning each mode word (`north-star`, `research`, `challenge`, `review`).
  - `test_other_skills_stay_user_invoked`: every non-role skill keeps `disable-model-invocation: true`. Split it out of the existing frontmatter test.
  - `test_every_role_has_one_agent`:
    - for each id in the tool's `ROLES`, `agents/<id>.md` exists;
    - its frontmatter `name` equals the id;
    - `skills` is `game-role-<id>`;
    - `disallowedTools` contains `Edit` and `Agent`;
    - `tools` doesn't contain `Edit`;
    - `model` is non-empty.

    Until Tasks 9–10, skip ids without a role skill folder via `subTest` plus `self.skipTest`. Task 10 removes the skip.

  Parse agent frontmatter with `^([A-Za-z-]+): (.*)$`, because `disallowedTools` and `maxTurns` have capitals that the existing skill parser's `[a-z-]+` drops. Confirm the `skills:` value format for a plugin's own skill against the Claude Code subagent docs. If preloading by name can't work, keep the field and rely on Task 11's fallback (the dispatch passes the skill's path).

- [ ] **Step 2: Run them to see them fail.** Expected: FAIL (no creative skill).

- [ ] **Step 3: Write the `creative` role.**

  **Sources:** the spec's role table and "game-review" sections, and the roles report sections "Creative and game direction" and "Studios that keep quality…".

  **The modes, each as a numbered step with a Done when:**
  - **north-star:**
    - ask the person for the genre default and the departure;
    - turn them into 2–5 identity invariants;
    - write `north_stars.creative` and `invariants`.
  - **research:** the hook, what's overdone, and where there's room, per reference.
  - **challenge:** at most five challenges, each tied to a pillar or invariant: "what would most games of this kind do here?".
  - **review:** cohesion against the invariants; whether a fresh capture reads as this game or its genre default.
  - **decide:**
    - for each advisory note, choose `fixed`, `feature`, `topic` or `wontfix` with a one-line reason, following the spec's rules;
    - output a decisions list for the main session.
  - **audit:** check a research dossier against each role's `dossier.md`, flagging claims without sources, generic lines and missing numbers or images. Findings are anchored to the dossier rules and are blocking.

  Every judgment cites its anchor. Write `agents/creative.md` with the stance from the spec ("a review that finds nothing on a first build has probably not looked"; "you see only artifacts, never the builder's reasoning"; skeptical; problems first; you never edit the game; write only your output file).

- [ ] **Step 4: Run the whole suite.** Expected: OK.

- [ ] **Step 5: Commit** `game-role-creative: the creative director's process and agent; packaging rules for roles`

---

### Task 9: The `design`, `feel` and `art` roles

**Files:**
- Create, for each of `design`, `feel` and `art`: `skills/game-role-<id>/` (SKILL.md, `questions.md`, `page-template.md`, `checklist.md`, `dossier.md`, `agents/openai.yaml`) and `agents/<id>.md`
- Modify: `.claude-plugin/plugin.json`

**Interfaces:**
- Consumes: the layout and agent format from Task 8.

- [ ] **Step 1:** Write each role from the spec's role table and the roles report's sections: "Design specialists", "Player experience" (feel) and "Art". The fixed points:
  - **design:**
    - `challenge` and `review` focus on dominant strategies, boring stretches and role clarity;
    - review runs only at verdicts (never on features), on bot traces;
    - its pages are the Mechanics, Systems and Content pages.
  - **feel:**
    - the page `feel` holds one feel sheet per core action: intent, references, timings in frames, feedback layers, scaling, tunables, acceptance;
    - measured: input-to-response frames, buffer windows, channels fired;
    - judged: strips beside reference clips;
    - calibrated by strips.
  - **art:**
    - the page `art-bible`: slogan, rule-pillars, hex colour-role table, value bands per layer, silhouette rules, UI visual language, motion and VFX rules, invariants;
    - north-star compares 2–3 directions;
    - measured: `measure.py` palette, values, contrast and derive;
    - judged: cohesion with the visual target, read order, placeholder or stock look;
    - calibrated by stills.

  Models: `opus` for design and art, `sonnet` for feel.

- [ ] **Step 2: Run the whole suite.** Expected: OK, with the agent test skipping only roles without a skill.

- [ ] **Step 3: Commit** `game-role-design, -feel, -art: processes and agents`

---

### Task 10: The `audio`, `narrative` and `ux` roles

**Files:**
- The same layout for `audio`, `narrative` and `ux`; `.claude-plugin/plugin.json`
- `tests/test_skills.py` (remove the skip in `test_every_role_has_one_agent`)

- [ ] **Step 1:** Write each from the role table and the roles report's sections: "Audio", "Narrative and world" and "Player experience" (ux). The fixed points:
  - **audio:**
    - the page `audio`: pillars, palette per category, signature sounds, priority tiers, music scheme, UI sound family, loudness target;
    - review is measured only (event coverage, variation counts, back-to-back repeats, loudness where the adapter measures it), and every review states "unheard";
    - taste belongs to the person.
  - **narrative:**
    - the page `tone-and-world`: fantasy line, setting sentence, tone words and anti-words, character cards, naming rules, glossary, UI voice;
    - the minimum kit for story-light games;
    - judges text against the page's rules.
  - **ux:**
    - the pages `screens` and `onboarding`: flow map, HUD information hierarchy, input map, FTUE plan, accessibility minimum;
    - measured: launch-to-control time, text size, overlaps and contrast ratios via `measure.py contrast`;
    - judged with usability heuristics;
    - calibrated by stills.

  Model `sonnet` for all three.

- [ ] **Step 2: Run the whole suite.** Expected: OK, with no skips.

- [ ] **Step 3: Commit** `game-role-audio, -narrative, -ux: processes and agents`

---

### Task 11: The `game-review` skill

**Files:**
- Create: `skills/game-review/SKILL.md`, `skills/game-review/agents/openai.yaml`
- Modify: `.claude-plugin/plugin.json`

**Interfaces:**
- Consumes:
  - the agents `game-director:<role>` (Tasks 8–10);
  - `measure.py` (Task 7);
  - the review JSON shape and decision grammar (Task 2);
  - `review_result` (Task 3).
- Produces the task forms other skills call: `game-review feature <id>`, `game-review topic <id>`, `game-review <scope>`, `game-review polish <id>`.

- [ ] **Step 1: Write SKILL.md** from the spec's "game-review: how a review runs" section. The numbered steps, each ending in a Done when:
  1. **Choose the roles.**
  2. **Prepare the inputs once:**
     - captures and strips from one build at one commit, under `docs/game/reviews/<target>/inputs/`;
     - the `measure.py` outputs;
     - the event log and bot metrics;
     - the anchors: the role's page, north stars, invariants, references, `LABELS`, and `docs/game/roles/<role>.md`.
  3. **Dispatch the role agents in parallel**, each with its input paths and its output path. The topic mode passes the topic, vision and pages instead, and gets challenges back as text.
  4. **Check independence:** `git status` shows only review files; anything else is discarded with `git checkout`/`git clean` on those paths and noted.
  5. **One extra capture round** when a reviewer asked for one.
  6. **Decide:** a `creative` agent in `decide` mode, only when advisory notes exist. In interactive mode, the person decides the notes a verdict review raises. The main session carries out the decisions and records `fixed <commit>` / `feature F..` / `topic T..` / `wontfix: ..`. The builder never decides on its own work.
  7. **Record and commit:** the reviews, the feature's `reviews` map, and the role memory files (overruled notes, A/B picks, label reasons).

  Also cover:
  - the no-subagent fallback: run roles one at a time, `"independent": false`;
  - the two-round cap for features;
  - the agent dispatch fallback when skill preloading by name fails: pass the role skill's absolute path from this skill's base directory.

- [ ] **Step 2: Run the whole suite.** Expected: OK.

- [ ] **Step 3: Commit** `game-review: run a review with the relevant roles in parallel`

---

### Task 12: The `game-research` skill and setup's research questions

**Files:**
- Modify: `skills/game-research/SKILL.md` (replace the Task 5 stub), plus a reference file `skills/game-research/sources.md`
- Modify: `skills/game-setup/SKILL.md` (project mode: ask `intent`; check research sources; warn when the repo is public)

**Interfaces:**
- Consumes:
  - the research files and `_research_action` steps (Task 5);
  - each role's `dossier.md` and `research` mode;
  - the creative `audit` mode;
  - `game-review` for dispatch mechanics.

- [ ] **Step 1: Write `game-research`** from the spec's "Research phase" section and `docs/research/2026-11-23-game-market-research.md`.

  **Modes:**
  - **`game-research` (scan):** comps with dated, sourced ranges by launch year (sell only; never from memory), anchors, the player profile (Quantic Foundry motivations and SDT/PENS), and the reference list.
  - **`ref <id>`:**
    - gather material once: store page, screenshots, reviews in all languages with negative ones first, wikis and guides;
    - play browser-playable games with Playwright and capture them;
    - downscale images to at most 1280 px;
    - dispatch the ref's roles in parallel in `research` mode;
    - run the creative `audit` with at most two fix rounds; what remains becomes homework candidates;
    - record `how_studied`.
  - **`brief`:**
    - the `research` page, written last as for every page;
    - `homework.json` with at most ten items ranked by impact, each with what, why, questions, minutes and roles;
    - homework published as a docs page and `ready-for-human` tickets;
    - `complete`.
  - **`homework`** (with a person):
    - go through the open items and record answers or skips;
    - fold answers into the dossiers (`played` by the person) and the brief;
    - after ideation, an answer that contradicts a decided north star or page becomes a topic.
  - **`restart <adr>`:** re-scan comps and references in light of the ADR, keeping studied dossiers, and set `scanned_for`.

  **`sources.md`** covers:
  - the Steam `GetAppReviews` API (all languages) and the store `appdetails` endpoint (about 200 requests per 5 minutes);
  - SteamSpy estimates, whose outliers run up to fivefold;
  - itch.io browse pages through their `.xml` RSS;
  - SteamDB, which must not be scraped;
  - the review-count multipliers by year from the market note.

- [ ] **Step 2: Update game-setup's project mode**:
  - one question: `sell` or `hobby` → `state.json` `intent`;
  - a research-sources check: try each source in `sources.md` and record `research_sources: {"checked": date, "reachable": [...], "unreachable": [...]}`; unreachable ones become homework in research;
  - when the repo is public, say that reference images will be committed and offer to keep them in the docs place instead.

- [ ] **Step 3: Run the whole suite.** Expected: OK.

- [ ] **Step 4: Commit** `game-research: scan, one reference per session, brief and homework; setup asks intent`

---

### Task 13: The shared reference, the adapter contract, and ideation, brainstorm and consolidate

**Files:**
- Modify:
  - `skills/game-setup/game.md`;
  - `skills/game-setup/adapter-contract.md`;
  - `skills/game-ideation/SKILL.md`, `vision-template.md`, `topic-map.md`, `slice-template.md`;
  - `skills/game-brainstorm/SKILL.md`;
  - `skills/game-consolidate/SKILL.md`, `fun-proxies.md`.

**Interfaces:**
- Consumes every schema from Tasks 1–6 and the skills from Tasks 8–12.

- [ ] **Step 1: `game.md`.** It now documents:
  - the roles and the area-to-roles default table, verbatim from the spec, including "features get roles only when visible; design is never a feature reviewer";
  - the `roles`, `reviews` and `target` fields;
  - the review JSON and its decision grammar;
  - review items, with their scoring and calibration;
  - queue kinds `calibrate` and `compare`;
  - the `vision.json` additions;
  - the research files;
  - role memory `docs/game/roles/<role>.md`;
  - `intent` and `research_sources`;
  - the research phase in the phase list.

  Keep its schema in step with `gamestate.py`.

- [ ] **Step 2: `adapter-contract.md`:**
  - `capture --state NAME` and `capture --strip INPUT --frames N --every K`;
  - the event log from `sim`, `replay` and `bot`: per action, input-to-response frames and the feedback channels fired;
  - smoke-test rows for each;
  - `n/a` rules.

- [ ] **Step 3: game-ideation:**
  - open by going through the research brief and homework answers; the person picks the comps that count as "us", the anchors to break, the hook and the references;
  - a new step "Set the roles' north stars" between the vision and the slice, using each role skill's `north-star` mode in the main session; art compares 2–3 directions; creative goes last and writes the invariants;
  - the slice quality-bar recommendation from the spec;
  - seed a slice topic per role page (topic-map), with `roles` on every topic;
  - the vision template gains "Direction per role".

- [ ] **Step 4: game-brainstorm.** Step 1 runs `game-review topic <id>` before asking anything, then attributes challenges to roles in the conversation. Follow-up topics get `roles`.

- [ ] **Step 5: game-consolidate:**
  - cross-role consistency:
    - colour roles match UI, VFX and faction palettes;
    - no information is carried by colour alone;
    - every player-critical sound has a visual cue;
    - the tone touchstones;
    - pillar wording is identical everywhere;
  - review items: slice items for creative, art and feel; full items per active role; the `taste` flag;
  - the cap rule;
  - gap topics get `roles`.

- [ ] **Step 6: Run the whole suite.** Expected: OK.

- [ ] **Step 7: Commit** `skills: roles in the shared reference, captures in the adapter, roles in ideation, brainstorm and consolidate`

---

### Task 14: Plan, build, verdict, polish, gdd and next

**Files:**
- Modify:
  - `skills/game-plan/SKILL.md`, `tech-decisions.md`;
  - `skills/game-build/SKILL.md`;
  - `skills/game-verdict/SKILL.md`, `playtesting.md`;
  - `skills/game-polish/SKILL.md`, `polish-checklist.md`;
  - `skills/game-gdd/SKILL.md`, `gdd-structure.md`;
  - `skills/game-next/SKILL.md`, `unattended.md`.

- [ ] **Step 1: game-plan:**
  - the capture protocol (named states and strips, recorded in `engine-notes.md`);
  - the walking skeleton covers capture and the event log;
  - the slice's first features: `target: visual` in slice and `target: feel` in core-loop;
  - `roles` on visible features;
  - measured checks in acceptance at the milestone's quality bar (none for `placeholder`).

- [ ] **Step 2: game-build:** after Verify, for a feature with `roles`:
  - capture;
  - run `game-review feature <id>`;
  - blocking notes are fixed, within two rounds;
  - record the reviews before `passes`;
  - when the visual target passes, queue the calibrate kit: 8–12 captures, the person's references, and 2–3 "not our game" examples (the engine's default scene, a stock-asset scene, a capture with the palette broken on purpose); for feel, strips beside reference clips;
  - calibration repeats when an adjust or restart changes `north_stars.art`. The new kit goes in a fresh queue entry, and `labels.json` is replaced.

- [ ] **Step 3: game-verdict.** Step 3 becomes `game-review <scope>` over the whole build. Review items are scored from the review files (the tool recomputes them), and the ADR lists every role's notes and decisions. The slice waits for calibration as well as the playtest.

- [ ] **Step 4: game-polish:**
  - role-owned checklist sections;
  - each polish feature names its role and is reviewed by `game-review polish <id>` plus creative against the invariants;
  - taste features use verify `human` with a `compare` entry, and picks go to `keep.json` and role memory.

- [ ] **Step 5: game-gdd:**
  - a "Research" page from the brief and homework;
  - a "Direction" page from the north stars, invariants and references;
  - the Status page shows review decisions.

- [ ] **Step 6: game-next.** Its phase list and unattended notes name `research` (which runs unattended) and the new stops: research homework and calibration.

- [ ] **Step 7: Run the whole suite.** Expected: OK.

- [ ] **Step 8: Commit** `skills: captures, reviews, calibration and role passes through plan, build, verdict and polish`

---

### Task 15: Release 0.7.0

**Files:**
- Modify: `README.md` (phases with research; roles; review flow; the person's moments; required research hosts; Known limits: audio unheard, taste provisional until calibration, agents are Claude Code-only)
- Modify: `.claude-plugin/plugin.json` (`"version": "0.7.0"`; description mentions roles and research; keywords add `roles`, `reviews`, `research`)

- [ ] **Step 1:** Update both files.
- [ ] **Step 2:** Run `python3 -m unittest discover tests`. Expected: OK.
- [ ] **Step 3: Commit** `Release 0.7.0: role reviews and a research phase`

  The release PR (`design/role-reviews` → `main`) is opened by the controller after the final review. The user merges it.
