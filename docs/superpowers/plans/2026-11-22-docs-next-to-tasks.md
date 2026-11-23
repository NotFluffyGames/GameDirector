# Docs Next to the Tasks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the agent-facing wiki next to the tasks beside the GDD, make setup choose and verify that tasks home with the user, and add a versioned upgrade, so EveLikeBrawl can move from its 0.3.0 setup.

**Architecture:** `gamestate.py` stops reading wiki pages as files. It checks two small JSON files in the home repo instead: `docs/game/wiki.json` (the index of pages that live in the docs place) and `docs/game/vision.json` (the vision facts the gates need). Pages themselves live wherever `docs/agents/docs.md` says, written only by sessions through the tracker's connector. Setup becomes a `with-user:` step gated on a recorded docs smoke test, and `gamestate.py upgrade` brings an older game's state files up to the current schema.

**Tech Stack:** Python 3.8+ standard library (`gamestate.py`, `unittest`), markdown skills (Agent Skills format), git.

**Spec:** `docs/superpowers/specs/2026-11-22-multi-repo-design.md`, sections "Docs next to the tasks", "Setup and upgrade" and decisions 3, 8 and 11. This is **plan 1 of 4**. Later plans cover: 2, components, cross-repo checks, session copies, push and pull-request integration, and the CI check; 3, parallel sessions; 4, the stack.

## Global Constraints

- `gamestate.py`: Python 3.8+, standard library only; it never calls a tracker or docs tool API.
- A single-repo game with one person pays nothing extra beyond choosing and verifying its tasks home in setup.
- Every SKILL.md step ends on a `**Done when**` line; `python3 -m unittest discover tests` stays green after every task.
- Wiki pages: current truth only; people comment, sessions edit; a session writes pages only after `check` passes and its state is committed.
- Local files are used for docs only when the user explicitly chooses them; the pages then live under `docs/game/wiki/` and are indexed the same way.
- State schema version after this plan: `6`.

## Review Focus

- **A page edited, but its index entry never committed** (the session died between writing the page and committing `wiki.json`): game-gdd must treat it like a direct edit (flag plus topic), not ignore it. *Owned by Task 8; it's skill behaviour, with no tool test.*
- **Running `upgrade` twice, or on a game already at version 6:** a no-op that says so. *Test in Task 5.*
- **An old state file with no `version` key, or a game mid-run on an older version:** upgrade refuses, naming the phase and version, instead of half-migrating. *Test in Task 5.*
- **Duplicate page ids, an area that isn't one of the nine, or a local link that doesn't exist:** check reports each one. *Tests in Task 1.*
- **`--no-user` at setup:** an unattended loop must stop, not run setup. *Test in Task 4.*

---

### Task 1: Index the wiki in `wiki.json` and the vision in `vision.json`

**Files:**
- Modify: `skills/game-setup/scripts/gamestate.py` (constants; `Game.__init__`; `pillars`; `_check_features`; `_check_topics`; new `_check_wiki`; `init`)
- Modify: `tests/test_gamestate.py` (fixtures and helpers move from wiki files to the two JSON files)

**Interfaces:**
- Produces:
  - `AREAS = ["Vision", "Mechanics", "Controls", "Systems", "Content", "Modes and sessions", "Screens and onboarding", "Feel", "Tone, art and world"]`
  - `SLICE_AREAS = [a for a in AREAS if a != "Modes and sessions"]`
  - `REQUIRED_PAGES = ["vision", "slice", "concepts"]` (all in area `"Vision"`)
  - `Game.wiki_index_path` (`docs/game/wiki.json`, default `{"pages": []}`) and `Game.vision_path` (`docs/game/vision.json`, default `{}`)
  - `Game.wiki_pages() -> list`, `Game.page_ids() -> set`, `Game.vision() -> dict`
  - `Game.pillars() -> list | None`: the `id`s in `vision.json` `pillars`; `None` when `vision.json` has no `pillars` key
  - Page entry: `{"id", "title", "area", "link", "version", "updated", "flagged"}`. `flagged` is optional: `{"topic": "T0xx", "note": "..."}`
  - Topic and feature `pages` hold page **ids**, not paths
