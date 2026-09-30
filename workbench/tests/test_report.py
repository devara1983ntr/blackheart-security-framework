"""Tests for the report assembler.

The report is the one artefact a reader may see without ever running the tool, so
the properties that matter are the ones about honesty rather than formatting:

* every number comes from the records, and a record's status is never rounded up
  on the way into a summary;
* a POTENTIAL or UNVERIFIED record is described as unvalidated in the summary and
  printed in full in the detail, with its own limitations;
* a bundle or manifest that no longer matches its hashes is reported as a problem
  in the report rather than passing silently;
* the zero case does not read as a finding, and the empty case does not read as a
  statement about the target at all.
"""

from __future__ import annotations

import json
import os

from workbench import evidence as ev
from workbench import fetch
from workbench import report as reportmod
from workbench import scope as sc
from workbench.tests import fixtures
from workbench.tests.harness import check, contains, equal, not_contains, raises

HOST = "127.0.0.1"


def _scope():
    data = fixtures.scope_data()
    return sc.ScopeGuard(sc.Scope(data), resolve=lambda host: [HOST])


def _record(entry_id, status="OBSERVED", severity="informational", **overrides):
    title = overrides.pop("title", f"Observation {entry_id}")
    fields = dict(
        severity=severity,
        confidence="high",
        status=status,
        target="http://127.0.0.1/soft",
        scope={"allowed_hosts": ["127.0.0.1"]},
        expected="the response is served without the header",
        observed="the response was served without the header",
        impact="an operator reading this must decide whether it matters",
        limitations="one response, at one time, from one address",
        remediation="assess against the deployment's own baseline",
        provenance=ev.provenance_for({}),
        reproduction=["request the URL", "request it again and compare"],
    )
    fields.update(overrides)
    return ev.Evidence(entry_id, title, **fields)


def _write_bundle(directory, records):
    bundle = ev.Bundle("tests", scope_file="<fixture>")
    for record in records:
        bundle.add(record)
    bundle.write(directory)
    return os.path.join(directory, "manifest.json")


# ------------------------------------------------------------------- counting
def test_every_count_is_derived_from_the_records():
    report = reportmod.build(records=[
        _record("E-1", "OBSERVED", "low"),
        _record("E-2", "POTENTIAL", "medium"),
        _record("E-3", "REPRODUCED", "high"),
        _record("E-4", "UNVERIFIED", "informational"),
    ])
    counts = report.counts()
    equal(counts["records"], 4)
    equal(counts["by_status"], {"OBSERVED": 1, "POTENTIAL": 1, "REPRODUCED": 1,
                                "UNVERIFIED": 1})
    equal(counts["by_severity"], {"low": 1, "medium": 1, "high": 1, "informational": 1})
    equal(counts["not_established"], 2)
    equal(counts["reproduced"], 1)


def test_the_summary_separates_validated_records_from_unvalidated_ones():
    report = reportmod.build(records=[_record("E-1", "OBSERVED"),
                                      _record("E-2", "POTENTIAL"),
                                      _record("E-3", "REPRODUCED")])
    text = report.markdown()
    contains(text, "- Evidence records: 3")
    contains(text, "- Validated (REPRODUCED): 1")
    contains(text, "- Not validated (POTENTIAL or UNVERIFIED): 1")


def test_a_potential_record_is_printed_in_full_and_never_promoted():
    record = _record("E-1", "POTENTIAL", "high",
                     title="Reflected query value in an HTML response",
                     limitations="the value was reflected; whether it executes was not tested")
    text = reportmod.build(records=[record]).markdown()
    contains(text, "### E-1 — Reflected query value in an HTML response")
    contains(text, "- **Status**: POTENTIAL")
    contains(text, "| E-1 | POTENTIAL | high |")
    contains(text, "the value was reflected; whether it executes was not tested")
    contains(text, "1 of 1 record(s) are not validated findings")
    not_contains(text, "confirmed", "an unvalidated record must not be summarised as confirmed")


