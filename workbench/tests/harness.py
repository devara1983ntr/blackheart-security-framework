"""The test harness: registration, assertions and helpers.

Kept in the package rather than in `run_tests.py` because a module executed as
`__main__` and imported as `workbench.run_tests` are two different objects with
two different registries — and a suite that silently runs zero tests is worse
than a suite that fails. One module, one registry, whichever way it is invoked.
"""

from __future__ import annotations

import tempfile

TESTS = []
FAILURES = []


def test(fn):
    """Register a test function. Source order keeps the output stable."""
    TESTS.append(fn)
    return fn


class AssertionFailed(AssertionError):
    """A failed expectation, reported without a traceback by default."""


def check(condition, message="assertion failed"):
    if not condition:
        raise AssertionFailed(message)


def equal(got, want, message=""):
    if got != want:
        raise AssertionFailed(f"{message or 'values differ'}: got {got!r}, want {want!r}")


def contains(haystack, needle, message=""):
    if needle not in haystack:
        raise AssertionFailed(f"{message or 'missing substring'}: {needle!r} not in {haystack!r}")


def not_contains(haystack, needle, message=""):
    if needle in haystack:
        raise AssertionFailed(f"{message or 'unexpected substring'}: {needle!r} found")


def raises(exc_type, fn, *args, **kwargs):
    """Assert that `fn` raises exactly the expected exception type."""
    try:
        fn(*args, **kwargs)
    except exc_type as exc:
        return exc
    except Exception as exc:                      # noqa: BLE001 - reported below
        raise AssertionFailed(
            f"expected {exc_type.__name__}, got {type(exc).__name__}: {exc}") from exc
    raise AssertionFailed(f"expected {exc_type.__name__}, nothing was raised")


def temp_dir(prefix="bh-test-"):
    return tempfile.mkdtemp(prefix=prefix)