- Removes: `VISION_HEADINGS`, `SLICE_HEADINGS`, `CONCEPT_HEADINGS`, `INDEX_SECTIONS`, `SLICE_INDEX_SECTIONS`, `sections()`, and `Game.wiki`. The gates that used them change in Task 2. Until then those gates may read `vision.json` and `wiki.json` minimally, enough to keep the suite green.

- [ ] **Step 1: Write the failing tests**

Replace the wiki-file fixtures with JSON ones:
- `VISION_JSON`: pillars P1–P3, one anti-pillar, a kill condition, a slice block, directions (the Task 2 schema);
- `wiki_index(*areas)`: page entries for the given areas with these ids: `vision`, `slice` and `concepts` (Vision), `mechanics`, `controls`, `weapons` (Systems), `content`, `modes`, `screens`, `feel`, `art`. Each has `link: "https://docs.example/<id>"`, `version: "1"` and `updated: "x"`. Ideation writes the Vision pages; consolidate's fixture adds the rest (`SLICE_AREAS` for the slice stage).

 Change `feature()` to `pages=["mechanics"]`, and `resolve()` to `pages=["mechanics"]`. Add:

```python
def test_wiki_index_rejects_duplicates_unknown_areas_and_missing_local_links(self):
    self.to_ideation()
    self.edit("wiki.json", lambda d: d["pages"].extend([
        {"id": "dup", "title": "A", "area": "Mechanics", "link": "https://docs.example/a", "version": "1", "updated": "x"},
        {"id": "dup", "title": "B", "area": "Mechanics", "link": "https://docs.example/b", "version": "1", "updated": "x"},
        {"id": "odd", "title": "C", "area": "Lore", "link": "https://docs.example/c", "version": "1", "updated": "x"},
        {"id": "gone", "title": "D", "area": "Feel", "link": "docs/game/wiki/gone.md", "version": "1", "updated": "x"}]))
    out = self.tool("check", ok=False)
    for expected in ("page dup: duplicate id", "page odd: area 'Lore' is not one of", "page gone: local link 'docs/game/wiki/gone.md' does not exist"):
        self.assertIn(expected, out)

def test_flagged_pages_need_an_open_topic(self):
    self.to_ideation()
    self.ideate()
    self.edit("wiki.json", lambda d: d["pages"][0].update(flagged={"topic": "T99", "note": "edited outside a session"}))
    self.assertIn("page vision: flagged for topic T99, which is not open", self.tool("check", ok=False))

def test_topics_and_features_refer_to_page_ids(self):
    self.to_plan()
    self.plan()
    self.edit("features.json", lambda d: d["features"][0].update(pages=["nope"]))
    self.assertIn("F1: page 'nope' is not in wiki.json", self.tool("check", ok=False))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests.test_gamestate -v 2>&1 | tail -20`
Expected: the three new tests FAIL. Others may fail until Step 3 too.

- [ ] **Step 3: Implement the index and vision model in `gamestate.py`**

`init` creates `wiki.json` and `vision.json`. `_check_wiki()` reports:
- `page <id>: duplicate id`;
- `page <id>: area '<a>' is not one of <AREAS>`;
- `page <id>: local link '<link>' does not exist`, for a link without a `scheme://` prefix, resolved from the repo root;
- `page <id>: flagged for topic <T>, which is not open`.

Feature and topic page checks report `<id>: page '<p>' is not in wiki.json`. `pillars()` reads `vision.json`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest discover tests 2>&1 | tail -3`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add skills/game-setup/scripts/gamestate.py tests/test_gamestate.py
git commit -m "gamestate: index wiki pages in wiki.json and vision facts in vision.json"
```

### Task 2: Gates read the JSON, not the pages

**Files:**
- Modify: `skills/game-setup/scripts/gamestate.py` (`_ideation_gate`, `_consolidate_gate`, new constants)
- Modify: `tests/test_gamestate.py` (gate tests and the `Templates` test)

**Interfaces:**
- Consumes: `AREAS`, `SLICE_AREAS`, `REQUIRED_PAGES`, `Game.vision()`, `Game.wiki_pages()` (Task 1)
- Produces:
  - `QUALITY_ASPECTS = ["code", "feel", "art", "audio", "ui", "onboarding"]`
  - `QUALITY_BARS = ["placeholder", "representative", "production", "final"]`
  - The `vision.json` schema the gates enforce:

