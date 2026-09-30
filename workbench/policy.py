"""The policy layer: what the framework acknowledges, and when that is required.

Two different things live here, and keeping them apart is the point:

* **The policy** is `policy/BLACKHEART-POLICY.json` plus the documents it names.
  It states the rules, the prohibited actions and the acquisition rules, in a
  form a person can read and a program can check.
* **Acceptance** is a local record that the operator read the policy. It holds a
  policy version, a policy hash and a timestamp. It holds nothing about who the
  operator is, and it is never transmitted anywhere.

**Acceptance is not authorization.** Accepting the policy says "I have read the
rules". It says nothing about whether the operator is allowed to test anything.
Authorization is the scope file, it is supplied separately, and it is checked by
`scope.require()` below every request.

Enforcement sits in `http_client.request()` rather than in the command layer,
because that function is the only place in the framework that opens a socket: a
caller who goes around the CLI still goes through it. The one thing this cannot
defend against is stated where it belongs — in
`docs/workbench/INDEPENDENT-SECURITY-REVIEW.md` and in the policy's own
`enforcement.documented_residual` — because a local acknowledgement file can be
written by anyone with local write access. It records an acknowledgement, not a
secret, and pretending otherwise would be a claim the code does not support.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

#: The state directory is relocatable so a run can keep its acceptance state
#: somewhere other than the home directory — a container, a CI job, a test.
#: Relocating it cannot *create* acceptance: pointing this at an empty directory
#: blocks active operations exactly as an unaccepted policy does.
STATE_DIR_ENV = "BLACKHEART_STATE_DIR"
ACCEPTANCE_FILE = "policy-acceptance.json"

#: Versions that must be present in the policy document. The authorization
#: schema version is separate because the scope-file schema and the policy
#: document change for different reasons.
REQUIRED_VERSIONS = (
    "policy_version",
    "terms_version",
    "acceptable_use_version",
    "privacy_version",
    "authorization_schema_version",
)

#: Documents the policy names, and the file each must resolve to.
REQUIRED_DOCUMENT_KEYS = (
    "legal",
    "terms_of_use",
    "acceptable_use",
    "security_research_disclaimer",
    "privacy_policy",
    "authorization_agreement",
    "responsible_use",
    "third_party_content",
    "download_and_acquisition",
    "ai_agent_terms",
)


class PolicyError(Exception):
    """The policy is missing, malformed, or not accepted where it must be."""


def repo_root():
    """The repository the running code belongs to."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def policy_path(path=None):
    return os.path.abspath(path or os.path.join(repo_root(), "policy",
                                                "BLACKHEART-POLICY.json"))


def state_dir(directory=None):
    """Where the acceptance record lives.

    Resolution order is explicit, in this order and no other: the argument, the
    environment variable, then the default. Nothing else in this module reads
    the environment, so there is no second override to reason about.
    """
    if directory:
        return os.path.abspath(directory)
    from_env = os.environ.get(STATE_DIR_ENV)
    if from_env:
        return os.path.abspath(os.path.expanduser(from_env))
    return os.path.join(os.path.expanduser("~"), ".blackheart")


def acceptance_path(directory=None):
    return os.path.join(state_dir(directory), ACCEPTANCE_FILE)


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path=None):
    """Read the policy document. Every failure is a `PolicyError`."""
    target = policy_path(path)
    if not os.path.isfile(target):
        raise PolicyError(
            f"the policy document is missing: {target}. Active operations require "
            f"a policy that can be read, because acceptance is recorded against a "
            f"version of it")
    try:
        with open(target, encoding="utf-8") as fh:
            policy = json.load(fh)
    except json.JSONDecodeError as exc:
        raise PolicyError(
            f"the policy document does not parse as JSON: {target} ({exc}). It is "
            f"not repaired automatically; a policy that is edited by hand is "
            f"either valid or refused") from None
    if not isinstance(policy, dict):
        raise PolicyError(f"the policy document is not a JSON object: {target}")
    return policy


