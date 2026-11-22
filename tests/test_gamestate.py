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

DESIGN = """# Design
## Pitch
A pitch.
## Pillars
- **P1**: fast
- **P2**: tense
- **P3**: readable
## Core loop
Dash, hit, score.
## Tone, art and world
Bright.
## Pillar test
Done.
"""

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
            "measures": list(measures), "tickets": [f"T{fid}"], "passes": False, "evidence": "",
            "attempts": 0, "blocked": ""}


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

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "step", "--allow-empty")

    def run_tool(self, *args, ok=True):
        r = subprocess.run([sys.executable, str(self.game / "gamestate.py"), *args],
                           cwd=self.root, capture_output=True, text=True)
        if ok:
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def load(self, name):
        return json.loads((self.game / name).read_text())

    def save(self, name, data):
        (self.game / name).write_text(json.dumps(data, indent=2))

    def edit(self, name, fn):
        data = self.load(name)
        fn(data)
        self.save(name, data)

    def phase(self):
        return self.load("state.json")["phase"], self.load("state.json")["milestone"]

    def pass_features(self, *ids):
        def fn(d):
            for f in d["features"]:
                if f["id"] in ids:
                    f["passes"], f["evidence"] = True, "test green"
        self.edit("features.json", fn)

    def verdict(self, outcome):
        def fn(s):
            s["verdicts"].append({"scope": s["verdict_scope"], "outcome": outcome, "adr": "docs/adr/0001-v.md",
                                  "scores": {i: {"result": "pass", "evidence": "e"} for i in ("FC1", "FC2", "FC3")}})
        self.edit("state.json", fn)

    def to_plan(self):
        self.run_tool("init")
        (self.root / "docs" / "agents" / "game.md").write_text("# Game workflow\n")
        self.run_tool("advance")
        (self.game / "design.md").write_text(DESIGN)
        self.save("fun-checklist.json", FUN)
        self.run_tool("advance")
        self.assertEqual(self.phase(), ("plan", None))

    def plan(self):
        self.edit("features.json", lambda d: d.update(features=[
            feature("F1", "core-loop", measures=["FC1"]), feature("F2", "core-loop"),
            feature("F3", "systems", measures=["FC3"]), feature("F4", "content", tier="nice"),
            feature("F5", "verdict-build", kind="human")]))
        self.edit("state.json", lambda s: s.update(adapter_verified=True))
        self.run_tool("advance")
        self.commit()

    def test_full_run_reaches_done_through_core_verdict_and_release(self):
        self.to_plan()
        self.plan()
        self.assertEqual(self.phase(), ("build", "core-loop"))
        self.assertIn("next: game-build F1", self.run_tool("status"))

        self.pass_features("F1", "F2")
        self.run_tool("advance")
        self.assertEqual(self.phase(), ("verdict", None))
        self.assertIn("game-verdict core-loop", self.run_tool("status"))

        self.verdict("ship")
        self.run_tool("advance")
        self.assertEqual(self.phase(), ("build", "systems"))

        self.pass_features("F3")
        self.run_tool("advance")
        self.assertEqual(self.phase(), ("build", "verdict-build"))  # content has no must features

        self.edit("state.json", lambda s: s["human_queue"].append(
            {"id": "H1", "what": "check F5 by hand", "unblocks": ["F5"]}))
        self.run_tool("advance")
        self.assertEqual(self.phase(), ("verdict", None))
        self.verdict("ship")
        self.run_tool("advance")
        self.assertEqual(self.phase(), ("release", "polish"))
        self.assertIn("next: game-release", self.run_tool("status"))

        self.edit("features.json", lambda d: d["features"].extend(
            [feature("F6", "polish"), feature("F7", "release")]))
        self.commit()
        self.pass_features("F6")
        self.run_tool("advance")
        self.assertEqual(self.phase(), ("release", "release"))
        self.pass_features("F7")
        self.run_tool("advance")
        self.assertEqual(self.phase()[0], "awaiting-human")  # H1 still open

        self.edit("state.json", lambda s: s.update(human_queue=[]))
        self.assertIn("next: advance", self.run_tool("status"))
        self.run_tool("advance")
        self.assertEqual(self.phase()[0], "done")

    def test_adjust_rejudges_core_loop_before_building_on_it(self):
        self.to_plan()
        self.plan()
        self.pass_features("F1", "F2")
        self.run_tool("advance")
        self.verdict("adjust")
        self.run_tool("advance")
        self.assertEqual(self.phase(), ("plan", None))
        self.run_tool("advance")  # plan changed nothing in core-loop
        self.assertEqual(self.phase(), ("verdict", None))

    def test_limits_stop_for_a_human(self):
        self.to_plan()
        self.plan()
        self.edit("state.json", lambda s: s["limits"].update(max_adjusts=0))
        self.pass_features("F1", "F2")
        self.run_tool("advance")
        self.verdict("adjust")
        self.run_tool("advance")
        state = self.load("state.json")
        self.assertEqual((state["phase"], state["resume_phase"]), ("awaiting-human", "plan"))
        self.assertIn("stop:", self.run_tool("status"))

    def test_restart_archives_the_definition_of_done(self):
        self.to_plan()
        self.plan()
        self.pass_features("F1", "F2")
        self.run_tool("advance")
        self.verdict("restart")
        self.run_tool("advance")
        self.assertEqual(self.phase(), ("ideate", None))
        self.assertEqual(self.load("features.json")["features"], [])
        self.assertTrue((self.game / "archive" / "restart-1" / "features.json").exists())

    def test_edit_guard_blocks_deleting_and_rewriting_items_during_build(self):
        self.to_plan()
        self.plan()

        def tamper(d):
            d["features"][1]["acceptance"] = ["easier"]
            del d["features"][3]
        self.edit("features.json", tamper)
        out = self.run_tool("check", ok=False)
        self.assertIn("F4: removed", out)
        self.assertIn("F2: acceptance changed", out)
        self.assertIn("cannot advance", self.run_tool("advance", ok=False))

    def test_passing_needs_evidence(self):
        self.to_plan()
        self.plan()
        self.edit("features.json", lambda d: d["features"][0].update(passes=True))
        self.assertIn("F1: passes is true without evidence", self.run_tool("check", ok=False))

    def test_budget_stops_the_run(self):
        self.to_plan()
        self.plan()
        self.edit("state.json", lambda s: s["limits"].update(budget_sessions=2))
        self.run_tool("tick")
        self.run_tool("tick")
        self.assertIn("next: stop: budget exhausted", self.run_tool("status"))


if __name__ == "__main__":
    unittest.main()
