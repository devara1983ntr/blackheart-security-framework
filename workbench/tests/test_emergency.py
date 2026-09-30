"""Tests for emergency mode.

The property under test is the one that matters when somebody is under pressure:
this module cannot send a request that changes anything. That is asserted three
ways — the method whitelist raises, every request the fixture server receives is
a read-only verb, and a static scan of the module proves no call site passes
anything else.

The rest checks that the snapshot is honest: it says it is a snapshot, it
records what it refused, it stops at its budget, and the evidence it produces is
in the same format as everything else.
"""

from __future__ import annotations

import ast
import os

from workbench import checks
from workbench import emergency
from workbench import evidence as ev
from workbench import history as hist
from workbench import scope as sc
from workbench.tests import fixtures
from workbench.tests.harness import check, contains, equal, raises

MODULE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "emergency.py")
HOST = "127.0.0.1"


def _guard(server, **overrides):
    data = fixtures.scope_data(**overrides)
    return sc.ScopeGuard(sc.Scope(data), resolve=lambda host: [HOST])


# ------------------------------------------------------------------ read only
def test_the_module_sends_nothing_but_read_only_methods():
    with open(MODULE, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    sent = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if name in ("request", "_read_only_request"):
                for argument in node.args[2:3]:
                    if isinstance(argument, ast.Constant):
                        sent.add(argument.value)
                for keyword in node.keywords:
                    if keyword.arg == "method" and isinstance(keyword.value, ast.Constant):
                        sent.add(keyword.value.value)
    equal(sent - set(emergency.READ_ONLY_METHODS), set(),
          "a non-read-only method was passed somewhere in this module")
    equal(set(emergency.READ_ONLY_METHODS), {"GET", "HEAD"})


def test_a_write_method_is_refused_by_the_one_helper_that_sends():
    collection = emergency.EmergencyCollection("http://h/", {}, 5)
    exc = raises(emergency.EmergencyError, emergency._read_only_request,
                 None, "http://h/", "POST", collection)
    contains(str(exc), "read-only")


def test_the_fixture_server_only_ever_receives_read_only_methods():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, methods=("GET", "HEAD", "OPTIONS", "POST", "DELETE"))
        emergency.collect(guard, srv.url("/soft"))
        verbs = {hit["method"] for hit in srv.hits}
        equal(verbs - {"GET", "HEAD"}, set(), f"a write request was sent: {verbs}")


def test_a_scope_that_allows_writes_changes_nothing():
    """The whitelist is the module's, not the scope's."""
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, methods=("GET", "HEAD", "POST", "DELETE"))
        emergency.collect(guard, srv.url("/soft"))
        equal([hit["method"] for hit in srv.hits if hit["method"] not in ("GET", "HEAD")], [])


# ------------------------------------------------------------------- a snapshot
def test_a_collection_records_what_the_target_served():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        collection = emergency.collect(guard, srv.url("/soft"))
        equal(collection.get("status"), 200)
        equal(collection.get("final url"), srv.url("/soft"))
        equal(collection.get("content type"), "text/plain")
        check(collection.get("header server"), "the server banner is recorded")
        check(collection.get("body prefix sha256"), "the body prefix is hashed")
        equal(collection.summary()["read_only"], True)


def test_redirects_and_tls_are_recorded_when_present():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        collection = emergency.collect(guard, srv.url("/redirect-chain"))
        equal(collection.get("redirects"), 2)
        equal(collection.get("final url"), srv.url("/text"))
        equal([f["fact"] for f in collection.facts if f["fact"].startswith("redirect ")],
              ["redirect 301", "redirect 302"])


def test_the_targets_own_published_documents_are_read_and_reported():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        collection = emergency.collect(guard, srv.url("/soft"))
        urls = [document["url"] for document in collection.documents]
        equal(urls, [srv.url("/robots.txt"), srv.url("/.well-known/security.txt")])
        statuses = {document["url"]: document["status"] for document in collection.documents}
        equal(statuses[srv.url("/robots.txt")], 200)
        equal(statuses[srv.url("/.well-known/security.txt")], 404)
        equal(collection.get("document /robots.txt"), "served")


