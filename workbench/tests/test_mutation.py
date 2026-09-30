"""Tests for the mutation framework and the bounded fuzzing engine.

The fuzzer is the component that can do damage if it is wrong, so its limits are
tested as hard as its features: a run must not exceed its budget, must stop when
cancelled, must send nothing outside the scope, must refuse to turn a read into a
write unless a human asked for it explicitly, and must not send the same request
twice. Each of those is a test that asserts a *refusal* — the shape of test that
catches a safety property being quietly removed later.

The mutation catalogue is tested for what it deliberately does not contain:
credential headers are never mutated, no write verb is ever generated, and no
value is a filter-evasion payload. A catalogue that quietly gained one of those
would look like progress in a diff.
"""

from __future__ import annotations

import json

from workbench import evidence as ev
from workbench import fuzz
from workbench import history as hist
from workbench import http_client as hc
from workbench import mutate
from workbench import scope as sc
from workbench.tests import fixtures
from workbench.tests.harness import check, contains, equal, not_contains, raises

HOST = "127.0.0.1"
WRITE_VERBS = ("POST", "PUT", "PATCH", "DELETE")


def _guard(server=None, **overrides):
    data = fixtures.scope_data(**overrides)
    return sc.ScopeGuard(sc.Scope(data), resolve=lambda host: [HOST])


def _base(url="http://127.0.0.1/api/items/7?page=1&q=alpha", method="GET", **kw):
    """A stored record shaped like one the history holds."""
    headers = {"Accept": "application/json", "X-Trace": "fixture-trace"}
    headers.update(kw.pop("headers", {}))
    return {
        "id": "H0001",
        "url": url,
        "method": method,
        "request_headers": headers,
        "request_body": kw.pop("body", ""),
        "response": {
            "status": kw.pop("status", 200),
            "headers": {"Content-Type": "application/json"},
            "body_text": kw.pop("body_text", '{"id": 7, "name": "alpha"}'),
            "content_type": "application/json",
            "bytes": 28,
            "elapsed_ms": 4,
        },
    }


def _capture(server, path, method="GET", **kw):
    guard = _guard(server)
    return hc.request(guard, server.url(path), method, **kw).record()


# ------------------------------------------------------------------ catalogue
def test_the_catalogue_contains_no_no_ops_and_no_duplicates():
    mutations = mutate.catalogue(_base())
    check(mutations, "a parameterised request must produce mutations")
    seen = set()
    for mutation in mutations:
        check(not (mutation.before is not None and str(mutation.before) == str(mutation.after)),
              f"{mutation.kind}:{mutation.target} would send the original request again")
        key = (mutation.kind, mutation.target, mutation.mode,
               str(mutation.before), str(mutation.after))
        check(key not in seen, f"duplicate mutation {key}")
        seen.add(key)


def test_credential_headers_are_never_mutated():
    record = _base(headers={"Authorization": "Bearer fixture-token",
                            "Proxy-Authorization": "Basic fixture",
                            "Cookie": "sid=fixture-session"})
    for mutation in mutate.catalogue(record):
        if mutation.kind == "header":
            check(mutation.target.lower() not in
                  ("authorization", "proxy-authorization", "cookie"),
                  f"{mutation.target} must not be mutated")
        if mutation.kind == "cookie":
            # Cookie *values* can be varied because they are input the target
            # parses; the credential header itself is never rewritten.
            check(mutation.target not in ("Authorization", "Proxy-Authorization"),
                  "a credential header is not a cookie")


def test_no_write_verb_is_ever_generated_by_the_catalogue():
    record = _base(headers={"Cookie": "sid=fixture-session"})
    methods = [m for m in mutate.catalogue(record) if m.kind == "method"]
    check(methods, "a GET request must produce read-only method mutations")
    for mutation in methods:
        check(mutation.after not in WRITE_VERBS,
              f"the catalogue generated {mutation.after}, a state-changing verb")


def test_state_changing_verbs_are_reported_for_a_human_and_never_planned():
    record = _base()
    reported = mutate.state_changing_methods(record)
    equal(reported, ["POST", "PUT", "PATCH", "DELETE"])
    planned = {m.after for m in mutate.catalogue(record, ["method"])}
    equal(planned & set(WRITE_VERBS), set())