```json
{"pillars": [{"id": "P1", "statement": "..."}], "anti_pillars": ["We will not ... because ..."],
 "kill_condition": "...",
 "slice": {"test_question": "...", "quality_bar": {"code": "production", "feel": "representative", "art": "representative",
           "audio": "representative", "ui": "representative", "onboarding": "representative"}},
 "directions": {"count": 4, "choice": "C2"}}
```

- [ ] **Step 1: Write the failing tests**

```python
def test_ideation_gate_reads_vision_json_and_required_pages(self):
    self.to_ideation()
    self.edit("vision.json", lambda d: d.update(pillars=[{"id": "P1", "statement": "x"}], anti_pillars=[],
                                                 kill_condition="", directions={"count": 2, "choice": ""},
                                                 slice={"test_question": "", "quality_bar": {"art": "shiny"}}))
    out = self.tool("gate", ok=False)
    for expected in ("vision.json has 1 pillars; needs 3-4", "vision.json has no anti-pillar",
                     "vision.json has no kill condition", "vision.json directions: 2 compared; needs 3-5",
                     "vision.json directions: no choice", "vision.json slice: no test question",
                     "vision.json slice quality bar: art is 'shiny'", "vision.json slice quality bar: code missing",
                     "wiki.json has no page 'slice'"):
        self.assertIn(expected, out)

def test_consolidate_gate_needs_a_page_per_area_for_the_stage(self):
    # reach the consolidate phase with the same steps as test_slice_consolidate_needs_a_human_item...,
    # then write wiki.json from wiki_index(*SLICE_AREAS) minus the 'feel' page
    self.assertIn("wiki.json has no page in area 'Feel'", self.tool("gate", ok=False))
```

Change the `Templates` test so it checks that `game-ideation/index-template.md` has a `## <area>` line for every area in `AREAS`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests.test_gamestate -v 2>&1 | grep -E "FAIL|ERROR" | head`
Expected: the two new gate tests FAIL.

- [ ] **Step 3: Rewrite `_ideation_gate` and `_consolidate_gate` against the JSON**

The reasons are exactly the strings in the tests. The topic seeding checks stay as they are. `_consolidate_gate` uses `SLICE_AREAS` in the slice stage and `AREAS` in production, and keeps its fun-checklist and richness rules.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest discover tests 2>&1 | tail -3`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add skills/game-setup/scripts/gamestate.py tests/test_gamestate.py
git commit -m "gamestate: ideation and consolidate gates read vision.json and wiki.json"
```

### Task 3: GDD staleness follows the index

**Files:**
- Modify: `skills/game-setup/scripts/gamestate.py` (`gdd_stale`)
- Modify: `tests/test_gamestate.py`

**Interfaces:**
- Produces: `Game.gdd_stale() -> bool`. It is False while `wiki.json` has no pages. Otherwise it is True when there is no `gdd_synced`, or when `git diff --name-only <gdd_synced> HEAD -- docs/game/wiki.json docs/game/own-calls.md` is non-empty.

- [ ] **Step 1: Write the failing test**

```python
def test_gdd_goes_stale_when_a_page_entry_or_own_call_changes(self):
    self.to_plan()
    self.plan()
    self.edit("wiki.json", lambda d: d["pages"][1].update(version="2", updated="dash cooldown added"))
    self.set_passes("F1", "F2")          # commits
    self.sync()                          # next must be game-gdd before the milestone moves on
    self.tool("advance")
    self.assertEqual(self.next(), "game-verdict core-loop")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest tests.test_gamestate.GameRun.test_gdd_goes_stale_when_a_page_entry_or_own_call_changes -v`
Expected: FAIL (next is `advance`, not `game-gdd`)

- [ ] **Step 3: Change `gdd_stale` to diff the two files**

- [ ] **Step 4: Run the suite**

Run: `python3 -m unittest discover tests 2>&1 | tail -3`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add skills/game-setup/scripts/gamestate.py tests/test_gamestate.py
git commit -m "gamestate: GDD staleness follows wiki.json and own-calls.md"
```

### Task 4: Setup is a conversation, gated on a verified docs place

