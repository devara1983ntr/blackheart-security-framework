"""The evidence record: one shape for every claim the workbench can make.

Why a schema and not free text
------------------------------
Because the framework's central rule is that a finding is a hypothesis until it
is validated, and a rule that lives only in prose is a rule that gets softened
in the writing. A record here cannot exist without a status, an expected and an
observed statement, a reproduction, **and a limitations field that cannot be
empty** — an unstated limitation reads as coverage, which is the specific
failure this repository was built to avoid.

The status ladder is ordered and enforced: a check may create `POTENTIAL` or
`OBSERVED`, and a status can only reach `REPRODUCED` by actually being
reproduced against the target with a matching second observation. Nothing in
this module — and nothing anywhere in the workbench — can promote a status by
assertion. There is no `set_status("CONFIRMED")`.

Hashing exists so an evidence bundle can be checked later: the record's hash
covers its own substantive content, and the bundle hash covers the set. A report
that cannot be verified against a hash is a claim about a run rather than a
record of one.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

from . import http_client as hc

STATUSES = ("OBSERVED", "REPRODUCED", "INFERRED", "POTENTIAL", "UNVERIFIED")

# What each status is allowed to become. Reproduction is the only path upward,
# and it requires a second matching observation rather than a decision.
ALLOWED_TRANSITIONS = {
    "POTENTIAL": ("REPRODUCED", "UNVERIFIED", "INFERRED"),
    "OBSERVED": ("REPRODUCED", "INFERRED", "UNVERIFIED"),
    "INFERRED": ("REPRODUCED", "UNVERIFIED"),
    "REPRODUCED": ("UNVERIFIED",),
    "UNVERIFIED": ("REPRODUCED", "INFERRED"),
}

SEVERITIES = ("informational", "low", "medium", "high", "critical")
CONFIDENCES = ("low", "medium", "high")

REQUIRED = ("id", "title", "severity", "confidence", "status", "target", "scope",
            "timestamp", "expected", "observed", "impact", "limitations",
            "remediation", "provenance")

# Words that assert a validated defect. A record that is not REPRODUCED may not
# use them, so the temptation to write a stronger claim than the evidence
# supports fails validation instead of passing review.
VALIDATED_LANGUAGE = ("vulnerable", "vulnerability", "confirmed", "exploitable",
                      "exploit works", "attack succeeded", "bypass succeeded",
                      "proof of concept works")

PROVENANCE_REQUIRED = ("tool", "tool_version", "origin", "generated_at")


class EvidenceError(Exception):
    """Raised when a record is incomplete, inconsistent, or overclaims."""


def canonical_json(payload):
    """Stable serialisation: sorted keys, no incidental whitespace."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_sha256(path, chunk=65536):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