def test_the_catalogue_contains_no_filter_evasion_payloads():
    record = _base()
    blob = json.dumps(mutate.describe_all(record)).lower()
    for payload in ("<script", "union select", "../", "%00", "or 1=1", "onerror="):
        not_contains(blob, payload)


def test_every_mutation_kind_can_be_selected_individually():
    record = _base(body='{"name": "alpha", "count": 2}',
                   headers={"Content-Type": "application/json; charset=utf-8",
                            "Cookie": "sid=fixture-session"})
    for kind in mutate.KINDS:
        mutations = mutate.catalogue(record, [kind])
        for mutation in mutations:
            equal(mutation.kind, kind)
    equal(mutate.catalogue(record, ["nothing-called-this"]), [])


def test_a_mutation_describes_itself_completely():
    payload = mutate.catalogue(_base())[0].as_dict()
    for field in ("kind", "target", "before", "after", "mode", "note"):
        check(field in payload, f"a mutation must record {field}")
    check(payload["mode"] in ("replace", "append", "add"), payload["mode"])


def test_a_json_mutation_changes_one_field_and_leaves_the_rest_alone():
    record = _base(method="POST", body='{"name": "alpha", "count": 2}',
                   headers={"Content-Type": "application/json"})
    mutations = [m for m in mutate.catalogue(record, ["json"]) if m.target == "name"]
    check(mutations, "a string field must produce mutations")
    for mutation in mutations:
        url, method, headers, body, conflict = mutate.apply(record, mutation)
        equal(conflict, None)
        parsed = json.loads(body)
        check("count" in parsed, "the untouched field must survive")
        equal(parsed["count"], 2)


def test_a_null_replacement_is_applied_as_json_null_not_as_a_word():
    """A "type changed to null" mutation used to be applied as an empty string."""
    record = _base(method="POST", body='{"name": "alpha"}',
                   headers={"Content-Type": "application/json"})
    mutation = [m for m in mutate.catalogue(record, ["json"]) if m.after == "null"][0]
    contains(mutation.note, "null")
    _url, _method, _headers, body, conflict = mutate.apply(record, mutation)
    equal(conflict, None)
    equal(json.loads(body)["name"], None)


def test_every_json_mutation_applies_the_value_its_note_describes():
    record = _base(method="POST", body='{"name": "alpha", "count": 2, "active": false}',
                   headers={"Content-Type": "application/json"})
    for mutation in mutate.catalogue(record, ["json"]):
        _url, _method, _headers, body, conflict = mutate.apply(record, mutation)
        equal(conflict, None, f"{mutation.target} -> {mutation.after}")
        parsed = json.loads(body)
        if "changed to null" in mutation.note:
            equal(parsed["name"] if mutation.target == "name" else None, None)
        if "changed to boolean" in mutation.note:
            equal(json.loads(body)["name"] if mutation.target == "name" else True, True)


def test_form_mutations_target_the_body_and_are_labelled_as_form():
    record = _base(method="POST", body="user=alpha&role=viewer",
                   headers={"Content-Type": "application/x-www-form-urlencoded"})
    mutations = mutate.catalogue(record, ["form"])
    check(mutations, "a urlencoded body must produce form mutations")
    for mutation in mutations:
        equal(mutation.kind, "form")
        url, _method, _headers, body, conflict = mutate.apply(record, mutation)
        equal(conflict, None)
        equal(url, record["url"], "a form mutation must not touch the URL")
        check("user=" in body or "field=" in body, "the body carries the field")


def test_a_form_record_without_a_urlencoded_body_produces_no_form_mutations():
    equal(mutate.catalogue(_base(headers={"Content-Type": "application/json"}), ["form"]), [])


def test_the_source_record_is_never_modified_by_applying_a_mutation():
    record = _base(headers={"Cookie": "sid=fixture-session"})
    before = json.dumps(record, sort_keys=True)
    for mutation in mutate.catalogue(record):
        mutate.apply(record, mutation)
    equal(json.dumps(record, sort_keys=True), before)