**Files:**
- Modify: `skills/game-setup/scripts/gamestate.py` (`DEFAULT_STATE`, the setup gate, `_work`)
- Modify: `tests/test_gamestate.py` (`to_ideation` records the verification)

**Interfaces:**
- Produces:
  - `state.json` gains `"docs_verified": null`. Setup sets it to `{"place": "<where the docs live>", "date": "<YYYY-MM-DD>"}`.
  - The setup gate reasons: `docs/agents/game.md is missing`; `docs/agents/docs.md is missing`; `docs not verified: run the docs smoke test (game-setup)`.
  - `next:` for a game-setup task is `with-user: game-setup` (or `with-user: game-setup upgrade`). Under `--no-user` it's a `stop: waiting for a person` line.

- [ ] **Step 1: Write the failing tests**

```python
def test_setup_waits_for_a_verified_docs_place(self):
    self.tool("init")
    (self.root / "docs" / "agents" / "game.md").write_text("# Game workflow\n")
    (self.root / "docs" / "agents" / "docs.md").write_text("# Docs\n")
    self.commit()
    self.assertEqual(self.next(), "with-user: game-setup")
    self.assertIn("docs not verified", self.tool("complete", ok=False))
    self.assertIn("stop: waiting for a person", self.next("--no-user"))
    self.edit("state.json", lambda s: s.update(docs_verified={"place": "ClickUp doc", "date": "2026-11-22"}))
    self.commit()
    self.tool("complete")
```

Update `to_ideation()` to write `docs.md` and `docs_verified` before `complete`, and to expect `with-user: game-setup`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests.test_gamestate.GameRun.test_setup_waits_for_a_verified_docs_place -v`
Expected: FAIL

- [ ] **Step 3: Implement**

`_work` treats a task starting with `game-setup` or `game-ideation` as `with-user:`. The setup gate checks both config files and that `docs_verified` has non-empty `place` and `date`.

- [ ] **Step 4: Run the suite**

Run: `python3 -m unittest discover tests 2>&1 | tail -3`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add skills/game-setup/scripts/gamestate.py tests/test_gamestate.py
git commit -m "gamestate: setup is a with-user step gated on a verified docs place"
```

### Task 5: Versioned upgrade

**Files:**
- Modify: `skills/game-setup/scripts/gamestate.py` (`CURRENT_VERSION`, `MIGRATIONS`, `Game.upgrade`, the `upgrade` command, docstring)
- Modify: `tests/test_gamestate.py`

**Interfaces:**
- Produces:
  - `CURRENT_VERSION = 6` (also `DEFAULT_STATE["version"]`)
  - `MIGRATIONS: dict` mapping `from_version` to a `migrate(game) -> list[str]` that brings state to `from_version + 1`. It's empty in this plan; later releases add entries.
  - `Game.upgrade() -> list[str]`, with these rules:
    - **at `CURRENT_VERSION`:** returns `["already at version 6"]`;
    - **phase `setup`, any older version** (a missing `version` counts as 1): rebuilds `state.json` from `DEFAULT_STATE`. It keeps `limits`, `counters` and `human_queue`, sets `task` to `"game-setup upgrade"`, writes missing state files (as `init` does), and returns notes. The first note is `version <old> -> 6`, followed by one line per file created;
    - **any other phase, older version:** applies `MIGRATIONS[v]` for `v` from the game's version up to `CURRENT_VERSION - 1`. If one is missing it raises, and the command exits 1 with `upgrade from version <v> in phase <phase> isn't supported: <reason>`.
  - Command `gamestate.py upgrade`: runs it, saves and commits `state.json` (and new files), and prints the notes and `next:`.

- [ ] **Step 1: Write the failing tests**

```python
def test_upgrade_resets_an_old_game_still_at_setup(self):
    self.tool("init")
    self.edit("state.json", lambda s: (s.pop("stage"), s.update(version=3, phase="setup", task=None)))
    (self.game / "vision.json").unlink()
    self.commit()
    out = self.tool("upgrade")
    self.assertIn("version 3 -> 6", out)
    s = self.load("state.json")
    self.assertEqual((s["version"], s["phase"], s["task"], s["stage"]), (6, "setup", "game-setup upgrade", "slice"))
    self.assertTrue((self.game / "vision.json").exists())
    self.assertEqual(self.next(), "with-user: game-setup upgrade")
    self.assertIn("already at version 6", self.tool("upgrade"))

