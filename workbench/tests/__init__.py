"""Workbench tests. Everything runs against local fixtures; nothing uses the network.

Test fixtures are not exempt from anything the workbench enforces, and that is
deliberate. A suite that quietly disabled a control to make itself pass would
prove nothing about the control, and the control is the thing worth proving.

So the fixtures do what an operator does, in the two places a fixture can:

* **The policy is accepted**, into a temporary state directory this package
  creates for the process and points ``BLACKHEART_STATE_DIR`` at. That is the
  documented mechanism for keeping the record somewhere other than a home
  directory, and it is how a CI job or a container runs the tool. It cannot be
  used to *create* acceptance: the tests that exercise the blocker point the same
  variable at an empty directory and assert that requests are refused.
* **The scope file authorises loopback only**, with the private-network opt-in
  that internal engagements legitimately use, and nothing else — see
  ``fixtures.scope_data``.

An acceptance recorded here is a real record written by ``policy.accept``, so the
gate is exercised rather than stubbed.
"""

from __future__ import annotations

import os
import tempfile

from workbench import policy as _policy

_ACCEPTANCE_DIR = os.path.join(tempfile.gettempdir(), "bh-workbench-test-state")
os.makedirs(_ACCEPTANCE_DIR, exist_ok=True)

# Set before anything imports the request path, so every module in the suite sees
# the same state directory.
os.environ[_policy.STATE_DIR_ENV] = _ACCEPTANCE_DIR

if not _policy.acceptance_status(directory=_ACCEPTANCE_DIR)["accepted"]:
    _policy.accept(_ACCEPTANCE_DIR)

del _policy
