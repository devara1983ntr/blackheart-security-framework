"""Tests for the evidence format and the observable checks that produce it.

The negative tests are the point of this module. It is easy to write a record
format that accepts everything, and easy to write a check that finds something on
every response. Both make a tool that is pleasant to use and useless in a report:
the first attaches a confident label to an unverified observation, the second
teaches its operator to ignore it.

So: a record with an empty limitations field must fail, a record whose status is
`OBSERVED` must fail if its own prose claims a validated defect, a missing
baseline header must not be reported on a response that has one, and the checks
must be unable to reach `REPRODUCED` at all — because none of them observes the
same condition a second time.
"""

from __future__ import annotations

import json
import os

from workbench import checks
from workbench import evidence as ev
from workbench import history as hist
from workbench import http_client as hc
from workbench import scope as sc
from workbench.tests import fixtures
from workbench.tests.harness import check, contains, equal, not_contains, raises

HOST = "127.0.0.1"


def _guard(server, **overrides):
    data = fixtures.scope_data(**overrides)
    return sc.ScopeGuard(sc.Scope(data), resolve=lambda host: [HOST])


def _record(payload=None, status=200, headers=None, ctype="text/html"):
    """A stored record shaped like a captured exchange."""
    payload = payload or {}
    return {
        "id": payload.get("id", "H0001"),
        "url": payload.get("url", "http://127.0.0.1/item"),
        "method": payload.get("method", "GET"),
        "request_headers": payload.get("request_headers", {}),
        "request_body": payload.get("request_body", ""),
        "response": {
            "status": status,
            "headers": headers or {},
            "body_text": payload.get("body", "<html><body>ok</body></html>"),
            "content_type": ctype,
            "bytes": len(payload.get("body", "")),
            "elapsed_ms": 5,
        },
    }


def _capture(server, path, **kw):
    """Perform one request and return the *stored* record, which is what checks read."""
    guard = _guard(server)
    exchange = hc.request(guard, server.url(path), kw.pop("method", "GET"), **kw)
    return exchange.record()


def _evidence(cid="E-TEST", **overrides):
    """A complete, honest record. Each test breaks exactly one thing."""
    fields = dict(
        severity="low", confidence="high", status="OBSERVED", target="http://127.0.0.1/x",
        scope={"file": "<fixture>"}, expected="An expectation.",
        observed="A thing was seen.", impact="What it would mean if it mattered.",
        limitations="What this record cannot show.",
        remediation="What to do about it.",
        reproduction=["1. Send the request.", "2. Read the response."],
        provenance={"tool": "blackheart-workbench", "tool_version": "1.0.0",
                    "origin": "test", "generated_at": "2026-01-01T00:00:00Z"},
    )
    fields.update(overrides)
    return ev.Evidence(cid, fields.pop("title", "A title"), **fields)


# --------------------------------------------------------------- record format
def test_a_complete_observable_record_validates():
    record = _evidence()
    equal(record.validate(), True)
    equal(record.status, "OBSERVED")
    check(record.timestamp, "a record must carry the time it was written")


def test_empty_limitations_is_refused():
    """The rule that stops a record reading as complete coverage."""
    record = _evidence(limitations="   ")
    exc = raises(ev.EvidenceError, record.validate)
    contains(str(exc), "limitations")


def test_a_record_without_reproduction_steps_is_refused():
    record = _evidence(reproduction=[])
    contains(str(raises(ev.EvidenceError, record.validate)), "reproduction")


def test_reproduction_must_be_a_list_not_a_sentence():
    record = _evidence()
    record.reproduction = "1. do the thing"
    contains(str(raises(ev.EvidenceError, record.validate)), "list of steps")


def test_a_missing_required_field_is_refused():
    record = _evidence()
    record.impact = ""
    contains(str(raises(ev.EvidenceError, record.validate)), "impact")


def test_provenance_must_name_the_tool_that_produced_the_record():
    record = _evidence()
    record.provenance = {"origin": "test"}
    contains(str(raises(ev.EvidenceError, record.validate)), "provenance")


def test_unknown_status_and_severity_are_refused_at_construction():
    contains(str(raises(ev.EvidenceError, _evidence, status="CONFIRMED")), "unknown status")
    contains(str(raises(ev.EvidenceError, _evidence, severity="severe")), "unknown severity")


# -------------------------------------------------------- claims and promotion
def test_an_unreproduced_record_may_not_use_validated_language():
    for word in ("vulnerable", "confirmed", "exploitable"):
        record = _evidence(observed=f"The endpoint is {word}.")
        exc = raises(ev.EvidenceError, record.validate)
        contains(str(exc), "REPRODUCED")