def test_upgrade_refuses_an_old_game_mid_run(self):
    self.to_plan()
    self.edit("state.json", lambda s: s.update(version=4))
    self.commit()
    self.assertIn("upgrade from version 4 in phase plan isn't supported", self.tool("upgrade", ok=False))

def test_upgrade_treats_a_missing_version_as_1(self):
    self.tool("init")
    self.edit("state.json", lambda s: s.pop("version"))
    self.commit()
    self.assertIn("version 1 -> 6", self.tool("upgrade"))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests.test_gamestate -v 2>&1 | grep upgrade`
Expected: three FAIL (unknown command)

- [ ] **Step 3: Implement `CURRENT_VERSION`, `MIGRATIONS`, `Game.upgrade` and the command**

`_load` must keep the file's own `version` rather than the default's. Read the raw JSON's `version`, or 1 when absent, before merging.

- [ ] **Step 4: Run the suite**

Run: `python3 -m unittest discover tests 2>&1 | tail -3`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add skills/game-setup/scripts/gamestate.py tests/test_gamestate.py
git commit -m "gamestate: versioned upgrade, resetting old games still at setup"
```

### Task 6: The shared config describes docs next to the tasks

**Files:**
- Modify: `skills/game-setup/game.md` (sections "The wiki", "The GDD", "Files", "Vocabulary", "Autonomy")
- Rename: `skills/game-setup/human-docs.md` → `skills/game-setup/docs.md` (and rewrite it)
- Test: `tests/test_skills.py` (existing link and command checks cover the rename)

**Interfaces:**
- Produces: the `docs.md` template sections that Task 7's setup fills: `## Tasks home`, `## Docs place`, `## How to read, write and comment`, `## Smoke test` (a table with the steps create, read, edit, comment, read comments, link from a task, delete, protect pages; result; date), `## Wiki pages` and `## GDD pages` (tables of id or link).

- [ ] **Step 1: Rewrite the game.md sections.** Cover:
  - where the wiki lives: the docs place in `docs/agents/docs.md`, indexed by `docs/game/wiki.json`, with the page entry schema from Task 1;
  - `docs/game/vision.json` and its schema from Task 2;
  - comments only: people comment, sessions edit; direct edits are detected and flagged;
  - pages written last, and the connector stop: `stop: <tracker> docs unreachable`;
  - local files only by the user's choice;
  - setup is always `with-user:`;
  - the Files table, adding `wiki.json`, `vision.json` and `docs.md`, and removing `docs/game/wiki/` as the default.

  Leave the Commands, Limits and Companion skills sections unchanged.
- [ ] **Step 2: Rename and rewrite `human-docs.md` as `docs.md`** with the sections listed under Interfaces.
- [ ] **Step 3: Update every reference** (`grep -rn "human-docs" skills README.md`) to `docs.md`.
- [ ] **Step 4: Run the suite**

Run: `python3 -m unittest discover tests 2>&1 | tail -3`
Expected: `OK`. `test_relative_links_resolve` catches any missed rename.

- [ ] **Step 5: Commit**

```bash
git add -A skills/game-setup README.md
git commit -m "game.md: the wiki and GDD live next to the tasks; docs.md replaces human-docs.md"
```

### Task 7: game-setup chooses, verifies and upgrades

**Files:**
- Modify: `skills/game-setup/SKILL.md` (project mode rewritten; new upgrade mode)
- Test: `tests/test_skills.py` (the step-and-mode check requires `upgrade` in this SKILL.md; every step needs **Done when**)

**Interfaces:**
- Consumes:
  - `docs_verified` and the task `game-setup upgrade` (Tasks 4–5);
  - `wiki.json` and `vision.json` (Tasks 1–2);
  - the `docs.md` template (Task 6).

- [ ] **Step 1: Rewrite project mode as numbered steps, each ending on Done when:**
  1. **explore:** today's step, plus the tracker's existing spaces, lists and projects;
  2. **the tasks home:** the user picks one, or setup creates one with their go-ahead;
  3. **the docs smoke test:** the steps in the `docs.md` Smoke test table, results recorded, with page protection set where supported. If the tracker can't host docs, the user picks a docs tool beside it, which gets the same test;
  4. **skeletons:** the wiki home page from `index-template.md`, an empty GDD with the pages from `gdd-structure.md`, ids recorded in `wiki.json` and `docs.md`;
  5. **write:** today's step 3, plus `docs_verified` set as `{place, date}`;
  6. **close:** `complete`.

  Open with "Setup is always a conversation with the user."
