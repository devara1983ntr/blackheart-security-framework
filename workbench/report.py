"""Build a report from evidence, an acquisition manifest and a run record.

Three rules shape everything here.

**Every number is derived.** The counts in a report are computed from the records
being reported on, never typed. A hand-written count is a claim that drifts from
the evidence the first time something is added, and the drift is invisible
because the number still looks plausible.

**Nothing is promoted.** A record that says `POTENTIAL` is reported as a
potential observation, with the limitation the record itself carries. The report
does not summarise a `POTENTIAL` record into stronger language, and the section
that lists what was *not* established is generated automatically from the
records' own statuses rather than remembered.

**The gaps are part of the report.** A report that lists six records and omits
that the crawl stopped at the page cap, that forty references were out of scope,
or that two files were refused by the extractor, invites a reader to conclude the
work was complete. The coverage section is generated from the same inputs and
cannot be skipped.
"""

from __future__ import annotations

import json
import os

from . import evidence as ev
from . import fetch as fetchmod

SEVERITY_ORDER = ("critical", "high", "medium", "low", "informational")
STATUS_ORDER = ("REPRODUCED", "OBSERVED", "INFERRED", "POTENTIAL", "UNVERIFIED")

NOT_ESTABLISHED = ("POTENTIAL", "UNVERIFIED")

STANDING_STATEMENTS = (
    "This framework does not bypass authentication, authorization, paywalls, DRM, "
    "licensing controls, or other access restrictions.",
    "An observable response difference is not a finding. A finding is a difference "
    "a person validated against the engagement's rules.",
    "A record stating POTENTIAL or UNVERIFIED has not been validated and must not be "
    "reported as a defect.",
    "Nothing in this report was fabricated, simulated or estimated: every observation "
    "comes from a request this tool actually made to the target named in the scope.",
    "That something is absent from this report is not evidence that it is absent from "
    "the target.",
)


def _dedupe_problems(problems):
    """Say each problem once.

    A missing record file is detected twice on purpose — once while reading the
    bundle and once by the verifier — and reporting it twice reads like two
    separate faults.
    """
    seen, unique = set(), []
    for problem in problems:
        identifier, _, rest = problem.partition(":")
        key = (identifier.strip(), "missing" if "missing" in rest else rest.strip())
        if key in seen:
            continue
        seen.add(key)
        unique.append(problem)
    return unique


def _count(items, field):
    counts = {}
    for item in items:
        value = item.get(field)
        counts[value] = counts.get(value, 0) + 1
    return counts


def _ordered(counts, order):
    out = []
    for key in order:
        if key in counts:
            out.append((key, counts[key]))
    for key in sorted(counts):
        if key not in order:
            out.append((key, counts[key]))
    return out