# ---------------------------------------------------------------------- apply
def test_duplicate_parameter_mutations_append_rather_than_replace():
    record = _base()
    mutation = [m for m in mutate.catalogue(record, ["query"])
                if m.mode == "append" and m.target == "page"][0]
    url, _method, _headers, _body, conflict = mutate.apply(record, mutation)
    equal(conflict, None)
    equal(url.count("page="), 2)
    contains(url, "page=1")
    contains(url, "page=second-value")


def test_a_header_mutation_replaces_only_that_header():
    record = _base()
    mutation = [m for m in mutate.catalogue(record, ["header"]) if m.target == "Accept"][0]
    _url, _method, headers, _body, conflict = mutate.apply(record, mutation)
    equal(conflict, None)
    equal(headers["X-Trace"], "fixture-trace")
    check(headers["Accept"] != record["request_headers"]["Accept"], "Accept was replaced")


def test_applying_a_json_mutation_to_a_non_json_body_reports_a_conflict():
    record = _base(body="not json at all", headers={"Content-Type": "application/json"})
    mutation = mutate.Mutation("json", "name", "alpha", "", "empty value")
    _url, _method, _headers, _body, conflict = mutate.apply(record, mutation)
    contains(conflict, "not JSON")


def test_applying_a_mutation_for_a_parameter_that_is_not_there_reports_a_conflict():
    record = _base()
    mutation = mutate.Mutation("query", "missing", "1", "", "empty value")
    _url, _method, _headers, _body, conflict = mutate.apply(record, mutation)
    contains(conflict, "no parameter")


def test_a_content_type_mutation_declares_a_different_type():
    record = _base(method="POST", body="a=1", headers={"Content-Type": "application/json"})
    mutation = mutate.catalogue(record, ["content-type"])[0]
    _url, _method, headers, _body, conflict = mutate.apply(record, mutation)
    equal(conflict, None)
    equal(headers["Content-Type"], "application/x-www-form-urlencoded")


def test_a_method_mutation_only_moves_between_read_only_verbs():
    record = _base(method="GET")
    url, method, headers, body, conflict = mutate.apply(
        record, mutate.Mutation("method", "method", "GET", "HEAD", ""))
    equal(conflict, None)
    equal(method, "HEAD")
    equal(url, record["url"])


# ------------------------------------------------------------------- planning
def test_planning_respects_the_requested_kinds_and_the_limit():
    record = _base()
    only_query = fuzz.plan_mutations(record, ["query"])
    check(only_query, "a parameterised URL must plan query mutations")
    equal({m.kind for m in only_query}, {"query"})
    equal(len(fuzz.plan_mutations(record, ["query"], limit=2)), 2)
    equal(fuzz.plan_mutations(record, ["query"], limit=0), [])


# ------------------------------------------------------------------- the run
def test_a_run_sends_requests_only_through_the_guard_and_records_every_one():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        base = hc.request(guard, srv.url("/json?page=1"), "GET").record()
        h = hist.History()
        state = fuzz.run(guard, base, kinds=["query"], limit=4, budget=50, history=h)
        equal(state.summary()["requests_sent"], 4)
        equal(len(h.entries), 4)
        for result in state.results:
            check(result.decision.get("allowed"), f"{result.index} was not allowed by the guard")
            equal(result.record["response"]["status"], 200)
            check(len(result.decision.get("rule", "")) > 0, "a decision states its rule")


def test_a_run_never_exceeds_the_budget_it_was_given():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        base = hc.request(guard, srv.url("/json?page=1"), "GET").record()
        spent_before = guard.requests_made
        state = fuzz.run(guard, base, kinds=["query", "header"], budget=spent_before + 3)
        equal(state.summary()["requests_sent"], 3)
        equal(guard.requests_made, spent_before + 3)