def test_validated_language_is_permitted_once_the_status_says_reproduced():
    record = _evidence(status="REPRODUCED", severity="high",
                       observed="The condition was reproduced twice from a clean session.")
    equal(record.validate(), True)


def test_critical_severity_without_reproduction_is_refused():
    record = _evidence(severity="critical")
    contains(str(raises(ev.EvidenceError, record.validate)), "critical")


def test_observed_cannot_be_promoted_straight_to_reproduced_without_evidence():
    record = _evidence(status="POTENTIAL")
    record.status = "POTENTIAL"
    contains(str(raises(ev.EvidenceError, record.transition, "REPRODUCED")),
             "second observation")


def test_the_transition_ladder_refuses_a_step_it_does_not_define():
    record = _evidence(status="UNVERIFIED")
    contains(str(raises(ev.EvidenceError, record.transition, "OBSERVED")),
             "not a permitted transition")


def test_transitioning_to_reproduced_records_the_second_observation():
    record = _evidence(status="POTENTIAL")
    record.transition("REPRODUCED", reproduction="Second run, same result.")
    equal(record.status, "REPRODUCED")
    equal(len(record.reproduction), 3)


def test_a_reproduced_record_may_be_marked_unverified_but_not_silently_returned():
    record = _evidence(status="REPRODUCED")
    record.transition("UNVERIFIED", reproduction="Environment changed.")
    equal(record.status, "UNVERIFIED")
    contains(str(raises(ev.EvidenceError, record.transition, "OBSERVED")),
             "not a permitted transition")


# --------------------------------------------------------------------- hashing
def test_hashes_are_stable_across_repeated_computation():
    record = _evidence()
    first = dict(record.compute_hashes())
    second = dict(record.compute_hashes())
    equal(first, second)
    check(len(first["record_sha256"]) == 64, "sha256 is 64 hex characters")


def test_changing_the_observation_changes_the_record_hash():
    before = _evidence().compute_hashes()["record_sha256"]
    after = _evidence(observed="A different thing was seen.").compute_hashes()["record_sha256"]
    check(before != after, "a changed observation must change the hash")


def test_annotations_do_not_change_the_record_hash():
    """Notes are commentary; the observation is what is hashed."""
    record = _evidence()
    first = record.compute_hashes()["record_sha256"]
    record.notes = "Added while reading the report."
    equal(record.compute_hashes()["record_sha256"], first)


def test_file_hashing_matches_the_text_hash_for_the_same_bytes():
    directory = fixtures.tempfile_dir()
    path = os.path.join(directory, "sample.bin")
    with open(path, "wb") as fh:
        fh.write(b"blackheart")
    equal(ev.file_sha256(path), ev.sha256_text("blackheart"))


# ------------------------------------------------------------------ the bundle
def test_bundle_writes_records_and_an_aggregate_manifest():
    bundle = ev.Bundle("test-bundle", scope_file="<fixture>")
    bundle.add(_evidence("E-ONE"))
    bundle.add(_evidence("E-TWO", severity="medium", status="POTENTIAL"))
    directory = fixtures.tempfile_dir()
    manifest = bundle.write(directory)
    equal(manifest["count"], 2)
    equal(manifest["by_status"], {"OBSERVED": 1, "POTENTIAL": 1})
    equal(manifest["by_severity"], {"low": 1, "medium": 1})
    check(os.path.isfile(os.path.join(directory, "E-ONE.json")), "record file written")
    equal(ev.Bundle.verify(directory), [])