class Report:
    """The report, as data first. Rendering is a separate, replaceable step."""

    def __init__(self, title, *, scope_file=None, scope_summary=None, generated_at=None,
                 tool_version=None):
        self.title = title
        self.scope_file = scope_file
        self.scope_summary = scope_summary or {}
        self.generated_at = generated_at or fetchmod.now()
        self.tool_version = tool_version or ev.provenance_for({})["tool_version"]
        self.records = []
        self.manifest = None
        self.manifest_path = None
        self.discovery = None
        self.fuzz_runs = []
        self.notes = []
        self.engagement = {}
        self.verification = {}

    # -- inputs ----------------------------------------------------------
    def add_records(self, records):
        for record in records:
            payload = record.as_dict() if hasattr(record, "as_dict") else record
            self.records.append(payload)
        return self

    def add_bundle(self, directory):
        """Read a written evidence bundle, and verify it while reading.

        A missing or unreadable piece is a problem in the report, not an
        exception: the reader of a report needs to know that a record was
        deleted, and a tool that refuses to produce the report at all tells them
        nothing. Nothing from an incomplete bundle is adopted as evidence — the
        count of records the report claims is the count it could actually read.
        """
        manifest_path = os.path.join(directory, "manifest.json")
        name = os.path.basename(os.path.normpath(directory))
        if not os.path.isfile(manifest_path):
            self.verification["evidence_bundle"] = {
                "directory": name, "manifest_sha256": None, "count": None,
                "problems": [f"{manifest_path} not found: no record in this directory "
                             f"is reported, because nothing in it says which records "
                             f"belong to the run"],
            }
            return self
        with open(manifest_path, encoding="utf-8") as fh:
            bundle = json.load(fh)
        problems = []
        for entry in bundle.get("records", []):
            path = os.path.join(directory, f"{entry['id']}.json")
            if not os.path.isfile(path):
                problems.append(f"{entry['id']}: record file missing, so it is not "
                                f"included in this report")
                continue
            with open(path, encoding="utf-8") as fh:
                self.records.append(json.load(fh))
        problems = _dedupe_problems(problems + list(ev.Bundle.verify(directory)))
        self.verification["evidence_bundle"] = {
            "directory": name,
            "manifest_sha256": bundle.get("manifest_sha256"),
            "count": bundle.get("count"),
            "problems": problems,
        }
        return self

    def add_manifest(self, path):
        """Read a downloads manifest, and verify the files it claims."""
        with open(path, encoding="utf-8") as fh:
            self.manifest = json.load(fh)
        self.manifest_path = path
        self.verification["downloads_manifest"] = {
            "path": os.path.basename(path),
            "problems": fetchmod.verify_manifest(path),
        }
        return self

    def add_discovery(self, discovery):
        self.discovery = discovery
        return self

    def add_fuzz_run(self, run_state):
        self.fuzz_runs.append(run_state)
        return self

    def note(self, text):
        self.notes.append(text)
        return self

    def set_engagement(self, **values):
        self.engagement.update(values)
        return self

    # -- derived facts ---------------------------------------------------
    def counts(self):
        by_status = _count(self.records, "status")
        by_severity = _count(self.records, "severity")
        return {
            "records": len(self.records),
            "by_status": by_status,
            "by_severity": by_severity,
            "not_established": sum(by_status.get(status, 0) for status in NOT_ESTABLISHED),
            "reproduced": by_status.get("REPRODUCED", 0),
        }

    def acquisition_counts(self):
        if not self.manifest:
            return {}
        return self.manifest.get("counts", {})

    def as_dict(self):
        return {
            "title": self.title,
            "generated_at": self.generated_at,
            "tool": "blackheart-workbench",
            "tool_version": self.tool_version,
            "scope_file": self.scope_file,
            "authorization_scope": self.scope_summary,
            "engagement": self.engagement,
            "counts": self.counts(),
            "records": self.records,
            "acquisitions": self.manifest,
            "discovery": self.discovery.summary() if self.discovery else None,
            "fuzzing": [run.summary() for run in self.fuzz_runs],
            "verification": self.verification,
            "notes": self.notes,
            "statements": list(STANDING_STATEMENTS),
        }

    # -- rendering -------------------------------------------------------
    def markdown(self):
        counts = self.counts()
        lines = [f"# {self.title}", ""]
        lines.append(f"Generated {self.generated_at} by blackheart-workbench "
                     f"{self.tool_version}.")
        lines.append("")
        for statement in STANDING_STATEMENTS:
            lines.append(f"> {statement}")
        lines.append("")

        if self.engagement:
            lines += ["## Engagement", ""]
            for key in sorted(self.engagement):
                lines.append(f"- **{key}**: {self.engagement[key]}")
            lines.append("")

        lines += ["## Scope", ""]
        if self.scope_file:
            lines.append(f"- Scope file: `{self.scope_file}`")
        for key in sorted(self.scope_summary):
            lines.append(f"- {key}: {self.scope_summary[key]}")
        if not self.scope_summary:
            lines.append("- No scope summary was supplied to this report.")
        lines.append("")

        lines += ["## Summary", ""]
        lines.append(f"- Evidence records: {counts['records']}")
        lines.append(f"- Validated (REPRODUCED): {counts['reproduced']}")
        lines.append(f"- Not validated (POTENTIAL or UNVERIFIED): {counts['not_established']}")
        if counts["by_status"]:
            lines.append("- By status: " + ", ".join(
                f"{name} {value}" for name, value in _ordered(counts["by_status"], STATUS_ORDER)))
        if counts["by_severity"]:
            lines.append("- By severity: " + ", ".join(
                f"{name} {value}"
                for name, value in _ordered(counts["by_severity"], SEVERITY_ORDER)))
        lines.append("")

        if self.records:
            lines += ["## Observations", "",
                      "| id | status | severity | confidence | target | title |",
                      "| --- | --- | --- | --- | --- | --- |"]
            for record in sorted(self.records, key=lambda r: str(r.get("id"))):
                lines.append(
                    f"| {record.get('id')} | {record.get('status')} | "
                    f"{record.get('severity')} | {record.get('confidence')} | "
                    f"`{record.get('target')}` | {record.get('title')} |")
            lines.append("")
            lines += ["## Record detail", ""]
            for record in sorted(self.records, key=lambda r: str(r.get("id"))):
                lines += self._record_markdown(record)

        if self.manifest:
            lines += self._acquisitions_markdown()

        if self.discovery:
            summary = self.discovery.summary()
            lines += ["## Discovery coverage", "",
                      f"- Root: `{summary['root']}`",
                      f"- Pages fetched: {summary['pages_fetched']} "
                      f"(cap {summary['max_pages']}, depth {summary['max_depth']})",
                      f"- Requests used: {summary['requests_used']} of {summary['budget']}",
                      f"- Findings: {summary['findings']} {summary['by_kind']}",
                      f"- References out of scope, not followed: "
                      f"{summary['refused_out_of_scope']}",
                      f"- In-scope URLs the target declined: {summary['unavailable']}",
                      f"- References left in the frontier when the run stopped: "
                      f"{summary['not_followed_by_cap']}",
                      "", summary["note"], ""]

        if self.fuzz_runs:
            lines += ["## Fuzzing coverage", ""]
            for run in self.fuzz_runs:
                summary = run.summary()
                lines += [f"- Mutations executed: {summary['executed']} of "
                          f"{summary['planned']} planned (budget {summary['budget']}, "
                          f"plan from the {summary['plan_source']})",
                          f"- Requests sent: {summary['requests_sent']}; duplicates "
                          f"skipped: {summary['duplicates_skipped']}",
                          f"- Observable response differences: "
                          f"{summary['differences_observed']}",
                          f"- {summary['note']}"]
            lines.append("")

        if self.notes:
            lines += ["## Notes", ""] + [f"- {note}" for note in self.notes] + [""]

        lines += ["## Verification", ""]
        if self.verification:
            for name, detail in sorted(self.verification.items()):
                problems = detail.get("problems") or []
                state = "clean" if not problems else f"{len(problems)} problem(s)"
                lines.append(f"- {name}: {state}")
                for problem in problems[:10]:
                    lines.append(f"  - {problem}")
        else:
            lines.append("- No bundle or manifest was supplied, so nothing was re-hashed.")
        lines.append("")

        lines += ["## What this report does not establish", ""]
        not_validated = [r for r in self.records if r.get("status") in NOT_ESTABLISHED]
        if not self.records:
            lines.append("- This report carries no evidence records at all, so it says "
                         "nothing about the target either way.")
        else:
            lines.append(f"- {len(not_validated)} of {len(self.records)} record(s) are not "
                         f"validated findings. They record what was observed; whether it "
                         f"matters is a separate question, answered by a person.")
            lines.append(f"- {len(self.records) - len(not_validated)} record(s) are OBSERVED, "
                         f"INFERRED or REPRODUCED; each states its own limitation, and those "
                         f"limitations appear in full above rather than being summarised "
                         f"here.")
        if self.discovery:
            lines.append(f"- Discovery did not exhaust the target: "
                         f"{self.discovery.summary()['not_followed_by_cap']} reference(s) "
                         f"were left unexplored and "
                         f"{self.discovery.summary()['refused_out_of_scope']} were out of "
                         f"scope by design.")
        lines.append("- Absence of an observation is not evidence of absence.")
        lines.append("")
        return "\n".join(lines)

    def _record_markdown(self, record):
        lines = [f"### {record.get('id')} — {record.get('title')}", ""]
        lines.append(f"- **Status**: {record.get('status')} "
                     f"(confidence {record.get('confidence')}, severity "
                     f"{record.get('severity')})")
        lines.append(f"- **Target**: `{record.get('target')}`")
        lines.append(f"- **Expected**: {record.get('expected')}")
        lines.append(f"- **Observed**: {record.get('observed')}")
        lines.append(f"- **Impact**: {record.get('impact')}")
        lines.append(f"- **Limitations**: {record.get('limitations')}")
        lines.append(f"- **Remediation**: {record.get('remediation')}")
        if record.get("request"):
            lines.append(f"- **Request**: `{record['request'].get('method')} "
                         f"{record['request'].get('url')}`")
        response = record.get("response") or {}
        if response:
            lines.append(f"- **Response**: status {response.get('status')}, "
                         f"{response.get('content_type')}, {response.get('bytes')} bytes")
        if record.get("reproduction"):
            lines.append("- **Reproduction**:")
            for step in record["reproduction"]:
                lines.append(f"  - {step}")
        hashes = record.get("hashes") or {}
        if hashes.get("record_sha256"):
            lines.append(f"- **Record SHA-256**: `{hashes['record_sha256']}`")
        provenance = record.get("provenance") or {}
        if provenance:
            lines.append(f"- **Provenance**: {provenance.get('tool')} "
                         f"{provenance.get('tool_version')}, origin "
                         f"{provenance.get('origin')}")
        lines.append("")
        return lines

    def _acquisitions_markdown(self):
        counts = self.acquisition_counts()
        lines = ["## Acquisitions", "",
                 f"- Obtained: {counts.get('success', 0)}",
                 f"- Blocked: {counts.get('blocked', 0)}",
                 f"- Failed: {counts.get('failed', 0)}",
                 f"- Skipped: {counts.get('skipped', 0)}",
                 ""]
        entries = self.manifest.get("entries", [])
        if entries:
            lines += ["| id | status | http | file | bytes | sha256 |",
                      "| --- | --- | --- | --- | --- | --- |"]
            for entry in entries:
                digest = (entry.get("sha256") or "")[:16]
                lines.append(f"| {entry.get('id')} | {entry.get('status')} | "
                             f"{entry.get('http_status')} | {entry.get('file') or '-'} | "
                             f"{entry.get('bytes')} | {digest or '-'} |")
            lines.append("")
        blocked = [entry for entry in entries if entry.get("status") == "blocked"]
        if blocked:
            lines += ["### Blocked paths, and the authorised route", ""]
            for entry in blocked:
                # A scope refusal never reached the target, so it has no HTTP status.
                # Printing "(HTTP None)" beside it would suggest a request was made.
                status = entry.get("http_status")
                suffix = f" (HTTP {status})" if status is not None else \
                    " (no request was made)"
                lines.append(f"- **{entry.get('id')}** `{entry.get('source_url')}` — "
                             f"{entry.get('blocked_reason')}{suffix}")
                for route in (entry.get("access") or {}).get("routes", []):
                    lines.append(f"  - {route['route']}: {route['detail']}")
            lines.append("")
        if self.manifest.get("note"):
            lines += [self.manifest["note"], ""]
        return lines

    # -- output ----------------------------------------------------------
    FORMATS = ("markdown", "json")

    def write(self, path, fmt=None):
        """Write the report. An unrequested-but-unrecognised format is an error.

        Writing markdown into a file called `report.html` would be a report that
        renders as one long paragraph, so an unknown format stops the write
        rather than falling back to the default.
        """
        fmt = fmt or ("json" if str(path).endswith(".json") else "markdown")
        fmt = "markdown" if fmt == "md" else fmt
        if fmt not in self.FORMATS:
            raise ValueError(f"unknown report format {fmt!r}; expected one of "
                             f"{', '.join(self.FORMATS)}")
        directory = os.path.dirname(os.path.abspath(path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        if fmt == "json":
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(self.as_dict(), fh, indent=2, sort_keys=True)
        else:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self.markdown())
        return path


def build(records=None, bundle_dir=None, manifest_path=None, discovery=None, fuzz_runs=(),
          scope_file=None, scope_summary=None, title="Assessment report",
          generated_at=None, notes=(), engagement=None):
    """Assemble a report from whatever the run produced."""
    report = Report(title, scope_file=scope_file, scope_summary=scope_summary,
                    generated_at=generated_at)
    if bundle_dir:
        report.add_bundle(bundle_dir)
    if records:
        report.add_records(records)
    if manifest_path:
        report.add_manifest(manifest_path)
    if discovery is not None:
        report.add_discovery(discovery)
    for run in fuzz_runs:
        report.add_fuzz_run(run)
    for note in notes:
        report.note(note)
    if engagement:
        report.set_engagement(**engagement)
    return report