def validate(policy=None, *, path=None):
    """Check the policy is complete and every document it names exists.

    Returns a list of problems, empty when the policy holds together. This is
    what `blackheart policy validate` prints and what the repository gate runs,
    so the two cannot drift into disagreeing about what "valid" means.
    """
    problems = []
    try:
        policy = policy if policy is not None else load(path)
    except PolicyError as exc:
        return [str(exc)]

    for key in REQUIRED_VERSIONS:
        value = policy.get(key)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{key} is missing or empty")
    for key in REQUIRED_DOCUMENT_KEYS:
        name = (policy.get("documents") or {}).get(key)
        if not name:
            problems.append(f"documents.{key} is missing")
            continue
        if not os.path.isfile(os.path.join(repo_root(), name)):
            problems.append(f"documents.{key} names {name}, which does not exist")

    prohibited = policy.get("prohibited_actions") or []
    if len(prohibited) < 10:
        problems.append("prohibited_actions is empty or too short to be a policy")
    requirements = policy.get("requirements") or {}
    for key in ("acceptance_required_for_active_operations",
                "authorization_required_for_active_operations"):
        if requirements.get(key) is not True:
            problems.append(f"requirements.{key} must be true")
    if requirements.get("acceptance_is_not_authorization") is not True:
        problems.append("requirements.acceptance_is_not_authorization must be true: "
                        "acceptance records an acknowledgement, not permission")
    acceptance = policy.get("acceptance") or {}
    if acceptance.get("transmitted_remotely") is not False:
        problems.append("acceptance.transmitted_remotely must be false; nothing in "
                        "this framework sends acceptance anywhere")
    if acceptance.get("collects_identity") is not False:
        problems.append("acceptance.collects_identity must be false")
    return problems


def read_acceptance(directory=None):
    """The recorded acceptance, or None.

    A symlinked state file is refused rather than followed: the acceptance record
    is read at the network boundary, and following a link there would let a file
    that is not the one the operator created decide whether requests go out.
    """
    target = acceptance_path(directory)
    if os.path.islink(target):
        raise PolicyError(
            f"the acceptance record at {target} is a symbolic link. It is read at "
            f"the network boundary, so it is refused rather than followed. Replace "
            f"it with a file written by `blackheart policy accept`")
    if not os.path.isfile(target):
        return None
    try:
        with open(target, encoding="utf-8") as fh:
            record = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        raise PolicyError(
            f"the acceptance record at {target} cannot be read ({exc}). Accept the "
            f"policy again with `blackheart policy accept`") from None
    if not isinstance(record, dict):
        raise PolicyError(f"the acceptance record at {target} is not a JSON object")
    return record


def acceptance_status(policy=None, *, directory=None, path=None):
    """Whether the policy has been accepted, and whether that acceptance is current.

    A stale acceptance — recorded against an older policy version or a policy
    document whose content has changed — is not acceptance. That is the whole
    reason the version and the hash are recorded: changing the terms silently
    must not carry the earlier acknowledgement forward.
    """
    status = {
        "accepted": False,
        "current_version": None,
        "accepted_version": None,
        "accepted_at": None,
        "recorded_policy_sha256": None,
        "current_policy_sha256": None,
        "target": acceptance_path(directory),
        "reason": "",
    }
    try:
        policy = policy if policy is not None else load(path)
    except PolicyError as exc:
        status["reason"] = str(exc)
        return status
    status["current_version"] = policy.get("policy_version")
    try:
        status["current_policy_sha256"] = file_sha256(policy_path(path))
    except OSError as exc:
        status["reason"] = f"the policy document cannot be read: {exc}"
        return status

    try:
        record = read_acceptance(directory)
    except PolicyError as exc:
        status["reason"] = str(exc)
        return status
    if record is None:
        status["reason"] = ("no acceptance has been recorded on this machine: "
                            "run `blackheart policy accept`")
        return status
    status["accepted_version"] = record.get("policy_version")
    status["accepted_at"] = record.get("accepted_at")
    status["recorded_policy_sha256"] = record.get("policy_sha256")
    if status["accepted_version"] != status["current_version"]:
        status["reason"] = (f"the recorded acceptance is for policy version "
                            f"{status['accepted_version']!r} and the policy is now "
                            f"{status['current_version']!r}")
        return status
    recorded = status["recorded_policy_sha256"]
    if not isinstance(recorded, str) or not recorded.strip():
        # A record with no hash cannot be checked against the policy in front of
        # it, and an unchecked record is not an acceptance. This is what a
        # hand-edited file looks like: the version still matches, so only
        # demanding the hash stops the edit from reading as current.
        status["reason"] = ("the recorded acceptance carries no policy hash, so it "
                            "cannot be checked against the policy in front of it. "
                            "Accept it again with `blackheart policy accept`")
        return status
    if recorded != status["current_policy_sha256"]:
        status["reason"] = ("the policy document has changed since it was accepted, "
                            "so the earlier acknowledgement does not cover it")
        return status
    status["accepted"] = True
    status["reason"] = "accepted, and the policy has not changed since"
    return status