def test_a_record_with_no_unvalidated_entries_does_not_claim_there_were_none():
    report = reportmod.build(records=[_record("E-1", "REPRODUCED")])
    text = report.markdown()
    contains(text, "0 of 1 record(s) are not validated findings")
    contains(text, "1 record(s) are OBSERVED, INFERRED or REPRODUCED")
    not_contains(text, "No record here is a validated finding",
                 "a REPRODUCED record must not be dismissed by the boilerplate")


def test_an_empty_report_says_it_establishes_nothing():
    text = reportmod.build().markdown()
    contains(text, "This report carries no evidence records at all")
    not_contains(text, "0 of 0 record(s)")
    contains(text, "- No bundle or manifest was supplied, so nothing was re-hashed.")


def test_a_reproduced_record_is_reported_with_its_reproduction_steps():
    text = reportmod.build(records=[_record("E-1", "REPRODUCED")]).markdown()
    contains(text, "**Reproduction**:")
    contains(text, "request it again and compare")


# ------------------------------------------------------------------ ownership
def test_the_report_states_the_standing_limits_including_the_bypass_sentence():
    text = reportmod.build().markdown()
    for statement in reportmod.STANDING_STATEMENTS:
        contains(text, statement)
    contains(text, "This framework does not bypass authentication, authorization, "
                   "paywalls, DRM, licensing controls, or other access restrictions.")


def test_the_report_names_the_scope_file_it_was_run_under():
    scope_path = os.path.join(fixtures.tempfile_dir(), "scope.json")
    text = reportmod.build(records=[_record("E-1")], scope_file=scope_path,
                           scope_summary={"allowed_hosts": ["127.0.0.1"],
                                          "max_requests": 50}).markdown()
    contains(text, f"- Scope file: `{scope_path}`")
    contains(text, "- allowed_hosts: ['127.0.0.1']")
    contains(text, "- max_requests: 50")


# --------------------------------------------------------------- verification
def test_a_bundle_that_matches_its_manifest_verifies_clean():
    directory = fixtures.tempfile_dir()
    _write_bundle(directory, [_record("E-1"), _record("E-2", "POTENTIAL")])
    report = reportmod.build(bundle_dir=directory)
    equal(report.counts()["records"], 2)
    equal(report.verification["evidence_bundle"]["problems"], [])
    equal(report.verification["evidence_bundle"]["count"], 2)
    contains(report.markdown(), "- evidence_bundle: clean")


