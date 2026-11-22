#!/usr/bin/env python3
"""State tool for the game-* skills. Python 3.8+, standard library only.

game-setup copies this file to docs/game/gamestate.py in the game's repo.

Commands:
  init               create any missing state files under docs/game/
  status [--no-user] one-screen summary, ending with the `next:` action.
                     --no-user: nobody is there to talk to, so skip `with-user:`
                     work (ideation, brainstorm topics) and do what else can be done
  check [--since C]  invariants; exit 1 on violations. --since: the commit the
                     session started from (default HEAD), for the edit guard
  gate               does the current task or phase gate pass? exit 1 if not
  complete           a phase skill's last step: clears the phase's task once
                     the task's gate passes
  advance            move to the next phase or milestone, when allowed
  tick "<next>"      record one dispatch of a `next:` action
  gdd-synced         game-gdd's last step: the human GDD now matches the wiki
Option: --root DIR  repo root (default: two levels above this file when it
                    lives in docs/game/, else the current directory)

advance, complete, tick and gdd-synced commit docs/game/state.json themselves,
so a reset to a session's base commit never loses the run's own bookkeeping.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PHASES = ["setup", "ideation", "brainstorm", "consolidate", "plan", "build", "verdict", "polish",
          "awaiting-human", "done"]
DESIGN_PHASES = ["setup", "ideation", "brainstorm", "consolidate"]  # the bar (fun checklist, richness) is set here
PLANNING_PHASES = DESIGN_PHASES + ["plan"]                          # the definition of done is rewritten here
TOPIC_PHASES = ["consolidate", "plan", "build", "verdict", "polish"]  # topics interrupt these when work needs them
REOPENABLE = ["build", "polish", "awaiting-human", "done"]
TIERS = ["must", "nice", "cut"]
VERIFY_KINDS = ["test", "sim", "replay", "bot", "capture", "check", "human"]
MILESTONES = ["core-loop", "slice", "systems", "content", "verdict-build", "polish"]
SLICE_MS = ["core-loop", "slice"]
POLISH = "polish"
STAGES = ["slice", "production"]
SCOPES = ["core-loop", "slice", "full", "final"]
FUN_SCOPES = ["core-loop", "slice", "full"]
RICH_SCOPES = ["slice", "full"]
OUTCOMES = ["ship", "adjust", "restart", "kill"]
SCORE_RESULTS = ["pass", "fail", "not-assessed", "pending-human"]
ASPECTS = ["depth", "breadth", "variety"]
TOPIC_STATUSES = ["open", "resolved", "deferred"]
PRIORITIES = ["core", "support", "later"]
AREAS = ["Vision", "Mechanics", "Controls", "Systems", "Content", "Modes and sessions",
         "Screens and onboarding", "Feel", "Tone, art and world"]
SLICE_AREAS = [a for a in AREAS if a != "Modes and sessions"]
REQUIRED_PAGES = ["vision", "slice", "concepts"]
FUN_FIELDS = ["statement", "scope", "kind", "metric", "threshold", "how"]
RICH_FIELDS = ["aspect", "scope", "statement", "metric", "threshold", "how"]
MIN_SEED_TOPICS = 5
NICE_RESERVE = 10  # sessions kept back for verdicts and polish before nice features are built

DEFAULT_STATE = {
    "version": 5,
    "phase": "setup",
    "stage": "slice",
    "milestone": None,
    "task": "game-setup",
    "verdict_scope": None,
    "verdict_index": 0,
    "passed_verdicts": [],
    "slice_sessions": None,
    "checkpoint_due": False,
    "adapter_verified": False,
    "gdd_synced": None,
    "restart_adr": None,
    "resume": None,
    "stop_reason": None,
    "counters": {"sessions": 0, "brainstorm_sessions": 0, "adjusts": 0, "restarts": 0},
    "limits": {"budget_sessions": 150, "brainstorm_share": 0.2, "max_adjusts": 2, "max_restarts": 1,
               "max_attempts": 3, "max_repeats": 5},
    "attempts": {},
    "last_dispatch": {"action": None, "repeats": 0},
    "human_queue": [],
    "verdicts": [],
}
DEFAULT_FEATURES = {"milestones": MILESTONES, "features": []}
DEFAULT_FUN = {"items": []}
DEFAULT_RICHNESS = {"targets": []}
DEFAULT_TOPICS = {"topics": []}
DEFAULT_KEEP = {"keep": []}
DEFAULT_WIKI = {"pages": []}
DEFAULT_VISION = {}
MISSING = object()
DEFAULT_TEXT = {
    "progress.md": "# Progress\n\nAppend-only session log. One entry per session, newest last, at most 10 lines each.\n",
    "own-calls.md": "# The AI's own calls\n\nPlayer-visible choices an agent made that no wiki page specified. "
    "Append-only; game-gdd shows the new ones to people, who keep or change each.\n\n"
    "| Date | Feature | Call | Page |\n| --- | --- | --- | --- |\n",
    "assets.md": "# Assets\n\nEvery asset in the game, where it came from, and its license.\n\n"
    "| Asset | Source (placeholder / generated / sourced / human) | License | Final? | Notes |\n"
    "| --- | --- | --- | --- | --- |\n",
}


def copy(data):
    return json.loads(json.dumps(data))


class Game:
    def __init__(self, root: Path):
        self.root = root
        self.dir = root / "docs" / "game"
        self.state_path = self.dir / "state.json"
        self.features_path = self.dir / "features.json"
        self.fun_path = self.dir / "fun-checklist.json"
        self.richness_path = self.dir / "richness.json"
        self.topics_path = self.dir / "topics.json"
        self.keep_path = self.dir / "keep.json"
        self.wiki_index_path = self.dir / "wiki.json"
        self.vision_path = self.dir / "vision.json"
        self.state = self._load(self.state_path, DEFAULT_STATE)
        self.features = self._load(self.features_path, DEFAULT_FEATURES)
        self.fun = self._load(self.fun_path, DEFAULT_FUN)
        self.richness = self._load(self.richness_path, DEFAULT_RICHNESS)
        self.topics_data = self._load(self.topics_path, DEFAULT_TOPICS)
        self.keep = self._load(self.keep_path, DEFAULT_KEEP)
        self.wiki_index = self._load(self.wiki_index_path, DEFAULT_WIKI)
        self.vision_data = self._load(self.vision_path, DEFAULT_VISION)

    def _load(self, path, default):
        merged = copy(default)
        if not path.exists():
            return merged
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"error: {path.relative_to(self.root)} is not valid JSON: {e}")
        for key, value in data.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key].update(value)
            else:
                merged[key] = value
        return merged

    # ---------- persistence ----------
    def _write(self, path, data):
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True)

    def in_git(self):
        try:
            return self._git("rev-parse", "--is-inside-work-tree").stdout.strip() == "true"
        except FileNotFoundError:
            return False

    def commit(self, message, *paths):
        """Commit only the given paths; leaves any other staged work alone."""
        if not self.in_git():
            return
        rel = [p.relative_to(self.root).as_posix() for p in paths if p.exists()]
        self._git("add", "--", *rel)
        self._git("commit", "-q", "-m", f"game-state: {message}", "--", *rel)

    def save_state(self, message):
        self._write(self.state_path, self.state)
        self.commit(message, self.state_path)

    # ---------- derived views ----------
    @staticmethod
    def text(path):
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def wiki_pages(self):
        return self.wiki_index.get("pages", [])

    def page_ids(self):
        return {p.get("id") for p in self.wiki_pages()}

    def vision(self):
        return self.vision_data

    def pillars(self):
        pillars = self.vision().get("pillars")
        if pillars is None:
            return None
        return [p.get("id") for p in pillars]

    def items(self):
        return self.features.get("features", [])

    def topics(self):
        return self.topics_data.get("topics", [])

    def milestones(self):
        return self.features.get("milestones", [])

    def build_ms(self):
        return [m for m in self.milestones() if m != POLISH]

    def production_ms(self):
        return [m for m in self.build_ms() if m not in SLICE_MS]

    def stage(self):
        return self.state.get("stage", "slice")

    def in_stage(self, topic):
        return self.stage() == "production" or topic.get("stage") == "slice"

    @staticmethod
    def upto(pool, m):
        return pool[: pool.index(m) + 1] if m in pool else list(pool)

    def queue(self, playtests=None):
        q = self.state.get("human_queue", [])
        if playtests is None:
            return q
        return [e for e in q if (e.get("kind") == "playtest") == playtests]

    def queued_ids(self):
        ids = set()
        for entry in self.queue():
            unblocks = entry.get("unblocks", [])
            ids.update([unblocks] if isinstance(unblocks, str) else unblocks)
        return ids

    def is_done(self, f):
        """Passing, or handed to a person: the run moves on and comes back once the queue clears."""
        return bool(f.get("passes")) or f.get("id") in self.queued_ids()

    def waits_on_topic(self, f):
        return any(f.get("id") in t.get("unblocks", []) for t in self.open_topics())

    def is_blocked(self, f):
        return bool(f.get("blocked")) or self.state["attempts"].get(f.get("id"), 0) >= self.state["limits"]["max_attempts"]

    def failing(self, pool, tier="must"):
        order = {m: i for i, m in enumerate(self.milestones())}
        fs = [f for f in self.items() if f.get("tier") == tier and f.get("milestone") in pool and not self.is_done(f)]
        return sorted(fs, key=lambda f: order.get(f.get("milestone"), 99))

    def earliest_failing_ms(self, pool):
        fs = self.failing(pool)
        return fs[0]["milestone"] if fs else None

    def has_polish_features(self):
        return any(f.get("tier") != "cut" and f.get("milestone") == POLISH for f in self.items())

    def green_pool(self):
        """Milestones whose must features have to pass in the current phase."""
        st = self.state
        phase, scope = st["phase"], st.get("verdict_scope")
        if phase == "build":
            return self.upto(self.build_ms(), st.get("milestone"))
        if phase == "verdict":
            return {"core-loop": SLICE_MS[:1], "slice": SLICE_MS, "full": self.build_ms()}.get(scope, self.milestones())
        if phase in ("polish", "done"):
            return self.milestones()
        return []

    def scored_ids(self, scope):
        fun_scopes = {"core-loop": ["core-loop"], "slice": ["core-loop", "slice"]}.get(scope, FUN_SCOPES)
        rich_scopes = {"core-loop": [], "slice": ["slice"]}.get(scope, RICH_SCOPES)
        fun = [i["id"] for i in self.fun.get("items", []) if i.get("scope") in fun_scopes]
        rich = [t["id"] for t in self.richness.get("targets", []) if t.get("scope", "full") in rich_scopes]
        return fun + rich

    def kinds(self):
        return {i.get("id"): i.get("kind") for i in self.fun.get("items", [])}

    def playtest_entry(self, scope):
        return next((e for e in self.queue(playtests=True) if e.get("scope") == scope), None)

    def pending_playtest(self):
        for entry in self.queue(playtests=True):
            answers = entry.get("answers")
            if answers and (self.root / answers).exists():
                return entry
        return None

    def open_topics(self, priorities=PRIORITIES):
        rank = {p: i for i, p in enumerate(PRIORITIES)}
        ts = [t for t in self.topics() if t.get("status") == "open" and t.get("priority") in priorities]
        return sorted(ts, key=lambda t: (rank.get(t.get("priority"), 9), t.get("id", "")))

    def brainstorm_share_spent(self):
        st = self.state
        budget = st["limits"].get("budget_sessions") or 0
        return bool(budget) and st["counters"]["brainstorm_sessions"] >= st["limits"]["brainstorm_share"] * budget

    def gdd_stale(self):
        """True when the wiki index or the AI's own calls changed since the human GDD was last synced from them."""
        if not self.wiki_pages():
            return False
        synced = self.state.get("gdd_synced")
        if not synced or not self.in_git():
            return True
        sources = [p.relative_to(self.root).as_posix() for p in (self.wiki_index_path, self.dir / "own-calls.md")]
        r = self._git("diff", "--name-only", synced, "HEAD", "--", *sources)
        return r.returncode != 0 or bool(r.stdout.strip())

    def read_pin(self, file, key):
        """The current value of a pinned tuning knob: a dotted path in JSON, or a `key = value` / `key: value` line."""
        path = self.root / file
        if not path.exists():
            return MISSING
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            try:
                value = json.loads(text)
                for part in key.split("."):
                    value = value[int(part)] if isinstance(value, list) else value[part]
                return value
            except (json.JSONDecodeError, KeyError, IndexError, ValueError, TypeError):
                return MISSING
        m = re.search(rf"^\s*{re.escape(key)}\s*[:=]\s*(.+?)\s*[,;]?\s*$", text, re.M)
        return m.group(1).strip("'\"") if m else MISSING

    @staticmethod
    def same(current, pinned):
        return current == pinned or str(current).strip("'\"") == str(pinned)

    # ---------- invariants ----------
    def check(self, since="HEAD"):
        errs = []
        st = self.state
        if st.get("phase") not in PHASES:
            errs.append(f"state.phase '{st.get('phase')}' is not one of {PHASES}")
        for key in ("max_adjusts", "max_restarts", "max_attempts", "max_repeats"):
            if not isinstance(st["limits"].get(key), int):
                errs.append(f"state.limits.{key} must be an integer")
        if not self.in_git():
            errs.append("not inside a git repository: run git init (the edit guard needs history)")
        if POLISH not in self.milestones():
            errs.append(f"features.milestones must include '{POLISH}'")
        errs += self._check_features()
        errs += self._check_targets()
        errs += self._check_topics()
        errs += self._check_wiki()
        errs += self._check_keep()
        if self.stage() not in STAGES:
            errs.append(f"state.stage must be one of {STAGES}")
        for e in self.queue():
            if not e.get("id") or not e.get("what"):
                errs.append("human_queue entries need id and what")
            if e.get("kind") == "playtest" and not (e.get("scope") in SCOPES and e.get("answers")):
                errs.append(f"human_queue {e.get('id')}: a playtest entry needs scope in {SCOPES} and answers")
        for v in st.get("verdicts", []):
            if v.get("outcome") not in OUTCOMES or not v.get("adr") or v.get("scope") not in SCOPES:
                errs.append(f"verdict {v.get('scope')}: needs scope in {SCOPES}, outcome in {OUTCOMES} and an adr path")
        if st.get("phase") not in PLANNING_PHASES:
            errs += self._feature_guard(since)
        if not (self.stage() == "slice" and st.get("phase") in DESIGN_PHASES):
            errs += self._target_guard(since, self.fun_path, "items", FUN_FIELDS, "fun", self.fun)
            errs += self._target_guard(since, self.richness_path, "targets", RICH_FIELDS, "richness", self.richness)
        errs += self._keep_guard(since)
        return errs

    def _check_features(self):
        errs, seen, page_ids = [], set(), self.page_ids()
        pillars, archived, milestones = self.pillars(), self._archived_ids(), self.milestones()
        for f in self.items():
            fid = f.get("id") or "<no id>"
            if fid in seen:
                errs.append(f"{fid}: duplicate id")
            if fid in archived:
                errs.append(f"{fid}: reuses an id from docs/game/archive/; number new features after the archived ones")
            seen.add(fid)
            if not f.get("title"):
                errs.append(f"{fid}: missing title")
            if f.get("tier") not in TIERS:
                errs.append(f"{fid}: tier must be one of {TIERS}")
            if f.get("milestone") not in milestones:
                errs.append(f"{fid}: milestone '{f.get('milestone')}' is not in features.milestones")
            if not f.get("pillar") or (pillars is not None and f.get("pillar") not in pillars):
                errs.append(f"{fid}: pillar '{f.get('pillar')}' is not a pillar in vision.json")
            if not f.get("acceptance") or not isinstance(f.get("acceptance"), list):
                errs.append(f"{fid}: acceptance must be a non-empty list")
            verify = f.get("verify") or {}
            if verify.get("kind") not in VERIFY_KINDS or not verify.get("how"):
                errs.append(f"{fid}: verify needs kind in {VERIFY_KINDS} and a non-empty how")
            if not isinstance(f.get("passes"), bool):
                errs.append(f"{fid}: passes must be true or false")
            if f.get("passes") and not f.get("evidence"):
                errs.append(f"{fid}: passes is true without evidence")
            if f.get("passes") and verify.get("kind") == "human" and not str(f.get("evidence", "")).startswith("human:"):
                errs.append(f"{fid}: a human-verified feature passes only with evidence starting 'human:'")
            if f.get("tier") == "cut" and not f.get("cut_reason"):
                errs.append(f"{fid}: cut without cut_reason")
            errs += [f"{fid}: page '{p}' is not in wiki.json" for p in f.get("pages", []) if p not in page_ids]
        return errs

    def _check_targets(self):
        errs, seen = [], set()
        for i in self.fun.get("items", []):
            iid = i.get("id") or "<no id>"
            if iid in seen:
                errs.append(f"fun {iid}: duplicate id")
            seen.add(iid)
            if not i.get("statement"):
                errs.append(f"fun {iid}: missing statement")
            if i.get("scope") not in FUN_SCOPES:
                errs.append(f"fun {iid}: scope must be one of {FUN_SCOPES}")
            if i.get("kind") not in ("proxy", "human"):
                errs.append(f"fun {iid}: kind must be proxy or human")
            if i.get("kind") == "proxy" and not all(i.get(k) for k in ("metric", "threshold", "how")):
                errs.append(f"fun {iid}: a proxy item needs metric, threshold and how")
        for t in self.richness.get("targets", []):
            tid = t.get("id") or "<no id>"
            if tid in seen:
                errs.append(f"richness {tid}: duplicate id (fun and richness ids share one namespace)")
            seen.add(tid)
            if t.get("aspect") not in ASPECTS:
                errs.append(f"richness {tid}: aspect must be one of {ASPECTS}")
            if t.get("scope", "full") not in RICH_SCOPES:
                errs.append(f"richness {tid}: scope must be one of {RICH_SCOPES}")
            if not all(t.get(k) for k in ("statement", "metric", "threshold", "how")):
                errs.append(f"richness {tid}: needs statement, metric, threshold and how")
        return errs

    def _check_topics(self):
        errs, seen = [], set()
        ids, page_ids = {t.get("id") for t in self.topics()}, self.page_ids()
        for t in self.topics():
            tid = t.get("id") or "<no id>"
            if tid in seen:
                errs.append(f"topic {tid}: duplicate id")
            seen.add(tid)
            if not t.get("title") or not t.get("question"):
                errs.append(f"topic {tid}: needs a title and a question")
            if t.get("status") not in TOPIC_STATUSES:
                errs.append(f"topic {tid}: status must be one of {TOPIC_STATUSES}")
            if t.get("priority") not in PRIORITIES:
                errs.append(f"topic {tid}: priority must be one of {PRIORITIES}")
            if t.get("stage") not in STAGES:
                errs.append(f"topic {tid}: stage must be one of {STAGES} (does the vertical slice need it?)")
            if t.get("parent") is not None and t.get("parent") not in ids:
                errs.append(f"topic {tid}: parent '{t.get('parent')}' is not a topic")
            if t.get("status") in ("resolved", "deferred") and not t.get("resolution"):
                errs.append(f"topic {tid}: a {t.get('status')} topic needs a resolution (the answer, or why it waits)")
            if t.get("status") == "resolved":
                pages = t.get("pages", [])
                if not pages:
                    errs.append(f"topic {tid}: resolved without a wiki page it wrote or updated")
                errs += [f"topic {tid}: page '{p}' is not in wiki.json" for p in pages if p not in page_ids]
        return errs

    def _check_wiki(self):
        errs, seen = [], set()
        open_topics = {t.get("id") for t in self.topics() if t.get("status") == "open"}
        for p in self.wiki_pages():
            pid = p.get("id") or "<no id>"
            if pid in seen:
                errs.append(f"page {pid}: duplicate id")
            seen.add(pid)
            if p.get("area") not in AREAS:
                errs.append(f"page {pid}: area '{p.get('area')}' is not one of {AREAS}")
            link = p.get("link") or ""
            if not link:
                errs.append(f"page {pid}: missing link")
            elif "://" not in link and not (self.root / link).exists():
                errs.append(f"page {pid}: local link '{link}' does not exist")
            flagged = p.get("flagged")
            if flagged and flagged.get("topic") not in open_topics:
                errs.append(f"page {pid}: flagged for topic {flagged.get('topic')}, which is not open")
        return errs

    def _check_keep(self):
        errs = []
        for k in self.keep.get("keep", []):
            kid = k.get("id") or "<no id>"
            if not k.get("what") or not k.get("source"):
                errs.append(f"keep {kid}: needs what was kept and its source (playtest answers or GDD comment)")
            for pin in k.get("pins", []):
                current = self.read_pin(pin.get("file", ""), pin.get("key", ""))
                if current is MISSING:
                    errs.append(f"keep {kid}: can't read pinned '{pin.get('key')}' in {pin.get('file')}")
                elif not self.same(current, pin.get("value")):
                    errs.append(f"keep {kid}: {pin.get('file')} {pin.get('key')} is {current}, kept at "
                                f"{pin.get('value')} ({k.get('what')}); restore it, or change the pin with an ADR")
        return errs

    def _keep_guard(self, since):
        """What people said to keep stays kept: a pin changes or goes only with a new ADR on its entry."""
        old_data = self._old(since, self.keep_path)
        if old_data is None:
            return []
        new = {k.get("id"): k for k in self.keep.get("keep", [])}
        errs = []
        for k in old_data.get("keep", []):
            kid, cur = k.get("id"), new.get(k.get("id"))
            if cur is None:
                errs.append(f"keep {kid}: removed; keep entries are changed with an ADR, not deleted")
            elif cur.get("pins") != k.get("pins"):
                adr = cur.get("adr")
                if not adr or adr == k.get("adr") or not (self.root / adr).exists():
                    errs.append(f"keep {kid}: pins changed without a new ADR in its adr field")
        return errs

    def _archived_ids(self):
        ids = set()
        for path in (self.dir / "archive").glob("*/features.json"):
            try:
                ids.update(f.get("id") for f in json.loads(path.read_text(encoding="utf-8")).get("features", []))
            except json.JSONDecodeError:
                pass
        return ids

    def _old(self, since, path):
        if not self.in_git():
            return None
        r = self._git("show", f"{since}:{path.relative_to(self.root).as_posix()}")
        if r.returncode != 0:
            return None
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            return None

    def _feature_guard(self, since):
        """Outside planning the definition of done only grows: items are cut or replaced, never removed or rewritten."""
        old_data = self._old(since, self.features_path)
        if old_data is None:
            return []
        old = {f.get("id"): f for f in old_data.get("features", [])}
        new = {f.get("id"): f for f in self.items()}
        errs = [f"{fid}: removed from features.json; set tier cut with a cut_reason instead" for fid in old if fid not in new]
        for fid, f in new.items():
            if fid not in old:
                continue
            for key in ("acceptance", "verify", "milestone"):
                if f.get(key) != old[fid].get(key):
                    errs.append(f"{fid}: {key} changed outside the plan phase; replace the feature instead")
            if old[fid].get("tier") == "must" and f.get("tier") != "must" and not self._replaced(f, new):
                errs.append(f"{fid}: a must feature left must outside the plan phase; "
                            "cut it only with cut_reason 'replaced by F..' naming live must features")
        return errs

    @staticmethod
    def _replaced(f, new):
        m = re.match(r"replaced by (.+)", str(f.get("cut_reason", "")))
        if f.get("tier") != "cut" or not m:
            return False
        ids = [i for i in re.split(r"[,\s]+", m.group(1)) if i]
        return bool(ids) and all(i in new and i != f.get("id") and new[i].get("tier") == "must" for i in ids)

    def _target_guard(self, since, path, key, fields, label, current):
        """The bar is set before planning; later phases may add to it but not lower or remove it."""
        old_data = self._old(since, path)
        if old_data is None:
            return []
        new = {i.get("id"): i for i in current.get(key, [])}
        errs = []
        for item in old_data.get(key, []):
            iid = item.get("id")
            if iid not in new:
                errs.append(f"{label} {iid}: removed after consolidate")
            elif any(item.get(k) != new[iid].get(k) for k in fields):
                errs.append(f"{label} {iid}: changed after consolidate")
        return errs

    # ---------- gates ----------
    def gate(self):
        """Reasons the current phase is not complete (its task aside)."""
        st, phase, why = self.state, self.state["phase"], []
        if phase == "setup":
            if not (self.root / "docs" / "agents" / "game.md").exists():
                why.append("docs/agents/game.md is missing")
        elif phase == "ideation":
            why += self._ideation_gate()
        elif phase == "brainstorm":
            open_now = ["core"] if self.brainstorm_share_spent() else ["core", "support"]
            why += [f"topic {t['id']}: open ({t.get('priority')})" for t in self.open_topics(open_now) if self.in_stage(t)]
        elif phase == "consolidate":
            why += self._consolidate_gate()
        elif phase == "plan":
            why += self._plan_gate()
        elif phase == "awaiting-human":
            if self.queue(playtests=False):
                why.append(f"{len(self.queue(playtests=False))} human queue entries open")
            if st.get("stop_reason"):
                why.append(f"stopped: {st['stop_reason']} (a human decides, then sets stop_reason to null)")
        if phase in ("build", "verdict", "polish", "done"):
            why += [f"{f['id']}: not passing" + (" (blocked)" if self.is_blocked(f) else "")
                    for f in self.failing(self.green_pool())]
        if phase == "verdict":
            why += self._verdict_gate()
        if phase == "polish" and not self.has_polish_features():
            why.append("no polish features yet (game-polish)")
        return why

    def _ideation_gate(self):
        why = []
        n = len(self.pillars() or [])
        if not 3 <= n <= 4:
            why.append(f"vision.json has {n} pillars; needs 3-4")
        directions = self.vision().get("directions") or {}
        if not isinstance(directions.get("count"), int) or not 3 <= directions["count"] <= 5:
            why.append(f"vision.json directions.count is {directions.get('count')}; needs 3-5")
        if not re.search(r"\bC\d+\b", str(directions.get("choice") or "")):
            why.append("vision.json directions.choice names no direction")
        ids = self.page_ids()
        why += [f"wiki.json has no page '{i}'" for i in REQUIRED_PAGES if i not in ids]
        seeded = [t for t in self.topics() if t.get("parent") is not None]
        if not any(t.get("stage") == "slice" for t in seeded):
            why.append("no topic marked for the vertical slice (stage: slice)")
        if len(seeded) < MIN_SEED_TOPICS:
            why.append(f"topics.json has {len(seeded)} follow-up topics; seed at least {MIN_SEED_TOPICS}")
        if not any(t.get("priority") == "core" for t in seeded):
            why.append("no core topic seeded")
        return why

    def _consolidate_gate(self):
        slice_stage = self.stage() == "slice"
        have = {p.get("area") for p in self.wiki_pages()}
        why = [f"wiki.json has no page in area '{a}'" for a in (SLICE_AREAS if slice_stage else AREAS) if a not in have]
        why += [f"topic {t['id']}: open ({t.get('priority')})"
                for t in self.open_topics(["core", "support"]) if self.in_stage(t)]
        items = self.fun.get("items", [])
        if slice_stage:
            early = [i for i in items if i.get("scope") in ("core-loop", "slice")]
            if not 3 <= len(early) <= 6:
                why.append(f"fun checklist has {len(early)} core-loop and slice items; needs 3-6")
            if not any(i.get("scope") == "core-loop" and i.get("kind") == "proxy" for i in items):
                why.append("fun checklist has no core-loop proxy item")
            if not any(i.get("kind") == "human" and i.get("scope") in ("core-loop", "slice") for i in items):
                why.append("fun checklist has no human item for the slice playtest")
        else:
            if not any(i.get("scope") == "full" for i in items):
                why.append("fun checklist has no item for the full game (scope full)")
            if len(items) > 10:
                why.append(f"fun checklist has {len(items)} items; keep it to 10 or fewer")
            aspects = {t.get("aspect") for t in self.richness.get("targets", []) if t.get("scope", "full") == "full"}
            why += [f"richness.json has no full-game {a} target" for a in ASPECTS if a not in aspects]
        return why

    def _plan_gate(self):
        st, why = self.state, []
        slice_stage = self.stage() == "slice"
        if not st.get("adapter_verified"):
            why.append("adapter commands not verified (game-setup adapter mode)")
        if not st["limits"].get("budget_sessions"):
            why.append("limits.budget_sessions is not set")
        pool = SLICE_MS if slice_stage else self.production_ms()
        build = [f for f in self.items() if f.get("tier") != "cut" and f.get("milestone") in pool]
        if slice_stage and not any(f.get("tier") == "must" and f.get("milestone") == SLICE_MS[0] for f in build):
            why.append(f"no must feature in milestone '{SLICE_MS[0]}'")
        if not slice_stage and not any(f.get("tier") == "must" for f in build):
            why.append("no must feature in the production milestones")
        why += [f"{f['id']}: no tickets" for f in build if not f.get("tickets")]
        why += [f"{f['id']}: no wiki pages it implements" for f in build if f.get("tier") == "must" and not f.get("pages")]
        measuring = SLICE_MS if slice_stage else self.build_ms()
        measured = {m for f in self.items() if f.get("tier") == "must" and f.get("milestone") in measuring
                    for m in f.get("measures", [])}
        scope = "slice" if slice_stage else "full"
        kinds = self.kinds()
        targets = [i for i in self.scored_ids(scope) if kinds.get(i) != "human"]
        why += [f"{t}: no must feature lists it in measures" for t in targets if t not in measured]
        return why

    def _verdict_gate(self):
        """A verdict counts only when every item in scope is scored with evidence; a ship only when all of it holds."""
        st = self.state
        verdicts, scope = st.get("verdicts", []), st.get("verdict_scope")
        if len(verdicts) <= st.get("verdict_index", 0) or verdicts[-1].get("scope") != scope:
            return [f"no {scope} verdict recorded since this phase began"]
        v, kinds, why = verdicts[-1], self.kinds(), []
        for iid in self.scored_ids(scope):
            score = v.get("scores", {}).get(iid, {})
            result, evidence = score.get("result"), str(score.get("evidence") or "")
            if result not in SCORE_RESULTS:
                why.append(f"{iid}: not scored")
                continue
            if result in ("pass", "fail") and not (evidence and (self.root / evidence).is_file()):
                why.append(f"{iid}: {result} needs an evidence file; '{evidence}' does not exist")
            if result == "not-assessed" and not evidence:
                why.append(f"{iid}: not-assessed needs the reason it could not be measured")
            if result == "pending-human" and kinds.get(iid) != "human":
                why.append(f"{iid}: only human items can wait for a person")
            if v.get("outcome") == "ship":
                if result in ("fail", "not-assessed"):
                    why.append(f"{iid}: {result}; a ship needs every item to pass")
                if result == "pending-human" and scope == "slice":
                    why.append(f"{iid}: the slice ships only after a person has played it")
        return why

    def task_gate(self):
        """What the current task still owes before `complete` may clear it."""
        phase = self.state["phase"]
        if phase == "verdict":
            return self._verdict_gate()
        if phase == "polish":
            return [] if self.has_polish_features() else ["no polish features yet"]
        return self.gate()

    # ---------- transitions ----------
    def advance(self):
        st, phase = self.state, self.state["phase"]
        notes = []
        entry = self.pending_playtest()
        if entry and phase in REOPENABLE:
            self._reopen(entry)
            return [f"playtest answers for {entry['scope']}: verdict reopened"]
        production = " production" if self.stage() == "production" else ""
        if phase == "setup":
            st.update(phase="ideation", task="game-ideation")
        elif phase == "ideation":
            st.update(phase="brainstorm", task=None)
        elif phase == "brainstorm":
            st.update(phase="consolidate", task="game-consolidate" + production)
        elif phase == "consolidate":
            adr = st.get("restart_adr")
            task = f"game-plan restart {adr}" if adr else "game-plan" + production
            st.update(phase="plan", task=task, restart_adr=None)
        elif phase in ("plan", "build", "polish"):
            if phase != "plan":
                notes.append(f"milestone complete: {st['milestone']}")
            if phase == "build":
                notes += self._checkpoint()
            self._route()
        elif phase == "verdict":
            notes += self._apply_verdict(st["verdicts"][-1])
        elif phase == "awaiting-human":
            self._resume()
        return notes

    def _route(self):
        """Send the run to whatever comes next: failing work first, then the verdict it has earned."""
        st, passed = self.state, self.state.get("passed_verdicts", [])
        if self.stage() == "slice":
            m = self.earliest_failing_ms(SLICE_MS)
            if m == SLICE_MS[0]:
                st.update(phase="build", milestone=m, task=None)
            elif "core-loop" not in passed:
                self._enter_verdict("core-loop")  # the core loop is judged on bots before the slice is polished
            elif m:
                st.update(phase="build", milestone=m, task=None)
            else:
                self._enter_verdict("slice")
            return
        m = self.earliest_failing_ms(self.build_ms())
        if m:
            st.update(phase="build", milestone=m, task=None)
        elif "full" not in passed:
            self._enter_verdict("full")
        elif not self.has_polish_features():
            st.update(phase="polish", milestone=POLISH, task="game-polish")
        elif self.failing([POLISH]):
            st.update(phase="polish", milestone=POLISH, task=None)
        elif "final" not in passed:
            self._enter_verdict("final")
        elif self.queue(playtests=False):
            self._stop(None, {"phase": "done"})
        else:
            st.update(phase="done", milestone=None, task=None)

    def _enter_verdict(self, scope):
        self.state.update(phase="verdict", milestone=None, verdict_scope=scope,
                          verdict_index=len(self.state.get("verdicts", [])), task=f"game-verdict {scope}")

    def _reopen(self, entry):
        st = self.state
        st["human_queue"] = [e for e in st["human_queue"] if e is not entry]
        self._enter_verdict(entry["scope"])
        st["task"] = f"game-verdict {entry['scope']} answers {entry['answers']}"
        st.update(stop_reason=None, resume=None)

    def _stop(self, reason, resume):
        self.state.update(phase="awaiting-human", milestone=None, task=None, stop_reason=reason, resume=resume)

    def _resume(self):
        st = self.state
        r = st.get("resume") or {"phase": "done"}
        st.update(resume=None, stop_reason=None)
        if r.get("restart_adr"):
            self._restart(r["restart_adr"])
        elif r.get("phase") in ("ideation", "brainstorm", "consolidate", "plan"):
            st.update(phase=r["phase"], milestone=None, task=r.get("task"))
        else:
            self._route()  # goes back to whatever still fails, or on to done

    def _apply_verdict(self, v):
        st, outcome, scope, adr = self.state, v["outcome"], v["scope"], v["adr"]
        passed = st.setdefault("passed_verdicts", [])
        if outcome == "ship":
            if scope not in passed:
                passed.append(scope)
            if scope == "slice":
                st.update(stage="production", slice_sessions=st["counters"]["sessions"],
                          phase="brainstorm", milestone=None, task=None)
                return [f"verdict slice: ship; production begins ({st['slice_sessions']} sessions for the slice)"]
            self._route()
            return [f"verdict {scope}: ship"]
        if outcome == "kill":
            self._stop(f"kill condition met ({adr}): keep going, restart from ideation, or stop the game",
                       {"restart_adr": adr})
            return [f"verdict {scope}: kill condition met; a human decides"]
        st["passed_verdicts"] = [s for s in passed if SCOPES.index(s) < SCOPES.index(scope)]
        key, limit = ("adjusts", "max_adjusts") if outcome == "adjust" else ("restarts", "max_restarts")
        st["counters"][key] += 1
        over = st["counters"][key] > st["limits"][limit]
        if outcome == "adjust":
            task = f"game-plan adjust {adr}"
            if over:
                self._stop(f"adjust limit reached ({st['limits'][limit]})", {"phase": "plan", "task": task})
                return [f"verdict {scope}: adjust, over limit: a human decides next"]
            st.update(phase="plan", milestone=None, task=task)
            return [f"verdict {scope}: adjust {st['counters']['adjusts']}/{st['limits']['max_adjusts']}"]
        if over:
            self._stop(f"restart limit reached ({st['limits'][limit]})", {"restart_adr": adr})
            return [f"verdict {scope}: restart, over limit: a human decides next"]
        return self._restart(adr)

    def _restart(self, adr):
        st = self.state
        n = st["counters"]["restarts"]
        archive = self.dir / "archive" / f"restart-{n}"
        archive.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.features_path, archive / "features.json")
        self._write(archive / "human-queue.json", st.get("human_queue", []))
        self.features["features"] = []
        self._write(self.features_path, self.features)
        st.update(phase="ideation", stage="slice", milestone=None, task=f"game-ideation restart {adr}",
                  restart_adr=adr, passed_verdicts=[], slice_sessions=None, adapter_verified=False,
                  checkpoint_due=False, human_queue=[], attempts={})
        self.commit(f"restart {n}", self.features_path, archive / "features.json", archive / "human-queue.json")
        return [f"restart {n}: definition of done and human queue archived to {archive.relative_to(self.root)}; "
                "close their open tickets"]

    def _checkpoint(self):
        st = self.state
        budget, pool = st["limits"].get("budget_sessions"), self.build_ms()
        if not budget or st.get("milestone") not in pool:
            return []
        done_share = (pool.index(st["milestone"]) + 1) / len(pool)
        used_share = st["counters"]["sessions"] / budget
        st["checkpoint_due"] = used_share > done_share + 0.1
        return [f"checkpoint: {used_share:.0%} of budget used, {done_share:.0%} of build milestones done"
                + (" -> behind: checkpoint due" if st["checkpoint_due"] else "")]

    def tick(self, action):
        st = self.state
        st["counters"]["sessions"] += 1
        if "game-brainstorm" in action:
            st["counters"]["brainstorm_sessions"] += 1
        last = st["last_dispatch"]
        last["repeats"] = last["repeats"] + 1 if last.get("action") == action else 1
        last["action"] = action
        passing = {f.get("id") for f in self.items() if f.get("passes")}
        st["attempts"] = {k: v for k, v in st["attempts"].items() if k not in passing}
        m = re.match(r"game-build (\S+)", action)
        if m:
            st["attempts"][m.group(1)] = st["attempts"].get(m.group(1), 0) + 1

    # ---------- next action ----------
    def next_action(self, no_user=False):
        st, phase = self.state, self.state["phase"]
        if self.pending_playtest() and phase in REOPENABLE:
            return "advance"
        if phase in ("done", "awaiting-human"):
            if phase == "awaiting-human" and not self.gate():
                return "advance"
            if not self.gdd_stale():
                if phase == "done":
                    kits = len(self.queue(playtests=True))
                    return "stop: done" + (f" ({kits} playtest kit(s) await answers; answers reopen the verdict)"
                                           if kits else "")
                return f"stop: {st.get('stop_reason') or 'waiting on the human queue'} ({len(self.queue(False))} open)"
            action = "game-gdd"  # people read the GDD while the run waits
        else:
            errs = self.check()
            action = "fix: " + "; ".join(errs[:3]) if errs else self._work(no_user)
            if action == "advance" or action.startswith("stop:"):
                return action
        budget = st["limits"].get("budget_sessions")
        if budget and st["counters"]["sessions"] >= budget:
            return "stop: budget exhausted (raise limits.budget_sessions in docs/game/state.json to continue)"
        last = st["last_dispatch"]
        if last.get("action") == action and last.get("repeats", 0) >= st["limits"]["max_repeats"]:
            return (f"stop: stalled on '{action}' after {last['repeats']} dispatches; fix the cause, "
                    "then set last_dispatch.repeats to 0 in docs/game/state.json")
        return action

    def _work(self, no_user=False):
        """The next action. Ideation and brainstorm topics happen with a person (`with-user:`); without one,
        the run does whatever else it can and stops only when nothing else is left."""
        st, phase, m = self.state, self.state["phase"], self.state.get("milestone")
        if phase in ("build", "polish") and st.get("checkpoint_due"):
            return "game-plan checkpoint"
        waiting = None
        topic = self._topic_action()  # design questions the work depends on come first
        if topic:
            if not no_user:
                return f"with-user: {topic}"
            waiting = topic
        if phase in ("build", "verdict", "polish"):
            pool = self.build_ms() if phase == "polish" else self.green_pool()
            action = self._build_action(pool)  # judge and polish only a green build
            if action:
                return action
        if phase == "verdict":
            entry = self.playtest_entry(st.get("verdict_scope"))
            if entry and (self.root / entry["answers"]).exists():
                return f"game-verdict {st['verdict_scope']} answers {entry['answers']}"
            if entry and st.get("verdict_scope") == "slice":
                return (f"stop: waiting for the slice playtest: a person plays the build with the kit "
                        f"({entry.get('how', 'see the human queue')}) and writes {entry['answers']}; then run /game-next")
        task = st.get("task")
        if task and task.startswith("game-ideation"):
            if not no_user:
                return f"with-user: {task}"
            waiting = waiting or task
        elif task:
            return task
        if phase == "polish":
            action = self._build_action([POLISH])
            if action:
                return action
        if phase in ("build", "polish"):
            action = self._nice_action(m)
            if action:
                return action
        if waiting:
            return f"stop: waiting for a person: start a session with someone present and run /game-next to do '{waiting}' together"
        if self.gate():
            if phase == "verdict":
                return f"game-verdict {st.get('verdict_scope')}"
            if phase == "brainstorm":
                return "with-user: game-brainstorm"
            return f"game-{phase}"
        if phase != "setup" and self.gdd_stale():
            return "game-gdd"  # the human GDD catches up before every phase or milestone change
        return "advance"

    def _topic_action(self):
        phase = self.state["phase"]
        if phase == "brainstorm":
            allowed = ["core"] if self.brainstorm_share_spent() else ["core", "support"]
            candidates = [t for t in self.open_topics(allowed) if self.in_stage(t)]
        elif phase in TOPIC_PHASES:
            needed = {f["id"] for f in self.failing(self.green_pool() or self.milestones())}
            candidates = [t for t in self.open_topics()
                          if (t.get("priority") == "core" and self.in_stage(t)) or needed & set(t.get("unblocks", []))]
        else:
            candidates = []
        if not candidates:
            return None
        return f"game-brainstorm {candidates[0]['id']} \"{candidates[0]['title']}\""

    def _build_action(self, pool):
        failing = self.failing(pool)
        if not failing:
            return None
        ready = [f for f in failing if not self.is_blocked(f) and not self.waits_on_topic(f)]
        if not ready:
            stuck = [f for f in failing if self.is_blocked(f)]
            return "game-plan unblock " + " ".join(f["id"] for f in stuck) if stuck else None
        alts = ", ".join(f["id"] for f in ready[1:3])
        return f"game-build {ready[0]['id']} \"{ready[0]['title']}\"" + (
            f" (if its tickets are blocked: {alts})" if alts else "")

    def _nice_action(self, milestone):
        st = self.state
        left = (st["limits"].get("budget_sessions") or 0) - st["counters"]["sessions"]
        remaining_must = len(self.failing(self.milestones()))
        nice = [f for f in self.failing([milestone], tier="nice") if not self.is_blocked(f) and not self.waits_on_topic(f)]
        if nice and left > 2 * remaining_must + NICE_RESERVE:
            return f"game-build {nice[0]['id']} \"{nice[0]['title']}\" (nice)"
        return None

    # ---------- report ----------
    def status(self, no_user=False):
        st, c, lim = self.state, self.state["counters"], self.state["limits"]
        out = [f"stage: {self.stage()}"
               + (f" (the slice took {st['slice_sessions']} sessions)" if st.get("slice_sessions") else "")
               + f"  phase: {st['phase']}"
               + (f"  milestone: {st['milestone']}" if st.get("milestone") else "")
               + (f"  scope: {st['verdict_scope']}" if st["phase"] == "verdict" else "")
               + f"  sessions: {c['sessions']}/{lim.get('budget_sessions') or '-'}"
               + f"  adjusts: {c['adjusts']}/{lim['max_adjusts']}  restarts: {c['restarts']}/{lim['max_restarts']}"]
        if st.get("task"):
            out.append(f"task: {st['task']}")
        if self.topics():
            by = {s: [t for t in self.topics() if t.get("status") == s] for s in TOPIC_STATUSES}
            open_by = ", ".join(f"{p} {sum(t.get('priority') == p for t in by['open'])}" for p in PRIORITIES)
            out.append(f"topics: open ({open_by}) | resolved {len(by['resolved'])} | deferred {len(by['deferred'])}"
                       f" | brainstorm sessions {c['brainstorm_sessions']}"
                       f"/{int(lim['brainstorm_share'] * (lim.get('budget_sessions') or 0))}")
        if self.items():
            out.append("definition of done (must done/total | nice done/total | cut | blocked):")
            for m in self.milestones():
                fs = [f for f in self.items() if f.get("milestone") == m]
                if not fs:
                    continue
                must = [f for f in fs if f.get("tier") == "must"]
                nice = [f for f in fs if f.get("tier") == "nice"]
                out.append(f"  {m:<14} {sum(self.is_done(f) for f in must)}/{len(must)} | "
                           f"{sum(self.is_done(f) for f in nice)}/{len(nice)} | "
                           f"{sum(f.get('tier') == 'cut' for f in fs)} | "
                           f"{sum(self.is_blocked(f) and not self.is_done(f) for f in fs)}")
        items, targets = self.fun.get("items", []), self.richness.get("targets", [])
        if items or targets:
            proxies = sum(i.get("kind") == "proxy" for i in items)
            out.append(f"fun checklist: {len(items)} items ({proxies} proxy); richness targets: {len(targets)}")
        if st.get("passed_verdicts"):
            out.append(f"verdicts passed: {', '.join(st['passed_verdicts'])}")
        if st.get("verdicts"):
            v = st["verdicts"][-1]
            out.append(f"last verdict: {v.get('scope')} -> {v.get('outcome')} ({v.get('adr')})")
        out.append(f"human GDD: {'stale' if self.gdd_stale() else 'in sync'}")
        for e in self.queue()[:5]:
            out.append(f"human queue: {e.get('id')} {e.get('what')}")
        why = self.gate()
        out.append(f"gate: {'PASS' if not why else 'FAIL: ' + '; '.join(why[:4]) + (' ...' if len(why) > 4 else '')}")
        out.append(f"next: {self.next_action(no_user)}")
        return "\n".join(out)


