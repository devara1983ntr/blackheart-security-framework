"""Tests for history, comparison and parameter analysis.

These run against captured exchanges from the fixture server, so the records
being compared are shaped exactly like the records a real run produces —
including the truncated bodies, the missing Content-Type and the 4xx responses
that the comparison code has to handle without special-casing them.
"""

from __future__ import annotations

import json
import os

from workbench import diff
from workbench import history as hist
from workbench import http_client as hc
from workbench import params
from workbench import scope as sc
from workbench.tests import fixtures
from workbench.tests.harness import contains, equal, not_contains, raises

HOST = "127.0.0.1"


def _guard(server, **overrides):
    data = fixtures.scope_data(**overrides)
    return sc.ScopeGuard(sc.Scope(data), resolve=lambda host: [HOST])


def _record(payload, status=200, headers=None, ctype="application/json"):
    """A stored record shaped like a captured one, for pure comparison tests."""
    return {
        "id": payload.get("id", "H0001"),
        "url": payload.get("url", "http://127.0.0.1/item"),
        "method": payload.get("method", "GET"),
        "request_headers": payload.get("request_headers", {}),
        "request_body": payload.get("request_body", ""),
        "response": {
            "status": status,
            "headers": headers or {},
            "body_text": payload.get("body", ""),
            "content_type": ctype,
            "bytes": len(payload.get("body", "")),
            "elapsed_ms": payload.get("ms", 10),
        },
    }


# ------------------------------------------------------------------- history
def test_history_adds_and_assigns_sequential_ids():
    with fixtures.FixtureServer() as srv:
        h = hist.History()
        guard = _guard(srv)
        for path in ("/text", "/json"):
            exchange = hc.request(guard, srv.url(path), "GET")
            h.add(exchange, tag="probe")
        equal([e["id"] for e in h.entries], ["H0001", "H0002"])
        equal(h.entries[0]["tag"], "probe")


def test_history_persists_redacted_records_only():
    with fixtures.FixtureServer() as srv:
        h = hist.History(path=os.path.join(fixtures.tempfile_dir(), "history.jsonl"))
        exchange = hc.request(_guard(srv), srv.url("/text"), "GET",
                              headers={"Authorization": "Bearer fixture-value"})
        h.add(exchange)
        with open(h.path, encoding="utf-8") as fh:
            written = fh.read()
        not_contains(written, "fixture-value")
        contains(written, hc.REDACTED)
        record = json.loads(written.strip())
        equal(record["request_headers"]["Authorization"], hc.REDACTED)


def test_history_loads_what_it_wrote():
    with fixtures.FixtureServer() as srv:
        path = os.path.join(fixtures.tempfile_dir(), "history.jsonl")
        h = hist.History(path=path)
        guard = _guard(srv)
        for path_name in ("/text", "/json", "/missing"):
            h.add(hc.request(guard, srv.url(path_name), "GET"))
        again = hist.History.load(path)
        equal(len(again.entries), 3)
        equal(again.get("H0002")["path"], "/json")
        new_id = again.add(hc.request(guard, srv.url("/text"), "GET"))
        equal(new_id, "H0004", "reloaded history must continue the numbering")