def test_a_record_edited_after_writing_is_reported_as_a_problem():
    directory = fixtures.tempfile_dir()
    _write_bundle(directory, [_record("E-1")])
    path = os.path.join(directory, "E-1.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    data["observed"] = "something a person typed in afterwards"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, sort_keys=True)
    report = reportmod.build(bundle_dir=directory)
    problems = report.verification["evidence_bundle"]["problems"]
    equal(len(problems), 1)
    contains(problems[0], "hash mismatch")
    contains(report.markdown(), "1 problem(s)")


def test_a_bundle_directory_without_a_manifest_is_reported_not_assumed_empty():
    directory = fixtures.tempfile_dir()
    with open(os.path.join(directory, "E-1.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(_record("E-1").as_dict()))
    report = reportmod.build(bundle_dir=directory)
    problems = report.verification["evidence_bundle"]["problems"]
    equal(len(problems), 1)
    contains(problems[0], "manifest.json not found")
    equal(report.counts()["records"], 0)
    check(not report.records, "a record in a bundle with no manifest is not adopted")


# ---------------------------------------------------------------- acquisitions
def test_an_acquisition_manifest_contributes_its_counts_and_blocked_routes():
    with fixtures.FixtureServer() as srv:
        guard = _scope()
        directory = fixtures.tempfile_dir()
        manifest = fetch.Manifest(directory, scope_file="<fixture>",
                                  scope=guard.summary())
        fetch.acquire(guard, srv.url("/file.pdf"), manifest, expect="document")
        fetch.acquire(guard, srv.url("/forbidden"), manifest)
        fetch.acquire(guard, srv.url("/unavailable-legal"), manifest)
        manifest_path = manifest.write()

        report = reportmod.build(manifest_path=manifest_path)
        counts = report.acquisition_counts()
        equal(counts["success"], 1)
        equal(counts["blocked"], 2)
        equal(report.verification["downloads_manifest"]["problems"], [])

        text = report.markdown()
        contains(text, "## Acquisitions")
        contains(text, "- Obtained: 1")
        contains(text, "- Blocked: 2")
        contains(text, "### Blocked paths, and the authorised route")
        contains(text, "(HTTP 403)")
        contains(text, "(HTTP 451)")
        contains(text, "Do not retry with altered headers")
        contains(text, "It does not use mirrors, caches, proxies, altered identities "
                       "or expired links to obtain a copy")


def test_a_download_that_disappeared_is_reported_as_a_verification_problem():
    with fixtures.FixtureServer() as srv:
        guard = _scope()
        directory = fixtures.tempfile_dir()
        manifest = fetch.Manifest(directory, scope_file="<fixture>",
                                  scope=guard.summary())
        fetch.acquire(guard, srv.url("/file.pdf"), manifest, expect="document")
        manifest_path = manifest.write()
        os.remove(os.path.join(directory, "file.pdf"))

        report = reportmod.build(manifest_path=manifest_path)
        problems = report.verification["downloads_manifest"]["problems"]
        equal(len(problems), 1)
        contains(problems[0], "file missing")
        contains(report.markdown(), "file missing")


def test_a_scope_refusal_is_not_reported_as_an_http_response():
    with fixtures.FixtureServer() as srv:
        guard = sc.ScopeGuard(sc.Scope(fixtures.scope_data(
            allowed_hosts=["elsewhere.invalid"])), resolve=lambda host: [HOST])
        directory = fixtures.tempfile_dir()
        manifest = fetch.Manifest(directory, scope_file="<fixture>", scope=guard.summary())
        fetch.acquire(guard, srv.url("/file.pdf"), manifest)
        manifest_path = manifest.write()
        text = reportmod.build(manifest_path=manifest_path).markdown()
        contains(text, "no request was made")
        not_contains(text, "HTTP None")


# --------------------------------------------------------------------- output
def test_the_json_output_carries_the_same_numbers_as_the_markdown():
    report = reportmod.build(records=[_record("E-1", "POTENTIAL"), _record("E-2")])
    body = report.as_dict()
    equal(body["counts"], report.counts())
    equal(len(body["records"]), 2)
    text = report.markdown()
    for value in (body["counts"]["records"], body["counts"]["not_established"],
                  body["counts"]["reproduced"]):
        contains(text, str(value))


def test_json_output_round_trips_and_markdown_writes_to_disk():
    directory = fixtures.tempfile_dir()
    report = reportmod.build(records=[_record("E-1")])
    json_path = report.write(os.path.join(directory, "report.json"))
    with open(json_path, encoding="utf-8") as fh:
        body = json.load(fh)
    equal(body["counts"]["records"], 1)
    equal(body["tool"], "blackheart-workbench")
    contains("\n".join(body["statements"]), "does not bypass authentication")
    markdown_path = report.write(os.path.join(directory, "report.md"))
    with open(markdown_path, encoding="utf-8") as fh:
        contains(fh.read(), "## What this report does not establish")


def test_an_unknown_output_format_is_refused_rather_than_written_as_markdown():
    report = reportmod.build(records=[_record("E-1")])
    path = os.path.join(fixtures.tempfile_dir(), "report.html")
    raises(ValueError, report.write, path, "html")
    check(not os.path.exists(path), "a refused write must not leave a file behind")


def test_discovery_and_fuzzing_sections_appear_only_when_they_ran():
    text = reportmod.build(records=[_record("E-1")]).markdown()
    not_contains(text, "## Discovery coverage")
    not_contains(text, "## Fuzzing coverage")
