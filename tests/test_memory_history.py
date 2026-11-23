"""GitHistory, the state tool's only door to git, and MemoryHistory, the tests' stand-in for it, answer alike.

The same script of edits runs once against a real temporary repo and once against the double. The real repo runs
with ISOLATED_GIT, so its few commits are local and unsigned.

Run: python3 -m unittest discover tests
"""
import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from memory_history import ISOLATED_GIT, MemoryHistory

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "game-setup" / "scripts" / "gamestate.py"
UNKNOWN = "0" * 40


def load_gamestate():
    spec = importlib.util.spec_from_file_location("gamestate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Script:
    """The script of edits; each subclass gives the history it runs against."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.root)
        self.history = self.make_history()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def test_commits_and_reads_back(self):
        h = self.history
        self.assertTrue(h.in_repo())
        self.assertIsNone(h.head())
        self.write("docs/game/state.json", '{"phase": "setup"}\n')
        self.write("docs/game/wiki.json", '{"pages": []}\n')
        h.commit("first", ["docs/game/state.json", "docs/game/wiki.json"])
        first = h.head()
        self.assertTrue(first)
        self.assertTrue(h.tracked("docs/game/state.json"))
        self.write("docs/game/state.json", '{"phase": "scan"}\n')
        self.write("notes.txt", "other work")
        h.commit("second", ["docs/game/state.json"])
        second = h.head()
        self.assertNotEqual(second, first)
        self.assertFalse(h.tracked("notes.txt"))  # only the given paths are committed
        sources = ["docs/game/state.json", "docs/game/wiki.json"]
        self.assertEqual(h.changed(first, second, sources), ["docs/game/state.json"])
        self.assertEqual(h.changed(second, "HEAD", sources), [])
        self.assertEqual(h.show(first, "docs/game/state.json"), '{"phase": "setup"}\n')
        self.assertEqual(h.show("HEAD", "docs/game/state.json"), '{"phase": "scan"}\n')
        self.assertIsNone(h.show(first, "notes.txt"))
        self.assertTrue(h.is_ancestor(first, second))
        self.assertFalse(h.is_ancestor(second, first))
        self.assertTrue(h.is_ancestor(second, second))

    def test_a_removed_tracked_file_is_committed_and_an_unchanged_one_is_not(self):
        h = self.history
        self.write("a.json", "1")
        self.write("b.json", "2")
        h.commit("both", ["a.json", "b.json"])
        (self.root / "b.json").unlink()
        h.commit("remove b", ["b.json"])
        removed = h.head()
        self.assertFalse(h.tracked("b.json"))
        self.assertIsNone(h.show("HEAD", "b.json"))
        h.commit("nothing changed", ["a.json"])
        self.assertEqual(h.head(), removed)

    def test_an_unknown_commit_reads_as_nothing_and_everything_changed(self):
        h = self.history
        self.write("a.json", "1")
        h.commit("a", ["a.json"])
        self.assertIsNone(h.show(UNKNOWN, "a.json"))
        self.assertEqual(h.changed(UNKNOWN, "HEAD", ["a.json"]), ["a.json"])
        self.assertFalse(h.is_ancestor(UNKNOWN, h.head()))
        self.assertFalse(h.is_ancestor(h.head(), "None"))


class RealGit(Script, unittest.TestCase):
    def make_history(self):
        env = mock.patch.dict(os.environ, ISOLATED_GIT)
        env.start()
        self.addCleanup(env.stop)
        for args in (["init", "-q"], ["config", "user.email", "test@example.com"], ["config", "user.name", "test"]):
            subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)
        return load_gamestate().GitHistory(self.root)

    def test_its_commits_are_unsigned(self):
        self.write("a.json", "1")
        self.history.commit("a", ["a.json"])
        body = subprocess.run(["git", "cat-file", "-p", "HEAD"], cwd=self.root, check=True, capture_output=True,
                              text=True).stdout
        self.assertNotIn("gpgsig", body)


class Memory(Script, unittest.TestCase):
    def make_history(self):
        return MemoryHistory(self.root)

    def test_commit_all_takes_the_whole_tree_even_unchanged(self):
        h = self.history
        self.assertTrue(h.clean())
        self.write("docs/game/state.json", "{}")
        self.write(".git/config", "ignored")
        self.assertFalse(h.clean())
        h.commit_all("work")
        first = h.rev_parse("HEAD")
        self.assertEqual(first, h.head())
        self.assertTrue(h.clean())
        self.assertTrue(h.tracked("docs/game/state.json"))
        self.assertFalse(h.tracked(".git/config"))
        h.commit_all("work")
        self.assertNotEqual(h.rev_parse("HEAD"), first)
        self.write("docs/game/state.json", '{"phase": "scan"}')
        self.assertFalse(h.clean())
        (self.root / "docs/game/state.json").unlink()
        self.assertFalse(h.clean())
        h.commit_all("work")
        self.assertTrue(h.clean())
        self.assertFalse(h.tracked("docs/game/state.json"))
        with self.assertRaises(ValueError):
            h.rev_parse(UNKNOWN)


if __name__ == "__main__":
    unittest.main()