def test_verify_reports_a_record_that_was_edited_after_writing():
    """The whole point of the hash: a record that changed is a record that failed."""
    bundle = ev.Bundle("test-bundle")
    bundle.add(_evidence("E-TAMPER"))
    directory = fixtures.tempfile_dir()
    bundle.write(directory)
    path = os.path.join(directory, "E-TAMPER.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    data["observed"] = "A much more alarming observation."
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    problems = ev.Bundle.verify(directory)
    equal(len(problems), 1)
    contains(problems[0], "E-TAMPER")
    contains(problems[0], "hash mismatch")


def test_verify_reports_a_deleted_record_file():
    bundle = ev.Bundle("test-bundle")
    bundle.add(_evidence("E-GONE"))
    directory = fixtures.tempfile_dir()
    bundle.write(directory)
    os.remove(os.path.join(directory, "E-GONE.json"))
    contains(ev.Bundle.verify(directory)[0], "record file missing")


def test_verify_reports_a_bundle_it_cannot_find():
    contains(ev.Bundle.verify(fixtures.tempfile_dir())[0], "manifest.json not found")


def test_adding_an_invalid_record_to_a_bundle_fails_rather_than_writing_it():
    bundle = ev.Bundle("test-bundle")
    contains(str(raises(ev.EvidenceError, bundle.add, _evidence(limitations=""))),
             "limitations")
    equal(bundle.records, [])


# ------------------------------------------------------------------- redaction
def test_redaction_covers_headers_and_secret_values_in_prose():
    record = _evidence(
        observed="The token fixture-secret-value appeared in the body.",
        request={"headers": {"Authorization": "Bearer fixture-secret-value",
                             "Accept": "*/*"}},
        response={"headers": {"Set-Cookie": "session=fixture-secret-value"},
                  "body_text": "fixture-secret-value"})
    record.redact(["fixture-secret-value"])
    blob = json.dumps(record.as_dict())
    not_contains(blob, "fixture-secret-value")
    contains(blob, hc.REDACTED)
    equal(record.request["headers"]["Authorization"], hc.REDACTED)


# ------------------------------------------------------------- the HTTP checks
def test_absence_of_baseline_headers_is_reported_with_its_limitations():
    with fixtures.FixtureServer() as srv:
        record = _capture(srv, "/soft")
        found = [r for r in checks.security_headers(record) if r.id.endswith("ABSENT")]
        equal(len(found), 1)
        contains(found[0].title, "strict-transport-security")
        contains(found[0].observed, "x-frame-options")
        contains(found[0].limitations, "not a defect")
        equal(found[0].status, "OBSERVED")


def test_a_hardened_response_produces_no_header_or_cookie_record():
    """The negative case that keeps the checks honest."""
    with fixtures.FixtureServer() as srv:
        record = _capture(srv, "/hardened")
        # The fixture server does announce itself in a Server header, so the
        # disclosure record is expected and correct. What must be absent is the
        # record about missing controls.
        equal([r.id for r in checks.security_headers(record) if r.id.endswith("ABSENT")], [])
        cookie = _capture(srv, "/setcookie-hardened")
        equal(checks.cookie_flags(cookie), [])


def test_a_soft_cookie_is_reported_with_the_attributes_that_are_missing():
    with fixtures.FixtureServer() as srv:
        record = _capture(srv, "/setcookie-soft")
        found = checks.cookie_flags(record)
        check(found, "a cookie without flags must produce a record")
        contains(found[0].observed, "httponly")
        contains(found[0].limitations, "does not know which this is")


def test_cookie_values_are_never_copied_into_the_record():
    with fixtures.FixtureServer() as srv:
        record = _capture(srv, "/setcookie-soft")
        set_cookie = [v for k, v in (record["response"]["headers"] or {}).items()
                      if k.lower() == "set-cookie"][0]
        check(hc.is_redacted(set_cookie), "the stored cookie value must be redacted")
        for item in checks.cookie_flags(record):
            blob = json.dumps(item.as_dict())
            not_contains(blob, "fixture-not-a-real-value")
            contains(blob, "Path=/")


def test_cors_wildcard_is_observed_while_a_reflected_origin_stays_potential():
    with fixtures.FixtureServer() as srv:
        wildcard = checks.cors_configuration(_capture(srv, "/cors-wildcard"))
        equal([r.status for r in wildcard], ["OBSERVED"])
        contains(wildcard[0].observed, "*")
        reflected = checks.cors_configuration(
            _capture(srv, "/cors-reflected", headers={"Origin": "https://fixture.invalid"}))
        equal([r.status for r in reflected], ["POTENTIAL"])
        contains(reflected[0].limitations, "required and is a deliberate authorization")


def test_a_response_without_cors_headers_produces_no_cors_record():
    with fixtures.FixtureServer() as srv:
        equal(checks.cors_configuration(_capture(srv, "/text")), [])


def test_reflection_is_only_considered_for_html_responses():
    with fixtures.FixtureServer() as srv:
        html = _capture(srv, "/reflect?q=fixturevalue")
        check(checks.reflected_input(html), "HTML reflection should be reported")
        equal(checks.reflected_input(_capture(srv, "/json?q=fixturevalue")), [])


def test_a_reflection_record_never_claims_execution():
    with fixtures.FixtureServer() as srv:
        record = checks.reflected_input(_capture(srv, "/reflect?q=fixturevalue"))[0]
        contains(record.limitations, "not execution")
        equal(record.status, "POTENTIAL")
        equal(record.validate(), True)


def test_a_short_query_value_is_not_treated_as_a_reflection():
    with fixtures.FixtureServer() as srv:
        equal(checks.reflected_input(_capture(srv, "/reflect?q=ab")), [])


def test_open_redirect_indicator_requires_the_value_to_reach_the_location():
    with fixtures.FixtureServer() as srv:
        hit = checks.open_redirect_indicator(
            _capture(srv, "/open-redirect?next=https://fixture.invalid/x"))
        equal(len(hit), 1)
        equal(hit[0].status, "POTENTIAL")
        contains(hit[0].limitations, "deliberate action")
        equal(checks.open_redirect_indicator(_capture(srv, "/redirect-offhost")), [])


def test_error_disclosure_is_reported_only_for_error_responses():
    with fixtures.FixtureServer() as srv:
        record = _capture(srv, "/stack-trace")
        found = checks.error_disclosure(record)
        check(found, "a traceback in a 500 response must be reported")
        contains(found[0].observed, "Python traceback")
        clean = _capture(srv, "/text")
        equal(checks.error_disclosure(clean), [])


def test_a_successful_response_with_a_500_in_its_body_is_not_disclosure():
    record = _record(status=200, payload={"body": "Traceback (most recent call last):"})
    equal(checks.error_disclosure(record), [])


def test_content_type_mismatch_is_reported_but_a_matching_type_is_not():
    with fixtures.FixtureServer() as srv:
        mismatch = checks.content_type_handling(_capture(srv, "/bad-type"))
        equal(len(mismatch), 1)
        contains(mismatch[0].id, "MISMATCH")
        equal(checks.content_type_handling(_capture(srv, "/hardened")), [])


def test_method_handling_reads_the_allow_header_and_ignores_read_only_routes():
    record = _record(status=204, headers={"Allow": "GET, POST, PUT"})
    found = checks.method_handling(record)
    equal(len(found), 1)
    contains(found[0].observed, "POST")
    contains(found[0].limitations, "separately")
    equal(checks.method_handling(_record(status=200, headers={"Allow": "GET"})), [])


def test_identifiers_are_flagged_as_informational_never_as_a_finding():
    record = checks.predictable_identifier(_record(payload={"url": "http://127.0.0.1/api/items/42"}))
    equal(len(record), 1)
    equal(record[0].status, "OBSERVED")
    equal(record[0].severity, "informational")
    contains(record[0].limitations, "not a defect")


def test_an_upload_acceptance_is_recorded_without_claiming_anything_was_stored():
    captured = _record(payload={"request_headers":
                                {"Content-Type": "multipart/form-data; boundary=x"}},
                       status=201)
    found = checks.upload_validation_observation(captured)
    equal(len(found), 1)
    contains(found[0].limitations, "does not")
    equal(checks.upload_validation_observation(_record(payload={"request_headers": {}})), [])


# ------------------------------------------------------- checks that need groups
def test_rate_limit_check_produces_nothing_from_a_single_call():
    equal(checks.rate_limit_behavior([_record()]), [])
    equal(checks.rate_limit_behavior([_record(), _record(payload={"url": "http://127.0.0.1/other"})]), [])


def test_rate_limit_check_groups_by_endpoint_and_reports_an_absence_as_potential():
    records = [_record() for _ in range(4)]
    found = checks.rate_limit_behavior(records)
    equal(len(found), 1)
    equal(found[0].status, "POTENTIAL")
    contains(found[0].limitations, "coverage gap")
    equal(found[0].severity, "informational")


def test_rate_limit_check_reports_a_limiter_when_one_is_present():
    records = [_record() for _ in range(3)] + [_record(status=429) for _ in range(2)]
    found = checks.rate_limit_behavior(records)
    equal(len(found), 1)
    contains(found[0].title, "Rate limiting observed")
    equal(found[0].status, "OBSERVED")
    contains(found[0].remediation, "No action")


def test_schema_consistency_only_compares_calls_to_the_same_endpoint():
    first = _record(payload={"body": '{"a": 1}'}, ctype="application/json")
    other_url = _record(payload={"body": '{"a": 1, "b": 2}', "url": "http://127.0.0.1/elsewhere"},
                        ctype="application/json")
    equal(checks.schema_consistency([first, other_url]), [])
    same_url = _record(payload={"body": '{"a": 1, "b": 2}'}, ctype="application/json")
    found = checks.schema_consistency([first, same_url])
    equal(len(found), 1)
    contains(found[0].observed, "+1 keys")


def test_authorization_comparison_produces_nothing_without_two_identities():
    a = _record(payload={"body": '{"owner": "a"}'}, ctype="application/json")
    b = _record(payload={"body": '{"owner": "b"}'}, ctype="application/json")
    equal(checks.authorization_boundary(a, b, "", ""), [])


def test_authorization_comparison_states_what_it_cannot_decide():
    a = _record(payload={"body": '{"owner": "a"}'}, ctype="application/json")
    b = _record(payload={"body": '{"owner": "b"}'}, ctype="application/json")
    found = checks.authorization_boundary(a, b, "identity-A", "identity-B")
    equal(len(found), 1)
    equal(found[0].status, "POTENTIAL")
    equal(found[0].confidence, "low")
    contains(found[0].limitations, "human must read")


def test_authorization_comparison_is_silent_when_one_identity_was_refused():
    a = _record(payload={"body": '{"owner": "a"}'}, ctype="application/json")
    refused = _record(payload={"body": "denied"}, status=403, ctype="application/json")
    equal(checks.authorization_boundary(a, refused, "identity-A", "identity-B"), [])


# ---------------------------------------------------------------- the whole set
def test_no_check_can_produce_a_reproduced_record():
    """None of these checks reproduces a condition a second time, so none may say so."""
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        h = hist.History()
        for path in ("/soft", "/setcookie-soft", "/cors-wildcard", "/cacheable", "/hardened",
                     "/setcookie-hardened", "/api/items/7", "/json", "/missing", "/bad-type",
                     "/reflect?q=fixturevalue", "/open-redirect?next=https://fixture.invalid/x",
                     "/redirect-offhost", "/stack-trace", "/openapi.json"):
            h.add(hc.request(guard, srv.url(path), "GET"), tag="check")
        for _ in range(4):
            h.add(hc.request(guard, srv.url("/json"), "GET"), tag="burst")
        produced = checks.run_checks(h.entries, scope_summary=guard.summary())
        check(len(produced) >= 8, f"expected the fixture set to produce records, got {len(produced)}")
        for record in produced:
            record.validate()
            check(record.status in ("OBSERVED", "POTENTIAL", "UNVERIFIED"),
                  f"{record.id} has status {record.status}, which a check cannot establish")
            check(record.limitations.strip(), f"{record.id} has no limitations")
            check(record.reproduction, f"{record.id} has no reproduction steps")
        equal(sorted({r.status for r in produced} & {"REPRODUCED"}), [])


def test_running_a_subset_of_checks_runs_only_that_subset():
    with fixtures.FixtureServer() as srv:
        record = _capture(srv, "/soft")
        produced = checks.run_checks([record], only=["headers"])
        equal(sorted(r.id for r in produced), ["E-HEADERS-ABSENT", "E-HEADERS-BANNER"])
        equal(checks.run_checks([record], only=[]), [])


def test_consolidation_merges_repeated_observations_and_lists_where_they_were_seen():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        h = hist.History()
        for path in ("/soft", "/missing", "/text"):
            h.add(hc.request(guard, srv.url(path), "GET"), tag="check")
        produced = checks.run_checks(h.entries, only=["headers"],
                                     scope_summary=guard.summary())
        absent = [r for r in produced if r.id.startswith("E-HEADERS-ABSENT")]
        equal(len(absent), 1)
        contains(absent[0].observed, "Also observed on 2 other response(s)")
        contains(absent[0].observed, "/missing")


def test_consolidation_never_merges_potential_records():
    """Each potential record points at one response a human has to go and look at."""
    records = [_record(payload={"url": f"http://127.0.0.1/redirect?next=https://x{i}.invalid/f"})
               for i in range(3)]
    for index, record in enumerate(records):
        record["redirect_chain"] = [{"status": 302, "from": record["url"],
                                     "location": f"https://x{index}.invalid/f"}]
    produced = checks.run_checks(records, only=["open-redirect"])
    equal(len(produced), 3)
    equal(sorted({r.status for r in produced}), ["POTENTIAL"])


def test_every_produced_record_survives_a_full_round_trip_through_a_bundle():
    with fixtures.FixtureServer() as srv:
        record = _capture(srv, "/soft")
        bundle = ev.Bundle("round-trip", scope_file="<fixture>")
        checks.run_checks([record], bundle=bundle, scope_summary={"file": "<fixture>"})
        directory = fixtures.tempfile_dir()
        manifest = bundle.write(directory)
        equal(manifest["count"], len(bundle.records))
        equal(ev.Bundle.verify(directory), [])
        for item in bundle.records:
            check(os.path.isfile(os.path.join(directory, f"{item.id}.json")),
                  f"{item.id} was written")