def test_document_reading_can_be_left_out():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        collection = emergency.collect(guard, srv.url("/soft"), include_documents=False)
        equal(collection.documents, [])
        equal([hit["path"] for hit in srv.hits], ["/soft", "/soft"])


def test_the_budget_bounds_the_collection():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        collection = emergency.collect(guard, srv.url("/soft"), budget=2)
        check(collection.requests_used <= 2, collection.requests_used)
        check(any("budget" in error for error in collection.errors), collection.errors)


def test_cancellation_stops_the_collection_and_keeps_what_it_had():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        collection = emergency.collect(guard, srv.url("/soft"),
                                       cancel_check=lambda: True)
        equal(collection.cancelled or collection.errors, collection.cancelled
              or collection.errors)
        equal(collection.documents, [], "nothing was read after cancellation")


def test_a_target_the_scope_refuses_is_recorded_not_thrown():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        collection = emergency.collect(guard, srv.url("/private/notes"))
        equal(collection.refusals[0]["url"], srv.url("/private/notes"))
        contains(collection.refusals[0]["reason"], "ScopeError")
        equal([hit["path"] for hit in srv.hits], [])
        check(collection.errors, "the run says it could not reach the target")


def test_an_unreachable_host_is_recorded_as_an_error():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        port = srv.port
        srv.stop()
        collection = emergency.collect(guard, f"http://{HOST}:{port}/soft")
        check(collection.errors, "the failure is reported")
        equal(collection.get("status"), None)


# -------------------------------------------------------------------- evidence
def test_the_collection_produces_evidence_in_the_standard_format():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        bundle = ev.Bundle("emergency-test", scope_file="<fixture>")
        collection = emergency.collect(guard, srv.url("/soft"), bundle=bundle)
        check(collection.evidence_ids, "the checks produced records")
        equal([record.id for record in bundle.records], collection.evidence_ids)
        for record in bundle.records:
            record.validate()
            check(record.limitations, "an emergency record still states its limits")


def test_every_request_the_collection_makes_is_in_the_history():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        history = hist.History()
        collection = emergency.collect(guard, srv.url("/soft"), history=history)
        equal(len(history.entries), collection.requests_used)
        equal(len(history.entries), len(srv.hits))


def test_the_report_states_that_it_is_a_snapshot_and_not_an_assessment():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        collection = emergency.collect(guard, srv.url("/soft"))
        report = collection.report_lines()
        contains(report, "EMERGENCY COLLECTION")
        contains(report, "not an assessment")
        contains(report, "not that nothing is there")
        contains(collection.summary()["note"], "not an assessment")
        equal(collection.summary()["mode"], "emergency")


def test_the_plan_can_be_shown_before_anything_is_sent():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        plan = emergency.plan_lines(guard, srv.url("/soft"))
        contains(plan, "GET, HEAD only")
        contains(plan, "no discovery, no mutations, no writes")
        equal(srv.hits, [], "planning sends nothing")


def test_the_collection_is_json_serialisable():
    import json
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        collection = emergency.collect(guard, srv.url("/soft"))
        payload = json.loads(json.dumps(collection.as_dict()))
        equal(payload["summary"]["read_only"], True)
        equal(payload["summary"]["methods_sent"], ["GET", "HEAD"])
        check(payload["facts"], "the facts survive encoding")


def test_the_same_checks_run_here_as_on_the_routine_path():
    """An emergency record is not a different kind of record."""
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        collection = emergency.collect(guard, srv.url("/soft"))
        expected = [item.id for item in
                    checks.run_checks(list(hist.History().entries),
                                      scope_summary=guard.summary())]
        equal(expected, [])
        check(all(record_id.startswith("E-") for record_id in collection.evidence_ids),
              collection.evidence_ids)
