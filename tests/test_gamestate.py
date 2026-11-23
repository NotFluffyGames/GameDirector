"""End-to-end tests for skills/game-setup/scripts/gamestate.py.

GameRun drives the tool in-process against a MemoryHistory, so a game run makes no git calls and no commits.

Run: python3 -m unittest discover tests
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from memory_history import MemoryHistory, isolated_git_env

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "game-setup" / "scripts" / "gamestate.py"
LOOP = Path(__file__).resolve().parents[1] / "skills" / "game-next" / "scripts" / "loop.sh"
CURRENT_VERSION = int(re.search(r"^CURRENT_VERSION = (\d+)$", SCRIPT.read_text(), re.M).group(1))


def load_gamestate():
    spec = importlib.util.spec_from_file_location("gamestate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gamestate = load_gamestate()


VISION_JSON = {
    "pillars": [{"id": "P1", "statement": "fast"}, {"id": "P2", "statement": "tense"},
                {"id": "P3", "statement": "readable"}],
    "anti_pillars": ["no grinding"],
    "kill_condition": "nobody wants a second match",
    "slice": {"test_question": "is one match fun?",
              "quality_bar": {"code": "production", "feel": "representative", "art": "representative",
                              "audio": "representative", "ui": "representative", "onboarding": "representative"}},
    "directions": {"count": 4, "choice": "C2"},
    "north_stars": {
        "creative": {"statement": "a duel you retell", "references": ["Samurai Gunn", "Towerfall"],
                     "genre_default": "arena brawler", "departure": "ink-wash duels"},
        "design": {"statement": "every round teaches", "references": ["Smash", "Rivals of Aether"]},
        "feel": {"statement": "hits land with weight", "references": ["Hades", "Celeste"],
                 "actions": {"dash": {"words": ["snappy"], "references": ["Celeste dash"]}}},
        "art": {"statement": "ink on paper", "references": ["Okami", "Sumi-e"], "directions": 3, "choice": "A2"},
        "audio": {"statement": "taiko drives the match", "references": ["Ghost of Tsushima", "Katana Zero"]},
        "narrative": {"statement": "a rivalry in few words", "references": ["Hades", "Bastion"]},
        "ux": {"statement": "one glance, one button", "references": ["Celeste menus", "Dead Cells"]},
    },
    "invariants": ["the ink-wash palette", "one-button dash"],
    "roles_off": {},
}

AREAS = ["Vision", "Mechanics", "Controls", "Systems", "Content", "Modes and sessions",
         "Screens and onboarding", "Feel", "Art", "Audio", "Narrative and world"]
SLICE_AREAS = [a for a in AREAS if a != "Modes and sessions"]
PAGE_IDS = {"Vision": ["vision", "slice", "concepts"], "Mechanics": ["mechanics"], "Controls": ["controls"],
            "Systems": ["weapons"], "Content": ["content"], "Modes and sessions": ["modes"],
            "Screens and onboarding": ["screens"], "Feel": ["feel"],
            "Art": ["art"], "Audio": ["audio"], "Narrative and world": ["tone"]}


ROLES = ["creative", "design", "feel", "art", "audio", "narrative", "ux"]
IMAGE_ROLES = ["art", "ux", "feel"]
RESEARCH_PAGES = ["landscape", "research"]  # the research skill's pages, both in area Vision
REFS = "research/references.json"
HOMEWORK = "research/homework.json"
SOURCES = {"checked": "2026-11-23", "reachable": [], "unreachable": []}
HOMEWORK_WAIT = ("stop: waiting for research homework: a person answers or skips each open item in "
                 "docs/game/research/homework.json (or the homework page), then run /game-next")


def page(pid, area="Vision"):
    return {"id": pid, "title": pid.title(), "area": area, "link": f"https://docs.example/{pid}",
            "version": "1", "updated": "x"}


def wiki_index(*areas):
    return {"pages": [page(i, a) for a in areas for i in PAGE_IDS[a]]}


def ref(rid, title, why="aspect", roles=("art",), status="candidate"):
    return {"id": rid, "title": title, "why": why, "roles": list(roles),
            "sources": [f"https://store.example/{rid}"], "status": status, "how_studied": {}}


COMPS = [ref("R1", "Towerfall", "comp", ("design", "feel", "art")),
         ref("R2", "Samurai Gunn", "comp", ("creative", "design", "feel")),
         ref("R3", "Nidhogg", "comp", ("creative", "ux"))]


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
    topic("T6", priority="later", stage="production"),
    topic("T7", roles=("feel",)), topic("T8", roles=("art",)), topic("T9", roles=("audio",)),
    topic("T10", roles=("narrative",)), topic("T11", roles=("ux",))]}

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
CALIBRATE = {"id": "H0", "what": "label the calibration kit", "kind": "calibrate",
             "how": "docs/game/calibration/kit.md", "answers": "docs/game/calibration/labels.json"}
PICKS = "docs/game/playtests/evidence/F8/compare/picks.md"
COMPARE = {"id": "H5", "what": "pick F8's grade", "kind": "compare",
           "how": "docs/game/playtests/evidence/F8/compare/index.md", "answers": PICKS, "unblocks": ["F8"]}
CALIBRATION_WAIT = ("stop: waiting for calibration: a person labels the kit (docs/game/calibration/kit.md) into "
                    "docs/game/calibration/labels.json; then run /game-next")
PICKS_WAIT = ("stop: waiting for A/B picks: a person picks from the kit "
              "(docs/game/playtests/evidence/F8/compare/index.md) into " + PICKS
              + ", leaving the queue entry; then run /game-next")

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


def feature(fid, milestone, tier="must", kind="test", measures=(), roles=(), target=None):
    f = {"id": fid, "title": f"feature {fid}", "pillar": "P1", "tier": tier, "milestone": milestone,
            "acceptance": ["it works"], "verify": {"kind": kind, "how": "run the test"},
            "measures": list(measures), "tickets": [f"#{fid}"], "pages": ["mechanics"],
            "roles": list(roles), "passes": False, "evidence": "", "blocked": ""}
    if target:
        f["target"] = target
    return f


class GameRun(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.game = self.root / "docs" / "game"
        self.game.mkdir(parents=True)
        (self.root / "docs" / "agents").mkdir()
        self.history = MemoryHistory(self.root)  # the game's git history

    def tearDown(self):
        shutil.rmtree(self.root)

    # ---------- helpers ----------
    def head(self):
        return self.history.rev_parse("HEAD")

    def commit(self):
        self.history.commit_all("work")

    def tool(self, *args, ok=True):
        """The state tool run on this game in-process: its stdout then stderr, and its exit code checked against ok."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = gamestate.main([*args, "--root", str(self.root)], history=self.history)
            except SystemExit as e:
                code = e.code
        if isinstance(code, str):  # sys.exit("error: ...") prints the message and exits 1
            err.write(code + "\n")
            code = 1
        output = out.getvalue() + err.getvalue()
        if ok:
            self.assertEqual(code or 0, 0, output)
        else:
            self.assertNotEqual(code or 0, 0, output)
        return output

    def plugin(self, *args, ok=True):
        """The plugin's own copy of the tool, run against this game (as game-next and upgrade do); in-process, tool()."""
        return self.tool(*args, ok=ok)

    def clean(self):
        return self.history.clean()

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
            commit = self.head()
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
        """Index the pages of these areas; the research pages already indexed stay."""
        kept = [p for p in self.load("wiki.json")["pages"] if p["id"] in RESEARCH_PAGES]
        self.write("docs/game/wiki.json", json.dumps({"pages": wiki_index(*areas)["pages"] + kept}))

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
    def agent_docs(self):
        (self.root / "docs" / "agents" / "game.md").write_text("# Game workflow\n")
        (self.root / "docs" / "agents" / "docs.md").write_text("# Docs\n")

    def to_scan(self):
        self.tool("init")
        self.agent_docs()
        self.edit("state.json", lambda s: s.update(docs_verified={"place": "ClickUp doc", "date": "2026-11-22"},
                                                   intent="sell", research_sources=SOURCES))
        self.commit()
        self.assertEqual(self.next(), "with-user: game-setup")
        self.tool("complete")
        self.tool("advance")
        self.assertEqual(self.next(), "game-research scan")

    def scan(self, refs=COMPS):
        """The landscape scan: the landscape page and the comps as candidate references."""
        self.edit("wiki.json", lambda d: d["pages"].append(page("landscape")))
        self.write("docs/game/" + REFS, json.dumps({"scanned_for": None, "refs": list(refs)}))
        self.commit()
        self.tool("complete")

    def to_ideation(self):
        self.to_scan()
        self.scan()
        self.sync()
        self.tool("advance")
        self.assertEqual(self.next(), "with-user: game-ideation")

    def test_setup_waits_for_a_verified_docs_place(self):
        self.tool("init")
        self.agent_docs()
        self.commit()
        self.assertEqual(self.next(), "with-user: game-setup")
        self.assertIn("docs not verified", self.tool("complete", ok=False))
        self.assertIn("stop: waiting for a person", self.next("--no-user"))
        self.edit("state.json", lambda s: s.update(docs_verified={"place": "ClickUp doc", "date": "2026-11-22"},
                                                   intent="sell", research_sources=SOURCES))
        self.commit()
        self.tool("complete")

    def open_references(self):
        """Ideation's pick: the comps are studied, plus one aspect reference per role they leave out."""
        def fn(d):
            for r in d["refs"]:
                if r["why"] == "comp":
                    r["status"] = "open"
            covered = {role for r in d["refs"] if r["status"] == "open" for role in r["roles"]}
            n = len(d["refs"])
            for role in ROLES:
                if role not in covered:
                    n += 1
                    d["refs"].append(ref(f"R{n}", f"the {role} reference", roles=(role,), status="open"))
        self.edit(REFS, fn)

    def ideate(self):
        (self.game / "vision.json").write_text(json.dumps(VISION_JSON))
        self.write_wiki(["Vision"])
        (self.game / "topics.json").write_text(json.dumps(SEED_TOPICS))
        self.open_references()
        self.commit()
        self.tool("complete")
        self.sync()
        self.tool("advance")
        self.assertEqual(self.phase(), ("research", None))

    def write_audit(self, rid, notes=()):
        notes = list(notes)
        self.write(f"docs/game/research/refs/{rid}/audit.json", json.dumps(
            {"role": "creative", "target": rid, "commit": self.head(), "independent": True,
             "inputs": [], "result": "notes" if notes else "ok", "reason": "", "notes": notes}))

    def study(self, rid):
        """One game-research ref session: a dossier per role, an image per image role, sources and an audit."""
        base = f"docs/game/research/refs/{rid}"

        def fn(d):
            r = next(r for r in d["refs"] if r["id"] == rid)
            for role in r["roles"]:
                self.write(f"{base}/{role}.md", f"# {r['title']}: {role}\n")
                if role in IMAGE_ROLES:
                    self.write(f"{base}/{role}/shot-1.png", "png")
            r.update(status="studied", sources=[f"https://store.example/{rid}/{n}" for n in range(3)],
                     how_studied={role: {"how": "read", "reason": ""} for role in r["roles"]})
        self.edit(REFS, fn)
        self.write_audit(rid)
        self.commit()

    def brief(self):
        """game-research brief: the research page and the homework list."""
        self.edit("wiki.json", lambda d: d["pages"].append(page("research")))
        self.write("docs/game/" + HOMEWORK, json.dumps({"reason": "", "items": [
            {"id": "H1", "what": "play R1 for 20 minutes", "why": "the feel north star",
             "questions": ["does the dash read at a glance?"], "minutes": 20, "roles": ["feel"],
             "status": "answered", "answer": "yes, from the trail"}]}))
        self.commit()

    def research(self):
        for r in self.load(REFS)["refs"]:
            if r["status"] == "open":
                self.study(r["id"])
        self.brief()
        self.tool("complete")

    def to_brainstorm(self):
        self.to_ideation()
        self.ideate()
        self.research()
        self.sync()
        self.tool("advance")
        self.assertEqual(self.phase(), ("brainstorm", None))

    def to_plan(self):
        self.to_brainstorm()
        self.assertTrue(self.next().startswith("with-user: game-brainstorm T2"))  # core before support
        self.write_wiki(SLICE_AREAS)
        self.resolve("T2", "T3", "T7", "T8", "T9", "T10", "T11")  # the slice's topics; T4-T6 wait for production
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
        base = self.head()
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
        old = self.head()
        self.commit()
        base = self.head()
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

    def test_slice_plan_needs_a_visual_target_and_a_feel_target(self):
        self.to_plan()
        self.edit("features.json", lambda d: d.update(features=[
            feature("F1", "core-loop", measures=["FC1"]), feature("F3", "slice", measures=["FC4"])]))
        self.edit("state.json", lambda s: s.update(adapter_verified=True))
        self.commit()
        out = self.tool("complete", ok=False)
        self.assertIn("no must feature with target visual in milestone slice", out)
        self.assertIn("no must feature with target feel in milestone core-loop", out)
        self.edit("vision.json", lambda v: v.update(roles_off={"art": "text game"}))
        self.commit()
        out = self.tool("complete", ok=False)
        self.assertNotIn("target visual", out)
        self.assertIn("no must feature with target feel in milestone core-loop", out)

    def test_a_feature_target_must_be_known(self):
        self.to_plan()
        self.plan()
        self.edit("features.json", lambda d: d["features"][0].update(target="shiny"))
        self.assertIn("F1: target must be one of ['visual', 'feel']", self.tool("check", ok=False))

    def test_a_passing_visual_target_queues_calibration(self):
        self.to_plan()
        self.plan()
        self.write_review("F5", "art", "HEAD")
        self.set_passes("F5")
        self.assertIn("the visual target passes: queue a calibrate entry for a person (kind calibrate)",
                      self.tool("check", ok=False))
        self.edit("state.json", lambda s: s["human_queue"].append(CALIBRATE))
        self.commit()
        self.tool("check")

    def test_labels_end_the_calibration_demand(self):
        self.to_plan()
        self.plan()
        self.write_review("F5", "art", "HEAD")
        self.set_passes("F5")
        self.calibrate()
        self.tool("check")

    def test_the_slice_verdict_waits_for_calibration(self):
        self.to_slice_verdict()
        self.assertEqual(self.next(), "stop: waiting for calibration: a person labels the kit "
                                      "(docs/game/calibration/kit.md) into docs/game/calibration/labels.json; "
                                      "then run /game-next")
        self.calibrate()
        self.assertEqual(self.next(), "game-verdict slice")
        self.record_verdict("ship")
        self.assertEqual(self.load("state.json")["human_queue"], [])  # the labelled calibrate entry was consumed

    def test_queue_entries_of_known_kinds_are_complete(self):
        self.to_plan()
        self.edit("state.json", lambda s: s["human_queue"].extend([
            {"id": "H1", "what": "label", "kind": "calibrate"},
            {"id": "H2", "what": "compare", "kind": "compare", "how": "kit.md", "answers": "a.md"}]))
        self.commit()
        out = self.tool("check", ok=False)
        self.assertIn("human_queue H1: a calibrate entry needs how and answers", out)
        self.assertIn("human_queue H2: a compare entry needs how, answers and unblocks", out)
        self.edit("state.json", lambda s: s["human_queue"].__setitem__(1, dict(s["human_queue"][1], unblocks=["F1"])))
        self.assertNotIn("H2", self.tool("check", ok=False))

    def test_labels_file_shape_is_checked(self):
        self.to_plan()
        for text, why in (("[]", "calibration labels: must be an object with a labels list"),
                          ('{"labels": [{"ours": "yes"}]}', "calibration labels: entry 0 needs a capture"),
                          ('{"labels": [{"capture": "x.png", "ours": "yes", "why": "palette"}]}',
                           "calibration labels: entry 0 needs ours true or false"),
                          ('{"labels": [{"capture": "x.png", "ours": true, "why": ""}]}',
                           "calibration labels: entry 0 needs a why"),
                          ("not json", "calibration labels: not valid JSON")):
            self.write("docs/game/calibration/labels.json", text)
            self.commit()
            self.assertIn(why, self.tool("check", ok=False))

    def test_upgrade_brings_a_version_6_game_at_setup_to_7(self):
        self.tool("init")
        self.edit("state.json", lambda s: s.update(version=6, phase="setup", task=None))
        self.commit()
        s = self.load("state.json")
        self.assertEqual(s["version"], 6)
        self.assertIn("version 6 -> 7", self.tool("upgrade"))
        s = self.load("state.json")
        self.assertEqual((s["version"], s["phase"], s["task"]), (7, "setup", "game-setup upgrade"))
        self.assertIsNone(s["intent"])
        self.assertIsNone(s["research_sources"])

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
        self.to_brainstorm()
        self.edit("vision.json", lambda v: v.update(roles_off={"audio": "muted"}))
        self.edit("topics.json", lambda d: d.update(topics=[t for t in d["topics"] if t["id"] != "T9"]))
        self.write_wiki([a for a in SLICE_AREAS if a != "Audio"])
        self.resolve("T2", "T3", "T7", "T8", "T10", "T11")
        self.sync()
        self.tool("advance")
        self.assertEqual(self.next(), "game-consolidate")
        self.assertNotIn("area 'Audio'", self.tool("complete", ok=False))

    def plan(self, extra=()):
        self.edit("features.json", lambda d: d.update(features=[
            feature("F1", "core-loop", measures=["FC1"], target="feel"), feature("F2", "core-loop"),
            feature("F3", "slice", measures=["FC4"]),
            feature("F5", "slice", kind="capture", roles=("art",), target="visual"), *extra]))
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
        self.write_review("F5", "art", "HEAD")
        self.edit("state.json", lambda s: s["human_queue"].append(CALIBRATE))  # the visual target passes
        self.set_passes("F3", "F5")
        self.tool("advance")
        self.assertEqual(self.load("state.json")["phase"], "verdict")

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
            feature("F4", "systems", measures=["FC3", "R1", "R2", "R3"]), feature("F6", "content", tier="nice"),
            feature("F7", "verdict-build", kind="human")]))
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
            {"id": "H2", "what": "check F7 by hand", "unblocks": ["F7"]}))
        self.commit()
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict full")
        self.record_verdict("ship", {"FC2": "pending-human"})  # full and final don't wait for a person
        self.tool("advance")
        self.assertEqual(self.next(), "game-polish")
        self.edit("features.json", lambda d: d["features"].append(feature("F8", "polish")))
        self.commit()
        self.tool("complete")
        self.set_passes("F8")
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict final")
        self.record_verdict("ship")
        self.tool("advance")
        self.assertEqual(self.phase()[0], "awaiting-human")  # H2 still open
        self.edit("state.json", lambda s: s.update(human_queue=[]))
        self.commit()
        self.tool("advance")
        self.assertEqual(self.phase(), ("build", "verdict-build"))  # F7 was never marked passing
        self.set_passes("F7", evidence="human: checked by hand")
        self.tool("advance")
        self.assertEqual(self.phase()[0], "done")
        self.assertEqual(self.next(), "stop: done")

    def test_the_games_copy_runs_as_a_program_and_finds_its_game(self):
        """game-next runs docs/game/gamestate.py with no --root; init makes no git calls."""
        shutil.copy(SCRIPT, self.game / "gamestate.py")
        r = subprocess.run([sys.executable, str(self.game / "gamestate.py"), "init"], cwd=self.root / "docs" / "agents",
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.game / "state.json").is_file())

    def test_game_runs_never_call_git(self):
        real_run = subprocess.run

        def run(args, *rest, **kwargs):
            program = args if isinstance(args, (str, bytes, os.PathLike)) else args[0]
            self.assertNotEqual(Path(os.fsdecode(program).split()[0]).name, "git", f"a game run called {args}")
            return real_run(args, *rest, **kwargs)
        with mock.patch("subprocess.run", run):
            self.test_full_run_through_the_slice_production_and_polish()

    # ---------- tests: polish ----------
    def to_full_verdict(self, polish=()):
        """The full verdict shipped; polish holds the polish-milestone features review decisions added before it."""
        self.to_production_plan()
        self.edit("features.json", lambda d: d["features"].extend(polish))
        self.set_passes("F4")
        self.set_passes("F7", evidence="human: checked by hand")
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict full")
        self.record_verdict("ship", {"FC2": "pending-human"})
        self.tool("advance")

    def to_polish(self):
        """game-polish planned F8 (a taste call, verified by A/B picks) and F9."""
        self.to_full_verdict()
        self.assertEqual(self.next(), "game-polish")
        self.edit("features.json", lambda d: d["features"].extend(
            [feature("F8", "polish", kind="human"), feature("F9", "polish")]))
        self.commit()
        self.tool("complete")

    def queue_picks(self):
        self.edit("state.json", lambda s: s["human_queue"].append(COMPARE))  # F8's first session made its kit
        self.commit()

    def test_polish_is_planned_even_when_reviews_already_added_polish_features(self):
        self.to_full_verdict(polish=[feature("F10", "polish", tier="nice")])  # a review note decided `feature`
        self.assertEqual(self.phase(), ("polish", "polish"))
        self.assertEqual(self.load("state.json")["task"], "game-polish")
        self.assertEqual(self.next(), "game-polish")
        self.assertIn("polish not planned yet (game-polish)", self.tool("status"))
        self.assertIn("no must polish features yet", self.tool("complete", ok=False))  # F10 is a review's, and nice
        self.edit("features.json", lambda d: d["features"].append(feature("F8", "polish")))
        self.commit()
        self.tool("complete")
        self.assertTrue(self.load("state.json")["polish_planned"])
        self.set_passes("F8", "F10")
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict final")

    def test_a_restart_clears_the_polish_plan(self):
        self.to_core_verdict()
        self.edit("state.json", lambda s: s.update(polish_planned=True))
        self.commit()
        self.record_verdict("restart")
        self.tool("advance")
        self.assertFalse(self.load("state.json")["polish_planned"])

    def test_answered_picks_are_applied_by_a_build_session_in_polish(self):
        self.to_polish()
        self.queue_picks()
        self.assertTrue(self.next().startswith("game-build F9"))  # the run moves past the feature awaiting picks
        self.write(PICKS, "pair 1: after (the warmer grade)")
        self.commit()
        step = f'game-build F8 "feature F8" picks {PICKS}'
        self.assertEqual(self.next(), step)
        self.assertEqual(self.next("--no-user"), step)

    def test_the_run_stops_for_picks_instead_of_entering_final(self):
        self.to_polish()
        self.queue_picks()
        self.set_passes("F9")  # every polish feature passes or waits for its picks
        self.assertEqual(self.next(), PICKS_WAIT)
        self.assertEqual(self.next("--no-user"), PICKS_WAIT)
        self.assertIn("cannot advance", self.tool("advance", ok=False))
        self.assertEqual(self.phase(), ("polish", "polish"))
        self.write(PICKS, "pair 1: after (the warmer grade)")
        self.commit()
        self.assertEqual(self.next(), f'game-build F8 "feature F8" picks {PICKS}')
        self.edit("state.json", lambda s: s.update(human_queue=[]))  # the picks session: applied, entry removed
        self.set_passes("F8", evidence=f"human: picks in {PICKS}")
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict final")

    def test_picks_that_keep_failing_go_to_unblock(self):
        self.to_polish()
        self.queue_picks()
        self.write(PICKS, "pair 1: after")
        self.edit("state.json", lambda s: s["attempts"].update(F8=3))
        self.commit()
        self.assertEqual(self.next(), "game-plan unblock F8")
        self.edit("state.json", lambda s: s.update(human_queue=[  # unblock hands it over: a plain entry replaces it
            {"id": "H6", "what": "apply F8's picks by hand", "unblocks": ["F8"]}]))
        self.commit()
        self.assertEqual(self.next(), 'game-build F9 "feature F9"')
        self.set_passes("F9")
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict final")

    def test_picks_queued_during_the_final_verdict_hold_it(self):
        self.to_polish()
        self.set_passes("F9")
        self.set_passes("F8", evidence="human: picked")
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict final")
        self.set_passes("F8", value=False)  # a regression, rebuilt during the verdict: its kit waits for picks
        self.queue_picks()
        self.assertEqual(self.next(), PICKS_WAIT)  # the final verdict never ships with picks pending
        self.assertEqual(self.next("--no-user"), PICKS_WAIT)
        self.write(PICKS, "pair 1: before")
        self.commit()
        self.assertEqual(self.next(), f'game-build F8 "feature F8" picks {PICKS}')
        self.edit("state.json", lambda s: s.update(human_queue=[]))  # the picks session: applied, entry removed
        self.set_passes("F8", evidence=f"human: picks in {PICKS}")
        self.assertEqual(self.next(), "game-verdict final")
        self.record_verdict("ship")
        self.tool("advance")
        self.assertEqual(self.phase()[0], "done")

    def test_a_reopened_full_verdict_routes_back_to_polish_for_picks(self):
        self.to_polish()
        self.queue_picks()
        self.set_passes("F9")
        answers = "docs/game/playtests/full/answers.md"
        self.edit("state.json", lambda s: s["human_queue"].append(
            {"id": "H3", "what": "playtest", "kind": "playtest", "scope": "full", "answers": answers}))
        self.write(answers, "FC2: yes")
        self.commit()
        self.tool("advance")
        self.assertEqual(self.next(), f"game-verdict full answers {answers}")
        self.record_verdict("ship")
        self.tool("advance")
        self.assertEqual(self.phase(), ("polish", "polish"))  # not into the final verdict while picks are queued
        self.assertEqual(self.next(), PICKS_WAIT)

    def test_the_picks_stop_names_every_kit(self):
        self.to_polish()
        kit, picks = "docs/game/playtests/evidence/F9/compare/index.md", "docs/game/playtests/evidence/F9/compare/picks.md"
        self.edit("state.json", lambda s: s["human_queue"].extend(
            [COMPARE, dict(COMPARE, id="H7", how=kit, answers=picks, unblocks=["F9"])]))
        self.commit()
        self.assertEqual(self.next(), "stop: waiting for A/B picks: a person picks from the kit "
                                      f"(docs/game/playtests/evidence/F8/compare/index.md) into {PICKS} and the kit "
                                      f"({kit}) into {picks}, leaving the queue entries; then run /game-next")

    def test_full_and_final_verdicts_wait_for_a_repeat_calibration(self):
        self.to_production_plan()
        self.set_passes("F4")
        self.set_passes("F7", evidence="human: checked by hand")
        self.tool("advance")
        self.assertEqual(self.next(), "game-verdict full")
        kit = self.game / "calibration" / "kit-1"
        kit.mkdir(parents=True)
        (self.game / "calibration" / "labels.json").rename(kit / "labels.json")  # an adjust changed north_stars.art
        self.edit("state.json", lambda s: s["human_queue"].append(CALIBRATE))
        self.commit()
        self.assertEqual(self.next(), CALIBRATION_WAIT)
        self.assertEqual(self.next("--no-user"), CALIBRATION_WAIT)
        self.calibrate()
        self.assertEqual(self.next(), "game-verdict full")

    def test_the_core_loop_verdict_never_waits_for_calibration(self):
        self.to_core_verdict()
        self.edit("state.json", lambda s: s["human_queue"].append(CALIBRATE))
        self.commit()
        self.assertEqual(self.next(), "game-verdict core-loop")  # judged on bots

    # ---------- tests: the slice ----------
    def test_production_topics_wait_until_the_slice_ships(self):
        self.to_plan()
        self.plan()
        self.edit("topics.json", lambda d: d["topics"].append(topic("T20", priority="core", stage="production")))
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
        self.assertEqual(self.next(), "game-research restart docs/adr/0001-v.md")

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
        self.edit("topics.json", lambda d: d["topics"].append(topic("T21", parent=None, pages=[["vision"]])))
        self.edit("features.json", lambda d: d["features"].append(dict(feature("F1", "core-loop"), pages=[["x"]])))
        out = self.tool("check", ok=False)
        for expected in ("wiki.json pages: entry 1 is not an object", "wiki.json pages: entry 2 has no id",
                         "page slice: missing title", "page slice: missing version", "page slice: missing updated",
                         "topic T21: pages must be a list of page ids", "F1: pages must be a list of page ids"):
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

    def test_ideation_needs_a_north_star_per_active_role_and_invariants(self):
        self.to_ideation()
        v = json.loads(json.dumps(VISION_JSON))
        del v["north_stars"]["art"]
        v["invariants"] = ["one"]
        (self.game / "vision.json").write_text(json.dumps(v))
        out = self.tool("complete", ok=False)
        self.assertIn("vision.json north_stars: art missing", out)
        self.assertIn("vision.json invariants: 1; needs 2-5", out)

    def test_north_stars_need_a_statement_and_two_references(self):
        self.to_ideation()
        v = json.loads(json.dumps(VISION_JSON))
        v["north_stars"]["ux"] = {"statement": " ", "references": ["one"]}
        (self.game / "vision.json").write_text(json.dumps(v))
        out = self.tool("complete", ok=False)
        self.assertIn("north_stars.ux: no statement", out)
        self.assertIn("north_stars.ux: 1 references; needs 2", out)

    def test_art_direction_and_feel_actions_are_required(self):
        self.to_ideation()
        v = json.loads(json.dumps(VISION_JSON))
        v["north_stars"]["art"].update(directions=1, choice="")
        v["north_stars"]["feel"]["actions"] = {}
        (self.game / "vision.json").write_text(json.dumps(v))
        out = self.tool("complete", ok=False)
        self.assertIn("north_stars.art: directions 1; needs 2-3", out)
        self.assertIn("north_stars.art: no choice", out)
        self.assertIn("north_stars.feel: no core action", out)

    def test_each_role_with_a_page_has_a_slice_topic(self):
        self.to_ideation()
        (self.game / "vision.json").write_text(json.dumps(VISION_JSON))
        self.edit("topics.json", lambda d: d.update(topics=[t for t in SEED_TOPICS["topics"] if t["id"] != "T8"]))
        self.write_wiki(["Vision"])
        self.open_references()
        self.commit()
        self.assertIn("no slice topic for role art (its page)", self.tool("complete", ok=False))
        v = dict(VISION_JSON, roles_off={"art": "no art role"})
        v["north_stars"] = {r: s for r, s in VISION_JSON["north_stars"].items() if r != "art"}
        (self.game / "vision.json").write_text(json.dumps(v))
        self.commit()
        self.tool("complete")

    def test_malformed_north_stars_invariants_and_roles_off_are_reasons(self):
        self.to_ideation()
        self.edit("vision.json", lambda d: d.update(north_stars=[], invariants="x", roles_off={"art": " "}))
        out = self.tool("gate", ok=False)
        self.assertNotIn("Traceback", out)
        self.assertIn("vision.json north_stars is not an object", out)
        self.assertIn("vision.json invariants is not a list", out)
        self.assertIn("vision.json roles_off: art has no reason", out)
        self.edit("vision.json", lambda d: d.update(north_stars={}, invariants=[], roles_off=[]))
        out = self.tool("gate", ok=False)
        self.assertNotIn("Traceback", out)
        self.assertIn("vision.json roles_off is not an object", out)

    def test_blank_anti_pillars_count_as_none(self):
        self.to_ideation()
        self.edit("vision.json", lambda d: d.update(VISION_JSON, anti_pillars=["", "  "]))
        self.assertIn("vision.json has no anti-pillar", self.tool("gate", ok=False))

    def test_consolidate_gate_needs_a_page_per_area_for_the_stage(self):
        self.to_brainstorm()
        self.write_wiki([a for a in SLICE_AREAS if a != "Feel"])
        self.resolve("T2", "T3", "T7", "T8", "T9", "T10", "T11")
        self.sync()
        self.tool("advance")
        self.assertIn("wiki.json has no page in area 'Feel'", self.tool("gate", ok=False))

    def test_slice_consolidate_needs_a_human_item_and_production_needs_richness(self):
        self.to_brainstorm()
        self.write_wiki(SLICE_AREAS)
        self.resolve("T2", "T3", "T7", "T8", "T9", "T10", "T11")
        self.sync()
        self.tool("advance")
        (self.game / "fun-checklist.json").write_text(json.dumps(
            {"items": [i for i in FUN["items"] if i["id"] != "FC2"]}))
        self.commit()
        self.assertIn("no human item for the slice playtest", self.tool("gate", ok=False))

    # ---------- tests: research ----------
    def test_setup_needs_intent_and_checked_research_sources(self):
        self.tool("init")
        self.agent_docs()
        self.edit("state.json", lambda s: s.update(docs_verified={"place": "ClickUp doc", "date": "2026-11-22"}))
        self.commit()
        out = self.tool("complete", ok=False)
        self.assertIn("state.intent must be one of ['sell', 'hobby']", out)
        self.assertIn("research sources not checked (game-setup records research_sources)", out)
        self.edit("state.json", lambda s: s.update(intent="profit", research_sources={"reachable": []}))
        self.commit()
        out = self.tool("complete", ok=False)
        self.assertIn("state.intent must be one of ['sell', 'hobby']", out)
        self.assertIn("research sources not checked (game-setup records research_sources)", out)
        self.edit("state.json", lambda s: s.update(intent="hobby", research_sources=SOURCES))
        self.commit()
        self.tool("complete")
        self.assertFalse((self.game / "research").exists())  # init writes no research files; the research skill does

    def test_the_scan_runs_alone_before_ideation(self):
        self.to_scan()
        self.assertEqual(self.next("--no-user"), "game-research scan")
        self.write("docs/game/" + REFS, json.dumps({"scanned_for": None, "refs": COMPS[:2]}))
        self.commit()
        out = self.tool("complete", ok=False)
        self.assertIn("scan: 2 comps; needs 3", out)
        self.assertIn("wiki.json has no page 'landscape'", out)
        self.edit("state.json", lambda s: s.update(task=None))  # with its task cleared, the scan still runs alone
        self.commit()
        self.assertEqual(self.next(), "game-research scan")
        self.assertEqual(self.next("--no-user"), "game-research scan")
        self.scan()
        self.sync()
        self.tool("advance")
        self.assertEqual(self.phase(), ("ideation", None))
        self.assertEqual(self.next(), "with-user: game-ideation")

    def test_hobby_needs_no_comps_but_sell_needs_three(self):
        self.to_scan()
        self.edit("wiki.json", lambda d: d["pages"].append(page("landscape")))
        self.write("docs/game/" + REFS, json.dumps({"scanned_for": None, "refs": COMPS[:2] + [ref("R3", "Okami")]}))
        self.commit()
        self.assertIn("scan: 2 comps; needs 3", self.tool("gate", ok=False))  # an aspect reference is no comp
        self.edit("state.json", lambda s: s.update(intent="hobby"))
        self.edit(REFS, lambda d: d.update(refs=[]))
        self.commit()
        self.assertIn("gate scan: PASS", self.tool("gate"))
        self.edit("state.json", lambda s: s.update(intent="sell"))
        self.edit(REFS, lambda d: d.update(refs=COMPS))
        self.commit()
        self.assertIn("gate scan: PASS", self.tool("gate"))

    def test_ideation_opens_a_reference_per_active_role(self):
        self.to_ideation()
        (self.game / "vision.json").write_text(json.dumps(VISION_JSON))
        self.write_wiki(["Vision"])
        (self.game / "topics.json").write_text(json.dumps(SEED_TOPICS))
        self.commit()
        out = self.tool("complete", ok=False)
        for role in ROLES:  # the scan's comps are only candidates
            self.assertIn(f"references.json: no reference opened for study for role {role}", out)
        self.open_references()
        self.edit(REFS, lambda d: d["refs"][0].update(status="candidate"))  # R1, the only comp with art
        self.commit()
        out = self.tool("complete", ok=False)
        self.assertIn("references.json: no reference opened for study for role art", out)
        self.assertEqual(out.count("no reference opened for study"), 1)
        self.edit("vision.json", lambda v: v.update(roles_off={"art": "the game is text only"}))
        self.edit("topics.json", lambda d: d.update(topics=[t for t in d["topics"] if t["id"] != "T8"]))
        self.commit()
        self.tool("complete")  # a role switched off needs no reference

    def test_research_runs_one_session_per_open_reference_then_the_brief(self):
        self.to_ideation()
        self.ideate()
        self.edit(REFS, lambda d: d["refs"].insert(0, ref("R9", "Okami")))  # a candidate nobody picked
        self.commit()
        self.assertIn("R1: open, not studied yet", self.tool("gate", ok=False))
        opened = [r["id"] for r in self.load(REFS)["refs"] if r["status"] == "open"]
        self.assertEqual(opened, ["R1", "R2", "R3", "R4", "R5"])
        for rid in opened:
            self.assertEqual(self.next(), f"game-research ref {rid}")
            self.assertEqual(self.next("--no-user"), f"game-research ref {rid}")
            self.study(rid)
        self.assertEqual(self.next(), "game-research brief")
        self.assertEqual(self.next("--no-user"), "game-research brief")
        self.write("docs/game/" + HOMEWORK, json.dumps({"reason": "the agent could do it all", "items": []}))
        self.commit()
        self.assertEqual(self.next(), "game-research brief")  # the research page is still missing
        self.edit("wiki.json", lambda d: d["pages"].append(page("research")))
        self.commit()
        self.tool("complete")
        self.sync()
        self.assertEqual(self.next("--no-user"), "advance")
        self.tool("advance")
        self.assertEqual(self.phase(), ("brainstorm", None))

    def test_research_gate_checks_evidence_per_reference(self):
        self.to_ideation()
        self.ideate()
        self.research()  # its complete passed the gate
        r1 = self.game / "research" / "refs" / "R1"
        (r1 / "art" / "shot-1.png").unlink()
        self.commit()
        self.assertEqual(self.next(), "game-research ref R1")  # a studied reference that falls short is studied again
        self.assertEqual(self.next("--no-user"), "game-research ref R1")
        self.edit(REFS, lambda d: d["refs"].append(ref("R9", "Okami", status="open")))
        self.assertEqual(self.next(), "game-research ref R9")  # open references come first
        self.edit(REFS, lambda d: d["refs"].pop())
        self.edit(REFS, lambda d: d["refs"][0].update(sources=d["refs"][0]["sources"][:2]))
        self.edit(REFS, lambda d: d["refs"][0]["how_studied"].pop("feel"))
        (r1 / "design.md").unlink()
        out = self.tool("gate", ok=False)
        self.assertIn("R1: 2 sources; needs 3", out)
        self.assertIn("R1: no image for the art section", out)
        self.assertIn("R1: no design dossier (docs/game/research/refs/R1/design.md)", out)
        self.assertIn("R1: feel how_studied not set", out)
        self.edit(REFS, lambda d: d["refs"][0]["how_studied"].update(art={"how": "not-assessed"}))
        out = self.tool("gate", ok=False)
        self.assertIn("R1: art not-assessed needs a reason", out)
        self.assertNotIn("R1: no image for the art section", out)  # what wasn't assessed needs no image
        self.write_audit("R1", [self.note(decision="")])
        self.assertIn("R1: audit note N1 is open", self.tool("gate", ok=False))
        self.write_audit("R1", [self.note(severity="blocking", decision="wontfix: the shot is fine")])
        self.assertIn("R1: audit note N1 is blocking and not fixed", self.tool("gate", ok=False))
        (r1 / "audit.json").unlink()
        self.assertIn("R1: no audit (docs/game/research/refs/R1/audit.json)", self.tool("gate", ok=False))

    def test_a_reference_short_of_sources_passes_when_the_gap_is_homework(self):
        self.to_ideation()
        self.ideate()
        self.research()
        self.edit(REFS, lambda d: d["refs"][0].update(sources=d["refs"][0]["sources"][:1]))
        self.commit()
        self.assertIn("R1: 1 sources; needs 3", self.tool("gate", ok=False))
        self.assertEqual(self.next(), "game-research ref R1")
        self.edit(REFS, lambda d: d["refs"][0].update(homework=["play R1 for 20 minutes and note the dash timing"]))
        self.commit()
        self.assertNotIn("R1: 1 sources", self.tool("gate"))  # what the agent couldn't reach is the person's
        self.assertEqual(self.tool("check"), "check: ok\n")
        self.assertNotEqual(self.next(), "game-research ref R1")
        for bad in ("play it", ["", "  "], [3]):
            self.edit(REFS, lambda d: d["refs"][0].update(homework=bad))
            out = self.tool("check", ok=False) + self.tool("gate", ok=False)
            self.assertNotIn("Traceback", out)
            self.assertIn("references.json R1: homework must be a list of non-empty strings", out)
            self.assertIn("R1: 1 sources; needs 3", out)  # a malformed list names no gap

    def test_research_keeps_a_reference_open_for_every_active_role(self):
        self.to_ideation()
        self.ideate()
        self.research()
        reason = "references.json: no reference opened for study for role narrative"

        def narrative(status):
            self.edit(REFS, lambda d: next(r for r in d["refs"] if r["roles"] == ["narrative"]).update(status=status))
            self.commit()
        narrative("candidate")  # R5, the only narrative reference
        self.assertTrue(self.next().startswith(f"fix: {reason}"))
        self.assertTrue(self.next("--no-user").startswith(f"fix: {reason}"))
        self.assertIn(reason, self.tool("complete", ok=False))
        self.assertIn(reason, self.tool("gate", ok=False))
        narrative("open")
        self.assertNotIn(reason, self.tool("check"))
        self.assertEqual(self.next(), "game-research ref R5")

    def test_brainstorm_waits_on_open_homework(self):
        self.to_brainstorm()
        self.edit(HOMEWORK, lambda d: d["items"][0].update(status="open", answer=""))
        self.commit()
        self.assertEqual(self.next(), "with-user: game-research homework")  # before any topic
        self.assertEqual(self.next("--no-user"), HOMEWORK_WAIT)
        self.tool("tick", "with-user: game-research homework")
        counters = self.load("state.json")["counters"]
        self.assertEqual((counters["sessions"], counters["brainstorm_sessions"]), (1, 0))
        self.edit(HOMEWORK, lambda d: d["items"][0].update(status="skip"))
        self.commit()
        self.assertTrue(self.next().startswith("with-user: game-brainstorm T2"))

    def test_malformed_research_files_are_reasons_not_crashes(self):
        self.to_ideation()
        self.ideate()

        def run():
            out = self.tool("check", ok=False) + self.tool("status") + self.tool("gate", ok=False)
            self.assertNotIn("Traceback", out)
            return out
        self.write("docs/game/" + REFS, "[]")
        self.write("docs/game/" + HOMEWORK, json.dumps({"items": "x"}))
        self.write("docs/game/research/refs/R1/audit.json", "[]")
        out = run()
        for expected in ("references.json is not an object", "homework.json items is not a list",
                         "docs/game/research/refs/R1/audit.json: not a JSON object"):
            self.assertIn(expected, out)
        self.write("docs/game/" + REFS, json.dumps({"refs": "x"}))
        self.write("docs/game/" + HOMEWORK, "[]")
        out = run()
        self.assertIn("references.json refs is not a list", out)
        self.assertIn("homework.json is not an object", out)
        bad = {"id": "R2", "why": "vibes", "status": "maybe", "roles": ["lighting"], "sources": "x",
               "how_studied": {"art": {"how": "dreamt"}, "lighting": "x"}}
        self.write("docs/game/" + REFS, json.dumps({"refs": ["R1", bad, dict(bad, roles="art", how_studied=[]),
                                                             {"why": "comp"}]}))
        items = [{"id": f"H{n}", "status": "open", "roles": []} for n in range(1, 12)]
        items[0]["status"], items[1]["id"], items[2]["roles"] = "later", "H1", ["lighting"]
        self.write("docs/game/" + HOMEWORK, json.dumps({"reason": "", "items": items + ["H12"]}))
        out = run()
        for expected in ("references.json refs: entry 1 is not an object",
                         "references.json R2: why must be one of ['comp', 'aspect']",
                         "references.json R2: status must be one of ['candidate', 'open', 'studied']",
                         "references.json R2: role 'lighting' is not one of",
                         "references.json R2: sources must be a list",
                         "references.json R2: how_studied art: how must be one of "
                         "['played', 'watched', 'read', 'not-assessed']",
                         "references.json R2: how_studied role 'lighting' is not one of",
                         "references.json R2: duplicate id", "references.json R2: roles must be a list",
                         "references.json R2: how_studied must be an object",
                         "references.json refs: entry 4 has no id",
                         "homework.json H1: status must be one of ['open', 'answered', 'skip']",
                         "homework.json H1: duplicate id", "homework.json H3: role 'lighting' is not one of",
                         "homework.json items: entry 12 is not an object",
                         "homework.json has 12 items; keep it to 10 or fewer"):
            self.assertIn(expected, out)
        self.write("docs/game/" + HOMEWORK, json.dumps({"reason": " ", "items": []}))
        self.assertIn("homework.json has no items and no reason", run())

    # ---------- tests: review items ----------
    def test_slice_consolidate_needs_review_items_for_creative_art_and_feel(self):
        self.to_brainstorm()
        self.write_wiki(SLICE_AREAS)
        self.resolve("T2", "T3", "T7", "T8", "T9", "T10", "T11")
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

    def test_non_string_roles_in_review_items_and_files_are_reasons_not_tracebacks(self):
        self.to_slice_verdict()
        self.calibrate()
        self.record_verdict("adjust", complete=False)
        self.edit("fun-checklist.json", lambda d: next(i for i in d["items"] if i["id"] == "FC5").update(roles=[["art"]]))
        self.commit()
        out = self.tool("complete", ok=False)
        self.assertNotIn("Traceback", out)
        self.assertIn("fun FC5: role '['art']' is not one of", out)
        self.edit("fun-checklist.json", lambda d: next(i for i in d["items"] if i["id"] == "FC5").update(roles=["art"]))
        art = self.root / "docs/game/reviews/verdict-slice/art.json"
        data = json.loads(art.read_text())
        data["role"] = ["art"]
        art.write_text(json.dumps(data))
        self.commit()
        out = self.tool("complete", ok=False)
        self.assertNotIn("Traceback", out)
        self.assertIn("FC5: needs a review by art", out)

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

    def test_restart_rescans_then_ideates_then_studies_only_new_references(self):
        self.to_core_verdict()
        self.edit("state.json", lambda s: s["human_queue"].append({"id": "H1", "what": "x", "unblocks": ["F2"]}))
        self.commit()
        dossier = self.game / "research" / "refs" / "R1" / "art.md"
        studied = dossier.read_text()
        self.record_verdict("restart")
        self.tool("advance")
        adr = "docs/adr/0001-v.md"
        self.assertEqual(self.next(), f"game-research restart {adr}")
        self.assertEqual(self.next("--no-user"), f"game-research restart {adr}")
        self.assertEqual(self.load("features.json")["features"], [])
        self.assertEqual(self.load("state.json")["human_queue"], [])
        archive = self.game / "archive" / "restart-1"
        self.assertTrue((archive / "features.json").exists() and (archive / "human-queue.json").exists())
        self.assertTrue((archive / "homework.json").exists())  # the homework served the old direction
        self.assertFalse((self.game / HOMEWORK).exists())
        self.assertTrue(self.clean())
        self.assertIn(f"references.json scanned_for is not {adr}: re-scan for the restart, then set it",
                      self.tool("complete", ok=False))
        self.edit(REFS, lambda d: d.update(scanned_for=adr))
        self.commit()
        self.tool("complete")
        self.tool("advance")  # scan -> ideation: the wiki unchanged
        self.assertEqual(self.next(), f"with-user: game-ideation restart {adr}")
        self.edit(REFS, lambda d: d["refs"].append(ref("R6", "Okami", roles=("art",), status="open")))
        self.commit()
        self.tool("complete")
        self.tool("advance")  # ideation -> research
        self.assertEqual(self.next(), "game-research ref R6")  # the studied references are not studied again
        self.study("R6")
        self.assertEqual(self.next(), "game-research brief")  # the brief is redone for the new direction
        self.assertEqual(dossier.read_text(), studied)
        self.assertEqual(next(r for r in self.load(REFS)["refs"] if r["id"] == "R1")["status"], "studied")
        self.write("docs/game/" + HOMEWORK, json.dumps({"reason": "R6 needs nothing from a person", "items": []}))
        self.edit("wiki.json", lambda d: next(p for p in d["pages"] if p["id"] == "research").update(version="2"))
        self.commit()
        self.tool("complete")
        self.sync()
        self.tool("advance")  # research -> brainstorm
        self.tool("advance")  # brainstorm -> consolidate: nothing open for the slice
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
        self.set_passes("F7", evidence="human: checked")
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
        base = self.head()
        state = json.loads(self.history.show(base, "docs/game/state.json"))  # what `git reset --hard base` restores
        self.assertEqual(state["counters"]["sessions"], 1)
        self.assertEqual((state["phase"], state["milestone"]), ("build", "core-loop"))

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
        self.edit("topics.json", lambda d: d["topics"].append(topic("T20", unblocks=["F2"])))
        self.edit("topics.json", lambda d: d["topics"].append(topic("T21")))
        self.commit()
        self.assertTrue(self.next().startswith("with-user: game-brainstorm T20"))  # unblocks F2; T21 waits
        self.resolve("T20")
        self.assertTrue(self.next().startswith("game-build F1"))
        self.edit("topics.json", lambda d: d["topics"].append(topic("T22", priority="core")))
        self.commit()
        self.assertTrue(self.next().startswith("with-user: game-brainstorm T22"))

    def test_without_a_person_the_run_builds_around_open_topics_then_waits(self):
        self.to_plan()
        self.plan()
        self.edit("topics.json", lambda d: d["topics"].append(topic("T20", unblocks=["F1"])))
        self.commit()
        self.assertTrue(self.next().startswith("with-user: game-brainstorm T20"))
        self.assertTrue(self.next("--no-user").startswith("game-build F2"))  # F1 waits on T20
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

    def test_gdd_synced_before_any_commit_records_nothing(self):
        self.tool("init")
        before = (self.game / "state.json").read_text()
        self.assertIn("cannot record the sync: commit the wiki first", self.tool("gdd-synced", ok=False))
        self.assertEqual((self.game / "state.json").read_text(), before)
        self.assertIsNone(self.history.head())

    def test_the_gdd_is_never_stale_while_the_index_has_no_pages(self):
        self.tool("init")  # an empty wiki.json, and the GDD never synced
        self.commit()
        self.assertIn("human GDD: in sync", self.tool("status"))
        self.write("docs/game/own-calls.md", "| today | F1 | a call |\n")
        self.write("docs/game/wiki.json", json.dumps({"pages": []}))
        self.commit()
        self.assertIn("human GDD: in sync", self.tool("status"))

    def test_brainstorm_share_lets_support_topics_wait_until_consolidate_defers_them(self):
        self.to_brainstorm()
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
                                            for t in d["topics"] if t["id"] in ("T3", "T7", "T8", "T9", "T10", "T11")])
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
        self.assertIn("version 3 -> 7", out)
        s = self.load("state.json")
        self.assertEqual((s["version"], s["phase"], s["task"], s["stage"]), (7, "setup", "game-setup upgrade", "slice"))
        self.assertEqual({k: s[k] for k in kept}, kept)
        self.assertEqual(self.load("features.json")["milestones"], MILESTONES)
        self.assertTrue((self.game / "vision.json").exists())
        self.assertTrue(self.clean())
        self.assertEqual(self.next(), "with-user: game-setup upgrade")
        self.assertIn("already at version 7", self.tool("upgrade"))

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
        self.assertIn("version 3 -> 7", self.plugin("upgrade"))
        s, old = self.load("state.json"), json.loads(EVE_STATE)
        self.assertEqual((s["version"], s["phase"], s["task"]), (7, "setup", "game-setup upgrade"))
        self.assertEqual(s["human_queue"], old["human_queue"])
        self.assertEqual(s["adapter_verified"], old["adapter_verified"])
        self.assertEqual({k: s["limits"][k] for k in old["limits"]}, old["limits"])
        self.assertEqual({k: s["counters"][k] for k in old["counters"]}, old["counters"])
        self.assertEqual(self.load("features.json")["milestones"], MILESTONES)
        self.assertTrue(self.clean())
        self.assertEqual(self.plugin("status").split("next: ", 1)[1].strip(), "with-user: game-setup upgrade")
        self.edit("features.json", lambda d: d["features"].append(feature("F1", "slice")))
        self.assertNotIn("milestone 'slice' is not in features.milestones", self.plugin("check", ok=False))

    def test_upgrade_needs_game_state_and_never_downgrades(self):
        out = self.tool("upgrade", ok=False)
        self.assertIn("no game state", out)
        self.assertIn("init", out)
        self.assertFalse((self.game / "state.json").exists())
        self.tool("init")
        self.edit("state.json", lambda s: s.update(version=8))
        self.commit()
        before = (self.game / "state.json").read_text()
        self.assertIn("version 8, newer than this tool (7)", self.tool("upgrade", ok=False))
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
        self.edit("state.json", lambda s: s.update(version=7))
        self.agent_docs()
        self.edit("state.json", lambda s: s.update(docs_verified={"place": "ClickUp doc", "date": "2026-11-22"},
                                                   intent="sell", research_sources=SOURCES))
        self.commit()
        self.tool("advance")
        self.scan()  # the scan between them is the agent's alone
        self.sync()
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
        self.assertIn("version 1 -> 7", self.tool("upgrade"))


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
                           env=dict(isolated_git_env(), AGENT_CMD=f"{sys.executable} agent.py"))
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
