#!/usr/bin/env python3
"""State tool for the game-* skills. Python 3.8+, standard library only.

game-setup copies this file to docs/game/gamestate.py in the game's repo.

Commands:
  init               create any missing state files under docs/game/
  status             one-screen summary, ending with the `next:` action
  check [--since C]  invariants; exit 1 on violations. --since: the commit a
                     session started from (default HEAD), for the edit guard
  gate               does the current phase's gate pass? exit 1 if not
  advance            check + gate, then move to the next phase or milestone
  tick               count one dispatched session against the budget
Option: --root DIR  repo root (default: two levels above this file when it
                    lives in docs/game/, else the current directory)
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

DEFAULT_STATE = {
    "version": 1,
    "phase": "setup",
    "milestone": None,
    "verdict_scope": None,
    "verdict_index": 0,
    "core_verdict_done": False,
    "checkpoint_due": False,
    "adapter_verified": False,
    "resume_phase": None,
    "stop_reason": None,
    "counters": {"sessions": 0, "adjusts": 0, "restarts": 0},
    "limits": {"budget_sessions": None, "max_adjusts": 2, "max_restarts": 1, "max_attempts": 3},
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
        if not path.exists():
            return json.loads(json.dumps(default))
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"error: {path.relative_to(self.root)} is not valid JSON: {e}")
        merged = json.loads(json.dumps(default))
        merged.update(data)
        return merged

    def save_state(self):
        self.state_path.write_text(json.dumps(self.state, indent=2) + "\n", encoding="utf-8")

    def save_features(self):
        self.features_path.write_text(json.dumps(self.features, indent=2) + "\n", encoding="utf-8")

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

    def live(self, milestone=None):
        return [f for f in self.items() if f.get("tier") != "cut"
                and (milestone is None or f.get("milestone") == milestone)]

    def queued_ids(self):
        ids = set()
        for entry in self.state.get("human_queue", []):
            unblocks = entry.get("unblocks", [])
            ids.update([unblocks] if isinstance(unblocks, str) else unblocks)
        return ids

    def is_done(self, f):
        """Passing, or handed to a person: the run moves on and resumes it once the queue clears."""
        return bool(f.get("passes")) or f.get("id") in self.queued_ids()

    def failing_must(self, milestone):
        return [f for f in self.live(milestone) if f.get("tier") == "must" and not self.is_done(f)]

    def build_milestones(self):
        return [m for m in self.features.get("milestones", []) if m not in RELEASE_MILESTONES]

    def next_milestone(self, candidates, after=None):
        start = candidates.index(after) + 1 if after in candidates else 0
        for m in candidates[start:]:
            if self.failing_must(m):
                return m
        return None

    def fun_in_scope(self, scope):
        return [i for i in self.fun.get("items", []) if scope == "full" or i.get("scope") == "core-loop"]

    # ---------- invariants ----------
    def check(self, since="HEAD"):
        errs = []
        st = self.state
        if st.get("phase") not in PHASES:
            errs.append(f"state.phase '{st.get('phase')}' is not one of {PHASES}")
        for key in ("max_adjusts", "max_restarts", "max_attempts"):
            if not isinstance(st["limits"].get(key), int):
                errs.append(f"state.limits.{key} must be an integer")

        milestones = self.features.get("milestones", [])
        for m in RELEASE_MILESTONES:
            if m not in milestones:
                errs.append(f"features.milestones must include '{m}'")
        pillars = self.pillars()
        seen = set()
        for f in self.items():
            fid = f.get("id") or "<no id>"
            if fid in seen:
                errs.append(f"{fid}: duplicate id")
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
        for v in st.get("verdicts", []):
            if v.get("outcome") not in OUTCOMES or not v.get("adr"):
                errs.append(f"verdict {v.get('scope')}: needs outcome in {OUTCOMES} and an adr path")

        if st.get("phase") in ("build", "verdict", "release"):
            errs += self._edit_guard(since)
        return errs

    def _edit_guard(self, since):
        """Outside plan phases the definition of done only grows; items are cut, not deleted or rewritten."""
        rel = self.features_path.relative_to(self.root).as_posix()
        try:
            old_raw = subprocess.run(["git", "show", f"{since}:{rel}"], cwd=self.root,
                                     capture_output=True, text=True, check=True).stdout
            old = {f.get("id"): f for f in json.loads(old_raw).get("features", [])}
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            return []
        new = {f.get("id"): f for f in self.items()}
        errs = [f"{fid}: removed from features.json; set tier cut with a cut_reason instead"
                for fid in old if fid not in new]
        for fid, f in new.items():
            if fid in old:
                for key in ("acceptance", "verify"):
                    if f.get(key) != old[fid].get(key):
                        errs.append(f"{fid}: {key} changed outside the plan phase")
        return errs

    # ---------- gates ----------
    def gate(self):
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
                why.append("adapter commands not verified (run game-setup adapter mode)")
            build = [f for f in self.live() if f.get("milestone") in self.build_milestones()]
            if not [f for f in build if f.get("tier") == "must" and f.get("milestone") == self.build_milestones()[0]]:
                why.append(f"no must feature in milestone '{self.build_milestones()[0]}'")
            why += [f"{f['id']}: no tickets" for f in build if not f.get("tickets")]
            measured = {m for f in build if f.get("tier") == "must" for m in f.get("measures", [])}
            why += [f"fun {i['id']}: no must feature lists it in measures"
                    for i in self.fun.get("items", []) if i.get("kind") == "proxy" and i.get("id") not in measured]
        elif phase in ("build", "release"):
            m = st.get("milestone")
            if phase == "release" and not any(self.live(r) for r in RELEASE_MILESTONES):
                why.append("no polish/release features yet (run game-release)")
            else:
                why += [f"{f['id']}: not passing" + (" (blocked)" if f.get("blocked") else "")
                        for f in self.failing_must(m)]
        elif phase == "verdict":
            verdicts, scope = st.get("verdicts", []), st.get("verdict_scope")
            if len(verdicts) <= st.get("verdict_index", 0) or verdicts[-1].get("scope") != scope:
                why.append(f"no {scope} verdict recorded since this phase began")
            else:
                scores = verdicts[-1].get("scores", {})
                why += [f"fun {i['id']}: not scored" for i in self.fun_in_scope(scope)
                        if scores.get(i["id"], {}).get("result") not in SCORE_RESULTS]
        elif phase == "awaiting-human":
            if st.get("human_queue"):
                why.append(f"{len(st['human_queue'])} human queue entries open")
            if st.get("stop_reason"):
                why.append(f"stopped: {st['stop_reason']} (a human decides, then sets stop_reason to null)")
        return why

    # ---------- transitions ----------
    def advance(self):
        st = self.state
        phase = st["phase"]
        notes = []
        if phase == "setup":
            st["phase"] = "ideate"
        elif phase == "ideate":
            st["phase"] = "plan"
        elif phase == "plan":
            self._enter_build(after=None)
        elif phase == "build":
            done = st["milestone"]
            notes.append(f"milestone complete: {done}")
            notes += self._checkpoint()
            self._enter_build(after=done)
        elif phase == "verdict":
            notes += self._apply_verdict(st["verdicts"][-1])
        elif phase == "release":
            nxt = self.next_milestone(RELEASE_MILESTONES, after=st["milestone"])
            if nxt:
                st["milestone"] = nxt
            elif st.get("human_queue"):
                self._stop(None, resume="done")
            else:
                st["phase"], st["milestone"] = "done", None
        elif phase == "awaiting-human":
            st["phase"], st["resume_phase"], st["stop_reason"] = st.get("resume_phase") or "build", None, None
            if st["phase"] in ("build", "release"):
                pool = self.build_milestones() if st["phase"] == "build" else RELEASE_MILESTONES
                st["milestone"] = self.next_milestone(pool) or pool[-1]
        self.save_state()
        return notes

    def _enter_build(self, after):
        first = self.build_milestones()[0]
        m = self.next_milestone(self.build_milestones(), after=after)
        if m != first and not self.failing_must(first) and not self.state.get("core_verdict_done"):
            self._enter_verdict("core-loop")  # the core loop is judged before anything is built on it
        elif m:
            self.state["phase"], self.state["milestone"] = "build", m
        else:
            self._enter_verdict("full")

    def _enter_verdict(self, scope):
        st = self.state
        st["phase"], st["milestone"], st["verdict_scope"] = "verdict", None, scope
        st["verdict_index"] = len(st.get("verdicts", []))

    def _stop(self, reason, resume):
        st = self.state
        st["phase"], st["stop_reason"], st["resume_phase"] = "awaiting-human", reason, resume

    def _apply_verdict(self, v):
        st, outcome, scope = self.state, v["outcome"], v["scope"]
        if outcome == "ship":
            if scope == "core-loop":
                st["core_verdict_done"] = True
                self._enter_build(after=self.build_milestones()[0])
            else:
                st["phase"] = "release"
                st["milestone"] = self.next_milestone(RELEASE_MILESTONES) or RELEASE_MILESTONES[0]
            return [f"verdict {scope}: ship"]
        key, limit = ("adjusts", "max_adjusts") if outcome == "adjust" else ("restarts", "max_restarts")
        st["counters"][key] += 1
        if st["counters"][key] > st["limits"][limit]:
            self._stop(f"{outcome} limit reached ({st['limits'][limit]})",
                       resume="plan" if outcome == "adjust" else "ideate")
            return [f"verdict {scope}: {outcome}, over limit: a human decides next"]
        if outcome == "adjust":
            st["phase"] = "plan"
            return [f"verdict {scope}: adjust {st['counters']['adjusts']}/{st['limits']['max_adjusts']}"]
        n = st["counters"]["restarts"]
        archive = self.dir / "archive" / f"restart-{n}"
        archive.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.features_path, archive / "features.json")
        self.features["features"] = []
        self.save_features()
        st.update(phase="ideate", milestone=None, core_verdict_done=False, adapter_verified=False)
        return [f"verdict {scope}: restart {n}; old definition of done archived to {archive.relative_to(self.root)}"]

    def _checkpoint(self):
        st = self.state
        budget = st["limits"].get("budget_sessions")
        pool = self.build_milestones()
        if not budget or st.get("milestone") not in pool:
            return []
        done_share = (pool.index(st["milestone"]) + 1) / len(pool)
        used_share = st["counters"]["sessions"] / budget
        behind = used_share > done_share + 0.1
        st["checkpoint_due"] = behind
        return [f"checkpoint: {used_share:.0%} of budget used, {done_share:.0%} of build milestones done"
                + (" -> behind: checkpoint due" if behind else "")]

    # ---------- next action ----------
    def next_action(self):
        st, phase = self.state, self.state["phase"]
        budget = st["limits"].get("budget_sessions")
        if phase == "done":
            return "stop: done"
        if phase == "awaiting-human":
            return ("advance" if not self.gate() else
                    f"stop: {st.get('stop_reason') or 'awaiting human'}; human queue: {len(st.get('human_queue', []))}")
        if budget and st["counters"]["sessions"] >= budget:
            return "stop: budget exhausted (raise limits.budget_sessions in state.json to continue)"
        if st.get("checkpoint_due") and phase in ("build", "release"):
            return "game-plan checkpoint"
        if not self.gate():
            return "advance"
        if phase in ("setup", "ideate", "plan"):
            return f"game-{phase}" + (f" ({self.gate()[0]})" if phase == "plan" else "")
        if phase == "verdict":
            return f"game-verdict {st['verdict_scope']}"
        if phase == "release" and not any(self.live(r) for r in RELEASE_MILESTONES):
            return "game-release"
        failing = self.failing_must(st.get("milestone"))
        ready = [f for f in failing if not f.get("blocked")]
        if ready:
            alts = ", ".join(f["id"] for f in ready[1:3])
            return f"game-build {ready[0]['id']} \"{ready[0]['title']}\"" + (
                f" (if its tickets are blocked: {alts})" if alts else "")
        return "game-plan unblock " + " ".join(f["id"] for f in failing)

    # ---------- report ----------
    def status(self):
        st, c, lim = self.state, self.state["counters"], self.state["limits"]
        out = [f"phase: {st['phase']}"
               + (f"  milestone: {st['milestone']}" if st.get("milestone") else "")
               + (f"  scope: {st['verdict_scope']}" if st["phase"] == "verdict" else "")
               + f"  sessions: {c['sessions']}/{lim.get('budget_sessions') or '-'}"
               + f"  adjusts: {c['adjusts']}/{lim['max_adjusts']}  restarts: {c['restarts']}/{lim['max_restarts']}"]
        if self.items():
            out.append("definition of done (must done/total | nice | cut | blocked):")
            for m in self.features.get("milestones", []):
                fs = [f for f in self.items() if f.get("milestone") == m]
                if not fs:
                    continue
                must = [f for f in fs if f.get("tier") == "must"]
                out.append(f"  {m:<14} {sum(self.is_done(f) for f in must)}/{len(must)} | "
                           f"{sum(f.get('tier') == 'nice' for f in fs)} | {sum(f.get('tier') == 'cut' for f in fs)} | "
                           f"{sum(bool(f.get('blocked')) for f in fs)}")
        items = self.fun.get("items", [])
        if items:
            proxies = sum(i.get("kind") == "proxy" for i in items)
            out.append(f"fun checklist: {len(items)} items ({proxies} proxy, {len(items) - proxies} human)")
        if st.get("verdicts"):
            v = st["verdicts"][-1]
            out.append(f"last verdict: {v.get('scope')} -> {v.get('outcome')} ({v.get('adr')})")
        for e in st.get("human_queue", [])[:5]:
            out.append(f"human queue: {e.get('id')} {e.get('what')}")
        errs = self.check()
        if errs:
            out.append(f"check: {len(errs)} violation(s); first: {errs[0]}")
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
    if cmd == "init":
        game.dir.mkdir(parents=True, exist_ok=True)
        for path, data in ((game.state_path, game.state), (game.features_path, game.features),
                           (game.fun_path, game.fun)):
            if not path.exists():
                path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
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
        why = game.gate()
        print("\n".join(why) if why else f"gate {game.state['phase']}: PASS")
        return 1 if why else 0
    if cmd == "advance":
        errs, why = game.check(), game.gate()
        if errs or why:
            print("cannot advance:\n" + "\n".join(errs + why))
            return 1
        before = game.state["phase"]
        for note in game.advance():
            print(note)
        print(f"{before} -> {game.state['phase']}"
              + (f" ({game.state['milestone']})" if game.state.get("milestone") else ""))
        print(f"next: {game.next_action()}")
        return 0
    if cmd == "tick":
        game.state["counters"]["sessions"] += 1
        game.save_state()
        print(f"sessions: {game.state['counters']['sessions']}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