def test_a_run_with_no_budget_left_sends_nothing():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        base = hc.request(guard, srv.url("/json"), "GET").record()
        state = fuzz.run(guard, base, kinds=["header"], budget=guard.requests_made)
        equal(state.summary()["requests_sent"], 0)
        equal(state.summary()["executed"], 0)
        equal(state.summary()["plan_truncated_by_budget"], len(fuzz.plan_mutations(base, ["header"])))


def test_a_run_reports_why_it_stopped_short_of_its_plan():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        base = hc.request(guard, srv.url("/json?page=1"), "GET").record()
        state = fuzz.run(guard, base, kinds=["query"], limit=1)
        equal(state.summary()["planned"], 1)
        check(state.summary()["plan_truncated_by_budget"] > 0, "the shortfall must be reported")
        equal(state.summary()["plan_source"], "catalogue")


def test_cancellation_stops_the_run_before_the_next_request():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        base = hc.request(guard, srv.url("/json?page=1"), "GET").record()
        spent_before = guard.requests_made
        state = fuzz.run(guard, base, kinds=["query"], cancel_check=lambda: True)
        equal(state.cancelled, True)
        equal(state.summary()["requests_sent"], 0)
        equal(guard.requests_made, spent_before)
        check(len(state.results) <= 1, "a cancelled run retains at most the partial work it did")


def test_a_cancelled_run_keeps_the_partial_results_it_already_has():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        base = hc.request(guard, srv.url("/json?page=1"), "GET").record()
        seen = {"count": 0}

        def cancel_after_two():
            seen["count"] += 1
            return seen["count"] > 2

        state = fuzz.run(guard, base, kinds=["query"], cancel_check=cancel_after_two)
        equal(state.cancelled, True)
        check(state.summary()["requests_sent"] >= 1, "the work already done is kept")


def test_requests_outside_the_scope_are_blocked_and_not_sent():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        outside = _base(url="http://outside-the-scope.invalid/api/items/7?page=1")
        spent_before = guard.requests_made
        state = fuzz.run(guard, outside, kinds=["query"])
        equal(state.summary()["requests_sent"], 0)
        equal(guard.requests_made, spent_before)
        check(state.results, "a blocked plan still produces results to account for")
        for result in state.results:
            equal(result.status, "blocked")
            equal(result.decision["allowed"], False)


def test_the_fixture_server_confirms_that_nothing_was_sent_when_scope_blocked_it():
    """An excluded path on an allowed host: refused, and provably not sent."""
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        excluded = _base(url=f"http://{HOST}:{srv.port}/private/items?page=1")
        state = fuzz.run(guard, excluded, kinds=["query"])
        equal(state.summary()["requests_sent"], 0)
        equal(srv.hits, [])
        check(state.results, "a refused plan is still accounted for")
        contains(state.results[0].decision["reason"], "exclusion")


def test_a_write_method_from_an_explicit_plan_is_refused_without_the_opt_in():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, methods=("GET", "HEAD", "OPTIONS", "POST"))
        base = hc.request(guard, srv.url("/json"), "GET").record()
        plan = [mutate.Mutation("method", "method", "GET", "POST",
                                "explicit write-method test")]
        hits_before = len(srv.hits)
        state = fuzz.run(guard, base, plan=plan)
        equal(state.summary()["plan_source"], "explicit")
        equal(state.summary()["requests_sent"], 0)
        equal(state.results[0].decision["rule"], "destructive")
        contains(state.results[0].error, "state-changing")
        equal(len(srv.hits), hits_before, "a refused mutation must not reach the target")


def test_a_write_method_is_sent_only_when_the_operator_opts_in():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, methods=("GET", "HEAD", "OPTIONS", "POST"))
        base = hc.request(guard, srv.url("/json"), "GET").record()
        plan = [mutate.Mutation("method", "method", "GET", "POST",
                                "explicit write-method test")]
        state = fuzz.run(guard, base, plan=plan, allow_state_changing=True)
        equal(state.summary()["requests_sent"], 1)
        equal([h["method"] for h in srv.hits], ["GET", "POST"])
        equal(state.results[0].record["method"], "POST")


