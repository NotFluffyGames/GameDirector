"""MemoryHistory: the state tool's git history kept in memory, for the tests only (never shipped in skills/).

It has gamestate.GitHistory's methods and answers them from snapshots of the working tree's files taken at each
commit, so a game run in the tests makes no git calls and no commits. test_memory_history.py holds the two to the
same script of edits.
"""
import hashlib
from pathlib import Path

# The environment of the few tests that still run real git: without global or system config their commits are
# local and unsigned, so the machine's commit-signing service is never called.
ISOLATED_GIT = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}


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
        return rel in self._at("HEAD", {})

    def commit(self, message, rels):
        """Commit these paths only, a removed one included; no commit when none of them changed, as with git."""
        before = self._at("HEAD", {})
        files = dict(before)
        for rel in rels:
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
        data = self._at(commit, {}).get(rel)
        return None if data is None else data.decode("utf-8")

    def changed(self, a, b, rels):
        old, new = self._at(a), self._at(b)
        if old is None or new is None:
            return list(rels)
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