def accept(directory=None, *, now=None, path=None):
    """Record acceptance of the current policy, and return what was written.

    Written to a temporary file and moved into place, so an interrupted write
    cannot leave a half-written acceptance that reads as valid. No identity, no
    hostname, no user name: the record says which policy version was accepted and
    when, and nothing else.
    """
    policy = load(path)
    problems = validate(policy)
    if problems:
        raise PolicyError("the policy does not validate, so it cannot be accepted: "
                          + "; ".join(problems[:3]))
    directory_used = state_dir(directory)
    os.makedirs(directory_used, exist_ok=True)
    record = {
        "policy_version": policy.get("policy_version"),
        "policy_sha256": file_sha256(policy_path(path)),
        "accepted_at": now or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "record_format": 1,
    }
    target = acceptance_path(directory_used)
    temporary = target + ".tmp"
    with open(temporary, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, sort_keys=True)
    os.chmod(temporary, 0o600)
    os.replace(temporary, target)
    return record


def require_acceptance(directory=None, *, path=None):
    """The gate. Raises `PolicyError` when active operations are not permitted.

    Called from the single place that opens sockets, so a caller that goes around
    the command surface is stopped by the same check as one that uses it.
    """
    status = acceptance_status(directory=directory, path=path)
    if not status["accepted"]:
        raise PolicyError(
            f"the policy has not been accepted, so no request may be sent: "
            f"{status['reason']}. Read policy/BLACKHEART-POLICY.json and the "
            f"documents it names, then run `blackheart policy accept`. Acceptance "
            f"records that you read the rules; it is not authorization for any "
            f"target, which is a separate requirement")
    return status


def summary(policy=None, path=None, directory=None):
    """A short, truthful description of the policy, for `blackheart policy show`."""
    policy = policy if policy is not None else load(path)
    documents = policy.get("documents") or {}
    return {
        "project": (policy.get("project") or {}).get("name"),
        "repository": (policy.get("project") or {}).get("repository"),
        "author": (policy.get("project") or {}).get("author"),
        "legal_review": (policy.get("project") or {}).get("legal_review"),
        "versions": {key: policy.get(key) for key in REQUIRED_VERSIONS},
        "updated": policy.get("updated"),
        "documents": {key: documents.get(key) for key in REQUIRED_DOCUMENT_KEYS},
        "requirements": dict(policy.get("requirements") or {}),
        "acceptance": dict(policy.get("acceptance") or {}),
        "exempt_operations": list(policy.get("exempt_operations") or []),
        "prohibited_actions": list(policy.get("prohibited_actions") or []),
        "allowed_actions": list(policy.get("allowed_actions") or []),
        "acquisition_rules": dict(policy.get("acquisition_rules") or {}),
        "status": acceptance_status(policy, directory=directory),
    }