def test_a_write_method_is_refused_even_with_the_opt_in_if_the_scope_forbids_it():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, methods=("GET", "HEAD", "OPTIONS"))
        base = hc.request(guard, srv.url("/json"), "GET").record()
        plan = [mutate.Mutation("method", "method", "GET", "POST", "explicit")]
        state = fuzz.run(guard, base, plan=plan, allow_state_changing=True)
        equal(state.summary()["requests_sent"], 0)
        equal(state.results[0].decision["allowed"], False)
        contains(state.results[0].decision["reason"].lower(), "method")
        equal([h["method"] for h in srv.hits], ["GET"])


def test_a_run_never_sends_the_same_request_twice():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        base = hc.request(guard, srv.url("/json?page=1"), "GET").record()
        duplicate = mutate.Mutation("query", "page", "1", "1", "a mutation that changes nothing")
        state = fuzz.run(guard, base, plan=[duplicate])
        equal(state.summary()["requests_sent"], 0)
        equal(state.summary()["duplicates_skipped"], 1)
        equal(state.results[0].duplicate_of, "earlier request")


def test_concurrency_comes_from_the_scope_file_and_is_never_exceeded():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, max_concurrency=2)
        base = hc.request(guard, srv.url("/json?page=1"), "GET").record()
        state = fuzz.run(guard, base, kinds=["query"], limit=4, budget=50)
        equal(state.summary()["requests_sent"], 4)
        equal(guard.scope.max_concurrency, 2)


def test_every_result_carries_the_mutation_that_produced_it():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        base = hc.request(guard, srv.url("/json?page=1"), "GET").record()
        state = fuzz.run(guard, base, kinds=["query"], limit=3)
        for result in state.results:
            payload = result.as_dict()
            for field in ("index", "mutation", "scope_decision", "status"):
                check(field in payload, f"an audit entry must record {field}")
            equal(payload["mutation"]["kind"], "query")
            check(payload["scope_decision"]["rule"], "a decision states its rule")


# ------------------------------------------------------------------ reporting
def test_the_summary_separates_what_ran_from_what_it_proves():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        base = hc.request(guard, srv.url("/json?page=1"), "GET").record()
        state = fuzz.run(guard, base, kinds=["query"], limit=3)
        summary = state.summary()
        equal(summary["budget"] >= summary["requests_sent"], True)
        contains(summary["note"], "not findings")
        contains(summary["note"], "human step")


def test_the_report_ends_by_stating_what_a_difference_is_not():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        base = hc.request(guard, srv.url("/json?page=1"), "GET").record()
        state = fuzz.run(guard, base, kinds=["query"], limit=3)
        report = fuzz.report_lines(state)
        contains(report, "A difference is not a finding")
        contains(report, "not clearance")


def test_interesting_results_exclude_errors_duplicates_and_non_differences():
    class Result:
        def __init__(self, difference, duplicate_of=None, error=None):
            self.difference = difference
            self.duplicate_of = duplicate_of
            self.error = error

    equal(fuzz.interesting(Result({"difference_count": 2})), True)
    equal(fuzz.interesting(Result(None)), False)
    equal(fuzz.interesting(Result({"difference_count": 0})), False)
    equal(fuzz.interesting(Result({"difference_count": 2}, duplicate_of="x")), False)
    equal(fuzz.interesting(Result({"difference_count": 2}, error="boom")), False)


def test_a_run_against_a_captured_status_change_is_reported_as_a_difference():
    """The one thing a fuzzing run is for: the target answered differently."""
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        base = hc.request(guard, srv.url("/json?page=1"), "GET").record()
        state = fuzz.run(guard, base, kinds=["query"], limit=4)
        check(state.summary()["differences_observed"] >= 1,
              "the fixture answers the mutated parameters differently")


def test_a_run_does_not_write_anything_into_an_evidence_bundle_by_itself():
    """A run produces observations. Turning them into records is a decision."""
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        base = hc.request(guard, srv.url("/json?page=1"), "GET").record()
        state = fuzz.run(guard, base, kinds=["query"], limit=2)
        bundle = ev.Bundle("fuzz-run")
        equal(bundle.records, [])
        check(len(state.results) == 2, "the run's own records exist independently of the bundle")