def find_root(argv):
    if "--root" in argv:
        return Path(argv[argv.index("--root") + 1]).resolve()
    here = Path(__file__).resolve().parent
    if here.name == "game" and here.parent.name == "docs":
        return here.parent.parent
    return Path.cwd()


def main(argv):
    cmd = argv[0] if argv and not argv[0].startswith("--") else "status"
    game = Game(find_root(argv))
    st = game.state
    if cmd == "init":
        game.dir.mkdir(parents=True, exist_ok=True)
        for path, data in ((game.state_path, game.state), (game.features_path, game.features),
                           (game.fun_path, game.fun), (game.richness_path, game.richness),
                           (game.topics_path, game.topics_data), (game.keep_path, game.keep),
                           (game.wiki_index_path, game.wiki_index), (game.vision_path, game.vision_data)):
            if not path.exists():
                game._write(path, data)
                print(f"created {path.relative_to(game.root)}")
        for name, text in DEFAULT_TEXT.items():
            if not (game.dir / name).exists():
                (game.dir / name).write_text(text, encoding="utf-8")
                print(f"created docs/game/{name}")
        return 0
    if cmd == "status":
        print(game.status(no_user="--no-user" in argv))
        return 0
    if cmd == "check":
        since = argv[argv.index("--since") + 1] if "--since" in argv else "HEAD"
        errs = game.check(since)
        print("\n".join(errs) if errs else "check: ok")
        return 1 if errs else 0
    if cmd == "gate":
        why = game.task_gate() if st.get("task") else game.gate()
        print("\n".join(why) if why else f"gate {st['phase']}: PASS")
        return 1 if why else 0
    if cmd == "complete":
        problems = game.check() + game.task_gate()
        if problems:
            print("cannot complete:\n" + "\n".join(problems))
            return 1
        done = st.get("task")
        st["task"] = None
        if st["phase"] == "verdict":  # answers read by this verdict are consumed with it
            st["human_queue"] = [e for e in st["human_queue"] if not (
                e.get("kind") == "playtest" and e.get("scope") == st.get("verdict_scope")
                and (game.root / e.get("answers", "")).is_file())]
        game.save_state(f"complete {done}")
        print(f"complete: {done}\nnext: {game.next_action()}")
        return 0
    if cmd == "gdd-synced":
        head = game._git("rev-parse", "HEAD").stdout.strip() if game.in_git() else None
        if not head:
            print("cannot record the sync: commit the wiki first")
            return 1
        st["gdd_synced"] = head
        game.save_state("human GDD synced")
        print(f"gdd synced at {head[:8]}\nnext: {game.next_action()}")
        return 0
    if cmd == "advance":
        if game.next_action() != "advance":
            print(f"cannot advance: next is '{game.next_action()}'")
            return 1
        before = st["phase"]
        notes = game.advance()
        where = f"{st['phase']}" + (f" ({st['milestone']})" if st.get("milestone") else "")
        game.save_state(f"{before} -> {where}")
        for note in notes:
            print(note)
        print(f"{before} -> {where}")
        print(f"next: {game.next_action()}")
        return 0
    if cmd == "tick":
        if len(argv) < 2 or argv[1].startswith("--"):
            print('usage: gamestate.py tick "<the next: action being dispatched>"')
            return 2
        game.tick(argv[1])
        game.save_state(f"dispatch {argv[1]}")
        print(f"sessions: {st['counters']['sessions']}/{st['limits'].get('budget_sessions') or '-'}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
