"""A tiny test runner, so the workbench's tests need no third-party framework.

The repository authors no dependency manifest on purpose (see
`docs/CAPABILITY-AUDIT.md` §4 and gap-audit group 20), so `pytest` is not
available and must not become a requirement to run the suite. What is actually
needed — discovery, assertions, setup/teardown, a deterministic exit code — is
about eighty lines, and this is those eighty lines.

Usage:
    python3 workbench/run_tests.py             # everything
    python3 workbench/run_tests.py scope       # modules matching "scope"
    python3 workbench/run_tests.py --json      # machine-readable summary
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import pkgutil
import sys
import tempfile
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# One registry, in the package. `run_tests.py` may be executed as __main__ or
# imported as workbench.run_tests; both must see the same list.
from workbench.tests.harness import (          # noqa: E402
    TESTS, FAILURES, AssertionFailed, test, check, equal, contains,
    not_contains, raises, temp_dir,
)

__all__ = ["main", "TESTS", "FAILURES", "test", "check", "equal", "contains",
           "not_contains", "raises", "temp_dir", "load_modules"]


def load_modules(pattern=None):
    """Import every `test_*` module and collect its `test_*` functions.

    Discovery is by name, and functions are ordered by the line they are defined
    on, so output order matches reading order in the file.
    """
    import inspect

    package = importlib.import_module("workbench.tests")
    names = [m.name for m in pkgutil.iter_modules(package.__path__)
             if m.name.startswith("test_")]
    names.sort()
    if pattern:
        names = [n for n in names if pattern in n]

    collected = []
    for name in names:
        module = importlib.import_module(f"workbench.tests.{name}")
        found = []
        for attr, value in vars(module).items():
            if not attr.startswith("test_") or not callable(value):
                continue
            if getattr(value, "__module__", "") != module.__name__:
                continue          # a re-exported helper, not this module's test
            try:
                lineno = inspect.getsourcelines(value)[1]
            except OSError:
                lineno = 0
            found.append((lineno, attr, value))
        found.sort(key=lambda item: (item[0], item[1]))
        collected.extend((f"{name}::{attr}", fn) for _, attr, fn in found)
    return names, collected


def main(argv=None):
    ap = argparse.ArgumentParser(description="run the workbench test suite")
    ap.add_argument("pattern", nargs="?", default=None,
                    help="only modules whose name contains this string")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    started = time.time()
    modules, discovered = load_modules(args.pattern)
    for name, fn in discovered:
        try:
            fn()
        except AssertionFailed as exc:
            FAILURES.append((name, str(exc), traceback.format_exc()))
        except Exception as exc:                  # noqa: BLE001 - reported, not swallowed
            FAILURES.append((name, f"{type(exc).__name__}: {exc}", traceback.format_exc()))
    elapsed = time.time() - started

    total = len(discovered)
    if args.json:
        print(json.dumps({
            "modules": modules,
            "tests": total,
            "passed": total - len(FAILURES),
            "failed": len(FAILURES),
            "seconds": round(elapsed, 2),
            "failures": [{"test": n, "error": e} for n, e, _ in FAILURES],
        }, indent=2, sort_keys=True))
    else:
        print("BLACKHEART workbench — test suite")
        print("=" * 68)
        print(f"  modules : {len(modules)} ({', '.join(m for m in modules)})")
        print(f"  tests   : {total}")
        for name, error, tb in FAILURES:
            print("-" * 68)
            print(f"  FAIL  {name}")
            print(f"        {error}")
            if os.environ.get("BH_TEST_TRACE"):
                print(tb)
        print("=" * 68)
        print(f"  {total - len(FAILURES)} passed, {len(FAILURES)} failed"
              f"  ({elapsed:.1f}s)")
        if FAILURES:
            print("\n  A failing test is a statement about the workbench, not about")
            print("  the test. Do not relax the assertion.")
        print("=" * 68)
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
