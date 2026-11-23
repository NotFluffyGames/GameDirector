"""Checks on the parallel test runner, tests/run.py.

Run: python3 -m unittest discover tests
"""
import importlib.util
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tests" / "run.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def unittest_ids(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from unittest_ids(item)
        else:
            yield item.id()


class Runner(unittest.TestCase):
    def test_discovers_the_same_tests_as_unittest(self):
        run = load_runner()
        expected = sorted(unittest_ids(unittest.defaultTestLoader.discover(
            str(ROOT / "tests"))))
        ids = run.discover_ids()
        self.assertEqual(sorted(ids), expected)
        self.assertTrue(any(i.startswith("test_gamestate.") for i in ids))
        self.assertTrue(any(i.startswith("test_skills.") for i in ids))

    def test_buckets_split_round_robin(self):
        run = load_runner()
        self.assertEqual(run.buckets(list("abcde"), 2), [list("ace"), list("bd")])
        self.assertEqual(len(run.buckets(list("abc"), 10)), 3)
        self.assertEqual(run.buckets(list("abc"), 0), [list("abc")])

    def test_runs_a_pattern_and_reports_ok(self):
        out = subprocess.run(
            [sys.executable, str(RUNNER), "-j", "2", "test_buckets_split_round_robin"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn(": OK", out.stdout)

    def test_a_failing_bucket_exits_1_and_shows_its_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_boom.py").write_text(textwrap.dedent("""
                import unittest
                class Boom(unittest.TestCase):
                    def test_fails(self):
                        self.fail("the failing assertion text")
            """))
            out = subprocess.run(
                [sys.executable, str(RUNNER), "--start", tmp],
                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        self.assertIn("the failing assertion text", out.stdout)
        self.assertIn("FAILED", out.stdout)

    def test_no_tests_found_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = subprocess.run(
                [sys.executable, str(RUNNER), "--start", tmp],
                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.returncode, 2, out.stdout + out.stderr)


if __name__ == "__main__":
    unittest.main()