- [ ] **Step 2: Add upgrade mode** (task `game-setup upgrade`):
  1. copy the current `scripts/gamestate.py` over `docs/game/gamestate.py` and run `gamestate.py upgrade`;
  2. refresh the sections of `docs/agents/game.md` the skills own (all but the autonomy mode and the Commands table), and rename `human-docs.md` to `docs.md`;
  3. when `docs_verified` is unset, run project steps 2–4 with the user;
  4. `complete`.
- [ ] **Step 3: Run the suite**

Run: `python3 -m unittest discover tests 2>&1 | tail -3`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add skills/game-setup/SKILL.md
git commit -m "game-setup: choose and verify the tasks home with the user; upgrade mode"
```

### Task 8: Phase skills use the docs place

**Files:**
- Modify the SKILL.md of game-next, game-ideation, game-brainstorm, game-consolidate, game-plan, game-build, game-verdict and game-gdd.
- Modify: `skills/game-ideation/index-template.md`, `vision-template.md`, `slice-template.md` and `concepts-template.md` (page templates in the docs place); `skills/game-gdd/gdd-structure.md`.
- Test: `tests/test_skills.py`

**Interfaces:**
- Consumes:
  - `wiki.json` page entries and `vision.json` (Tasks 1–2);
  - `docs.md` (Task 6);
  - the connector stop wording `stop: <tracker> docs unreachable` (Task 6).

- [ ] **Step 1: game-next.** Before any step except setup and `fix:`, read the wiki home page through the connector. If that fails, report `stop: <tracker> docs unreachable` and end the session.
- [ ] **Step 2: game-ideation.**
  - Write the vision, slice and directions pages in the docs place from the templates.
  - Write `vision.json` to match them.
  - Write `wiki.json` entries with ids `vision`, `slice` and `concepts`.
  - Topic `pages` are ids.
- [ ] **Step 3: game-brainstorm and game-consolidate.**
  - Pages are written in the docs place, last, after `check --since <base>` passes and the state commit is made.
  - Each page written updates its `wiki.json` entry (`version` from the docs tool, `updated`).
  - Consolidate's completeness walk reads areas from `wiki.json`.
  - A change to the vision or slice also updates `vision.json`.
- [ ] **Step 4: game-plan, game-build and game-verdict.**
  - `pages` are ids.
  - A page fix is written last and updates its `wiki.json` entry.
  - Verdict's wiki check reads pages through the connector.
- [ ] **Step 5: game-gdd.**
  - Both layers are in the same docs place.
  - Staleness comes from `wiki.json` and `own-calls.md`.
  - **Direct-edit detection:** compare each page's version in the docs tool with `wiki.json`. A mismatch (including a page edited but never committed: see Review Focus) becomes a topic quoting the change, plus a `flagged` entry on the page and a visible note on it.
  - **Missing pages:** a page missing from the tool is treated as edited.
- [ ] **Step 6: Run the suite**

Run: `python3 -m unittest discover tests 2>&1 | tail -3`
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add skills
git commit -m "skills: wiki pages live next to the tasks, indexed in wiki.json"
```

### Task 9: Release

**Files:**
- Modify: `README.md` (Living documents, Use, Known limits); `.claude-plugin/plugin.json` (`"version": "0.6.0"`)

- [ ] **Step 1: Update the README:** docs next to the tasks, setup with the user, `game-setup upgrade`.
- [ ] **Step 2: Bump the version to `0.6.0`.**
- [ ] **Step 3: Run the suite**

Run: `python3 -m unittest discover tests 2>&1 | tail -3`
Expected: `OK`

- [ ] **Step 4: Commit, push the branch and open a release pull request against `main`** (merging it syncs the account marketplace)

```bash
git add README.md .claude-plugin/plugin.json
git commit -m "Release 0.6.0: docs next to the tasks, verified tasks home, upgrade"
```
