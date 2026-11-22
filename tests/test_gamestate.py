"""End-to-end tests for skills/game-setup/scripts/gamestate.py.

Run: python3 -m unittest discover tests
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "game-setup" / "scripts" / "gamestate.py"

VISION = "# Vision\n" + "\n".join(
    f"{h}\n{body}" for h, body in [
        ("## Pitch", "A pitch."), ("## Audience and platforms", "Couch, desktop."),
        ("## Pillars", "- **P1**: fast\n- **P2**: tense\n- **P3**: readable"),
        ("## Core loop", "Dash, hit, score."), ("## Target feeling", "Tension."),
        ("## Tone, art and world", "Bright."), ("## References", "x"), ("## Scope", "x")]) + "\n"

CONCEPTS = """# Concepts
## Concepts
### C1: Weapon swap brawler
### C2: Tag arena
### C3: Ring-out sumo
## Choice
C1, because it fits the seed best.
"""

INDEX_AREAS = ["Vision", "Mechanics", "Controls", "Systems", "Content", "Modes and sessions",
               "Screens and onboarding", "Feel", "Tone, art and world"]
PAGES = {"Vision": "vision.md", "Mechanics": "mechanics.md", "Controls": "controls.md",
         "Systems": "systems/weapons.md", "Content": "content.md", "Modes and sessions": "modes.md",
         "Screens and onboarding": "screens.md", "Feel": "feel.md", "Tone, art and world": "art.md"}
INDEX = "# Wiki\n" + "".join(f"## {a}\n- [{a}]({PAGES[a]})\n" for a in INDEX_AREAS)


def topic(tid, parent="T1", priority="support", status="open", pages=(), unblocks=()):
    t = {"id": tid, "title": f"topic {tid}", "question": "what?", "parent": parent, "priority": priority,
         "method": "think", "status": status, "pages": list(pages), "unblocks": list(unblocks)}
    if status != "open":
        t["resolution"] = "answered"
    return t


SEED_TOPICS = {"topics": [topic("T1", parent=None, priority="core", status="resolved", pages=["wiki/vision.md"]),
                          topic("T2", priority="core"), topic("T3"), topic("T4"), topic("T5"),
                          topic("T6", priority="later")]}

RICHNESS = {"targets": [
    {"id": "R1", "aspect": "depth", "statement": "every system matters", "metric": "win-rate shift with a system off",
     "threshold": ">= 10 points per system", "how": "bot x100 per toggle"},
    {"id": "R2", "aspect": "breadth", "statement": "plenty of arenas and weapons", "metric": "content count",
     "threshold": ">= 6 arenas, >= 12 weapons", "how": "count data files"},
    {"id": "R3", "aspect": "variety", "statement": "matches differ", "metric": "weapon-sequence overlap",
     "threshold": "<= 50% between seeds", "how": "bot x50"},
]}

FUN = {"items": [
    {"id": "FC1", "statement": "the lead changes", "scope": "core-loop", "kind": "proxy",
     "metric": "lead changes per match", "threshold": ">= 2 in 60% of matches", "how": "bot x50"},
    {"id": "FC2", "statement": "one more round", "scope": "full", "kind": "human"},
    {"id": "FC3", "statement": "no dominant pick", "scope": "full", "kind": "proxy",
     "metric": "top pick rate", "threshold": "< 40%", "how": "bot x200"},
]}


def feature(fid, milestone, tier="must", kind="test", measures=()):
    return {"id": fid, "title": f"feature {fid}", "pillar": "P1", "tier": tier, "milestone": milestone,
            "acceptance": ["it works"], "verify": {"kind": kind, "how": "run the test"},
            "measures": list(measures), "tickets": [f"#{fid}"], "pages": ["wiki/mechanics.md"],
            "passes": False, "evidence": "", "blocked": ""}


class GameRun(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.game = self.root / "docs" / "game"
        self.game.mkdir(parents=True)
        (self.root / "docs" / "agents").mkdir()
        shutil.copy(SCRIPT, self.game / "gamestate.py")
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "test")

    def tearDown(self):
        shutil.rmtree(self.root)

    # ---------- helpers ----------
    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True, text=True).stdout

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "work", "--allow-empty")

    def tool(self, *args, ok=True):
        r = subprocess.run([sys.executable, str(self.game / "gamestate.py"), *args],
                           cwd=self.root, capture_output=True, text=True)
        if ok:
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def next(self, *flags):
        return self.tool("status", *flags).split("next: ", 1)[1].strip()

    def load(self, name):
        return json.loads((self.game / name).read_text())

    def edit(self, name, fn):
        data = self.load(name)
        fn(data)
        (self.game / name).write_text(json.dumps(data, indent=2))

    def phase(self):
        s = self.load("state.json")
        return s["phase"], s["milestone"]

    def set_passes(self, *ids, value=True, evidence="test green"):
        def fn(d):
            for f in d["features"]:
                if f["id"] in ids:
                    f["passes"], f["evidence"] = value, (evidence if value else "")
        self.edit("features.json", fn)
        self.commit()

    def record_verdict(self, outcome):
        def fn(s):
            s["verdicts"].append({"scope": s["verdict_scope"], "outcome": outcome, "adr": "docs/adr/0001-v.md",
                                  "scores": {i: {"result": "pass", "evidence": "e"}
                                             for i in ("FC1", "FC2", "FC3", "R1", "R2", "R3")}})
        self.edit("state.json", fn)
        self.commit()
        self.tool("complete")

    def write_wiki(self, pages):
        for rel in pages:
            path = self.game / "wiki" / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text(f"# {rel}\n")

    def sync(self):
        self.assertEqual(self.next(), "game-gdd")
        self.tool("gdd-synced")

    def resolve(self, *ids):
        def fn(d):
            for t in d["topics"]:
                if t["id"] in ids:
                    t.update(status="resolved", resolution="answered", pages=["wiki/mechanics.md"])
        self.edit("topics.json", fn)
        self.commit()

    def to_ideation(self):
        self.tool("init")
        (self.root / "docs" / "agents" / "game.md").write_text("# Game workflow\n")
        self.commit()
        self.assertEqual(self.next(), "game-setup")
        self.tool("complete")
        self.tool("advance")
        self.assertEqual(self.next(), "with-user: game-ideation")

    def ideate(self):
        (self.game / "wiki").mkdir()
        (self.game / "wiki" / "vision.md").write_text(VISION)
        (self.game / "wiki" / "concepts.md").write_text(CONCEPTS)
        (self.game / "wiki" / "index.md").write_text("# Wiki\n## Vision\n- [Vision](vision.md)\n")
        (self.game / "topics.json").write_text(json.dumps(SEED_TOPICS))
        self.commit()
        self.tool("complete")
        self.sync()
        self.tool("advance")
        self.assertEqual(self.phase(), ("brainstorm", None))

    def to_plan(self):
        self.to_ideation()
        self.ideate()
        self.assertTrue(self.next().startswith("with-user: game-brainstorm T2"))  # core before support
        self.write_wiki(PAGES.values())
        self.resolve("T2", "T3", "T4", "T5")
        self.sync()  # pages changed: the GDD catches up before the phase changes
        self.tool("advance")
        self.assertEqual(self.next(), "game-consolidate")
        (self.game / "wiki" / "index.md").write_text(INDEX)
        (self.game / "fun-checklist.json").write_text(json.dumps(FUN))
        (self.game / "richness.json").write_text(json.dumps(RICHNESS))
        self.commit()
        self.tool("complete")
        self.sync()
        self.tool("advance")
        self.assertEqual(self.phase(), ("plan", None))

    def plan(self, extra=()):
        self.edit("features.json", lambda d: d.update(features=[
            feature("F1", "core-loop", measures=["FC1"]), feature("F2", "core-loop"),
            feature("F3", "systems", measures=["FC3", "R1", "R2", "R3"]), feature("F4", "content", tier="nice"),
            feature("F5", "verdict-build", kind="human"), *extra]))
        self.edit("state.json", lambda s: s.update(adapter_verified=True))
        self.commit()
        self.tool("complete")
        self.tool("advance")

    def to_core_verdict(self):
        self.to_plan()
        self.plan()
        self.set_passes("F1", "F2")
        self.tool("advance")
        self.assertEqual(self.phase(), ("verdict", None))

    # ---------- tests ----------
    def test_full_run_reaches_done_through_verdicts_and_polish(self):
        self.to_plan()
        self.plan()
        self.assertEqual(self.phase(), ("build", "core-loop"))
        self.assertTrue(self.next().startswith("game-build F1"))

        self.set_passes("F1", "F2")
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict core-loop")
        self.assertIn("cannot advance", self.tool("advance", ok=False))
        self.record_verdict("ship")
        self.tool("advance")
        self.assertEqual(self.phase(), ("build", "systems"))

        self.set_passes("F3")
        self.tool("advance")
        self.assertEqual(self.phase(), ("build", "verdict-build"))  # content has only a nice feature

        self.edit("state.json", lambda s: s["human_queue"].append(
            {"id": "H1", "what": "check F5 by hand", "unblocks": ["F5"]}))
        self.commit()
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict full")
        self.record_verdict("ship")
        self.tool("advance")
        self.assertEqual(self.phase(), ("polish", "polish"))
        self.assertEqual(self.next(), "game-polish")

        self.edit("features.json", lambda d: d["features"].extend([feature("F6", "polish"), feature("F7", "polish")]))
        self.commit()
        self.tool("complete")
        self.assertTrue(self.next().startswith("game-build F6"))
        self.set_passes("F6", "F7")
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict final")
        self.edit("state.json", lambda s: s["human_queue"].append(
            {"id": "H2", "what": "playtest final", "kind": "playtest", "scope": "final",
             "answers": "docs/game/playtests/final/answers.md"}))
        self.commit()
        self.record_verdict("ship")
        self.tool("advance")
        self.assertEqual(self.phase()[0], "awaiting-human")  # H1 still open; the playtest kit doesn't block
        self.assertTrue(self.next().startswith("stop:"))

        self.edit("state.json", lambda s: s.update(human_queue=[e for e in s["human_queue"] if e["id"] != "H1"]))
        self.commit()
        self.tool("advance")
        self.assertEqual(self.phase(), ("build", "verdict-build"))  # F5 was never marked passing: back to it

        self.set_passes("F5", evidence="human: checked by hand")
        self.tool("advance")
        self.assertEqual(self.phase()[0], "done")
        self.assertIn("stop: done (1 playtest kit(s) await answers", self.next())

    def test_adjust_dispatches_a_replan_then_rejudges_the_core_loop(self):
        self.to_core_verdict()
        self.record_verdict("adjust")
        self.tool("advance")
        self.assertEqual(self.next(), "game-plan adjust docs/adr/0001-v.md")
        self.assertIn("cannot advance", self.tool("advance", ok=False))
        self.tool("complete")
        self.tool("advance")  # the re-plan changed nothing in core-loop
        self.assertEqual(self.next(), "game-verdict core-loop")

    def test_restart_dispatches_ideate_and_archives_features_and_queue(self):
        self.to_core_verdict()
        self.edit("state.json", lambda s: s["human_queue"].append({"id": "H1", "what": "x", "unblocks": ["F2"]}))
        self.commit()
        self.record_verdict("restart")
        self.tool("advance")
        self.assertEqual(self.next(), "with-user: game-ideation restart docs/adr/0001-v.md")
        self.assertEqual(self.load("features.json")["features"], [])
        self.assertEqual(self.load("state.json")["human_queue"], [])
        archive = self.game / "archive" / "restart-1"
        self.assertTrue((archive / "features.json").exists() and (archive / "human-queue.json").exists())
        self.tool("complete")
        self.tool("advance")  # ideation -> brainstorm: nothing open, the wiki unchanged
        self.tool("advance")  # brainstorm -> consolidate
        self.tool("complete")
        self.tool("advance")
        self.assertEqual(self.next(), "game-plan restart docs/adr/0001-v.md")
        self.edit("features.json", lambda d: d["features"].append(feature("F1", "core-loop")))
        self.assertIn("F1: reuses an id", self.tool("check", ok=False))

    def test_limits_stop_for_a_human_and_resume_the_owed_task(self):
        self.to_plan()
        self.plan()
        self.edit("state.json", lambda s: s["limits"].update(max_adjusts=0))
        self.commit()
        self.set_passes("F1", "F2")
        self.tool("advance")
        self.record_verdict("adjust")
        self.tool("advance")
        self.assertEqual(self.phase()[0], "awaiting-human")
        self.assertIn("stop: adjust limit reached", self.next())
        self.edit("state.json", lambda s: s.update(stop_reason=None))
        self.commit()
        self.tool("advance")
        self.assertEqual(self.next(), "game-plan adjust docs/adr/0001-v.md")

    def test_regressions_in_earlier_milestones_come_first_and_verdicts_wait_for_green(self):
        self.to_core_verdict()
        self.set_passes("F1", value=False)
        self.assertTrue(self.next().startswith("game-build F1"))
        self.set_passes("F1")
        self.record_verdict("ship")
        self.tool("advance")
        self.assertEqual(self.phase(), ("build", "systems"))
        self.set_passes("F2", value=False)
        self.assertTrue(self.next().startswith("game-build F2"))

    def test_edit_guard_outside_plan(self):
        self.to_plan()
        self.plan(extra=[feature("F8", "systems")])

        def tamper(d):
            fs = {f["id"]: f for f in d["features"]}
            fs["F2"]["acceptance"] = ["easier"]
            fs["F3"]["milestone"] = "content"
            fs["F8"]["tier"] = "nice"
            d["features"].remove(fs["F4"])
        self.edit("features.json", tamper)
        self.edit("fun-checklist.json", lambda d: d["items"][0].update(threshold=">= 0"))
        self.edit("richness.json", lambda d: d["targets"].pop())
        out = self.tool("check", ok=False)
        for expected in ("F4: removed", "F2: acceptance changed", "F3: milestone changed",
                         "F8: a must feature left must", "fun FC1: changed after consolidate",
                         "richness R3: removed after consolidate"):
            self.assertIn(expected, out)
        self.assertTrue(self.next().startswith("fix: "))

    def test_a_must_feature_can_be_replaced_outside_plan(self):
        self.to_plan()
        self.plan()

        def replace(d):
            d["features"].append(feature("F9", "core-loop"))
            for f in d["features"]:
                if f["id"] == "F2":
                    f.update(tier="cut", cut_reason="replaced by F9")
        self.edit("features.json", replace)
        self.assertIn("check: ok", self.tool("check"))

    def test_passing_needs_evidence(self):
        self.to_plan()
        self.plan()
        self.edit("features.json", lambda d: d["features"][0].update(passes=True))
        self.assertIn("F1: passes is true without evidence", self.tool("check", ok=False))

    def test_attempts_stalls_and_budget_stop_the_run(self):
        self.to_plan()
        self.plan()
        action = self.next()
        for _ in range(3):
            self.tool("tick", action)
        self.assertEqual(self.next(), "game-build F2 \"feature F2\"")  # F1 used its 3 attempts
        self.set_passes("F2")
        self.assertEqual(self.next(), "game-plan unblock F1")
        for _ in range(5):
            self.tool("tick", "game-plan unblock F1")
        self.assertIn("stop: stalled", self.next())
        self.edit("state.json", lambda s: s["limits"].update(budget_sessions=8))
        self.assertIn("stop: budget exhausted", self.next())

    def test_bookkeeping_survives_a_reset_to_the_session_base(self):
        self.to_plan()
        self.plan()
        self.tool("tick", self.next())
        base = self.git("rev-parse", "HEAD").strip()
        (self.root / "junk.txt").write_text("a bad session")
        self.commit()
        self.git("reset", "--hard", base)
        self.assertEqual(self.load("state.json")["counters"]["sessions"], 1)
        self.assertEqual(self.phase(), ("build", "core-loop"))

    def test_playtest_answers_reopen_the_verdict(self):
        self.to_core_verdict()
        answers = "docs/game/playtests/core/answers.md"
        self.edit("state.json", lambda s: s["human_queue"].append(
            {"id": "H1", "what": "playtest", "kind": "playtest", "scope": "core-loop", "answers": answers}))
        self.commit()
        self.record_verdict("ship")
        self.tool("advance")
        self.assertEqual(self.phase(), ("build", "systems"))
        (self.root / answers).parent.mkdir(parents=True)
        (self.root / answers).write_text("FC1: no")
        self.assertEqual(self.next(), "advance")
        self.tool("advance")
        self.assertEqual(self.next(), f"game-verdict core-loop answers {answers}")

    def test_nice_features_are_built_when_the_budget_allows(self):
        self.to_plan()
        self.plan(extra=[feature("F8", "core-loop", tier="nice")])
        self.set_passes("F1", "F2")
        self.assertTrue(self.next().startswith("game-build F8"))
        self.edit("state.json", lambda s: s["limits"].update(budget_sessions=12))
        self.assertEqual(self.next(), "advance")

    def test_ideation_needs_directions_and_seed_topics(self):
        self.to_ideation()
        (self.game / "wiki").mkdir()
        (self.game / "wiki" / "vision.md").write_text(VISION)
        (self.game / "wiki" / "concepts.md").write_text(CONCEPTS.replace("### C3: Ring-out sumo\n", ""))
        self.commit()
        out = self.tool("gate", ok=False)
        for expected in ("2 directions", "wiki/index.md is missing", "0 follow-up topics"):
            self.assertIn(expected, out)

    def test_consolidate_needs_every_area_and_richness_aspect_and_plan_must_measure_them(self):
        self.to_ideation()
        self.ideate()
        self.write_wiki(PAGES.values())
        self.resolve("T2", "T3", "T4", "T5")
        self.sync()
        self.tool("advance")
        (self.game / "wiki" / "index.md").write_text(INDEX.replace("## Feel\n- [Feel](feel.md)\n", "## Feel\n"))
        (self.game / "fun-checklist.json").write_text(json.dumps(FUN))
        (self.game / "richness.json").write_text(json.dumps({"targets": RICHNESS["targets"][:2]}))
        self.commit()
        out = self.tool("gate", ok=False)
        self.assertIn("'## Feel' links no existing page", out)
        self.assertIn("richness.json has no variety target", out)
        (self.game / "wiki" / "index.md").write_text(INDEX)
        (self.game / "richness.json").write_text(json.dumps(RICHNESS))
        self.commit()
        self.tool("complete")
        self.sync()
        self.tool("advance")
        self.edit("features.json", lambda d: d.update(features=[feature("F1", "core-loop", measures=["FC1", "FC3"])]))
        self.edit("state.json", lambda s: s.update(adapter_verified=True))
        self.commit()
        self.assertIn("R1: no must feature lists it in measures", self.tool("gate", ok=False))

    def test_brainstorm_share_lets_support_topics_wait_until_consolidate_defers_them(self):
        self.to_ideation()
        self.ideate()
        self.edit("state.json", lambda s: s["limits"].update(budget_sessions=10))
        for _ in range(2):
            self.tool("tick", "game-brainstorm T9 \"x\"")
        self.assertTrue(self.next().startswith("with-user: game-brainstorm T2"))  # core topics still run
        self.write_wiki(PAGES.values())
        self.resolve("T2")
        self.sync()
        self.tool("advance")  # support topics T3-T5 wait: the brainstorm share is spent
        self.assertEqual(self.next(), "game-consolidate")
        (self.game / "wiki" / "index.md").write_text(INDEX)
        (self.game / "fun-checklist.json").write_text(json.dumps(FUN))
        (self.game / "richness.json").write_text(json.dumps(RICHNESS))
        self.commit()
        self.assertIn("topic T3: open (support)", self.tool("complete", ok=False))

        def defer(d):
            for t in d["topics"]:
                if t["status"] == "open":
                    t.update(status="deferred", resolution="not needed before the core-loop verdict")
        self.edit("topics.json", defer)
        self.commit()
        self.tool("complete")

    def test_topics_opened_during_build_interrupt_the_work_that_needs_them(self):
        self.to_plan()
        self.plan()
        self.edit("topics.json", lambda d: d["topics"].append(topic("T7", unblocks=["F2"])))
        self.edit("topics.json", lambda d: d["topics"].append(topic("T8")))
        self.commit()
        self.assertTrue(self.next().startswith("with-user: game-brainstorm T7"))  # unblocks F2; T8 waits
        self.resolve("T7")
        self.assertTrue(self.next().startswith("game-build F1"))
        self.edit("topics.json", lambda d: d["topics"].append(topic("T9", priority="core")))
        self.commit()
        self.assertTrue(self.next().startswith("with-user: game-brainstorm T9"))

    def test_without_a_person_the_run_builds_around_open_topics_then_waits(self):
        self.to_plan()
        self.plan()
        self.edit("topics.json", lambda d: d["topics"].append(topic("T7", unblocks=["F1"])))
        self.commit()
        self.assertTrue(self.next().startswith("with-user: game-brainstorm T7"))
        self.assertTrue(self.next("--no-user").startswith("game-build F2"))  # F1 waits on T7
        self.set_passes("F2")
        self.assertIn("stop: waiting for a person", self.next("--no-user"))

    def test_ideation_waits_for_a_person(self):
        self.to_ideation()
        self.assertIn("stop: waiting for a person", self.next("--no-user"))

    def test_changed_pages_resync_the_gdd_before_the_next_milestone_and_before_stopping(self):
        self.to_plan()
        self.plan()
        (self.game / "wiki" / "mechanics.md").write_text("# Mechanics\nDash now has a cooldown.\n")
        self.set_passes("F1", "F2")
        self.sync()
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict core-loop")

    def test_resolved_topics_need_a_page(self):
        self.to_ideation()
        self.ideate()
        self.edit("topics.json", lambda d: d["topics"][1].update(status="resolved", resolution="x", pages=[]))
        self.assertIn("topic T2: resolved without a wiki page", self.tool("check", ok=False))

    def test_final_adjust_keeps_earlier_verdicts(self):
        self.to_core_verdict()
        self.record_verdict("ship")
        self.tool("advance")
        self.set_passes("F3")
        self.tool("advance")
        self.set_passes("F5", evidence="human: ok")
        self.tool("advance")
        self.record_verdict("ship")  # full
        self.tool("advance")
        self.edit("features.json", lambda d: d["features"].append(feature("F6", "polish")))
        self.commit()
        self.tool("complete")
        self.set_passes("F6")
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict final")
        self.record_verdict("adjust")
        self.tool("advance")
        self.assertEqual(self.load("state.json")["passed_verdicts"], ["core-loop", "full"])
        self.tool("complete")
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict final")  # nothing changed: straight back to the final verdict


class Templates(unittest.TestCase):
    """The skills' templates must produce files the gates accept."""

    def test_template_headings_match_the_gates(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("gamestate", SCRIPT)
        gamestate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gamestate)
        skills = SCRIPT.parents[2]
        for template, headings in (("game-ideation/vision-template.md", gamestate.VISION_HEADINGS),
                                   ("game-ideation/concepts-template.md", gamestate.CONCEPT_HEADINGS),
                                   ("game-ideation/index-template.md", gamestate.INDEX_SECTIONS)):
            lines = (skills / template).read_text().splitlines()
            self.assertEqual([h for h in headings if h not in lines], [], template)


if __name__ == "__main__":
    unittest.main()