def test_history_load_reports_unparseable_lines():
    path = os.path.join(fixtures.tempfile_dir(), "history.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write('{"id": "H0001", "url": "http://x/", "method": "GET"}\n')
        fh.write("not json at all\n")
    h = hist.History.load(path)
    equal(len(h.entries), 1)
    equal(h.skipped_lines, [2])


def test_history_summary_counts_methods_and_status_classes():
    with fixtures.FixtureServer() as srv:
        h = hist.History()
        guard = _guard(srv)
        h.add(hc.request(guard, srv.url("/text"), "GET"))
        h.add(hc.request(guard, srv.url("/missing"), "GET"))
        summary = h.summary()
        equal(summary["entries"], 2)
        equal(summary["by_status"]["2xx"], 1)
        equal(summary["by_status"]["4xx"], 1)


def test_replay_creates_a_new_record_and_keeps_the_original():
    with fixtures.FixtureServer() as srv:
        h = hist.History()
        guard = _guard(srv)
        original = hc.request(guard, srv.url("/json"), "GET")
        first_id = h.add(original, tag="original")
        _, replayed = hist.replay(guard, original, history=h,
                                  headers={"X-Case": "modified"}, tag="replay")
        equal(len(h.entries), 2)
        equal(h.entries[0]["id"], first_id)
        equal(h.entries[0]["request_headers"].get("X-Case"), None)
        equal(h.entries[1]["request_headers"].get("X-Case"), "modified")
        equal(h.entries[1]["replayed_from"], original.url)
        equal(replayed.response.status, 200)


def test_replay_refuses_a_write_method_without_confirmation():
    with fixtures.FixtureServer() as srv:
        h = hist.History()
        guard = _guard(srv, methods=("GET", "DELETE"))
        original = hc.request(guard, srv.url("/echo"), "GET")
        raises(sc.ScopeError, hist.replay, guard, original, method="DELETE",
               history=h)


def test_replay_from_a_stored_record_drops_redacted_headers():
    with fixtures.FixtureServer() as srv:
        path = os.path.join(fixtures.tempfile_dir(), "history.jsonl")
        h = hist.History(path=path)
        guard = _guard(srv)
        exchange = hc.request(guard, srv.url("/echo"), "GET",
                              headers={"Authorization": "Bearer fixture-value"})
        entry_id = h.add(exchange)
        loaded = hist.History.load(path, secrets=["fixture-value"])
        _, replayed = hist.replay_from_record(guard, loaded, entry_id)
        echoed = json.loads(replayed.response.text)
        # The redacted header must not be replayed literally, and must not be a
        # silent 401 either: it is simply absent.
        equal(echoed["headers"].get("Authorization"), None)


def test_diff_against_previous_finds_the_earlier_request():
    with fixtures.FixtureServer() as srv:
        h = hist.History()
        guard = _guard(srv)
        h.add(hc.request(guard, srv.url("/json"), "GET"))
        second = h.add(hc.request(guard, srv.url("/json"), "GET"))
        result = hist.diff_against_previous(h, second)
        assert result is not None
        equal(result["observable_response_difference"], True)


def test_diff_against_previous_returns_none_for_the_first():
    with fixtures.FixtureServer() as srv:
        h = hist.History()
        guard = _guard(srv)
        first = h.add(hc.request(guard, srv.url("/json"), "GET"))
        equal(hist.diff_against_previous(h, first), None)


# ---------------------------------------------------------------------- diff
def test_identical_records_report_no_differences():
    a = _record({"body": '{"a":1}'})
    b = _record({"body": '{"a":1}', "id": "H0002"})
    result = diff.compare_records(a, b)
    equal(result["difference_count"], 0)
    equal(result["status"]["changed"], False)
    equal(result["body"]["exact_equal"], True)


def test_status_change_is_reported_with_classes():
    result = diff.compare_records(_record({}), _record({}, status=403))
    equal(result["status"]["changed"], True)
    equal(result["status"]["class_changed"], True)
    equal(result["status"]["from"], 200)
    equal(result["status"]["to"], 403)


def test_same_class_status_change_is_not_a_class_change():
    # 200 -> 201 is a different status in the same class; 200 -> 404 is not.
    result = diff.compare_records(_record({}), _record({}, status=201))
    equal(result["status"]["changed"], True)
    equal(result["status"]["class_changed"], False)


def test_cross_class_status_change_is_reported_as_a_class_change():
    result = diff.compare_records(_record({}), _record({}, status=404))
    equal(result["status"]["class_changed"], True)


def test_header_additions_removals_and_changes_are_separated():
    a = _record({}, headers={"X-A": "1", "X-B": "2"})
    b = _record({}, headers={"X-A": "1", "X-B": "3", "X-C": "4"})
    block = diff.compare_headers(a["response"]["headers"], b["response"]["headers"])
    equal(block["added"], {"x-c": "4"})
    equal(block["removed"], {})
    equal(block["changed"], {"x-b": {"from": "2", "to": "3"}})
    equal(block["count"], 2)


def test_header_comparison_is_case_insensitive():
    a = _record({}, headers={"Content-Type": "text/html"})
    b = _record({}, headers={"content-type": "text/html"})
    equal(diff.compare_headers(a["response"]["headers"],
                               b["response"]["headers"])["count"], 0)


def test_cookie_flags_are_compared():
    a = _record({}, headers={"Set-Cookie": "sid=1; Path=/; HttpOnly; Secure"})
    b = _record({}, headers={"Set-Cookie": "sid=1; Path=/"})
    block = diff.compare_cookies(a, b)
    equal(block["count"], 1)
    assert "secure" in block["changed"]["sid"]["attributes"]
    assert "httponly" in block["changed"]["sid"]["attributes"]


def test_cookie_value_change_is_reported_without_the_value():
    a = _record({}, headers={"Set-Cookie": "sid=fixture-one; Path=/"})
    b = _record({}, headers={"Set-Cookie": "sid=fixture-two; Path=/"})
    block = diff.compare_cookies(a, b)
    equal(block["changed"]["sid"]["value"], "changed")


def test_cookie_added_and_removed():
    a = _record({}, headers={"Set-Cookie": "sid=1"})
    b = _record({}, headers={"Set-Cookie": "other=2"})
    block = diff.compare_cookies(a, b)
    equal(list(block["added"]), ["other"])
    equal(list(block["removed"]), ["sid"])


def test_normalisation_ignores_whitespace_and_line_endings_only():
    equal(diff.normalise_text("a\r\n  b  \n"), "a\nb")
    assert diff.normalise_text("A") != diff.normalise_text("a")


def test_body_diff_reports_the_first_difference():
    result = diff.body_diff('{"a":1,"b":2}', '{"a":1,"b":3}')
    equal(result["exact_equal"], False)
    equal(result["normalised_equal"], False)
    equal(result["first_difference"]["offset"], 11)


def test_body_diff_reports_normalised_equality():
    result = diff.body_diff("hello   world", "hello world")
    equal(result["exact_equal"], False)
    equal(result["normalised_equal"], True)


def test_json_structure_compares_shape_not_values():
    a = _record({"body": '{"items":[{"id":1,"name":"alpha"}],"total":2}'})
    b = _record({"body": '{"items":[{"id":9,"name":"zeta"}],"total":99}'})
    result = diff.compare_json(a["response"]["body_text"],
                               b["response"]["body_text"])
    equal(result["parsed"], True)
    equal(result["count"], 0)


def test_json_structure_detects_added_and_removed_keys():
    a = _record({"body": '{"id":1,"name":"alpha"}'})
    b = _record({"body": '{"id":1,"label":"alpha","extra":true}'})
    result = diff.compare_json(a["response"]["body_text"],
                               b["response"]["body_text"])
    equal(list(result["added_keys"]), ["$.extra", "$.label"])
    equal(list(result["removed_keys"]), ["$.name"])


def test_json_structure_detects_a_type_change():
    a = _record({"body": '{"count":2}'})
    b = _record({"body": '{"count":"2"}'})
    result = diff.compare_json(a["response"]["body_text"],
                               b["response"]["body_text"])
    equal(result["changed_types"]["$.count"], {"from": "number", "to": "string"})


def test_json_structure_handles_non_json_without_raising():
    a = _record({"body": "<html></html>"})
    b = _record({"body": "<html></html>"})
    result = diff.compare_json(a["response"]["body_text"],
                               b["response"]["body_text"])
    equal(result["parsed"], False)
    assert result["reason"]


def test_json_structure_depth_is_capped():
    deep = json.dumps({"a": {"b": {"c": {"d": {"e": 1}}}}})
    shape = diff.json_structure(json.loads(deep), max_depth=2)
    assert any(v == "truncated" for v in shape.values())


def test_array_structure_reports_length():
    shape = diff.json_structure({"items": [1, 2, 3]})
    equal(shape["$.items"], "array[3]")


def test_content_type_change_is_visible():
    a = _record({"body": "{}"}, ctype="application/json")
    b = _record({"body": "{}"}, ctype="text/html")
    equal(diff.compare_records(a, b)["content_type"]["changed"], True)


def test_timing_delta_is_computed_when_both_are_present():
    a = _record({"ms": 10})
    b = _record({"ms": 25, "id": "H0002"})
    equal(diff.compare_records(a, b)["timing"]["delta_ms"], 15)


def test_difference_count_reflects_the_number_of_changed_sections():
    a = _record({"body": '{"a":1}'}, headers={"X-A": "1"})
    b = _record({"body": '{"a":2}'}, headers={"X-B": "2"}, status=500)
    result = diff.compare_records(a, b)
    assert result["difference_count"] >= 3, result["difference_count"]


def test_comparison_never_claims_a_vulnerability():
    a = _record({"body": '{"role":"user"}'})
    b = _record({"body": '{"role":"admin"}'}, status=200)
    result = diff.compare_records(a, b)
    rendered = json.dumps(result) + diff.as_text(result)
    equal(diff.assert_no_overclaim(rendered), [])
    contains(result["interpretation"], "not by itself")


def test_rendered_diff_states_that_a_difference_is_not_a_finding():
    text = diff.as_text(diff.compare_records(_record({"body": "a"}), _record({"body": "b"})))
    contains(text, "A difference is not a finding")


def test_overclaim_guard_actually_detects_overclaiming():
    # The guard is only worth having if it fails on the text it exists to catch.
    assert diff.assert_no_overclaim("the target is vulnerable")
    assert diff.assert_no_overclaim("CONFIRMED exploit")
    equal(diff.assert_no_overclaim("observable response difference"), [])


def test_compare_exchanges_uses_the_same_path_as_stored_records():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        a = hc.request(guard, srv.url("/json"), "GET")
        b = hc.request(guard, srv.url("/json-alt"), "GET")
        result = diff.compare_exchanges(a, b, id_a="A", id_b="B")
        equal(result["from"]["id"], "A")
        assert result["json_structure"]["count"] >= 1


# -------------------------------------------------------------------- paras
def test_query_parameters_are_extracted():
    found = params.from_url("http://x/search?q=cats&page=2&empty=")
    equal([(p.name, p.value) for p in found], [("q", "cats"), ("page", "2"),
                                               ("empty", "")])


def test_path_segments_with_values_are_extracted():
    found = params.from_url("http://x/api/items/42")
    equal([p.name for p in found], ["segment[2]"])
    equal(found[0].category, "identifier")


def test_static_path_words_are_not_parameters():
    found = params.from_url("http://x/api/v2/users")
    equal(found, [])


def test_form_body_parameters_are_extracted():
    found = params.from_body("username=a&password=b", "application/x-www-form-urlencoded")
    equal([p.name for p in found], ["username", "password"])


def test_json_fields_are_extracted_with_nested_paths():
    found = params.from_body('{"user":{"id":7,"name":"a"},"tags":["x"]}',
                             "application/json")
    paths = sorted(p.path for p in found)
    equal(paths, ["tags[0]", "user.id", "user.name"])


def test_json_array_index_is_marked_indexed():
    found = params.from_body('[{"id":1},{"id":2}]', "application/json")
    assert all(p.indexed for p in found)


def test_malformed_json_body_is_not_an_exception():
    equal(params.from_body("{not json", "application/json"), [])


def test_multipart_metadata_is_extracted_without_file_content():
    body = ('--b\r\nContent-Disposition: form-data; name="attachment"; '
            'filename="report.pdf"\r\nContent-Type: application/pdf\r\n\r\n'
            '<binary>\r\n--b--')
    found = params.from_body(body, "multipart/form-data")
    equal(len(found), 1)
    equal(found[0].name, "attachment")
    contains(found[0].note, "report.pdf")


def test_custom_headers_are_parameters_but_plumbing_is_not():
    found = params.from_headers({"X-Tenant": "acme", "Accept": "*/*",
                                 "Authorization": "Bearer x", "Cookie": "sid=1"})
    equal([p.name for p in found], ["X-Tenant"])


def test_cookie_parameters_are_extracted_from_the_header():
    found = params.from_cookies({"Cookie": "sid=1; theme=dark"})
    equal([p.name for p in found], ["sid", "theme"])


def test_classification_across_the_documented_categories():
    cases = {
        ("q", "cats"): "search",
        ("page", "3"): "pagination",
        ("sort", "name"): "sorting",
        ("status", "open"): "filter",
        ("avatar", "x.png"): "file",
        ("user_id", "7"): "identifier",
        ("quantity", "12"): "numeric",
        ("count", "12"): "pagination",   # "count" is page-size vocabulary here
        ("enabled", "true"): "boolean",
        ("next", "/home"): "url",
        ("contact", "a@b.co"): "email",
        ("topic", "some-slug"): "slug",
        ("weird", "???"): "unknown",
    }
    for (name, value), expected in cases.items():
        equal(params.classify(name, value), expected, f"{name}={value}")


def test_identifier_classification_does_not_catch_words_ending_in_id():
    equal(params.classify("valid", "true"), "boolean")
    equal(params.classify("paid", "0"), "numeric")


def test_sensitive_values_are_masked_in_output():
    found = params.from_body("password=fixture-secret-value&user=bob",
                             "application/x-www-form-urlencoded")
    rendered = json.dumps([p.as_dict() for p in found])
    not_contains(rendered, "fixture-secret-value")
    contains(rendered, params.MASK)


def test_long_values_are_truncated_in_previews():
    found = params.from_url("http://x/?q=" + "A" * 500)
    assert len(found[0].as_dict()["value_preview"]) <= 121


def test_inventory_covers_every_location_in_one_request():
    record = {
        "url": "http://x/search?q=cats&page=1",
        "request_headers": {"Content-Type": "application/json", "X-Tenant": "acme",
                            "Cookie": "sid=1"},
        "request_body": '{"filter":{"status":"open"}}',
    }
    found = params.inventory(record)
    locations = {p["location"] for p in found}
    equal(locations, {"query", "json", "header", "cookie"})
    summary = params.summarise(found)
    equal(summary["total"], len(found))
    assert summary["by_category"]["search"] == 1


def test_suggested_cases_are_per_category_and_never_exploit_payloads():
    param = params.Parameter("query", "page", "2").as_dict()
    cases = params.suggested_cases(param)
    labels = [c["case"] for c in cases]
    assert "page-zero" in labels and "negative-page" in labels
    for case in cases:
        assert "<script" not in str(case["value"])
        assert "UNION" not in str(case["value"])


def test_suggested_cases_never_echo_a_masked_value():
    param = params.Parameter("query", "token", "fixture-secret").as_dict()
    for case in params.suggested_cases(param):
        assert case["value"] != "fixture-secret"


def test_case_matrix_respects_the_budget_round_robin():
    inventory = [{"category": "numeric", "location": "query", "path": f"p{i}",
                  "name": f"p{i}", "value_preview": "1"} for i in range(5)]
    cases = params.case_matrix(inventory, budget=5)
    equal(len(cases), 5)
    equal(len({c["path"] for c in cases}), 5, "budget should spread across parameters")


def test_case_matrix_without_a_budget_covers_everything():
    inventory = [{"category": "boolean", "location": "query", "path": "flag",
                  "name": "flag", "value_preview": "true"}]
    cases = params.case_matrix(inventory)
    equal(len(cases), len(params.CASES["boolean"]))
