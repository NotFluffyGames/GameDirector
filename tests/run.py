"""Run the test suite in parallel: python3 tests/run.py [-j N] [--start DIR] [pattern ...]

Discovers the tests `python3 -m unittest discover tests` would, keeps the ids containing any pattern, splits
them round-robin into N buckets and runs each bucket as its own `python3 -m unittest` subprocess.
Exit code: 0 all passed, 1 a bucket failed, 2 no tests found or discovery failed.
"""
import argparse
import os
import subprocess
import sys
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _start_dir(start):
    path = Path(start)
    return (path if path.is_absolute() else ROOT / path).resolve()


def _ids(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _ids(item)
        else:
            yield item.id()


def discover_ids(start="tests", pattern=None):
    """The dotted ids of the tests under `start`, only those containing any of `pattern` (a list) if given."""
    # Like `python3 -m unittest discover tests`: the start dir is also the top-level dir, so ids are
    # `test_skills.Class.test_x` and a subprocess started in that dir can import them.
    suite = unittest.defaultTestLoader.discover(str(_start_dir(start)))
    ids = list(_ids(suite))
    broken = [i for i in ids if i.startswith("unittest.loader.")]
    if broken:
        raise RuntimeError("test discovery failed: " + ", ".join(broken))
    if pattern:
        ids = [i for i in ids if any(p in i for p in pattern)]
    return ids


def buckets(ids, n):
    """Split ids round-robin into n buckets (at least 1, at most len(ids))."""
    n = max(1, min(n, len(ids)))
    return [ids[i::n] for i in range(n)]


def run_bucket(ids, cwd):
    started = time.time()
    proc = subprocess.run([sys.executable, "-m", "unittest", *ids], cwd=cwd,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc.returncode == 0, proc.stdout, time.time() - started


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the tests in parallel.")
    parser.add_argument("-j", type=int, default=os.cpu_count() or 1, help="number of parallel buckets")
    parser.add_argument("--start", default="tests", help="start directory (default: tests)")
    parser.add_argument("pattern", nargs="*", help="keep only test ids containing any of these")
    args = parser.parse_args(argv)

    try:
        ids = discover_ids(args.start, args.pattern)
    except Exception as err:
        print(err)
        return 2
    if not ids:
        print("no tests found")
        return 2

    cwd = _start_dir(args.start)
    groups = buckets(ids, args.j)
    started = time.time()
    with ThreadPoolExecutor(max_workers=len(groups)) as pool:
        results = list(pool.map(lambda g: run_bucket(g, cwd), groups))

    failed = []
    for number, (group, (ok, output, seconds)) in enumerate(zip(groups, results), 1):
        print("bucket %d/%d: %d tests %s in %.1fs" % (number, len(groups), len(group),
                                                      "OK" if ok else "FAILED", seconds))
        if not ok:
            failed.append(output)
    for output in failed:
        print()
        print(output)
    wall = time.time() - started
    if failed:
        print("Ran %d tests in %.1fs: FAILED (%d bucket(s))" % (len(ids), wall, len(failed)))
        return 1
    print("Ran %d tests in %.1fs: OK" % (len(ids), wall))
    return 0


if __name__ == "__main__":
    sys.exit(main())