class Evidence:
    """One record. Construction is deliberately verbose: every field is required."""

    def __init__(self, checking_id, title, *, severity, confidence, status,
                 target, scope, expected, observed, impact, limitations,
                 remediation, request=None, response=None, notes="",
                 reproduction=None, provenance=None, tool_version="1.0.0"):
        if status not in STATUSES:
            raise EvidenceError(f"unknown status {status!r}; expected one of {STATUSES}")
        if severity not in SEVERITIES:
            raise EvidenceError(f"unknown severity {severity!r}; expected one of {SEVERITIES}")
        if confidence not in CONFIDENCES:
            raise EvidenceError(f"unknown confidence {confidence!r}; expected one of {CONFIDENCES}")
        self.id = checking_id
        self.title = title
        self.severity = severity
        self.confidence = confidence
        self.status = status
        self.target = target
        self.scope = scope
        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.expected = expected
        self.observed = observed
        self.impact = impact
        self.limitations = limitations
        self.remediation = remediation
        self.request = request or {}
        self.response = response or {}
        self.notes = notes
        self.reproduction = reproduction or []
        self.provenance = dict(provenance or {}, tool="blackheart-workbench",
                               tool_version=tool_version,
                               origin="local-run",
                               generated_at=self.timestamp)
        self.hashes = {}

    # -- serialisation ---------------------------------------------------
    def payload(self):
        """The substantive content. Hashes and notes are excluded from the hash."""
        return {
            "id": self.id, "title": self.title, "severity": self.severity,
            "confidence": self.confidence, "status": self.status,
            "target": self.target, "scope": self.scope, "timestamp": self.timestamp,
            "expected": self.expected, "observed": self.observed,
            "impact": self.impact, "limitations": self.limitations,
            "remediation": self.remediation, "reproduction": self.reproduction,
            "provenance": {k: v for k, v in self.provenance.items() if k != "generated_at"},
            "request": self.request, "response": self.response,
        }

    def as_dict(self):
        data = self.payload()
        data["notes"] = self.notes
        data["hashes"] = dict(self.hashes)
        return data

    def compute_hashes(self):
        content = canonical_json(self.payload())
        self.hashes["record_sha256"] = sha256_text(content)
        request_json = canonical_json(self.request or {})
        self.hashes["request_sha256"] = sha256_text(request_json)
        self.hashes["response_sha256"] = sha256_text(
            canonical_json({k: v for k, v in (self.response or {}).items()
                            if k != "body_text"}))
        if (self.response or {}).get("body_text"):
            self.hashes["response_body_sha256"] = sha256_text(self.response["body_text"])
        return self.hashes

    # -- validation ------------------------------------------------------
    def validate(self):
        """Raise on anything that would make this record dishonest or incomplete."""
        for field in REQUIRED:
            value = getattr(self, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                raise EvidenceError(f"{self.id}: {field} is required and must not be empty")
        if not self.limitations.strip():
            raise EvidenceError(
                f"{self.id}: limitations is empty. A record without a stated "
                f"limitation reads as complete coverage")
        if not self.reproduction:
            raise EvidenceError(f"{self.id}: reproduction steps are required")
        if not isinstance(self.reproduction, list):
            raise EvidenceError(f"{self.id}: reproduction must be a list of steps")
        for key in PROVENANCE_REQUIRED:
            if key not in self.provenance:
                raise EvidenceError(f"{self.id}: provenance is missing {key}")
        if self.status != "REPRODUCED":
            blob = " ".join([self.title, self.impact, self.observed]).lower()
            used = [word for word in VALIDATED_LANGUAGE if word in blob]
            if used:
                raise EvidenceError(
                    f"{self.id}: status is {self.status} but the record claims "
                    f"{used}. Only a REPRODUCED record may assert a validated defect.")
        if self.severity == "critical" and self.status not in ("REPRODUCED",):
            raise EvidenceError(
                f"{self.id}: critical severity with status {self.status} is not "
                f"permitted: critical requires reproduction")
        return True

    def transition(self, new_status, *, reproduction=None):
        """Move along the ladder. No call site can skip the rules."""
        if new_status not in STATUSES:
            raise EvidenceError(f"unknown status {new_status!r}")
        if new_status not in ALLOWED_TRANSITIONS[self.status]:
            raise EvidenceError(
                f"{self.id}: {self.status} -> {new_status} is not a permitted "
                f"transition (allowed: {ALLOWED_TRANSITIONS[self.status]})")
        if new_status == "REPRODUCED":
            if not reproduction:
                raise EvidenceError(
                    f"{self.id}: REPRODUCED requires the second observation that "
                    f"reproduced it, not an assertion")
            self.reproduction.append(reproduction)
        self.status = new_status
        return self

    def redact(self, secrets=()):
        """Replace credential values and sensitive headers wherever they appear."""
        if self.request.get("headers"):
            self.request["headers"] = hc.redact_headers(self.request["headers"])
        if self.response.get("headers"):
            self.response["headers"] = hc.redact_headers(self.response["headers"])
        blob = canonical_json(self.as_dict())
        for value in secrets or ():
            if value and len(str(value)) >= 4 and str(value) in blob:
                self._replace(str(value))
        return self

    def _replace(self, value):
        for holder in (self.request, self.response, self.__dict__):
            for key, item in list(holder.items()):
                if isinstance(item, str):
                    holder[key] = item.replace(value, hc.REDACTED)
                elif isinstance(item, list):
                    holder[key] = [i.replace(value, hc.REDACTED)
                                   if isinstance(i, str) else i for i in item]


class Bundle:
    """A set of records with a manifest, written as a directory."""

    def __init__(self, name="evidence", directory=None, scope_file=None):
        self.name = name
        self.directory = directory
        self.scope_file = scope_file
        self.records = []
        self.started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def add(self, record):
        record.validate()
        record.compute_hashes()
        self.records.append(record)
        return record

    def manifest(self):
        entries = [{"id": r.id, "title": r.title, "status": r.status,
                    "severity": r.severity, "sha256": r.hashes.get("record_sha256"),
                    "target": r.target} for r in self.records]
        body = {
            "bundle": self.name,
            "created_at": self.started_at,
            "scope_file": self.scope_file,
            "records": entries,
            "count": len(entries),
            "by_status": _count(entries, "status"),
            "by_severity": _count(entries, "severity"),
        }
        body["manifest_sha256"] = sha256_text(canonical_json(
            {k: v for k, v in body.items() if k != "manifest_sha256"}))
        return body

    def write(self, directory):
        os.makedirs(directory, exist_ok=True)
        for record in self.records:
            path = os.path.join(directory, f"{record.id}.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(record.as_dict(), fh, indent=2, sort_keys=True)
        manifest = self.manifest()
        with open(os.path.join(directory, "manifest.json"), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, sort_keys=True)
        return manifest

    @staticmethod
    def verify(directory):
        """Re-hash the records in a written bundle and report the first mismatch.

        This is what makes a bundle checkable by someone who was not present for
        the run, which is the only kind of evidence worth attaching.
        """
        problems = []
        manifest_path = os.path.join(directory, "manifest.json")
        if not os.path.isfile(manifest_path):
            return [f"{manifest_path} not found"]
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
        for entry in manifest.get("records", []):
            path = os.path.join(directory, f"{entry['id']}.json")
            if not os.path.isfile(path):
                problems.append(f"{entry['id']}: record file missing")
                continue
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            recomputed = sha256_text(canonical_json({
                key: value for key, value in data.items()
                if key not in ("hashes", "notes")}))
            if recomputed != entry["sha256"]:
                problems.append(f"{entry['id']}: hash mismatch "
                                f"({recomputed[:12]} != {entry['sha256'][:12]})")
        return problems


def _count(entries, field):
    counts = {}
    for entry in entries:
        counts[entry[field]] = counts.get(entry[field], 0) + 1
    return counts


def provenance_for(scope_summary=None, source="local-run", extra=None):
    """Provenance stamped into every record: what ran, where, under which scope."""
    data = {
        "tool": "blackheart-workbench",
        "tool_version": "1.0.0",
        "origin": source,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": scope_summary or {},
        "fixture": False,
    }
    data.update(extra or {})
    return data
