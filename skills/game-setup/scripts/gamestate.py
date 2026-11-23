#!/usr/bin/env python3
"""State tool for the game-* skills. Python 3.8+, standard library only.

game-setup copies this file to docs/game/gamestate.py in the game's repo.

Commands:
  init               create any missing state files under docs/game/
  upgrade            bring an older game's state to this tool's version: a game
                     still at setup is reset (limits, counters, human_queue and
                     adapter_verified kept; milestones refreshed); later phases
                     apply MIGRATIONS. Refuses, changing nothing, a missing,
                     newer or malformed state, or a phase with no migration
  status [--no-user] one-screen summary, ending with the `next:` action.
                     --no-user: nobody is there to talk to, so skip `with-user:`
                     work (ideation, research homework, brainstorm topics) and do
                     what else can be done
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

PHASES = ["setup", "scan", "ideation", "research", "brainstorm", "consolidate", "plan", "build", "verdict", "polish",
          "awaiting-human", "done"]
DESIGN_PHASES = ["setup", "scan", "ideation", "research", "brainstorm", "consolidate"]  # the bar is set here
PHASE_SKILLS = {"scan": "game-research"}  # phases whose skill isn't game-<phase>
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
ROLES = ["creative", "design", "feel", "art", "audio", "narrative", "ux"]
TASTE_AREAS = ["Screens and onboarding", "Feel", "Art", "Audio", "Narrative and world"]
AREAS = ["Vision", "Mechanics", "Controls", "Systems", "Content", "Modes and sessions",
         "Screens and onboarding", "Feel", "Art", "Audio", "Narrative and world"]
AREA_ROLES = {"Art": "art", "Audio": "audio", "Narrative and world": "narrative"}  # areas that vanish with their role
SLICE_AREAS = [a for a in AREAS if a != "Modes and sessions"]
REQUIRED_PAGES = ["vision", "slice", "concepts"]
QUALITY_ASPECTS = ["code", "feel", "art", "audio", "ui", "onboarding"]
QUALITY_BARS = ["placeholder", "representative", "production", "final"]
FUN_FIELDS = ["statement", "scope", "kind", "metric", "threshold", "how"]
RICH_FIELDS = ["aspect", "scope", "statement", "metric", "threshold", "how"]
REVIEW_RESULTS = ["ok", "notes", "not-assessed"]
SEVERITIES = ["blocking", "advisory"]
ANCHOR_KINDS = ["label", "reference", "rule"]
FUN_KINDS = ["proxy", "human", "review"]
CALIBRATED_ROLES = ["creative", "feel", "art", "ux"]  # roles whose taste judgments need the person's labels first
LABELS = "docs/game/calibration/labels.json"
DECISION_RE = r"^(fixed [0-9a-f]{7,40}|feature F\d+|topic T\d+|wontfix: \S.*)$"
MIN_SEED_TOPICS = 5
INTENTS = ["sell", "hobby"]
REF_WHY = ["comp", "aspect"]
REF_STATUSES = ["candidate", "open", "studied"]
HOW_STUDIED = ["played", "watched", "read", "not-assessed"]
HOMEWORK_STATUSES = ["open", "answered", "skip"]
MAX_HOMEWORK = 10
MIN_COMPS = 3
MIN_SOURCES = 3
IMAGE_ROLES = ["art", "ux", "feel"]  # dossier sections that need an image in refs/<id>/<role>/ unless not assessed
IMAGE_TYPES = (".png", ".jpg", ".jpeg", ".webp")
PAGE_ROLES = ("feel", "art", "audio", "narrative", "ux")  # roles whose page ideation seeds a slice topic for
NICE_RESERVE = 10  # sessions kept back for verdicts and polish before nice features are built

QUEUE_KINDS = ["playtest", "calibrate", "compare"]
TARGETS = ["visual", "feel"]  # a feature's target: the visual look or the feel the slice is built to fix

CURRENT_VERSION = 7
# from_version -> migrate(game) -> notes; brings game.state to from_version + 1. Write files with
# game._write, so `upgrade` commits them.
# Empty so far: a game past setup can't be upgraded until a release adds entries.
MIGRATIONS = {}

DEFAULT_STATE = {
    "version": CURRENT_VERSION,
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
    "docs_verified": None,
    "intent": None,
    "research_sources": None,
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
DEFAULT_REFERENCES = {"scanned_for": None, "refs": []}  # research files: the research skill writes them, init doesn't
DEFAULT_HOMEWORK = {"reason": "", "items": []}
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


def whole(value):
    return isinstance(value, int) and not isinstance(value, bool)


class UpgradeError(Exception):
    pass


class GitHistory:
    """The game's git history: the only code that runs git. Paths are relative to the root, which is the repo's top."""

    def __init__(self, root: Path):
        self.root = root

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True)

    def in_repo(self):
        try:
            return self._git("rev-parse", "--is-inside-work-tree").stdout.strip() == "true"
        except FileNotFoundError:  # git isn't installed
            return False

    def tracked(self, rel):
        return self._git("ls-files", "--error-unmatch", "--", rel).returncode == 0

    def commit(self, message, rels):
        """Stage and commit these paths only, a tracked one that was removed included; other staged work stays."""
        if rels:
            self._git("add", "--", *rels)
            self._git("commit", "-q", "-m", message, "--", *rels)

    def head(self):
        """The current commit, or None before the first one."""
        r = self._git("rev-parse", "--verify", "-q", "HEAD")
        return r.stdout.strip() if r.returncode == 0 else None

    def show(self, commit, rel):
        """The file's text at that commit; None when the commit is unknown or the file isn't in it."""
        r = self._git("show", f"{commit}:{rel}")
        return r.stdout if r.returncode == 0 else None

    def changed(self, a, b, rels):
        """The paths that differ between commits a and b; all of them when either commit is unknown."""
        r = self._git("diff", "--name-only", a, b, "--", *rels)
        return r.stdout.splitlines() if r.returncode == 0 else list(rels)

    def is_ancestor(self, a, b):
        return self._git("merge-base", "--is-ancestor", a, b).returncode == 0


class Game:
    def __init__(self, root: Path, history=None):
        self.root = root
        self.history = history or GitHistory(root)  # the tests pass an in-memory stand-in
        self.dir = root / "docs" / "game"
        self.state_path = self.dir / "state.json"
        self.features_path = self.dir / "features.json"
        self.fun_path = self.dir / "fun-checklist.json"
        self.richness_path = self.dir / "richness.json"
        self.topics_path = self.dir / "topics.json"
        self.keep_path = self.dir / "keep.json"
        self.wiki_index_path = self.dir / "wiki.json"
        self.vision_path = self.dir / "vision.json"
        self.research_dir = self.dir / "research"
        self.references_path = self.research_dir / "references.json"
        self.homework_path = self.research_dir / "homework.json"
        self.written = []  # every file this run wrote, so the command that wrote them can commit them
        self.state = self._load(self.state_path, DEFAULT_STATE)
        self.found_version = self._found_version()
        self.features = self._load(self.features_path, DEFAULT_FEATURES)
        self.fun = self._load(self.fun_path, DEFAULT_FUN)
        self.richness = self._load(self.richness_path, DEFAULT_RICHNESS)
        self.topics_data = self._load(self.topics_path, DEFAULT_TOPICS)
        self.keep = self._load(self.keep_path, DEFAULT_KEEP)
        self.wiki_index = self._load(self.wiki_index_path, DEFAULT_WIKI, shape_checked=True)
        self.vision_data = self._load(self.vision_path, DEFAULT_VISION, shape_checked=True)
        self.references_data = self._load(self.references_path, DEFAULT_REFERENCES, shape_checked=True)
        self.homework_data = self._load(self.homework_path, DEFAULT_HOMEWORK, shape_checked=True)

    def _read(self, path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"error: {path.relative_to(self.root)} is not valid JSON: {e}")

    def _load(self, path, default, shape_checked=False):
        """The file merged over its defaults. A file that isn't a JSON object stops the tool, unless its
        shape check reports it (then it is returned as is)."""
        merged = copy(default)
        if not path.exists():
            return merged
        data = self._read(path)
        if not isinstance(data, dict):
            if shape_checked:
                return data
            sys.exit(f"error: {path.relative_to(self.root)} must hold a JSON object, not {type(data).__name__}")
        for key, value in data.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key].update(value)
            else:
                merged[key] = value
        return merged

    def _found_version(self):
        """The version written in state.json: 1 when absent, None without a state.json (_load fills in the default)."""
        if not self.state_path.exists():
            return None
        return self._read(self.state_path).get("version", 1)

    def older(self):
        """The game's state predates this tool."""
        return whole(self.found_version) and self.found_version < CURRENT_VERSION

    # ---------- persistence ----------
    def _write(self, path, data):
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.written.append(path)

    def in_git(self):
        return self.history.in_repo()

    def commit(self, message, *paths):
        """Commit only the given paths, a tracked one that was removed included; leaves any other staged work alone."""
        if not self.in_git():
            return
        rel = [p.relative_to(self.root).as_posix() for p in paths]
        self.history.commit(f"game-state: {message}",
                            [r for r in rel if (self.root / r).exists() or self.history.tracked(r)])

    def write_missing_files(self):
        """Create every state file that doesn't exist yet; returns the paths created, relative to the root."""
        self.dir.mkdir(parents=True, exist_ok=True)
        created = []
        for path, data in ((self.state_path, self.state), (self.features_path, self.features),
                           (self.fun_path, self.fun), (self.richness_path, self.richness),
                           (self.topics_path, self.topics_data), (self.keep_path, self.keep),
                           (self.wiki_index_path, self.wiki_index), (self.vision_path, self.vision_data)):
            if not path.exists():
                self._write(path, data)
                created.append(path.relative_to(self.root).as_posix())
        for name, text in DEFAULT_TEXT.items():
            if not (self.dir / name).exists():
                (self.dir / name).write_text(text, encoding="utf-8")
                created.append(f"docs/game/{name}")
        return created

    def upgrade(self):
        """Bring the state to CURRENT_VERSION; returns notes. Raises UpgradeError, changing nothing, when it can't."""
        old = self.found_version
        if old is None:
            raise UpgradeError("no game state here (docs/game/state.json is missing): nothing to upgrade; "
                               "set the game up with game-setup, which runs `gamestate.py init`")
        if not whole(old):
            raise UpgradeError(f"docs/game/state.json version {old!r} is not a whole number: set it to the "
                               "version of the tool that wrote the game (a missing version counts as 1)")
        if old > CURRENT_VERSION:
            raise UpgradeError(f"this game is at version {old}, newer than this tool ({CURRENT_VERSION}): "
                               "nothing changed; update the plugin and use its gamestate.py")
        if old == CURRENT_VERSION:
            return [f"already at version {CURRENT_VERSION}"]
        if self.state.get("phase") == "setup":
            fresh = copy(DEFAULT_STATE)
            for key in ("limits", "counters", "human_queue", "adapter_verified"):
                fresh[key] = self.state.get(key, fresh[key])
            fresh["task"] = "game-setup upgrade"
            self.state.clear()
            self.state.update(fresh)
            self._write(self.state_path, self.state)
            self.features["milestones"] = list(MILESTONES)  # no features exist yet at setup
            self._write(self.features_path, self.features)
            self.found_version = CURRENT_VERSION
            notes = [f"version {old} -> {CURRENT_VERSION}"]
            return notes + [f"created {path}" for path in self.write_missing_files()]
        missing = [v for v in range(old, CURRENT_VERSION) if v not in MIGRATIONS]
        if missing:
            raise UpgradeError(f"upgrade from version {old} in phase {self.state.get('phase')} isn't supported "
                               f"(no migration from version {missing[0]}): nothing changed; finish this game with "
                               "the plugin release it was made with")
        notes = []
        for v in range(old, CURRENT_VERSION):
            notes += MIGRATIONS[v](self)
            self.state["version"] = v + 1
        self._write(self.state_path, self.state)
        self.found_version = CURRENT_VERSION
        return [f"version {old} -> {CURRENT_VERSION}"] + notes

    def save_state(self, message):
        self._write(self.state_path, self.state)
        self.commit(message, self.state_path)

    # ---------- derived views ----------
    @staticmethod
    def text(path):
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def wiki_pages(self):
        """The well-formed page entries; _wiki_shape reports the rest."""
        pages = self.wiki_index.get("pages") if isinstance(self.wiki_index, dict) else None
        if not isinstance(pages, list):
            return []
        return [p for p in pages if isinstance(p, dict) and isinstance(p.get("id"), str) and p["id"]]

    def page_ids(self):
        return {p["id"] for p in self.wiki_pages()}

    def _wiki_shape(self):
        """Reasons wiki.json has a value of the wrong type; wiki_pages() leaves those entries out."""
        if not isinstance(self.wiki_index, dict):
            return ["wiki.json is not an object"]
        pages = self.wiki_index.get("pages", [])
        if not isinstance(pages, list):
            return ["wiki.json pages is not a list"]
        why = []
        for n, p in enumerate(pages, 1):
            if not isinstance(p, dict):
                why.append(f"wiki.json pages: entry {n} is not an object")
            elif not (isinstance(p.get("id"), str) and p["id"]):
                why.append(f"wiki.json pages: entry {n} has no id")
        return why

    @staticmethod
    def page_list(owner, pages):
        """Reasons a feature's or topic's `pages` isn't a list of page ids."""
        if isinstance(pages, list) and all(isinstance(p, str) for p in pages):
            return []
        return [f"{owner}: pages must be a list of page ids"]

    def vision(self):
        return self.vision_data if isinstance(self.vision_data, dict) else {}

    def active_roles(self):
        off = self.vision().get("roles_off")
        off = off if isinstance(off, dict) else {}
        return [r for r in ROLES if r not in off]

    def _check_roles(self, owner, roles, on_feature=False):
        """Reasons a topic's or feature's `roles` isn't a list of active role ids."""
        if not isinstance(roles, list):
            return [f"{owner}: roles must be a list"]
        errs, active = [], self.active_roles()
        for r in roles:
            if r not in ROLES:
                errs.append(f"{owner}: role '{r}' is not one of {ROLES}")
            elif r not in active:
                errs.append(f"{owner}: role '{r}' is switched off in vision.json roles_off")
            elif r == "design" and on_feature:
                errs.append(f"{owner}: design judges at verdicts, not on features")
        return errs

    def pillars(self):
        pillars = self.vision().get("pillars")
        if not isinstance(pillars, list):
            return None
        return [p.get("id") for p in pillars if isinstance(p, dict)]

    def _vision_shape(self):
        """Reasons vision.json has a value of the wrong type, so later reads can trust the shapes."""
        if not isinstance(self.vision_data, dict):
            return ["vision.json is not an object"]
        v, why = self.vision_data, []
        pillars = v.get("pillars", [])
        if not isinstance(pillars, list):
            why.append("vision.json pillars is not a list")
        else:
            why += [f"vision.json pillars: entry {n} is not an object"
                    for n, p in enumerate(pillars, 1) if not isinstance(p, dict)]
        if not isinstance(v.get("anti_pillars", []), list):
            why.append("vision.json anti_pillars is not a list")
        for key in ("slice", "directions"):
            if not isinstance(v.get(key, {}), dict):
                why.append(f"vision.json {key} is not an object")
        sl = v.get("slice")
        if isinstance(sl, dict) and not isinstance(sl.get("quality_bar", {}), dict):
            why.append("vision.json slice quality_bar is not an object")
        if not isinstance(v.get("north_stars", {}), dict):
            why.append("vision.json north_stars is not an object")
        if not isinstance(v.get("invariants", []), list):
            why.append("vision.json invariants is not a list")
        off = v.get("roles_off", {})
        if not isinstance(off, dict):
            why.append("vision.json roles_off is not an object")
        else:
            why += [f"vision.json roles_off: {r} has no reason" for r, reason in off.items()
                    if not str(reason or "").strip()]
        return why

    def references(self):
        """The well-formed reference entries in references.json; _check_research reports the rest."""
        refs = self.references_data.get("refs") if isinstance(self.references_data, dict) else None
        if not isinstance(refs, list):
            return []
        return [r for r in refs if isinstance(r, dict) and isinstance(r.get("id"), str) and r["id"]]

    def homework(self):
        items = self.homework_data.get("items") if isinstance(self.homework_data, dict) else None
        return [i for i in items if isinstance(i, dict)] if isinstance(items, list) else []

    def homework_open(self):
        return [i for i in self.homework() if i.get("status") == "open"]

    @staticmethod
    def ref_roles(entry):
        roles = entry.get("roles")
        return [r for r in roles if isinstance(r, str)] if isinstance(roles, list) else []

    @staticmethod
    def ref_homework(entry):
        """The candidate homework a reference names for what the agent couldn't reach; [] when malformed."""
        hw = entry.get("homework", [])
        if not isinstance(hw, list) or not all(isinstance(h, str) and h.strip() for h in hw):
            return []
        return hw

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
        return bool(self.history.changed(synced, "HEAD", sources))

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
        if self.found_version is not None and not whole(self.found_version):
            errs.append(f"state.json version {self.found_version!r} is not a whole number: set it to the version "
                        "of the tool that wrote the game")
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
        errs += self._wiki_shape()
        errs += self._check_wiki()
        errs += self._vision_shape()
        errs += self._check_keep()
        errs += self._check_reviews()
        errs += self._check_labels()
        errs += self._check_research()
        if st.get("phase") == "research":  # a role that lost its reference is a fix: step
            errs += self._reference_coverage()
        if self.stage() not in STAGES:
            errs.append(f"state.stage must be one of {STAGES}")
        for e in self.queue():
            if not e.get("id") or not e.get("what"):
                errs.append("human_queue entries need id and what")
            if e.get("kind") == "playtest" and not (e.get("scope") in SCOPES and e.get("answers")):
                errs.append(f"human_queue {e.get('id')}: a playtest entry needs scope in {SCOPES} and answers")
            if e.get("kind") == "calibrate" and not (e.get("how") and e.get("answers")):
                errs.append(f"human_queue {e.get('id')}: a calibrate entry needs how and answers")
            if e.get("kind") == "compare" and not (e.get("how") and e.get("answers") and e.get("unblocks")):
                errs.append(f"human_queue {e.get('id')}: a compare entry needs how, answers and unblocks")
        for v in st.get("verdicts", []):
            if v.get("outcome") not in OUTCOMES or not v.get("adr") or v.get("scope") not in SCOPES:
                errs.append(f"verdict {v.get('scope')}: needs scope in {SCOPES}, outcome in {OUTCOMES} and an adr path")
        if st.get("phase") not in PLANNING_PHASES:
            errs += self._feature_guard(since)
            errs += self._review_guard(since)
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
            pages = f.get("pages", [])
            bad = self.page_list(fid, pages)
            errs += bad or [f"{fid}: page '{p}' is not in wiki.json" for p in pages if p not in page_ids]
            if "target" in f and f["target"] not in TARGETS:
                errs.append(f"{fid}: target must be one of {TARGETS}")
            roles = f.get("roles", [])
            errs += self._check_roles(fid, roles, on_feature=True)
            if not roles:
                taste = {p["id"] for p in self.wiki_pages() if p.get("area") in TASTE_AREAS}
                if verify.get("kind") == "capture" or (not bad and taste & set(pages)):
                    errs.append(f"{fid}: visible work needs roles (pages in {TASTE_AREAS} or verify kind capture)")
        if (any(f.get("passes") and f.get("target") == "visual" for f in self.items())
                and not (self.root / LABELS).exists()
                and not any(e.get("kind") == "calibrate" for e in self.queue())):
            errs.append("the visual target passes: queue a calibrate entry for a person (kind calibrate)")
        return errs

    def _check_labels(self):
        path = self.root / LABELS
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            return ["calibration labels: not valid JSON"]
        if not isinstance(data, dict) or not isinstance(data.get("labels"), list):
            return ["calibration labels: must be an object with a labels list"]
        errs = []
        for n, label in enumerate(data["labels"]):
            if not isinstance(label, dict):
                errs.append(f"calibration labels: entry {n} must be an object")
                continue
            if not label.get("capture"):
                errs.append(f"calibration labels: entry {n} needs a capture")
            if not isinstance(label.get("ours"), bool):
                errs.append(f"calibration labels: entry {n} needs ours true or false")
            if not (isinstance(label.get("why"), str) and label["why"].strip()):
                errs.append(f"calibration labels: entry {n} needs a why")
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
            if i.get("kind") not in FUN_KINDS:
                errs.append(f"fun {iid}: kind must be one of {FUN_KINDS}")
            if i.get("kind") == "proxy" and not all(i.get(k) for k in ("metric", "threshold", "how")):
                errs.append(f"fun {iid}: a proxy item needs metric, threshold and how")
            if i.get("kind") == "review":
                if not i.get("roles"):
                    errs.append(f"fun {iid}: a review item needs roles")
                if "roles" in i:
                    errs += self._check_roles(f"fun {iid}", i["roles"])
                if not isinstance(i.get("taste"), bool):
                    errs.append(f"fun {iid}: taste must be true or false")
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
            roles = t.get("roles", [])
            errs += self._check_roles(f"topic {tid}", roles)
            if t.get("status") == "open" and not roles:
                errs.append(f"topic {tid}: open without roles (who prepares its challenges?)")
            pages, bad = t.get("pages", []), self.page_list(f"topic {tid}", t.get("pages", []))
            errs += bad
            if not bad and t.get("status") == "resolved":
                if not pages:
                    errs.append(f"topic {tid}: resolved without a wiki page it wrote or updated")
                errs += [f"topic {tid}: page '{p}' is not in wiki.json" for p in pages if p not in page_ids]
        return errs

    def _check_wiki(self):
        errs, seen = [], set()
        open_topics = {t.get("id") for t in self.topics() if t.get("status") == "open"}
        for p in self.wiki_pages():
            pid = p["id"]
            if pid in seen:
                errs.append(f"page {pid}: duplicate id")
            seen.add(pid)
            errs += [f"page {pid}: missing {key}" for key in ("title", "version", "updated")
                     if p.get(key) is None or str(p.get(key)).strip() == ""]
            if p.get("area") not in AREAS:
                errs.append(f"page {pid}: area '{p.get('area')}' is not one of {AREAS}")
            link = p.get("link") or ""
            if not link:
                errs.append(f"page {pid}: missing link")
            elif "://" not in link and not (self.root / link).exists():
                errs.append(f"page {pid}: local link '{link}' does not exist")
            flagged = p.get("flagged")
            if flagged and not isinstance(flagged, dict):
                errs.append(f"page {pid}: flagged is not an object")
            elif flagged and flagged.get("topic") not in open_topics:
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

    # ---------- research ----------
    @staticmethod
    def _entries(label, data, key):
        """The object entries of data[key] that have an id, and the reasons data falls short of that shape."""
        if not isinstance(data, dict):
            return [], [f"{label} is not an object"]
        entries = data.get(key, [])
        if not isinstance(entries, list):
            return [], [f"{label} {key} is not a list"]
        good, why, seen = [], [], set()
        for n, e in enumerate(entries, 1):
            if not isinstance(e, dict):
                why.append(f"{label} {key}: entry {n} is not an object")
            elif not (isinstance(e.get("id"), str) and e["id"]):
                why.append(f"{label} {key}: entry {n} has no id")
            else:
                if e["id"] in seen:
                    why.append(f"{label} {e['id']}: duplicate id")
                seen.add(e["id"])
                good.append(e)
        return good, why

    @staticmethod
    def _known_roles(owner, roles):
        """Reasons a research entry's roles aren't role ids. Research outlives roles_off, so only unknown ids count."""
        if not isinstance(roles, list):
            return [f"{owner}: roles must be a list"]
        return [f"{owner}: role '{r}' is not one of {ROLES}" for r in roles if r not in ROLES]

    def _check_research(self):
        """Reasons references.json, homework.json or a reference's audit is malformed; the gates read around them."""
        refs, errs = self._entries("references.json", self.references_data, "refs")
        for r in refs:
            owner = f"references.json {r['id']}"
            if r.get("why") not in REF_WHY:
                errs.append(f"{owner}: why must be one of {REF_WHY}")
            if r.get("status") not in REF_STATUSES:
                errs.append(f"{owner}: status must be one of {REF_STATUSES}")
            errs += self._known_roles(owner, r.get("roles", []))
            if not isinstance(r.get("sources", []), list):
                errs.append(f"{owner}: sources must be a list")
            if "homework" in r and r["homework"] != [] and not self.ref_homework(r):
                errs.append(f"{owner}: homework must be a list of non-empty strings")
            how = r.get("how_studied", {})
            if not isinstance(how, dict):
                errs.append(f"{owner}: how_studied must be an object")
                continue
            for role, h in how.items():
                if role not in ROLES:
                    errs.append(f"{owner}: how_studied role '{role}' is not one of {ROLES}")
                elif not (isinstance(h, dict) and h.get("how") in HOW_STUDIED):
                    errs.append(f"{owner}: how_studied {role}: how must be one of {HOW_STUDIED}")
        if self.homework_path.exists():  # its default is empty without a reason, so only a written list is checked
            items, why = self._entries("homework.json", self.homework_data, "items")
            errs += why
            for i in items:
                if i.get("status") not in HOMEWORK_STATUSES:
                    errs.append(f"homework.json {i['id']}: status must be one of {HOMEWORK_STATUSES}")
                errs += self._known_roles(f"homework.json {i['id']}", i.get("roles", []))
            listed = self.homework_data.get("items") if isinstance(self.homework_data, dict) else None
            if isinstance(listed, list) and len(listed) > MAX_HOMEWORK:
                errs.append(f"homework.json has {len(listed)} items; keep it to {MAX_HOMEWORK} or fewer")
            if listed == [] and not str(self.homework_data.get("reason") or "").strip():
                errs.append("homework.json has no items and no reason")
        for p in sorted((self.research_dir / "refs").glob("*/audit.json")):
            errs += self._review_shape(p.relative_to(self.root).as_posix())
        return errs

    # ---------- reviews ----------
    def review(self, path):
        """The review file at path (relative to the game root) as a dict; None when missing, unreadable or not an object."""
        try:
            data = json.loads((self.root / path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def _review_shape(self, path):
        """Reasons the review file at path is malformed."""
        r = self.review(path)
        if r is None:
            return [f"{path}: not a JSON object"]
        errs = []
        if r.get("role") not in ROLES:
            errs.append(f"{path}: role '{r.get('role')}' is not one of {ROLES}")
        for key in ("target", "commit"):
            if not r.get(key):
                errs.append(f"{path}: missing {key}")
        if r.get("result") not in REVIEW_RESULTS:
            errs.append(f"{path}: result must be one of {REVIEW_RESULTS}")
        if r.get("result") == "not-assessed" and not r.get("reason"):
            errs.append(f"{path}: a not-assessed review needs a reason")
        notes = r.get("notes", [])
        if not isinstance(notes, list) or not all(isinstance(n, dict) for n in notes):
            return errs + [f"{path}: notes must be a list of objects"]
        features, topics = {f.get("id") for f in self.items()}, {t.get("id") for t in self.topics()}
        for n in notes:
            nid = n.get("id") or "<no id>"
            for key in ("id", "what", "evidence"):
                if not n.get(key):
                    errs.append(f"{path}: note {nid} is missing {key}")
            if n.get("severity") not in SEVERITIES:
                errs.append(f"{path}: note {nid} severity must be one of {SEVERITIES}")
            anchor = n.get("anchor")
            if anchor is not None and not (isinstance(anchor, dict) and anchor.get("kind") in ANCHOR_KINDS
                                           and anchor.get("ref")):
                errs.append(f"{path}: note {nid} anchor needs kind in {ANCHOR_KINDS} and a ref")
            d = n.get("decision") or ""
            if not d:
                continue  # reviews are written before the decide pass; the pass gate demands the decision
            m = re.match(DECISION_RE, str(d))
            if not m:
                errs.append(f"{path}: note {nid} decision '{d}' is not one of "
                            "fixed <commit> | feature F.. | topic T.. | wontfix: <reason>")
            elif d.startswith(("feature ", "topic ")):
                kind, ref = d.split(" ", 1)
                if ref not in (features if kind == "feature" else topics):
                    errs.append(f"{path}: note {nid} decision names {ref}, which does not exist")
        return errs

    def _check_reviews(self):
        errs = []
        for p in sorted((self.dir / "reviews").glob("*/*.json")):
            errs += self._review_shape(p.relative_to(self.root).as_posix())
        for f in self.items():
            fid, roles = f.get("id") or "<no id>", f.get("roles")
            if not f.get("passes") or not roles or not isinstance(roles, list):
                continue
            reviews = f.get("reviews") if isinstance(f.get("reviews"), dict) else {}
            for role in roles:
                if not isinstance(role, str):
                    continue  # _check_roles reports it
                r = self.review(reviews[role]) if isinstance(reviews.get(role), str) else None
                if r is None:
                    errs.append(f"{fid}: passes without a review by {role}")
                    continue
                for n in r.get("notes", []) if isinstance(r.get("notes"), list) else []:
                    if not isinstance(n, dict):
                        continue
                    d = str(n.get("decision") or "")
                    if n.get("severity") == "blocking" and not d.startswith("fixed"):
                        errs.append(f"{fid}: {role} review note {n.get('id')} is blocking and not fixed")
                    if not d:
                        errs.append(f"{fid}: {role} review note {n.get('id')} has no decision")
        return errs

    def _review_guard(self, since):
        """A feature that passes in this session needs reviews made on this session's work, not before it."""
        old_data = self._old(since, self.features_path)
        if old_data is None:
            return []
        old = {f.get("id"): f for f in old_data.get("features", [])}
        errs = []
        for f in self.items():
            fid = f.get("id")
            if fid not in old or old[fid].get("passes") or not f.get("passes"):
                continue
            reviews = f.get("reviews") if isinstance(f.get("reviews"), dict) else {}
            for role in f.get("roles") if isinstance(f.get("roles"), list) else []:
                if not isinstance(role, str):
                    continue  # _check_roles reports it
                r = self.review(reviews[role]) if isinstance(reviews.get(role), str) else None
                if r is None:
                    continue  # _check_reviews reports the missing review
                if not self.history.is_ancestor(since, str(r.get("commit"))):
                    errs.append(f"{fid}: the {role} review predates this session's work; review again")
        return errs

    def _old(self, since, path):
        if not self.in_git():
            return None
        text = self.history.show(since, path.relative_to(self.root).as_posix())
        if text is None:
            return None
        try:
            return json.loads(text)
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
            if not (self.root / "docs" / "agents" / "docs.md").exists():
                why.append("docs/agents/docs.md is missing")
            dv = st.get("docs_verified")
            if not (isinstance(dv, dict) and dv.get("place") and dv.get("date")):
                why.append("docs not verified: run the docs smoke test (game-setup)")
            if st.get("intent") not in INTENTS:
                why.append(f"state.intent must be one of {INTENTS}")
            sources = st.get("research_sources")
            if not (isinstance(sources, dict) and sources.get("checked")):
                why.append("research sources not checked (game-setup records research_sources)")
        elif phase == "scan":
            why += self._scan_gate()
        elif phase == "ideation":
            why += self._ideation_gate()
        elif phase == "research":
            why += self._research_gate()
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
        why = self._vision_shape()
        v = self.vision()
        n = len(self.pillars() or [])
        if not 3 <= n <= 4:
            why.append(f"vision.json has {n} pillars; needs 3-4")
        anti = v.get("anti_pillars") if isinstance(v.get("anti_pillars"), list) else []
        if not any(str(a).strip() for a in anti):  # a blank anti-pillar protects nothing
            why.append("vision.json has no anti-pillar")
        if not str(v.get("kill_condition") or "").strip():
            why.append("vision.json has no kill condition")
        directions = v.get("directions") if isinstance(v.get("directions"), dict) else {}
        count = directions.get("count")
        if not isinstance(count, int) or isinstance(count, bool) or not 3 <= count <= 5:
            why.append(f"vision.json directions: {count if isinstance(count, int) else 0} compared; needs 3-5")
        if not re.search(r"\bC\d+\b", str(directions.get("choice") or "")):
            why.append("vision.json directions: no choice")
        sl = v.get("slice") if isinstance(v.get("slice"), dict) else {}
        if not str(sl.get("test_question") or "").strip():
            why.append("vision.json slice: no test question")
        bar = sl.get("quality_bar") if isinstance(sl.get("quality_bar"), dict) else {}
        for aspect in QUALITY_ASPECTS:
            level = bar.get(aspect)
            if level is None:
                why.append(f"vision.json slice quality bar: {aspect} missing")
            elif level not in QUALITY_BARS:
                why.append(f"vision.json slice quality bar: {aspect} is '{level}'; needs one of {QUALITY_BARS}")
        why += self._north_star_reasons(v)
        ids = self.page_ids()
        why += [f"wiki.json has no page '{i}'" for i in REQUIRED_PAGES if i not in ids]
        seeded = [t for t in self.topics() if t.get("parent") is not None]
        if not any(t.get("stage") == "slice" for t in seeded):
            why.append("no topic marked for the vertical slice (stage: slice)")
        if len(seeded) < MIN_SEED_TOPICS:
            why.append(f"topics.json has {len(seeded)} follow-up topics; seed at least {MIN_SEED_TOPICS}")
        if not any(t.get("priority") == "core" for t in seeded):
            why.append("no core topic seeded")
        for r in self.active_roles():
            if r in PAGE_ROLES and not any(t.get("stage") == "slice" and isinstance(t.get("roles"), list)
                                           and r in t["roles"] for t in seeded):
                why.append(f"no slice topic for role {r} (its page)")
        return why + self._reference_coverage()

    def _scan_gate(self):
        why = [] if "landscape" in self.page_ids() else ["wiki.json has no page 'landscape'"]
        if self.state.get("intent") != "hobby":  # only a hobby game goes without comps
            n = sum(r.get("why") == "comp" for r in self.references())
            if n < MIN_COMPS:
                why.append(f"scan: {n} comps; needs {MIN_COMPS}")
        adr = self.state.get("restart_adr")
        scanned = self.references_data.get("scanned_for") if isinstance(self.references_data, dict) else None
        if adr and scanned != adr:
            why.append(f"references.json scanned_for is not {adr}: re-scan for the restart, then set it")
        return why

    def _reference_coverage(self):
        """Reasons an active role has no reference opened for study (open now, or studied before a restart)."""
        covered = {role for r in self.references() if r.get("status") in ("open", "studied")
                   for role in self.ref_roles(r)}
        return [f"references.json: no reference opened for study for role {r}"
                for r in self.active_roles() if r not in covered]

    def _research_gate(self):
        """Coverage is also a check() reason in this phase and each other reason has a _research_action step,
        so the phase never stalls on a bare game-research."""
        why = self._reference_coverage()
        for r in self.references():
            if r.get("status") == "open":
                why.append(f"{r['id']}: open, not studied yet")
            elif r.get("status") == "studied":
                why += self._dossier_reasons(r)
        if "research" not in self.page_ids():
            why.append("wiki.json has no page 'research'")
        if not self.homework_path.exists():
            why.append("docs/game/research/homework.json is missing (it may be empty, with a reason)")
        return why

    def _dossier_reasons(self, r):
        """Reasons a studied reference's dossier falls short: its sections, how each was studied, images, sources
        (fewer pass when its homework names how a person fills the gap) and the creative audit."""
        rid, why = r["id"], []
        base = f"docs/game/research/refs/{rid}"
        how = r.get("how_studied") if isinstance(r.get("how_studied"), dict) else {}
        for role in self.ref_roles(r):
            if not (self.root / base / f"{role}.md").is_file():
                why.append(f"{rid}: no {role} dossier ({base}/{role}.md)")
            h = how.get(role)
            if not (isinstance(h, dict) and h.get("how") in HOW_STUDIED):
                why.append(f"{rid}: {role} how_studied not set")
            elif h["how"] == "not-assessed":
                if not str(h.get("reason") or "").strip():
                    why.append(f"{rid}: {role} not-assessed needs a reason")
            elif role in IMAGE_ROLES and not self._has_image(self.root / base / role):
                why.append(f"{rid}: no image for the {role} section")
        sources = r.get("sources") if isinstance(r.get("sources"), list) else []
        n = len([s for s in sources if s])
        if n < MIN_SOURCES and not self.ref_homework(r):  # sources it couldn't reach are the person's homework
            why.append(f"{rid}: {n} sources; needs {MIN_SOURCES}")
        audit = self.review(f"{base}/audit.json")
        if audit is None:
            why.append(f"{rid}: no audit ({base}/audit.json)")
        for note in audit.get("notes") if audit and isinstance(audit.get("notes"), list) else []:
            if not isinstance(note, dict):
                continue  # _review_shape reports it
            d = str(note.get("decision") or "")
            if not d:
                why.append(f"{rid}: audit note {note.get('id')} is open")
            elif note.get("severity") == "blocking" and not d.startswith("fixed"):
                why.append(f"{rid}: audit note {note.get('id')} is blocking and not fixed")
        return why

    @staticmethod
    def _has_image(folder):
        return folder.is_dir() and any(p.is_file() and p.suffix.lower() in IMAGE_TYPES for p in folder.rglob("*"))

    def _research_action(self):
        """The research phase's next session: each open reference in turn, then a studied one whose dossier falls
        short, then the brief; None once all are done."""
        refs = self.references()
        ref = next((r for r in refs if r.get("status") == "open"), None)
        ref = ref or next((r for r in refs if r.get("status") == "studied" and self._dossier_reasons(r)), None)
        if ref:
            return f"game-research ref {ref['id']}"
        if "research" not in self.page_ids() or not self.homework_path.exists():
            return "game-research brief"
        return None

    def _north_star_reasons(self, v):
        """Reasons the north stars and invariants ideation sets are missing or thin."""
        stars = v.get("north_stars") if isinstance(v.get("north_stars"), dict) else {}
        why = []
        for r in self.active_roles():
            star = stars.get(r)
            if not isinstance(star, dict):
                why.append(f"vision.json north_stars: {r} missing")
                continue
            if not str(star.get("statement") or "").strip():
                why.append(f"north_stars.{r}: no statement")
            refs = star.get("references")
            n = len([x for x in refs if str(x).strip()]) if isinstance(refs, list) else 0
            if n < 2:
                why.append(f"north_stars.{r}: {n} references; needs 2")
            if r == "art":
                d = star.get("directions")
                if not isinstance(d, int) or isinstance(d, bool) or not 2 <= d <= 3:
                    why.append(f"north_stars.art: directions {d if isinstance(d, int) else 0}; needs 2-3")
                if not str(star.get("choice") or "").strip():
                    why.append("north_stars.art: no choice")
            if r == "feel" and not (isinstance(star.get("actions"), dict) and star["actions"]):
                why.append("north_stars.feel: no core action")
        inv = v.get("invariants") if isinstance(v.get("invariants"), list) else []
        n = len([x for x in inv if str(x).strip()])
        if not 2 <= n <= 5:
            why.append(f"vision.json invariants: {n}; needs 2-5")
        return why

    def _consolidate_gate(self):
        slice_stage = self.stage() == "slice"
        have = {p.get("area") for p in self.wiki_pages()}
        active = self.active_roles()
        areas = [a for a in (SLICE_AREAS if slice_stage else AREAS) if AREA_ROLES.get(a, "") in active + [""]]
        why = [f"wiki.json has no page in area '{a}'" for a in areas if a not in have]
        why += [f"topic {t['id']}: open ({t.get('priority')})"
                for t in self.open_topics(["core", "support"]) if self.in_stage(t)]
        items = self.fun.get("items", [])
        counted = [i for i in items if i.get("kind") != "review"]
        if slice_stage:
            early = [i for i in counted if i.get("scope") in ("core-loop", "slice")]
            why += [f"fun checklist has no slice review item for {r}" for r in ("creative", "art", "feel")
                    if r in active and not any(i.get("kind") == "review" and i.get("scope") == "slice"
                                               and r in (i.get("roles") or []) for i in items)]
            if not 3 <= len(early) <= 6:
                why.append(f"fun checklist has {len(early)} core-loop and slice items; needs 3-6")
            if not any(i.get("scope") == "core-loop" and i.get("kind") == "proxy" for i in items):
                why.append("fun checklist has no core-loop proxy item")
            if not any(i.get("kind") == "human" and i.get("scope") in ("core-loop", "slice") for i in items):
                why.append("fun checklist has no human item for the slice playtest")
        else:
            if not any(i.get("scope") == "full" for i in items):
                why.append("fun checklist has no item for the full game (scope full)")
            why += [f"fun checklist has no full review item for {r}" for r in active
                    if not any(i.get("kind") == "review" and i.get("scope") == "full"
                               and r in (i.get("roles") or []) for i in items)]
            if len(counted) > 10:
                why.append(f"fun checklist has {len(counted)} items; keep it to 10 or fewer")
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
        if slice_stage:
            for target, role, ms in (("visual", "art", SLICE_MS[1]), ("feel", "feel", SLICE_MS[0])):
                if role in self.active_roles() and not any(
                        f.get("tier") == "must" and f.get("milestone") == ms and f.get("target") == target
                        for f in build):
                    why.append(f"no must feature with target {target} in milestone {ms}")
        why += [f"{f['id']}: no tickets" for f in build if not f.get("tickets")]
        why += [f"{f['id']}: no wiki pages it implements" for f in build if f.get("tier") == "must" and not f.get("pages")]
        measuring = SLICE_MS if slice_stage else self.build_ms()
        measured = {m for f in self.items() if f.get("tier") == "must" and f.get("milestone") in measuring
                    for m in f.get("measures", [])}
        scope = "slice" if slice_stage else "full"
        kinds = self.kinds()
        targets = [i for i in self.scored_ids(scope) if kinds.get(i) not in ("human", "review")]
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
            if kinds.get(iid) == "review":
                why += self._review_item_gate(iid, score)
            if v.get("outcome") == "ship":
                if result in ("fail", "not-assessed"):
                    why.append(f"{iid}: {result}; a ship needs every item to pass")
                if result == "pending-human" and scope == "slice":
                    why.append(f"{iid}: the slice ships only after a person has played it")
        return why

    def review_result(self, item, paths):
        """pass, fail or not-assessed for a review item, from its reviews: only anchored notes fail it."""
        reviews = [r for r in (self.review(p) for p in paths) if r is not None]
        for r in reviews:
            for n in r.get("notes", []) if isinstance(r.get("notes"), list) else []:
                a = n.get("anchor") if isinstance(n, dict) else None
                if (isinstance(n, dict) and n.get("item") == item.get("id") and isinstance(a, dict)
                        and a.get("kind") in ANCHOR_KINDS and a.get("ref")):
                    return "fail"
        roles = item.get("roles") if isinstance(item.get("roles"), list) else []
        if item.get("taste") and any(r in CALIBRATED_ROLES for r in roles) and not (self.root / LABELS).exists():
            return "not-assessed"
        if any(r.get("result") == "not-assessed" or r.get("independent") is not True for r in reviews):
            return "not-assessed"
        return "pass"

    def _review_item_gate(self, iid, score):
        item = next(i for i in self.fun.get("items", []) if i.get("id") == iid)
        paths = score.get("reviews") if isinstance(score.get("reviews"), list) else []
        by_role = {}
        for p in paths:
            r = self.review(p) if isinstance(p, str) else None
            if r is not None and isinstance(r.get("role"), str) and not self._review_shape(p):
                by_role[r["role"]] = p
        roles = [r for r in item.get("roles", []) if isinstance(r, str)] if isinstance(item.get("roles"), list) else []
        why = [f"{iid}: needs a review by {role}" for role in roles if role not in by_role]
        if not why and score.get("result") in ("pass", "fail", "not-assessed"):
            said = self.review_result(item, [by_role[r] for r in roles])
            if score["result"] != said:
                why.append(f"{iid}: scored {score['result']} but its reviews say {said}")
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
            st.update(phase="scan", task="game-research scan")
        elif phase == "scan":
            adr = st.get("restart_adr")
            st.update(phase="ideation", task=f"game-ideation restart {adr}" if adr else "game-ideation")
        elif phase == "ideation":
            st.update(phase="research", task=None)
        elif phase == "research":
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
        if self.homework_path.exists():  # the brief is redone for the new direction
            shutil.move(str(self.homework_path), str(archive / "homework.json"))
            self.homework_data = copy(DEFAULT_HOMEWORK)
        st.update(phase="scan", stage="slice", milestone=None, task=f"game-research restart {adr}",
                  restart_adr=adr, passed_verdicts=[], slice_sessions=None, adapter_verified=False,
                  checkpoint_due=False, human_queue=[], attempts={})
        self.commit(f"restart {n}", self.features_path, archive / "features.json", archive / "human-queue.json",
                    self.homework_path, archive / "homework.json")
        return [f"restart {n}: definition of done, human queue and research homework archived to "
                f"{archive.relative_to(self.root)}; close their open tickets"]

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
        if "game-brainstorm" in action:  # a research homework session isn't a topic: it spends no share
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
            errs = [] if phase == "setup" and self.older() else self.check()  # an old game is upgraded, then checked
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
        """The next action. Ideation, research homework and brainstorm topics happen with a person (`with-user:`);
        without one, the run does whatever else it can and stops only when nothing else is left."""
        st, phase, m = self.state, self.state["phase"], self.state.get("milestone")
        if phase in ("build", "polish") and st.get("checkpoint_due"):
            return "game-plan checkpoint"
        if phase == "scan" and self._scan_gate():  # the agent alone, from the seed
            adr = st.get("restart_adr")
            return st.get("task") or (f"game-research restart {adr}" if adr else "game-research scan")
        if phase == "research":
            action = self._research_action()  # the agent alone; what it can't do becomes homework
            if action:
                return action
        if phase == "brainstorm" and self.homework_open():  # topics are grilled with the homework's answers
            if no_user:
                return ("stop: waiting for research homework: a person answers or skips each open item in "
                        "docs/game/research/homework.json (or the homework page), then run /game-next")
            return "with-user: game-research homework"
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
            calibrate = next((e for e in self.queue() if e.get("kind") == "calibrate"), None)
            if calibrate and st.get("verdict_scope") == "slice" and not (self.root / LABELS).exists():
                return (f"stop: waiting for calibration: a person labels the kit ({calibrate['how']}) "
                        f"into {LABELS}; then run /game-next")
            if entry and (self.root / entry["answers"]).exists():
                return f"game-verdict {st['verdict_scope']} answers {entry['answers']}"
            if entry and st.get("verdict_scope") == "slice":
                return (f"stop: waiting for the slice playtest: a person plays the build with the kit "
                        f"({entry.get('how', 'see the human queue')}) and writes {entry['answers']}; then run /game-next")
        task = st.get("task")
        if phase == "setup" and self.older():
            task = "game-setup upgrade"
        elif phase in ("setup", "ideation") and not task and self.gate():
            task = f"game-{phase}"  # conversations, even when no task was recorded
        if task and task.startswith(("game-ideation", "game-setup")):
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
            return PHASE_SKILLS.get(phase, f"game-{phase}")
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


def main(argv, history=None):
    """history: the game's git history, a GitHistory of the root unless given (the tests give a stand-in)."""
    cmd = argv[0] if argv and not argv[0].startswith("--") else "status"
    game = Game(find_root(argv), history)
    st = game.state
    if cmd == "init":
        for path in game.write_missing_files():
            print(f"created {path}")
        return 0
    if cmd == "upgrade":
        try:
            notes = game.upgrade()
        except UpgradeError as e:
            print(e)
            return 1
        created = [game.root / n[len("created "):] for n in notes if n.startswith("created ")]
        if game.written or created:  # everything the upgrade wrote, so a migration's own files are committed too
            game.commit(f"upgrade to version {CURRENT_VERSION}", *dict.fromkeys(game.written + created))
        print("\n".join(notes))
        print(f"next: {game.next_action()}")
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
                (e.get("kind") == "playtest" and e.get("scope") == st.get("verdict_scope")
                 and (game.root / e.get("answers", "")).is_file())
                or (e.get("kind") == "calibrate" and (game.root / LABELS).is_file()))]
        game.save_state(f"complete {done}")
        print(f"complete: {done}\nnext: {game.next_action()}")
        return 0
    if cmd == "gdd-synced":
        head = game.history.head() if game.in_git() else None
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
