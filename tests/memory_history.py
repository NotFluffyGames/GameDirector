"""MemoryHistory: the state tool's git history kept in memory, for the tests only (never shipped in skills/).

It has gamestate.GitHistory's methods and answers them from snapshots of the working tree's files taken at each
commit, so a game run in the tests makes no git calls and no commits. test_memory_history.py holds the two to the
same script of edits.
"""
import hashlib
import os
from pathlib import Path


def isolated_git_env(env=None):
    """A copy of env (default os.environ) for the few tests that still run real git. It cuts every config source
    but the repo's own: the global and system files, and the config set in the environment (GIT_CONFIG_COUNT with
    its GIT_CONFIG_KEY_n/VALUE_n, and GIT_CONFIG_PARAMETERS). Their commits are local and unsigned, so the
    machine's commit-signing service is never called."""
    env = dict(os.environ if env is None else env)
    env.pop("GIT_CONFIG_PARAMETERS", None)
    env.update(GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_COUNT="0")
    return env


class MemoryHistory:
    """A linear chain of commits, each a snapshot {path relative to the root: bytes} of the files it holds."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.snapshots = {}  # commit id -> snapshot
        self.chain = []  # commit ids, oldest first

    # ---------- GitHistory's methods ----------
    def in_repo(self):
        return True

    def tracked(self, rel):
        files = self._at("HEAD", {})
        return self._file(rel, files) in files

    def commit(self, message, rels):
        """Commit these paths only, a removed one included; no commit when none of them changed, as with git."""
        before = self._at("HEAD", {})
        files = dict(before)
        for rel in [self._file(r, before) for r in rels]:
            path = self.root / rel
            if path.is_file():
                files[rel] = path.read_bytes()
            else:
                files.pop(rel, None)
        if files != before:
            self._add(message, files)

    def head(self):
        return self.chain[-1] if self.chain else None

    def show(self, commit, rel):
        files = self._at(commit, {})
        data = files.get(self._file(rel, files))
        return None if data is None else data.decode("utf-8")

    def changed(self, a, b, rels):
        old, new = self._at(a), self._at(b)
        rels = [self._file(r, old or {}, new or {}) for r in rels]
        if old is None or new is None:
            return rels
        return sorted(r for r in rels if old.get(r) != new.get(r))

    def is_ancestor(self, a, b):
        a, b = self._id(a), self._id(b)
        return a is not None and b is not None and self.chain.index(a) <= self.chain.index(b)

    # ---------- for the tests' own helpers ----------
    def commit_all(self, message):
        """`git add -A` then `git commit --allow-empty`: the whole working tree, a new commit even when unchanged."""
        self._add(message, self._tree())

    def clean(self):
        """The working tree holds exactly the files of HEAD (`git status --porcelain` prints nothing)."""
        return self._tree() == self._at("HEAD", {})

    def rev_parse(self, ref):
        commit = self._id(ref)
        if commit is None:
            raise ValueError(f"unknown revision {ref!r}")
        return commit

    # ---------- internals ----------
    def _file(self, rel, *snapshots):
        """rel, refused when it names a directory in the working tree or in these snapshots: git would take the
        directory's files, and the double holds files only."""
        inside = rel.rstrip("/") + "/"
        if (self.root / rel).is_dir() or any(p.startswith(inside) for files in snapshots for p in files):
            raise ValueError(f"MemoryHistory takes file paths only: {rel!r} is a directory")
        return rel

    def _id(self, ref):
        if ref == "HEAD":
            return self.head()
        return ref if ref in self.snapshots else None

    def _at(self, ref, default=None):
        commit = self._id(ref)
        return default if commit is None else self.snapshots[commit]

    def _tree(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*")
                if p.is_file() and ".git" not in p.relative_to(self.root).parts}

    def _add(self, message, files):
        commit = hashlib.sha1(f"{len(self.chain)} {message}".encode()).hexdigest()
        self.snapshots[commit] = files
        self.chain.append(commit)
