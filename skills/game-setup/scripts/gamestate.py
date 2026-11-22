#!/usr/bin/env python3
"""State tool for the game-* skills. Python 3.8+, standard library only.

game-setup copies this file to docs/game/gamestate.py in the game's repo.

Commands:
  init               create any missing state files under docs/game/
  status             one-screen summary, ending with the `next:` action
  check [--since C]  invariants; exit 1 on violations. --since: the commit the
                     session started from (default HEAD), for the edit guard
  gate               does the current phase's gate pass? exit 1 if not
  complete           a phase skill's last step: clears the phase's task once
                     the task's gate passes
  advance            move to the next phase or milestone, when allowed
  tick "<next>"      record one dispatch of a `next:` action
Option: --root DIR  repo root (default: two levels above this file when it
                    lives in docs/game/, else the current directory)

advance, complete and tick commit docs/game/state.json themselves, so a reset
to a session's base commit never loses the run's own bookkeeping.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PHASES = ["setup", "ideate", "plan", "build", "verdict", "release", "awaiting-human", "done"]
TIERS = ["must", "nice", "cut"]
VERIFY_KINDS = ["test", "sim", "replay", "bot", "capture", "check", "human"]
MILESTONES = ["core-loop", "systems", "content", "verdict-build", "polish", "release"]
RELEASE_MILESTONES = ["polish", "release"]
OUTCOMES = ["ship", "adjust", "restart"]
SCORE_RESULTS = ["pass", "fail", "pending-human"]
DESIGN_HEADINGS = ["## Pitch", "## Pillars", "## Core loop", "## Tone, art and world", "## Pillar test"]
FUN_FIELDS = ["statement", "scope", "kind", "metric", "threshold", "how"]
REOPENABLE = ["build", "release", "awaiting-human", "done"]
NICE_RESERVE = 10  # sessions kept back for verdicts and release before nice features are built

DEFAULT_STATE = {
    "version": 2,
    "phase": "setup",
    "milestone": None,
    "task": "game-setup",
    "verdict_scope": None,
    "verdict_index": 0,
    "core_verdict_done": False,
    "full_verdict_done": False,
    "checkpoint_due": False,
    "adapter_verified": False,
    "restart_adr": None,
    "resume": None,
    "stop_reason": None,
    "counters": {"sessions": 0, "adjusts": 0, "restarts": 0},
    "limits": {"budget_sessions": 150, "max_adjusts": 2, "max_restarts": 1, "max_attempts": 3, "max_repeats": 5},
    "attempts": {},
    "last_dispatch": {"action": None, "repeats": 0},
    "human_queue": [],
    "verdicts": [],
}
DEFAULT_FEATURES = {"milestones": MILESTONES, "features": []}
DEFAULT_FUN = {"items": []}
DEFAULT_TEXT = {
    "progress.md": "# Progress\n\nAppend-only session log. One entry per session, newest last, at most 10 lines each.\n",
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
        self.design_path = self.dir / "design.md"
        self.state = self._load(self.state_path, DEFAULT_STATE)
        self.features = self._load(self.features_path, DEFAULT_FEATURES)
        self.fun = self._load(self.fun_path, DEFAULT_FUN)

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
    def pillars(self):
        if not self.design_path.exists():
            return None
        ids, inside = [], False
        for line in self.design_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                inside = line.strip() == "## Pillars"
                continue
            m = re.match(r"\s*[-*]\s*\*\*(P\d+)\*\*", line)
            if inside and m:
                ids.append(m.group(1))
        return ids

    def items(self):
        return self.features.get("features", [])

    def milestones(self):
        return self.features.get("milestones", [])

    def build_ms(self):
        return [m for m in self.milestones() if m not in RELEASE_MILESTONES]

    @staticmethod
    def upto(pool, m):
        return pool[: pool.index(m) + 1] if m in pool else list(pool)

    def queued_ids(self):
        ids = set()
        for entry in self.state.get("human_queue", []):
            unblocks = entry.get("unblocks", [])
            ids.update([unblocks] if isinstance(unblocks, str) else unblocks)
        return ids

    def is_done(self, f):
        """Passing, or handed to a person: the run moves on and comes back once the queue clears."""
        return bool(f.get("passes")) or f.get("id") in self.queued_ids()

    def is_blocked(self, f):
        return bool(f.get("blocked")) or self.state["attempts"].get(f.get("id"), 0) >= self.state["limits"]["max_attempts"]

    def failing(self, pool, tier="must"):
        order = {m: i for i, m in enumerate(self.milestones())}
        fs = [f for f in self.items() if f.get("tier") == tier and f.get("milestone") in pool and not self.is_done(f)]
        return sorted(fs, key=lambda f: order.get(f.get("milestone"), 99))

    def earliest_failing_ms(self, pool):
        fs = self.failing(pool)
        return fs[0]["milestone"] if fs else None

    def has_release_features(self):
        return any(f.get("tier") != "cut" and f.get("milestone") in RELEASE_MILESTONES for f in self.items())

    def green_pool(self):
        """Milestones whose must features have to pass in the current phase."""
        st = self.state
        phase, m = st["phase"], st.get("milestone")
        if phase == "build":
            return self.upto(self.build_ms(), m)
        if phase == "verdict":
            return self.build_ms()[:1] if st.get("verdict_scope") == "core-loop" else self.build_ms()
        if phase == "release":
            return self.build_ms() + self.upto(RELEASE_MILESTONES, m)
        if phase == "done":
            return self.milestones()
        return []

    def fun_in_scope(self, scope):
        return [i for i in self.fun.get("items", []) if scope == "full" or i.get("scope") == "core-loop"]

    def pending_playtest(self):
        for entry in self.state.get("human_queue", []):
            answers = entry.get("answers")
            if entry.get("kind") == "playtest" and answers and (self.root / answers).exists():
                return entry
        return None

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

        milestones = self.milestones()
        for m in RELEASE_MILESTONES:
            if m not in milestones:
                errs.append(f"features.milestones must include '{m}'")
        pillars = self.pillars()
        archived = self._archived_ids()
        seen = set()
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
                errs.append(f"{fid}: pillar '{f.get('pillar')}' is not a pillar in design.md")
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

        fun_ids = set()
        for i in self.fun.get("items", []):
            iid = i.get("id") or "<no id>"
            if iid in fun_ids:
                errs.append(f"fun {iid}: duplicate id")
            fun_ids.add(iid)
            if not i.get("statement"):
                errs.append(f"fun {iid}: missing statement")
            if i.get("scope") not in ("core-loop", "full"):
                errs.append(f"fun {iid}: scope must be core-loop or full")
            if i.get("kind") not in ("proxy", "human"):
                errs.append(f"fun {iid}: kind must be proxy or human")
            if i.get("kind") == "proxy" and not all(i.get(k) for k in ("metric", "threshold", "how")):
                errs.append(f"fun {iid}: a proxy item needs metric, threshold and how")

        for e in st.get("human_queue", []):
            if not e.get("id") or not e.get("what"):
                errs.append("human_queue entries need id and what")
            if e.get("kind") == "playtest" and not (e.get("scope") and e.get("answers")):
                errs.append(f"human_queue {e.get('id')}: a playtest entry needs scope and answers")
        for v in st.get("verdicts", []):
            if v.get("outcome") not in OUTCOMES or not v.get("adr"):
                errs.append(f"verdict {v.get('scope')}: needs outcome in {OUTCOMES} and an adr path")

        if st.get("phase") not in ("setup", "ideate", "plan"):
            errs += self._feature_guard(since)
        if st.get("phase") not in ("setup", "ideate"):
            errs += self._fun_guard(since)
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

    def _fun_guard(self, since):
        """The bar is set in ideate; later phases may add items but not lower or remove them."""
        old_data = self._old(since, self.fun_path)
        if old_data is None:
            return []
        new = {i.get("id"): i for i in self.fun.get("items", [])}
        errs = []
        for item in old_data.get("items", []):
            iid = item.get("id")
            if iid not in new:
                errs.append(f"fun {iid}: removed outside ideate")
            elif any(item.get(k) != new[iid].get(k) for k in FUN_FIELDS):
                errs.append(f"fun {iid}: changed outside ideate")
        return errs

    # ---------- gates ----------
    def gate(self):
        """Reasons the current phase is not complete (its task aside)."""
        st, phase, why = self.state, self.state["phase"], []
        if phase == "setup":
            if not (self.root / "docs" / "agents" / "game.md").exists():
                why.append("docs/agents/game.md is missing")
        elif phase == "ideate":
            text = self.design_path.read_text(encoding="utf-8") if self.design_path.exists() else ""
            why += [f"design.md lacks '{h}'" for h in DESIGN_HEADINGS if h not in text.splitlines()]
            n = len(self.pillars() or [])
            if not 3 <= n <= 4:
                why.append(f"design.md has {n} pillars; needs 3-4 written as '- **P1**: ...'")
            items = self.fun.get("items", [])
            if not 3 <= len(items) <= 6:
                why.append(f"fun checklist has {len(items)} items; needs 3-6")
            if not any(i.get("scope") == "core-loop" for i in items):
                why.append("fun checklist has no core-loop item")
            if not any(i.get("kind") == "proxy" for i in items):
                why.append("fun checklist has no proxy item")
        elif phase == "plan":
            if not st.get("adapter_verified"):
                why.append("adapter commands not verified (game-setup adapter mode)")
            if not st["limits"].get("budget_sessions"):
                why.append("limits.budget_sessions is not set")
            build = [f for f in self.items() if f.get("tier") != "cut" and f.get("milestone") in self.build_ms()]
            first = self.build_ms()[0]
            if not any(f.get("tier") == "must" and f.get("milestone") == first for f in build):
                why.append(f"no must feature in milestone '{first}'")
            why += [f"{f['id']}: no tickets" for f in build if not f.get("tickets")]
            measured = {m for f in build if f.get("tier") == "must" for m in f.get("measures", [])}
            why += [f"fun {i['id']}: no must feature lists it in measures"
                    for i in self.fun.get("items", []) if i.get("kind") == "proxy" and i.get("id") not in measured]
        elif phase == "awaiting-human":
            if st.get("human_queue"):
                why.append(f"{len(st['human_queue'])} human queue entries open")
            if st.get("stop_reason"):
                why.append(f"stopped: {st['stop_reason']} (a human decides, then sets stop_reason to null)")
        if phase in ("build", "verdict", "release", "done"):
            why += [f"{f['id']}: not passing" + (" (blocked)" if self.is_blocked(f) else "")
                    for f in self.failing(self.green_pool())]
        if phase == "verdict":
            why += self._verdict_gate()
        if phase == "release" and not self.has_release_features():
            why.append("no polish/release features yet (game-release)")
        return why

    def _verdict_gate(self):
        st = self.state
        verdicts, scope = st.get("verdicts", []), st.get("verdict_scope")
        if len(verdicts) <= st.get("verdict_index", 0) or verdicts[-1].get("scope") != scope:
            return [f"no {scope} verdict recorded since this phase began"]
        scores = verdicts[-1].get("scores", {})
        return [f"fun {i['id']}: not scored" for i in self.fun_in_scope(scope)
                if scores.get(i["id"], {}).get("result") not in SCORE_RESULTS]

    def task_gate(self):
        """What the current task still owes before `complete` may clear it."""
        phase = self.state["phase"]
        if phase == "verdict":
            return self._verdict_gate()
        if phase == "release":
            return [] if self.has_release_features() else ["no polish/release features yet"]
        return self.gate()

    # ---------- transitions ----------
    def advance(self):
        st, phase = self.state, self.state["phase"]
        notes = []
        entry = self.pending_playtest()
        if entry and phase in REOPENABLE:
            self._reopen(entry)
            return [f"playtest answers for {entry['scope']}: verdict reopened"]
        if phase == "setup":
            st.update(phase="ideate", task="game-ideate")
        elif phase == "ideate":
            adr = st.get("restart_adr")
            st.update(phase="plan", task=f"game-plan restart {adr}" if adr else "game-plan", restart_adr=None)
        elif phase == "plan":
            self._enter_build()
        elif phase == "build":
            notes.append(f"milestone complete: {st['milestone']}")
            notes += self._checkpoint()
            self._enter_build()
        elif phase == "verdict":
            notes += self._apply_verdict(st["verdicts"][-1])
        elif phase == "release":
            notes.append(f"milestone complete: {st['milestone']}")
            self._enter_release()
        elif phase == "awaiting-human":
            self._resume()
        return notes

    def _enter_build(self):
        st, pool = self.state, self.build_ms()
        m = self.earliest_failing_ms(pool)
        if m == pool[0]:
            st.update(phase="build", milestone=m, task=None)
        elif not st.get("core_verdict_done"):
            self._enter_verdict("core-loop")  # the core loop is judged before anything is built on it
        elif m:
            st.update(phase="build", milestone=m, task=None)
        elif not st.get("full_verdict_done"):
            self._enter_verdict("full")
        else:
            self._enter_release()

    def _enter_verdict(self, scope):
        self.state.update(phase="verdict", milestone=None, verdict_scope=scope,
                          verdict_index=len(self.state.get("verdicts", [])), task=f"game-verdict {scope}")

    def _enter_release(self):
        st = self.state
        if not self.has_release_features():
            st.update(phase="release", milestone=RELEASE_MILESTONES[0], task="game-release")
            return
        m = self.earliest_failing_ms(RELEASE_MILESTONES)
        if m:
            st.update(phase="release", milestone=m, task=None)
        elif st.get("human_queue"):
            self._stop(None, {"phase": "done"})
        else:
            st.update(phase="done", milestone=None, task=None)

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
        elif r.get("phase") in ("ideate", "plan"):
            st.update(phase=r["phase"], milestone=None, task=r.get("task"))
        else:
            self._enter_build()  # goes back to whatever still fails, or on to done

    def _apply_verdict(self, v):
        st, outcome, scope, adr = self.state, v["outcome"], v["scope"], v["adr"]
        if outcome == "ship":
            st["core_verdict_done"] = True
            if scope == "full":
                st["full_verdict_done"] = True
            self._enter_build()
            return [f"verdict {scope}: ship"]
        st["full_verdict_done"] = False
        if scope == "core-loop":
            st["core_verdict_done"] = False
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
        st.update(phase="ideate", milestone=None, task=f"game-ideate restart {adr}", restart_adr=adr,
                  core_verdict_done=False, full_verdict_done=False, adapter_verified=False,
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
        last = st["last_dispatch"]
        last["repeats"] = last["repeats"] + 1 if last.get("action") == action else 1
        last["action"] = action
        passing = {f.get("id") for f in self.items() if f.get("passes")}
        st["attempts"] = {k: v for k, v in st["attempts"].items() if k not in passing}
        m = re.match(r"game-build (\S+)", action)
        if m:
            st["attempts"][m.group(1)] = st["attempts"].get(m.group(1), 0) + 1

    # ---------- next action ----------
    def next_action(self):
        st, phase = self.state, self.state["phase"]
        if self.pending_playtest() and phase in REOPENABLE:
            return "advance"
        if phase == "done":
            return "stop: done"
        if phase == "awaiting-human":
            if not self.gate():
                return "advance"
            return f"stop: {st.get('stop_reason') or 'waiting on the human queue'} ({len(st.get('human_queue', []))} open)"
        errs = self.check()
        action = "fix: " + "; ".join(errs[:3]) if errs else self._work()
        if action == "advance":
            return action
        budget = st["limits"].get("budget_sessions")
        if budget and st["counters"]["sessions"] >= budget:
            return "stop: budget exhausted (raise limits.budget_sessions in docs/game/state.json to continue)"
        last = st["last_dispatch"]
        if last.get("action") == action and last.get("repeats", 0) >= st["limits"]["max_repeats"]:
            return (f"stop: stalled on '{action}' after {last['repeats']} dispatches; fix the cause, "
                    "then set last_dispatch.repeats to 0 in docs/game/state.json")
        return action

    def _work(self):
        st, phase, m = self.state, self.state["phase"], self.state.get("milestone")
        if phase in ("build", "release") and st.get("checkpoint_due"):
            return "game-plan checkpoint"
        if phase in ("build", "verdict", "release"):
            pool = self.green_pool() if phase != "release" else self.build_ms()
            action = self._build_action(pool)  # judge and ship only a green build
            if action:
                return action
        if st.get("task"):
            return st["task"]
        if phase == "release":
            action = self._build_action(self.upto(RELEASE_MILESTONES, m))
            if action:
                return action
        if phase in ("build", "release"):
            action = self._nice_action(m)
            if action:
                return action
        if self.gate():
            return f"game-verdict {st.get('verdict_scope')}" if phase == "verdict" else f"game-{phase}"
        return "advance"

    def _build_action(self, pool):
        failing = self.failing(pool)
        if not failing:
            return None
        ready = [f for f in failing if not self.is_blocked(f)]
        if not ready:
            return "game-plan unblock " + " ".join(f["id"] for f in failing)
        alts = ", ".join(f["id"] for f in ready[1:3])
        return f"game-build {ready[0]['id']} \"{ready[0]['title']}\"" + (
            f" (if its tickets are blocked: {alts})" if alts else "")

    def _nice_action(self, milestone):
        st = self.state
        budget = st["limits"].get("budget_sessions") or 0
        left = budget - st["counters"]["sessions"]
        remaining_must = len(self.failing(self.milestones()))
        nice = [f for f in self.failing([milestone], tier="nice") if not self.is_blocked(f)]
        if nice and left > 2 * remaining_must + NICE_RESERVE:
            return f"game-build {nice[0]['id']} \"{nice[0]['title']}\" (nice)"
        return None

    # ---------- report ----------
    def status(self):
        st, c, lim = self.state, self.state["counters"], self.state["limits"]
        out = [f"phase: {st['phase']}"
               + (f"  milestone: {st['milestone']}" if st.get("milestone") else "")
               + (f"  scope: {st['verdict_scope']}" if st["phase"] == "verdict" else "")
               + f"  sessions: {c['sessions']}/{lim.get('budget_sessions') or '-'}"
               + f"  adjusts: {c['adjusts']}/{lim['max_adjusts']}  restarts: {c['restarts']}/{lim['max_restarts']}"]
        if st.get("task"):
            out.append(f"task: {st['task']}")
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
        items = self.fun.get("items", [])
        if items:
            proxies = sum(i.get("kind") == "proxy" for i in items)
            out.append(f"fun checklist: {len(items)} items ({proxies} proxy, {len(items) - proxies} human)")
        if st.get("verdicts"):
            v = st["verdicts"][-1]
            out.append(f"last verdict: {v.get('scope')} -> {v.get('outcome')} ({v.get('adr')})")
        for e in st.get("human_queue", [])[:5]:
            out.append(f"human queue: {e.get('id')} {e.get('what')}")
        why = self.gate()
        out.append(f"gate: {'PASS' if not why else 'FAIL: ' + '; '.join(why[:4]) + (' ...' if len(why) > 4 else '')}")
        out.append(f"next: {self.next_action()}")
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
        for path, data in ((game.state_path, game.state), (game.features_path, game.features), (game.fun_path, game.fun)):
            if not path.exists():
                game._write(path, data)
                print(f"created {path.relative_to(game.root)}")
        for name, text in DEFAULT_TEXT.items():
            if not (game.dir / name).exists():
                (game.dir / name).write_text(text, encoding="utf-8")
                print(f"created docs/game/{name}")
        return 0
    if cmd == "status":
        print(game.status())
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
        game.save_state(f"complete {done}")
        print(f"complete: {done}\nnext: {game.next_action()}")
        return 0
    if cmd == "advance":
        if game.next_action() != "advance":
            print(f"cannot advance: next is '{game.next_action()}'")
            return 1
        before = st["phase"]
        notes = game.advance()
        game.save_state(f"{before} -> {st['phase']}" + (f" ({st['milestone']})" if st.get("milestone") else ""))
        for note in notes:
            print(note)
        print(f"{before} -> {st['phase']}" + (f" ({st['milestone']})" if st.get("milestone") else ""))
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
