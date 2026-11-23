"""End-to-end tests for skills/game-setup/scripts/gamestate.py.

Run: python3 -m unittest discover tests
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "game-setup" / "scripts" / "gamestate.py"
LOOP = Path(__file__).resolve().parents[1] / "skills" / "game-next" / "scripts" / "loop.sh"
CURRENT_VERSION = int(re.search(r"^CURRENT_VERSION = (\d+)$", SCRIPT.read_text(), re.M).group(1))


VISION_JSON = {
    "pillars": [{"id": "P1", "statement": "fast"}, {"id": "P2", "statement": "tense"},
                {"id": "P3", "statement": "readable"}],
    "anti_pillars": ["no grinding"],
    "kill_condition": "nobody wants a second match",
    "slice": {"test_question": "is one match fun?",
              "quality_bar": {"code": "production", "feel": "representative", "art": "representative",
                              "audio": "representative", "ui": "representative", "onboarding": "representative"}},
    "directions": {"count": 4, "choice": "C2"},
}

AREAS = ["Vision", "Mechanics", "Controls", "Systems", "Content", "Modes and sessions",
         "Screens and onboarding", "Feel", "Art", "Audio", "Narrative and world"]
SLICE_AREAS = [a for a in AREAS if a != "Modes and sessions"]
PAGE_IDS = {"Vision": ["vision", "slice", "concepts"], "Mechanics": ["mechanics"], "Controls": ["controls"],
            "Systems": ["weapons"], "Content": ["content"], "Modes and sessions": ["modes"],
            "Screens and onboarding": ["screens"], "Feel": ["feel"],
            "Art": ["art"], "Audio": ["audio"], "Narrative and world": ["tone"]}


def wiki_index(*areas):
    return {"pages": [{"id": i, "title": i.title(), "area": a, "link": f"https://docs.example/{i}",
                       "version": "1", "updated": "x"} for a in areas for i in PAGE_IDS[a]]}


def topic(tid, parent="T1", priority="support", status="open", stage="slice", pages=(), unblocks=(),
          roles=("design",)):
    t = {"id": tid, "title": f"topic {tid}", "question": "what?", "parent": parent, "priority": priority,
         "stage": stage, "status": status, "pages": list(pages), "unblocks": list(unblocks),
         "roles": list(roles)}
    if status != "open":
        t["resolution"] = "answered"
    return t


SEED_TOPICS = {"topics": [
    topic("T1", parent=None, priority="core", status="resolved", pages=["vision"]),
    topic("T2", priority="core"), topic("T3"),
    topic("T4", stage="production"), topic("T5", stage="production"),
    topic("T6", priority="later", stage="production")]}

FUN = {"items": [
    {"id": "FC1", "statement": "the lead changes", "scope": "core-loop", "kind": "proxy",
     "metric": "lead changes per match", "threshold": ">= 2 in 60% of matches", "how": "bot x50"},
    {"id": "FC2", "statement": "one more round", "scope": "slice", "kind": "human"},
    {"id": "FC4", "statement": "the arena matters", "scope": "slice", "kind": "proxy",
     "metric": "hazard kills share", "threshold": ">= 20%", "how": "bot x50"},
    {"id": "FC3", "statement": "no dominant pick", "scope": "full", "kind": "proxy",
     "metric": "top pick rate", "threshold": "< 40%", "how": "bot x200"},
    {"id": "FC5", "statement": "the art reads as ours", "scope": "slice", "kind": "review",
     "roles": ["art"], "taste": True},
    {"id": "FC6", "statement": "hits feel good", "scope": "slice", "kind": "review",
     "roles": ["feel"], "taste": True},
    {"id": "FC7", "statement": "it is the game we meant", "scope": "slice", "kind": "review",
     "roles": ["creative"], "taste": True},
    {"id": "FC8", "statement": "the audio carries the match", "scope": "full", "kind": "review",
     "roles": ["audio"], "taste": False},
]}

FULL_REVIEWS = [  # with FC8 (audio), a full review item for every role
    {"id": f"FC1{n}", "statement": f"{role} holds up", "scope": "full", "kind": "review",
     "roles": [role], "taste": role in ("creative", "feel", "art", "ux")}
    for n, role in enumerate(["creative", "design", "feel", "art", "narrative", "ux"])]

RICHNESS = {"targets": [
    {"id": "R1", "aspect": "depth", "scope": "full", "statement": "every system matters",
     "metric": "win-rate shift with a system off", "threshold": ">= 10 points per system", "how": "bot x100"},
    {"id": "R2", "aspect": "breadth", "scope": "full", "statement": "plenty of arenas and weapons",
     "metric": "content count", "threshold": ">= 6 arenas, >= 12 weapons", "how": "count data files"},
    {"id": "R3", "aspect": "variety", "scope": "full", "statement": "matches differ",
     "metric": "weapon-sequence overlap", "threshold": "<= 50% between seeds", "how": "bot x50"},
]}

EVIDENCE = "docs/game/playtests/evidence.md"
ANSWERS = "docs/game/playtests/slice/answers.md"

# EveLikeBrawl's real files: a game set up with release 0.3.0 (state version 3), still at setup, no task.
EVE_STATE = """{
  "version": 3,
  "phase": "setup",
  "milestone": null,
  "task": null,
  "verdict_scope": null,
  "verdict_index": 0,
  "passed_verdicts": [],
  "checkpoint_due": false,
  "adapter_verified": false,
  "restart_adr": null,
  "resume": null,
  "stop_reason": null,
  "counters": {
    "sessions": 0,
    "adjusts": 0,
    "restarts": 0
  },
  "limits": {
    "budget_sessions": 150,
    "max_adjusts": 2,
    "max_restarts": 1,
    "max_attempts": 3,
    "max_repeats": 5
  },
  "attempts": {},
  "last_dispatch": {
    "action": null,
    "repeats": 0
  },
  "human_queue": [],
  "verdicts": []
}
"""
EVE_FEATURES = """{
  "milestones": [
    "core-loop",
    "systems",
    "content",
    "verdict-build",
    "polish"
  ],
  "features": []
}
"""
MILESTONES = ["core-loop", "slice", "systems", "content", "verdict-build", "polish"]


def feature(fid, milestone, tier="must", kind="test", measures=(), roles=()):
    return {"id": fid, "title": f"feature {fid}", "pillar": "P1", "tier": tier, "milestone": milestone,
            "acceptance": ["it works"], "verify": {"kind": kind, "how": "run the test"},
            "measures": list(measures), "tickets": [f"#{fid}"], "pages": ["mechanics"],
            "roles": list(roles), "passes": False, "evidence": "", "blocked": ""}


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

    def tool(self, *args, ok=True, script=None):
        r = subprocess.run([sys.executable, str(script or self.game / "gamestate.py"), *args],
                           cwd=self.root, capture_output=True, text=True)
        if ok:
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        else:
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout + r.stderr

    def plugin(self, *args, ok=True):
        """The plugin's own copy of the tool, run against this game (as game-next and upgrade do)."""
        return self.tool(*args, "--root", str(self.root), ok=ok, script=SCRIPT)

    def clean(self):
        return self.git("status", "--porcelain") == ""

    def next(self, *flags):
        return self.tool("status", *flags).split("next: ", 1)[1].strip()

    def load(self, name):
        return json.loads((self.game / name).read_text())

    def edit(self, name, fn):
        data = self.load(name)
        fn(data)
        (self.game / name).write_text(json.dumps(data, indent=2))

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def phase(self):
        s = self.load("state.json")
        return s["phase"], s["milestone"]

    def stage(self):
        return self.load("state.json")["stage"]

    def set_passes(self, *ids, value=True, evidence="test green"):
        def fn(d):
            for f in d["features"]:
                if f["id"] in ids:
                    f["passes"], f["evidence"] = value, (evidence if value else "")
        self.edit("features.json", fn)
        self.commit()

    def note(self, **overrides):
        n = {"id": "N1", "what": "HUD text sinks into the sky", "evidence": "inputs/hud-bright.png contrast 2.1:1",
             "rule": "art-bible: HUD contrast >= 4.5:1", "severity": "advisory",
             "anchor": {"kind": "rule", "ref": "art-bible#hud"}, "item": "FC7",
             "suggestion": "outline the text", "decision": "feature F031"}
        n.update(overrides)
        return n

    def write_review(self, target, role, commit, notes=(), result=None):
        """A valid review file for target by role; for a feature target it also sets that feature's reviews[role]."""
        if commit == "HEAD":
            commit = self.git("rev-parse", "HEAD").strip()
        rel = f"docs/game/reviews/{target}/{role}.json"
        notes = list(notes)
        self.write(rel, json.dumps({"role": role, "target": target, "commit": commit, "independent": True,
                                    "inputs": [], "result": result or ("notes" if notes else "ok"),
                                    "reason": "", "notes": notes}))
        if re.fullmatch(r"F\d+", target):
            def fn(d):
                for f in d["features"]:
                    if f["id"] == target:
                        f.setdefault("reviews", {})[role] = rel
            self.edit("features.json", fn)
        self.commit()

    def calibrate(self):
        self.write("docs/game/calibration/labels.json",
                   json.dumps({"labels": [{"capture": "x.png", "ours": True, "why": "palette"}]}))
        self.commit()

    def record_verdict(self, outcome, results=None, complete=True, reviews=None):
        """Scores every item; review items FC5-FC8 get one review file per role under reviews/verdict-<scope>/."""
        self.write(EVIDENCE, "metrics")
        results, reviews = results or {}, reviews or {}
        scope = self.load("state.json")["verdict_scope"]
        review_items = {i["id"]: i["roles"][0] for i in self.load("fun-checklist.json")["items"]
                        if i["kind"] == "review"}
        for role in dict.fromkeys(review_items.values()):
            self.write_review(f"verdict-{scope}", role, "HEAD", reviews.get(role, ()))

        def fn(s):
            scores = {i: {"result": results.get(i, "pass"), "evidence": EVIDENCE}
                      for i in ("FC1", "FC2", "FC3", "FC4", "R1", "R2", "R3")}
            for iid, role in review_items.items():
                path = f"docs/game/reviews/verdict-{scope}/{role}.json"
                scores[iid] = {"result": results.get(iid, "pass"), "evidence": path, "reviews": [path]}
            s["verdicts"].append({"scope": s["verdict_scope"], "outcome": outcome, "adr": "docs/adr/0001-v.md",
                                  "scores": scores})
        self.edit("state.json", fn)
        self.commit()
        if complete:
            self.tool("complete")

    def write_wiki(self, areas):
        self.write("docs/game/wiki.json", json.dumps(wiki_index(*areas)))

    def sync(self):
        self.assertEqual(self.next(), "game-gdd")
        self.tool("gdd-synced")

    def resolve(self, *ids):
        def fn(d):
            for t in d["topics"]:
                if t["id"] in ids:
                    t.update(status="resolved", resolution="answered", pages=["mechanics"])
        self.edit("topics.json", fn)
        self.commit()

    # ---------- the slice ----------
    def to_ideation(self):
        self.tool("init")
        (self.root / "docs" / "agents" / "game.md").write_text("# Game workflow\n")
        (self.root / "docs" / "agents" / "docs.md").write_text("# Docs\n")
        self.edit("state.json", lambda s: s.update(docs_verified={"place": "ClickUp doc", "date": "2026-11-22"}))
        self.commit()
        self.assertEqual(self.next(), "with-user: game-setup")
        self.tool("complete")
        self.tool("advance")
        self.assertEqual(self.next(), "with-user: game-ideation")

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

    def ideate(self):
        (self.game / "vision.json").write_text(json.dumps(VISION_JSON))
        self.write_wiki(["Vision"])
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
        self.write_wiki(SLICE_AREAS)
        self.resolve("T2", "T3")  # the slice's topics; T4-T6 wait for production
        self.sync()
        self.tool("advance")
        self.assertEqual(self.next(), "game-consolidate")
        self.edit("wiki.json", lambda d: d["pages"][0].update(version="2"))  # consolidate touches the wiki
        (self.game / "fun-checklist.json").write_text(json.dumps(FUN))
        (self.game / "richness.json").write_text(json.dumps(RICHNESS))
        self.commit()
        self.tool("complete")
        self.sync()
        self.tool("advance")
        self.assertEqual(self.phase(), ("plan", None))
        self.assertEqual(self.next(), "game-plan")

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

    def test_a_review_older_than_the_session_does_not_count(self):
        self.to_plan()
        self.plan(extra=[feature("F4", "slice", kind="capture", roles=("art",))])
        self.set_passes("F1", "F2")
        old = self.git("rev-parse", "HEAD").strip()
        self.commit()
        base = self.git("rev-parse", "HEAD").strip()
        self.write_review("F4", "art", old, notes=[self.note(decision="wontfix: fine")])
        self.set_passes("F4")
        self.assertIn("F4: the art review predates this session's work; review again",
                      self.tool("check", "--since", base, ok=False))
        self.write_review("F4", "art", "HEAD", notes=[self.note(decision="wontfix: fine")])
        self.assertNotIn("predates", self.tool("check", "--since", base))

    def test_review_notes_need_decisions_that_point_somewhere(self):
        self.to_plan()
        self.write_review("F1", "art", "HEAD", notes=[self.note(decision="feature F099")])
        self.assertIn("docs/game/reviews/F1/art.json: note N1 decision names F099, which does not exist",
                      self.tool("check", ok=False))
        self.write_review("F1", "art", "HEAD", notes=[self.note(decision="maybe later")])
        self.assertIn("note N1 decision 'maybe later' is not", self.tool("check", ok=False))
        self.write_review("F1", "art", "HEAD", notes=[self.note(decision="")])
        self.tool("check")  # a note still awaiting its decision is fine until the feature passes

    def test_malformed_reviews_are_reasons_not_crashes(self):
        self.to_plan()
        self.write("docs/game/reviews/F1/art.json", "[]")
        self.assertIn("docs/game/reviews/F1/art.json: not a JSON object", self.tool("check", ok=False))
        self.write("docs/game/reviews/F1/art.json", "{nope")
        self.assertIn("docs/game/reviews/F1/art.json: not a JSON object", self.tool("check", ok=False))

    def test_topics_and_features_name_known_roles(self):
        self.to_plan()
        self.edit("topics.json", lambda d: d["topics"][1].update(roles=["lighting"]))
        self.assertIn("topic T2: role 'lighting' is not one of", self.tool("check", ok=False))
        self.edit("topics.json", lambda d: d["topics"][1].update(roles=[], status="open"))
        self.assertIn("topic T2: open without roles", self.tool("check", ok=False))

    def test_visible_features_need_roles_and_design_reviews_only_at_verdicts(self):
        self.to_plan()
        self.edit("features.json", lambda d: d.update(features=[feature("F1", "core-loop", kind="capture")]))
        self.assertIn("F1: visible work needs roles", self.tool("check", ok=False))
        self.edit("features.json", lambda d: d["features"][0].update(roles=["design"]))
        self.assertIn("F1: design judges at verdicts, not on features", self.tool("check", ok=False))
        self.edit("features.json", lambda d: d["features"][0].update(roles=["art"]))
        self.tool("check")  # passes

    def test_a_page_in_a_taste_area_makes_a_feature_visible(self):
        self.to_plan()
        self.edit("features.json", lambda d: d.update(features=[feature("F1", "core-loop")]))
        self.tool("check")
        self.edit("features.json", lambda d: d["features"][0].update(pages=["art"]))
        self.assertIn("F1: visible work needs roles", self.tool("check", ok=False))

    def test_a_role_switched_off_cannot_be_named(self):
        self.to_plan()
        self.edit("vision.json", lambda v: v.update(roles_off={"audio": "played muted in class"}))
        self.edit("topics.json", lambda d: d["topics"][1].update(roles=["audio"]))
        self.assertIn("topic T2: role 'audio' is switched off in vision.json roles_off", self.tool("check", ok=False))

    def test_consolidate_gate_skips_areas_of_roles_switched_off(self):
        self.to_ideation()
        self.ideate()
        self.edit("vision.json", lambda v: v.update(roles_off={"audio": "muted"}))
        self.write_wiki([a for a in SLICE_AREAS if a != "Audio"])
        self.resolve("T2", "T3")
        self.sync()
        self.tool("advance")
        self.assertEqual(self.next(), "game-consolidate")
        self.assertNotIn("area 'Audio'", self.tool("complete", ok=False))

    def plan(self, extra=()):
        self.edit("features.json", lambda d: d.update(features=[
            feature("F1", "core-loop", measures=["FC1"]), feature("F2", "core-loop"),
            feature("F3", "slice", measures=["FC4"]), *extra]))
        self.edit("state.json", lambda s: s.update(adapter_verified=True))
        self.commit()
        self.tool("complete")
        self.tool("advance")

    def to_core_verdict(self):
        self.to_plan()
        self.plan()
        self.set_passes("F1", "F2")
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict core-loop")

    def to_slice_verdict(self):
        self.to_core_verdict()
        self.record_verdict("ship")
        self.tool("advance")
        self.assertEqual(self.phase(), ("build", "slice"))
        self.set_passes("F3")
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict slice")

    def ship_slice(self):
        self.calibrate()
        self.edit("state.json", lambda s: s["human_queue"].append(
            {"id": "H1", "what": "play the slice", "kind": "playtest", "scope": "slice", "answers": ANSWERS,
             "how": "docs/game/playtests/slice/kit.md"}))
        self.commit()
        self.assertIn("stop: waiting for the slice playtest", self.next())
        self.write(ANSWERS, "FC2: yes")
        self.commit()
        self.assertEqual(self.next(), f"game-verdict slice answers {ANSWERS}")
        self.record_verdict("ship")
        self.assertEqual(self.load("state.json")["human_queue"], [])  # the answers were consumed
        self.tool("advance")

    def to_production_consolidate(self):
        self.to_slice_verdict()
        self.ship_slice()
        self.assertEqual((self.stage(), self.phase()), ("production", ("brainstorm", None)))
        self.assertTrue(self.next().startswith("with-user: game-brainstorm T4"))
        self.write_wiki(AREAS)
        self.resolve("T4", "T5")
        self.sync()
        self.tool("advance")
        self.assertEqual(self.next(), "game-consolidate production")

    def to_production_plan(self):
        self.to_production_consolidate()
        self.edit("wiki.json", lambda d: d["pages"][0].update(version="3"))  # consolidate touches the wiki
        self.edit("fun-checklist.json", lambda d: d["items"].extend(FULL_REVIEWS))  # a full review item per role
        self.commit()
        self.tool("complete")
        self.sync()
        self.tool("advance")
        self.assertEqual(self.next(), "game-plan production")
        self.edit("features.json", lambda d: d["features"].extend([
            feature("F4", "systems", measures=["FC3", "R1", "R2", "R3"]), feature("F5", "content", tier="nice"),
            feature("F6", "verdict-build", kind="human")]))
        self.commit()
        self.tool("complete")
        self.tool("advance")
        self.assertEqual(self.phase(), ("build", "systems"))

    # ---------- tests: the whole run ----------
    def test_full_run_through_the_slice_production_and_polish(self):
        self.to_production_plan()
        self.set_passes("F4")
        self.tool("advance")
        self.assertEqual(self.phase(), ("build", "verdict-build"))  # content has only a nice feature
        self.edit("state.json", lambda s: s["human_queue"].append(
            {"id": "H2", "what": "check F6 by hand", "unblocks": ["F6"]}))
        self.commit()
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict full")
        self.record_verdict("ship", {"FC2": "pending-human"})  # full and final don't wait for a person
        self.tool("advance")
        self.assertEqual(self.next(), "game-polish")
        self.edit("features.json", lambda d: d["features"].append(feature("F7", "polish")))
        self.commit()
        self.tool("complete")
        self.set_passes("F7")
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict final")
        self.record_verdict("ship")
        self.tool("advance")
        self.assertEqual(self.phase()[0], "awaiting-human")  # H2 still open
        self.edit("state.json", lambda s: s.update(human_queue=[]))
        self.commit()
        self.tool("advance")
        self.assertEqual(self.phase(), ("build", "verdict-build"))  # F6 was never marked passing
        self.set_passes("F6", evidence="human: checked by hand")
        self.tool("advance")
        self.assertEqual(self.phase()[0], "done")
        self.assertEqual(self.next(), "stop: done")

    # ---------- tests: the slice ----------
    def test_production_topics_wait_until_the_slice_ships(self):
        self.to_plan()
        self.plan()
        self.edit("topics.json", lambda d: d["topics"].append(topic("T7", priority="core", stage="production")))
        self.commit()
        self.assertTrue(self.next().startswith("game-build F1"))

    def test_the_slice_verdict_waits_for_a_person(self):
        self.to_slice_verdict()
        self.record_verdict("ship", {"FC2": "pending-human"}, complete=False)
        self.assertIn("the slice ships only after a person has played it", self.tool("complete", ok=False))

    def test_ship_needs_every_item_passing_with_evidence(self):
        self.to_core_verdict()
        self.record_verdict("ship", {"FC1": "not-assessed"}, complete=False)
        self.assertIn("FC1: not-assessed; a ship needs every item to pass", self.tool("complete", ok=False))

        def missing_file(s):
            s["verdicts"][-1]["scores"]["FC1"] = {"result": "pass", "evidence": "docs/game/playtests/nope.md"}
        self.edit("state.json", missing_file)
        self.commit()
        self.assertIn("FC1: pass needs an evidence file", self.tool("complete", ok=False))

    def test_slice_velocity_is_recorded_when_production_begins(self):
        self.to_slice_verdict()
        for _ in range(3):
            self.tool("tick", "game-build F9 \"x\"")
        self.ship_slice()
        self.assertEqual(self.load("state.json")["slice_sessions"], 3)
        self.assertIn("the slice took 3 sessions", self.tool("status"))

    def test_kill_condition_stops_for_a_human(self):
        self.to_slice_verdict()
        self.calibrate()  # taste items wait for the person's labels
        self.record_verdict("kill", {"FC2": "pending-human"})
        self.tool("advance")
        self.assertEqual(self.phase()[0], "awaiting-human")
        self.assertIn("kill condition met", self.next())
        self.edit("state.json", lambda s: s.update(stop_reason=None))
        self.commit()
        self.tool("advance")
        self.assertEqual(self.next(), "with-user: game-ideation restart docs/adr/0001-v.md")

    def test_ideation_needs_the_slice_and_a_slice_topic(self):
        self.to_ideation()
        (self.game / "vision.json").write_text(json.dumps(
            dict(VISION_JSON, directions={"count": 2, "choice": "C1"})))
        self.write_wiki([])
        self.edit("wiki.json", lambda d: d["pages"].extend(wiki_index("Vision")["pages"][:1]))
        (self.game / "topics.json").write_text(json.dumps({"topics": [
            topic(f"T{i}", stage="production") for i in range(2, 8)]}))
        self.commit()
        out = self.tool("gate", ok=False)
        for expected in ("directions: 2 compared; needs 3-5", "wiki.json has no page 'slice'", "wiki.json has no page 'concepts'", "no topic marked"):
            self.assertIn(expected, out)

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

    def test_malformed_vision_and_flagged_shapes_are_reasons_not_crashes(self):
        self.to_ideation()
        self.edit("vision.json", lambda d: d.update(pillars=["P1", "P2", "P3"], slice="x", directions=[]))
        self.write_wiki(["Vision"])
        self.edit("wiki.json", lambda d: d["pages"][0].update(flagged="T9"))
        self.commit()
        out = self.tool("gate", ok=False)
        self.assertNotIn("Traceback", out)
        self.assertIn("vision.json pillars: entry 1 is not an object", out)
        self.assertIn("vision.json slice is not an object", out)
        out = self.tool("check", ok=False)
        self.assertNotIn("Traceback", out)
        self.assertIn("vision.json directions is not an object", out)
        self.assertIn("flagged is not an object", out)

    def test_malformed_wiki_shapes_are_reasons_not_crashes(self):
        self.to_ideation()
        self.write("docs/game/wiki.json", json.dumps({"pages": [
            "vision", {"id": ["x"], "area": "Vision"}, {"id": "slice", "area": "Vision", "link": "https://d/s"}]}))
        self.edit("topics.json", lambda d: d["topics"].append(topic("T9", parent=None, pages=[["vision"]])))
        self.edit("features.json", lambda d: d["features"].append(dict(feature("F1", "core-loop"), pages=[["x"]])))
        out = self.tool("check", ok=False)
        for expected in ("wiki.json pages: entry 1 is not an object", "wiki.json pages: entry 2 has no id",
                         "page slice: missing title", "page slice: missing version", "page slice: missing updated",
                         "topic T9: pages must be a list of page ids", "F1: pages must be a list of page ids"):
            self.assertIn(expected, out)
        self.assertNotIn("Traceback", out)
        self.assertNotIn("Traceback", self.tool("status"))
        for text, expected in (("[]", "wiki.json is not an object"), ('{"pages": "x"}', "wiki.json pages is not a list")):
            self.write("docs/game/wiki.json", text)
            out = self.tool("check", ok=False) + self.tool("status") + self.tool("gate", ok=False)
            self.assertIn(expected, out)
            self.assertNotIn("Traceback", out)
        self.write("docs/game/features.json", "[]")
        out = self.tool("status", ok=False)
        self.assertIn("features.json must hold a JSON object", out)
        self.assertNotIn("Traceback", out)

    def test_blank_anti_pillars_count_as_none(self):
        self.to_ideation()
        self.edit("vision.json", lambda d: d.update(VISION_JSON, anti_pillars=["", "  "]))
        self.assertIn("vision.json has no anti-pillar", self.tool("gate", ok=False))

    def test_consolidate_gate_needs_a_page_per_area_for_the_stage(self):
        self.to_ideation()
        self.ideate()
        self.write_wiki([a for a in SLICE_AREAS if a != "Feel"])
        self.resolve("T2", "T3")
        self.sync()
        self.tool("advance")
        self.assertIn("wiki.json has no page in area 'Feel'", self.tool("gate", ok=False))

    def test_slice_consolidate_needs_a_human_item_and_production_needs_richness(self):
        self.to_ideation()
        self.ideate()
        self.write_wiki(SLICE_AREAS)
        self.resolve("T2", "T3")
        self.sync()
        self.tool("advance")
        (self.game / "fun-checklist.json").write_text(json.dumps(
            {"items": [i for i in FUN["items"] if i["id"] != "FC2"]}))
        self.commit()
        self.assertIn("no human item for the slice playtest", self.tool("gate", ok=False))

    # ---------- tests: review items ----------
    def test_slice_consolidate_needs_review_items_for_creative_art_and_feel(self):
        self.to_ideation()
        self.ideate()
        self.write_wiki(SLICE_AREAS)
        self.resolve("T2", "T3")
        self.sync()
        self.tool("advance")
        (self.game / "fun-checklist.json").write_text(json.dumps(
            {"items": [i for i in FUN["items"] if i["id"] != "FC6"]}))
        self.commit()
        self.assertIn("fun checklist has no slice review item for feel", self.tool("gate", ok=False))

    def test_review_items_need_roles_and_a_bool_taste(self):
        self.to_ideation()
        bad = {"id": "FC9", "statement": "x", "scope": "full", "kind": "review", "roles": "art", "taste": "yes"}
        self.edit("fun-checklist.json", lambda d: d["items"].append(bad))
        out = self.tool("check", ok=False)
        self.assertIn("fun FC9: roles must be a list", out)
        self.assertIn("fun FC9: taste must be true or false", out)
        self.edit("fun-checklist.json", lambda d: d["items"][-1].update(roles=[], taste=True))
        self.assertIn("fun FC9: a review item needs roles", self.tool("check", ok=False))
        self.edit("fun-checklist.json", lambda d: d["items"][-1].update(kind="vibes"))
        self.assertIn("fun FC9: kind must be one of", self.tool("check", ok=False))

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

    def test_a_review_that_is_not_independent_scores_not_assessed(self):
        self.to_slice_verdict()
        self.calibrate()
        self.record_verdict("adjust", complete=False)
        art = self.root / "docs/game/reviews/verdict-slice/art.json"
        data = json.loads(art.read_text())
        data["independent"] = False
        art.write_text(json.dumps(data))
        self.commit()
        self.assertIn("FC5: scored pass but its reviews say not-assessed", self.tool("complete", ok=False))

    def test_a_review_item_needs_a_valid_review_by_each_of_its_roles(self):
        self.to_slice_verdict()
        self.calibrate()
        self.record_verdict("adjust", complete=False)
        self.edit("state.json", lambda s: s["verdicts"][-1]["scores"]["FC6"].update(reviews=[]))
        self.commit()
        self.assertIn("FC6: needs a review by feel", self.tool("complete", ok=False))

    def test_review_items_do_not_count_toward_the_ten_item_cap(self):
        self.to_production_consolidate()
        proxies = [{"id": f"X{n}", "statement": "x", "scope": "full", "kind": "proxy",
                    "metric": "m", "threshold": "t", "how": "h"} for n in range(6)]
        self.edit("fun-checklist.json", lambda d: d["items"].extend(FULL_REVIEWS + proxies))  # 10 + 10 review
        self.edit("wiki.json", lambda d: d["pages"][0].update(version="3"))
        self.commit()
        self.assertIn("gate consolidate: PASS", self.tool("gate"))
        self.edit("fun-checklist.json", lambda d: d["items"].append(dict(proxies[0], id="X9")))
        self.assertIn("fun checklist has 11 items; keep it to 10 or fewer", self.tool("gate", ok=False))

    def test_production_consolidate_needs_a_full_review_item_per_active_role(self):
        self.to_production_consolidate()
        self.edit("fun-checklist.json", lambda d: d["items"].extend(FULL_REVIEWS))
        self.edit("fun-checklist.json", lambda d: d.update(items=[i for i in d["items"] if i["id"] != "FC8"]))
        self.assertIn("fun checklist has no full review item for audio", self.tool("gate", ok=False))

    def test_plan_gate_does_not_ask_for_a_measuring_feature_for_review_items(self):
        self.to_plan()
        self.plan()  # F1, F3 measure FC1 and FC4 only; FC5-FC7 are review items
        self.assertEqual(self.phase(), ("build", "core-loop"))

    def test_review_lint_looks_one_level_down_only(self):
        self.to_plan()
        self.write("docs/game/reviews/F1/inputs/measure.json", "[1, 2]")
        self.commit()
        self.assertNotIn("measure.json", self.tool("check"))

    def test_a_non_string_role_on_a_feature_is_a_reason_not_a_traceback(self):
        self.to_plan()
        self.plan()
        self.set_passes("F1", "F2")
        self.edit("features.json", lambda d: d["features"][0].update(roles=[["art"]]))
        self.commit()
        out = self.tool("check", ok=False)
        self.assertIn("F1: role '['art']' is not one of", out)
        self.assertNotIn("Traceback", out)

    # ---------- tests: verdict outcomes ----------
    def test_adjust_dispatches_a_replan_then_rejudges_the_core_loop(self):
        self.to_core_verdict()
        self.record_verdict("adjust")
        self.tool("advance")
        self.assertEqual(self.next(), "game-plan adjust docs/adr/0001-v.md")
        self.assertIn("cannot advance", self.tool("advance", ok=False))
        self.tool("complete")
        self.tool("advance")  # the re-plan changed nothing in core-loop
        self.assertEqual(self.next(), "game-verdict core-loop")

    def test_restart_goes_back_to_ideation_and_archives_features_and_queue(self):
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
        self.tool("advance")  # ideation -> brainstorm: nothing open for the slice, the wiki unchanged
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
        self.assertEqual(self.phase(), ("build", "slice"))
        self.set_passes("F2", value=False)
        self.assertTrue(self.next().startswith("game-build F2"))

    def test_playtest_answers_reopen_a_finished_verdict(self):
        self.to_production_plan()
        self.set_passes("F4")
        self.set_passes("F6", evidence="human: checked")
        answers = "docs/game/playtests/full/answers.md"
        self.edit("state.json", lambda s: s["human_queue"].append(
            {"id": "H3", "what": "playtest", "kind": "playtest", "scope": "full", "answers": answers}))
        self.commit()
        self.write(answers, "FC2: no")
        self.assertEqual(self.next(), "advance")
        self.tool("advance")
        self.assertEqual(self.next(), f"game-verdict full answers {answers}")

    # ---------- tests: guards ----------
    def test_edit_guard_outside_plan(self):
        self.to_plan()
        self.plan(extra=[feature("F8", "slice")])

        def tamper(d):
            fs = {f["id"]: f for f in d["features"]}
            fs["F2"]["acceptance"] = ["easier"]
            fs["F3"]["milestone"] = "core-loop"
            fs["F8"]["tier"] = "nice"
            d["features"].remove(fs["F1"])
        self.edit("features.json", tamper)
        self.edit("fun-checklist.json", lambda d: d["items"][0].update(threshold=">= 0"))
        self.edit("richness.json", lambda d: d["targets"].pop())
        out = self.tool("check", ok=False)
        for expected in ("F1: removed", "F2: acceptance changed", "F3: milestone changed",
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

    def test_kept_values_stay_kept_unless_an_adr_changes_the_pin(self):
        self.to_plan()
        self.plan()
        self.write("knobs/player.json", json.dumps({"dash": {"speed": 14}}))
        self.write("knobs/arena.toml", "hazard_rate = 0.3\n")
        self.edit("keep.json", lambda d: d["keep"].append(
            {"id": "K1", "what": "dash feels snappy", "source": ANSWERS,
             "pins": [{"file": "knobs/player.json", "key": "dash.speed", "value": 14},
                      {"file": "knobs/arena.toml", "key": "hazard_rate", "value": 0.3}]}))
        self.commit()
        self.assertIn("check: ok", self.tool("check"))
        self.write("knobs/player.json", json.dumps({"dash": {"speed": 16}}))
        self.assertIn("K1: knobs/player.json dash.speed is 16, kept at 14", self.tool("check", ok=False))
        self.edit("keep.json", lambda d: d["keep"][0]["pins"][0].update(value=16))
        self.assertIn("K1: pins changed without a new ADR", self.tool("check", ok=False))
        self.write("docs/adr/0002-faster-dash.md", "playtest 2 asked for a faster dash")
        self.edit("keep.json", lambda d: d["keep"][0].update(adr="docs/adr/0002-faster-dash.md"))
        self.assertIn("check: ok", self.tool("check"))

    def test_resolved_topics_need_a_page(self):
        self.to_ideation()
        self.ideate()
        self.edit("topics.json", lambda d: d["topics"][1].update(status="resolved", resolution="x", pages=[]))
        self.assertIn("topic T2: resolved without a wiki page", self.tool("check", ok=False))

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

    # ---------- tests: flow control ----------
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

    def test_nice_features_are_built_when_the_budget_allows(self):
        self.to_plan()
        self.plan(extra=[feature("F8", "core-loop", tier="nice")])
        self.set_passes("F1", "F2")
        self.assertTrue(self.next().startswith("game-build F8"))
        self.edit("state.json", lambda s: s["limits"].update(budget_sessions=12))
        self.assertEqual(self.next(), "advance")

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

    def test_changed_pages_or_own_calls_resync_the_gdd_before_the_next_milestone(self):
        self.to_plan()
        self.plan()
        (self.game / "own-calls.md").write_text("| today | F1 | dash has a 0.2 s cooldown | mechanics |\n")
        self.set_passes("F1", "F2")
        self.sync()
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict core-loop")

    def test_gdd_goes_stale_when_a_page_entry_or_own_call_changes(self):
        self.to_plan()
        self.plan()
        self.set_passes("F1", "F2")  # the milestone is done, so the next step is advance unless the GDD is stale
        self.sync_if_stale()
        self.assertIn("human GDD: in sync", self.tool("status"))
        self.assertEqual(self.next(), "advance")
        self.edit("features.json", lambda d: d["features"][0].update(notes="touched"))  # not a GDD source
        self.commit()
        self.assertIn("human GDD: in sync", self.tool("status"))
        self.assertEqual(self.next(), "advance")
        self.edit("wiki.json", lambda d: d["pages"][1].update(version="2", updated="dash cooldown added"))
        self.commit()
        self.assertIn("human GDD: stale", self.tool("status"))
        self.assertEqual(self.next(), "game-gdd")
        self.sync()
        self.assertIn("human GDD: in sync", self.tool("status"))
        self.write("docs/game/own-calls.md", "| today | F1 | dash has a 0.2 s cooldown | mechanics |\n")
        self.commit()
        self.assertIn("human GDD: stale", self.tool("status"))
        self.assertEqual(self.next(), "game-gdd")
        self.sync()
        self.assertIn("human GDD: in sync", self.tool("status"))

    def sync_if_stale(self):
        if "human GDD: stale" in self.tool("status"):
            self.sync()

    def test_the_gdd_is_never_stale_while_the_index_has_no_pages(self):
        self.to_ideation()  # init wrote an empty wiki.json, and the GDD was never synced
        self.assertIn("human GDD: in sync", self.tool("status"))
        self.write("docs/game/own-calls.md", "| today | F1 | a call |\n")
        self.write("docs/game/wiki.json", json.dumps({"pages": []}))
        self.commit()
        self.assertIn("human GDD: in sync", self.tool("status"))

    def test_brainstorm_share_lets_support_topics_wait_until_consolidate_defers_them(self):
        self.to_ideation()
        self.ideate()
        self.edit("state.json", lambda s: s["limits"].update(budget_sessions=10))
        self.commit()
        for _ in range(2):
            self.tool("tick", "game-brainstorm T9 \"x\"")
        self.assertTrue(self.next().startswith("with-user: game-brainstorm T2"))  # core topics still run
        self.write_wiki(SLICE_AREAS)
        self.resolve("T2")
        self.sync()
        self.tool("advance")  # support topic T3 waits: the brainstorm share is spent
        self.assertEqual(self.next(), "game-consolidate")
        (self.game / "fun-checklist.json").write_text(json.dumps(FUN))
        self.commit()
        self.assertIn("topic T3: open (support)", self.tool("complete", ok=False))
        self.edit("topics.json", lambda d: [t.update(status="deferred", resolution="after the slice")
                                            for t in d["topics"] if t["id"] == "T3"])
        self.commit()
        self.tool("complete")

    def test_upgrade_resets_an_old_game_still_at_setup(self):
        self.tool("init")
        kept = {"limits": dict(self.load("state.json")["limits"], budget_sessions=80),
                "counters": {"sessions": 4, "brainstorm_sessions": 0, "adjusts": 0, "restarts": 0},
                "human_queue": [{"id": "H1", "what": "make a ClickUp space"}], "adapter_verified": True}
        self.edit("state.json", lambda s: (s.pop("stage"), s.update(version=3, phase="setup", task=None, **kept)))
        self.edit("features.json", lambda d: d.update(milestones=["core-loop", "systems", "content", "verdict-build",
                                                                  "polish"]))
        (self.game / "vision.json").unlink()
        self.commit()
        out = self.tool("upgrade")
        self.assertIn("version 3 -> 6", out)
        s = self.load("state.json")
        self.assertEqual((s["version"], s["phase"], s["task"], s["stage"]), (6, "setup", "game-setup upgrade", "slice"))
        self.assertEqual({k: s[k] for k in kept}, kept)
        self.assertEqual(self.load("features.json")["milestones"], MILESTONES)
        self.assertTrue((self.game / "vision.json").exists())
        self.assertTrue(self.clean(), self.git("status", "--porcelain"))
        self.assertEqual(self.next(), "with-user: game-setup upgrade")
        self.assertIn("already at version 6", self.tool("upgrade"))

    def test_upgrade_brings_eve_like_brawl_up_to_date(self):
        """The real 0.3.0 game: the plugin's tool upgrades it before its old copy is replaced."""
        self.write("docs/game/state.json", EVE_STATE)
        self.write("docs/game/features.json", EVE_FEATURES)
        self.write("docs/game/fun-checklist.json", '{\n  "items": []\n}\n')
        self.write("docs/game/richness.json", '{\n  "targets": []\n}\n')
        self.write("docs/game/gamestate.py", "# the 0.3.0 tool\n")
        self.write("docs/agents/game.md", "# Game workflow\n")
        self.commit()
        self.assertEqual(self.plugin("status").split("next: ", 1)[1].strip(), "with-user: game-setup upgrade")
        self.assertIn("to do 'game-setup upgrade' together", self.plugin("status", "--no-user"))
        self.assertIn("version 3 -> 6", self.plugin("upgrade"))
        s, old = self.load("state.json"), json.loads(EVE_STATE)
        self.assertEqual((s["version"], s["phase"], s["task"]), (6, "setup", "game-setup upgrade"))
        self.assertEqual(s["human_queue"], old["human_queue"])
        self.assertEqual(s["adapter_verified"], old["adapter_verified"])
        self.assertEqual({k: s["limits"][k] for k in old["limits"]}, old["limits"])
        self.assertEqual({k: s["counters"][k] for k in old["counters"]}, old["counters"])
        self.assertEqual(self.load("features.json")["milestones"], MILESTONES)
        self.assertTrue(self.clean(), self.git("status", "--porcelain"))
        self.assertEqual(self.plugin("status").split("next: ", 1)[1].strip(), "with-user: game-setup upgrade")
        self.edit("features.json", lambda d: d["features"].append(feature("F1", "slice")))
        self.assertNotIn("milestone 'slice' is not in features.milestones", self.plugin("check", ok=False))

    def test_upgrade_needs_game_state_and_never_downgrades(self):
        out = self.tool("upgrade", ok=False)
        self.assertIn("no game state", out)
        self.assertIn("init", out)
        self.assertFalse((self.game / "state.json").exists())
        self.tool("init")
        self.edit("state.json", lambda s: s.update(version=7))
        self.commit()
        before = (self.game / "state.json").read_text()
        self.assertIn("version 7, newer than this tool (6)", self.tool("upgrade", ok=False))
        self.assertEqual((self.game / "state.json").read_text(), before)
        self.assertTrue(self.clean())
        self.edit("state.json", lambda s: s.update(version="3"))
        self.commit()
        out = self.tool("upgrade", ok=False)
        self.assertNotIn("Traceback", out)
        self.assertIn("version '3' is not a whole number", out)
        out = self.tool("status")
        self.assertNotIn("Traceback", out)
        self.assertIn("next: fix: state.json version '3' is not a whole number", out)

    def test_setup_and_ideation_without_a_task_are_conversations(self):
        self.tool("init")
        self.edit("state.json", lambda s: s.update(task=None))
        self.commit()
        self.assertEqual(self.next(), "with-user: game-setup")
        self.assertIn("to do 'game-setup' together", self.next("--no-user"))
        self.edit("state.json", lambda s: s.update(version=3))
        self.commit()
        self.assertEqual(self.next(), "with-user: game-setup upgrade")
        self.assertIn("stop: waiting for a person", self.next("--no-user"))
        self.assertIn("to do 'game-setup upgrade' together", self.next("--no-user"))
        self.edit("state.json", lambda s: s.update(version=6))
        (self.root / "docs" / "agents" / "game.md").write_text("# Game workflow\n")
        (self.root / "docs" / "agents" / "docs.md").write_text("# Docs\n")
        self.edit("state.json", lambda s: s.update(docs_verified={"place": "ClickUp doc", "date": "2026-11-22"}))
        self.commit()
        self.tool("advance")
        self.edit("state.json", lambda s: s.update(task=None))
        self.commit()
        self.assertEqual(self.next(), "with-user: game-ideation")
        self.assertIn("to do 'game-ideation' together", self.next("--no-user"))

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


class Loop(unittest.TestCase):
    """skills/game-next/scripts/loop.sh, driving a stand-in state tool and agent."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "docs" / "game").mkdir(parents=True)
        (self.root / "docs" / "game" / "gamestate.py").write_text('print("next: game-build F1")\n')
        (self.root / "agent.py").write_text(
            "import sys\nfrom pathlib import Path\n"
            "with open('calls.txt', 'a') as f:\n    f.write(sys.argv[-1] + '\\n')\n"
            "print(Path('says.txt').read_text())\n")
        self.state(version=CURRENT_VERSION, phase="build")

    def tearDown(self):
        shutil.rmtree(self.root)

    def state(self, **fields):
        (self.root / "docs" / "game" / "state.json").write_text(json.dumps(fields))

    def loop(self, says="built F1", sessions="3"):
        (self.root / "says.txt").write_text(says)
        (self.root / "calls.txt").unlink(missing_ok=True)
        r = subprocess.run(["bash", str(LOOP), sessions], cwd=self.root, capture_output=True, text=True,
                           env=dict(os.environ, AGENT_CMD=f"{sys.executable} agent.py"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        calls = self.root / "calls.txt"
        return r.stdout, len(calls.read_text().splitlines()) if calls.exists() else 0

    def test_runs_one_unattended_session_per_step_up_to_the_limit(self):
        out, calls = self.loop()
        self.assertEqual(calls, 3)
        self.assertIn("built F1", out)
        self.assertIn("reached 3 sessions", out)

    def test_stops_when_the_session_reports_a_stop(self):
        out, calls = self.loop("could not read the home page\nstop: ClickUp docs unreachable\n")
        self.assertEqual(calls, 1)
        self.assertIn("could not read the home page", out)  # the user still sees the session's report
        self.assertIn("loop: stop: ClickUp docs unreachable", out)

    def test_an_older_or_newer_game_stops_before_any_session(self):
        for fields, expected in (({"version": 3, "phase": "setup"}, "game-setup upgrade"),
                                 ({"phase": "setup"}, "version 1"),
                                 ({"version": 3, "phase": "build"}, f"version 3 and the plugin at {CURRENT_VERSION}"),
                                 ({"version": CURRENT_VERSION + 1, "phase": "build"}, "newer than the plugin")):
            with self.subTest(**fields):
                self.state(**fields)
                out, calls = self.loop()
                self.assertEqual(calls, 0)
                self.assertIn("loop: stop: ", out)
                self.assertIn(expected, out)


class Templates(unittest.TestCase):
    """The skills' templates must produce files the gates accept."""

    def test_index_template_has_a_section_per_area(self):
        template = (SCRIPT.parents[2] / "game-ideation" / "index-template.md").read_text().splitlines()
        self.assertEqual([a for a in AREAS if f"## {a}" not in template], [])


if __name__ == "__main__":
    unittest.main()
