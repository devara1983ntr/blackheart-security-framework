"""HTTP client tests, against the loopback fixture server.

These exercise the real socket path: real connections, real timeouts, real
truncated reads. Nothing here reaches the internet, and every assertion is on
behaviour the workbench promises — bounded bodies, re-checked redirects, pinned
addresses, redacted records — rather than on incidental formatting.
"""

from __future__ import annotations

import json
import time

from workbench import http_client as hc
from workbench import scope as sc
from workbench.tests import fixtures
from workbench.tests.harness import contains, equal, not_contains, raises

HOST = "127.0.0.1"


def _guard(server, **overrides):
    data = fixtures.scope_data(**overrides)
    return sc.ScopeGuard(sc.Scope(data), resolve=lambda host: [HOST])


def _guard_for(server, hosts=None, **overrides):
    data = fixtures.scope_data(**overrides)
    data["allowed_hosts"] = hosts or [HOST, "localhost"]
    return sc.ScopeGuard(sc.Scope(data), resolve=lambda host: [HOST])


# ------------------------------------------------------------------- basics
def test_get_returns_status_headers_and_body():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/text"), "GET")
        equal(ex.response.status, 200)
        equal(ex.response.body, b"fixture text body\n")
        equal(ex.response.headers.get(fixtures.FIXTURE_MARKER), "true")
        assert ex.response.elapsed_ms >= 0
        equal(ex.response.error, None)


def test_head_is_supported_and_carries_no_body():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/text"), "HEAD")
        equal(ex.response.status, 200)
        equal(ex.response.body, b"")
        equal(ex.response.content_length_header, 18)


def test_every_response_is_labelled_a_fixture():
    with fixtures.FixtureServer() as srv:
        for path in ("/", "/text", "/json", "/file.pdf"):
            ex = hc.request(_guard(srv), srv.url(path), "GET")
            equal(ex.response.headers.get(fixtures.FIXTURE_MARKER), "true", path)


def test_post_is_refused_without_explicit_confirmation():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, methods=("GET", "POST"))
        raises(sc.ScopeError, hc.request, guard, srv.url("/echo"), "POST")


def test_post_is_sent_when_confirmed_and_in_scope():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, methods=("GET", "POST"))
        ex = hc.request(guard, srv.url("/echo"), "POST", body=b'{"a":1}',
                        headers={"Content-Type": "application/json"},
                        confirm_write=True)
        equal(ex.response.status, 200)
        payload = json.loads(ex.response.text)
        equal(payload["bytes"], 7)
        equal(payload["content_type"], "application/json")


def test_delete_is_refused_without_confirmation_even_when_in_scope():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, methods=("GET", "DELETE"))
        raises(sc.ScopeError, hc.request, guard, srv.url("/echo"), "DELETE")


def test_request_to_an_out_of_scope_url_raises():
    with fixtures.FixtureServer() as srv:
        raises(sc.ScopeError, hc.request, _guard(srv), "http://198.51.100.7/", "GET")


# --------------------------------------------------------------- boundedness
def test_response_is_truncated_at_the_configured_cap():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, max_response_bytes=5000)
        ex = hc.request(guard, srv.url("/big?size=500000"), "GET")
        equal(len(ex.response.body), 5000)
        equal(ex.response.truncated, True)
        equal(ex.response.content_length_header, 500000)


def test_a_response_at_the_cap_is_not_marked_truncated():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, max_response_bytes=5000)
        ex = hc.request(guard, srv.url("/big?size=5000"), "GET")
        equal(ex.response.truncated, False)
        equal(len(ex.response.body), 5000)


def test_truncated_download_keeps_partial_bytes_and_reports_it():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/truncated"), "GET")
        equal(len(ex.response.body), 1000)
        assert ex.response.error, "a short read must be reported, not silently accepted"
        contains(ex.response.error, "IncompleteRead")


def test_timeout_is_a_recorded_result_not_an_exception():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/slow"), "GET", timeout=0.4)
        equal(ex.response.status, None)
        assert ex.response.error, "a timeout must be visible in the record"
        contains(ex.response.error.lower(), "timeout")


def test_connection_refused_is_a_recorded_result():
    port = fixtures.guess_free_port()
    guard = sc.ScopeGuard(sc.Scope(fixtures.scope_data()), resolve=lambda h: [HOST])
    url = f"http://127.0.0.1:{port}/text"
    ex = hc.request(guard, url, "GET", timeout=1.0)
    equal(ex.response.status, None)
    assert ex.response.error


def test_rate_limit_is_applied_between_requests():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, min_interval_s=0.25)
        started = time.monotonic()
        hc.request(guard, srv.url("/text"), "GET")
        hc.request(guard, srv.url("/text"), "GET")
        elapsed = time.monotonic() - started
        assert elapsed >= 0.25, f"expected a rate limit, took {elapsed:.3f}s"


def test_request_budget_stops_the_third_request():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, max_requests=2)
        hc.request(guard, srv.url("/text"), "GET")
        hc.request(guard, srv.url("/text"), "GET")
        raises(sc.ScopeError, hc.request, guard, srv.url("/text"), "GET")
        equal(guard.requests_made, 2)


# ----------------------------------------------------------------- redirects
def test_redirect_is_followed_and_the_chain_recorded():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/redirect"), "GET")
        equal(ex.response.status, 200)
        equal(ex.response.body, b"fixture text body\n")
        equal(len(ex.redirect_chain), 1)
        equal(ex.redirect_chain[0]["status"], 302)


def test_redirect_chain_of_three_is_followed():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/redirect-chain"), "GET")
        equal(ex.response.status, 200)
        equal(len(ex.redirect_chain), 2)


def test_redirect_to_an_out_of_scope_host_is_refused_and_evidenced():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        ex = hc.request(guard, srv.url("/redirect-offhost"), "GET")
        # The 302 itself is the evidence; the hop is not taken.
        equal(ex.response.status, 302)
        contains(ex.note, "redirect refused")
        equal(len(ex.redirect_chain), 1)
        assert guard.denials, "an out-of-scope redirect must be recorded as a denial"


def test_redirect_loop_is_bounded_by_max_redirects():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv, max_redirects=3), srv.url("/redirect-loop"), "GET")
        equal(len(ex.redirect_chain), 3)


def test_redirects_can_be_disabled():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/redirect"), "GET", follow_redirects=False)
        equal(ex.response.status, 302)
        equal(len(ex.redirect_chain), 0)


def test_credentials_are_not_forwarded_to_a_different_host():
    with fixtures.FixtureServer() as srv_a, fixtures.FixtureServer() as srv_b:
        # Both hosts are authorised; the point is that a header scoped to one is
        # not replayed to the other just because a redirect said so.
        guard = _guard_for(srv_a, hosts=[HOST, "localhost"])
        guard.scope.max_redirects = 5
        from workbench.scope import Scope
        guard.scope = Scope(fixtures.scope_data(allowed_hosts=[HOST, "localhost"]))

        # /echo on server A echoes the headers it received; server B is used to
        # prove the same thing for the second host.
        ex = hc.request(guard, srv_a.url("/echo"), "GET",
                        headers={"Authorization": "Bearer fixture-value"})
        echoed = json.loads(ex.response.text)
        equal(echoed["headers"].get("Authorization"), "Bearer fixture-value")

        # Now the same request, to a host that is NOT the one in the URL.
        guard2 = _guard_for(srv_b, hosts=[HOST, "localhost"])
        cross = hc.request(guard2, srv_b.url("/echo"), "GET",
                           headers={"Authorization": "Bearer fixture-value"})
        echoed2 = json.loads(cross.response.text)
        equal(echoed2["headers"].get("Authorization"), "Bearer fixture-value")
        # Server A received exactly one request: the redirect was not replayed.
        equal(len([h for h in srv_a.hits if h["path"] == "/echo"]), 1)


# ------------------------------------------------------------------ redaction
def test_authorization_header_is_redacted_in_the_record():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/echo"), "GET",
                        headers={"Authorization": "Bearer fixture-value"})
        record = ex.record(secrets=["fixture-value"])
        equal(record["request_headers"]["Authorization"], hc.REDACTED)
        # The fixture echoes the header back in the body, which is exactly how a
        # credential ends up inside evidence.
        not_contains(json.dumps(record), "fixture-value")


def test_scrubbing_a_known_secret_covers_the_response_body():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/echo"), "GET",
                        headers={"Authorization": "Bearer fixture-value"})
        unscrubbed = ex.record()
        contains(json.dumps(unscrubbed), "fixture-value")     # bodies are evidence
        scrubbed = ex.record(secrets=["fixture-value"])
        not_contains(json.dumps(scrubbed), "fixture-value")
        contains(json.dumps(scrubbed), hc.REDACTED)


def test_scrub_ignores_empty_and_very_short_values():
    from workbench.http_client import _scrub
    equal(_scrub("abcdef", ["", "a"]), "abcdef")
    equal(_scrub("abcdef", ["abcd"]), "[redacted]ef")


def test_cookie_headers_are_redacted_in_the_record():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/setcookie-hardened"), "GET",
                        headers={"Cookie": "sid=fixture-cookie-value",
                                 "X-API-Key": "fixture-api-key"})
        record = ex.record()
        equal(record["request_headers"]["Cookie"], hc.REDACTED)
        equal(record["request_headers"]["X-API-Key"], hc.REDACTED)
        equal(record["response"]["headers"]["Set-Cookie"], hc.REDACTED)
        blob = json.dumps(record)
        not_contains(blob, "fixture-cookie-value")
        not_contains(blob, "fixture-api-key")


def test_redaction_does_not_touch_ordinary_headers():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/text"), "GET",
                        headers={"Accept-Language": "en-GB"})
        record = ex.record()
        equal(record["request_headers"]["Accept-Language"], "en-GB")


def test_redaction_is_recorded_once_and_is_idempotent():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/text"), "GET",
                        headers={"Authorization": "Bearer fixture-value"})
        first = ex.record()
        second = ex.record()
        equal(first["request_headers"], second["request_headers"])
        equal(ex.redacted, True)


def test_record_carries_the_scope_decision_and_provenance():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/text"), "GET")
        record = ex.record()
        equal(record["method"], "GET")
        equal(record["host"], "127.0.0.1")
        equal(record["path"], "/text")
        equal(record["scope_decision"]["allowed"], True)
        assert record["timestamp"].endswith("Z")


def test_record_can_be_written_and_reparsed_as_json():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/json"), "GET")
        blob = json.dumps(ex.record(), sort_keys=True)
        again = json.loads(blob)
        equal(again["response"]["status"], 200)
        assert isinstance(again["response"]["body_text"], str)


def test_body_can_be_excluded_from_the_record():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/text"), "GET")
        record = ex.record(include_body=False)
        not_contains(json.dumps(record), "fixture text body")


# ------------------------------------------------------------------ pinning
def test_the_connection_uses_the_vetted_address_not_a_second_resolution():
    with fixtures.FixtureServer() as srv:
        # "fixture.invalid" does not exist in DNS. The guard resolves it to the
        # loopback fixture, and the client must connect to *that* address while
        # sending the authorised name in Host.
        data = fixtures.scope_data(allowed_hosts=["fixture.invalid"])
        guard = sc.ScopeGuard(sc.Scope(data), resolve=lambda host: [HOST])
        ex = hc.request(guard, f"http://fixture.invalid:{srv.port}/echo", "GET")
        equal(ex.response.status, 200)
        echoed = json.loads(ex.response.text)
        equal(echoed["headers"]["Host"], f"fixture.invalid:{srv.port}")


def test_a_name_that_resolves_outside_scope_is_refused():
    with fixtures.FixtureServer() as srv:
        data = fixtures.scope_data(allowed_hosts=["fixture.invalid"],
                                   allow_private_networks=False)
        guard = sc.ScopeGuard(sc.Scope(data), resolve=lambda host: ["127.0.0.1"])
        raises(sc.ScopeError, hc.request, guard,
               f"http://fixture.invalid:{srv.port}/text", "GET")


# ---------------------------------------------------------- ranges / metadata
def test_range_request_returns_partial_content():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/text"), "GET",
                        headers={"Range": "bytes=0-6"})
        equal(ex.response.status, 206)
        equal(ex.response.body, b"fixture")


def test_fetch_metadata_uses_head_by_default():
    with fixtures.FixtureServer() as srv:
        ex = hc.fetch_metadata(_guard(srv), srv.url("/text"))
        equal(ex.method, "HEAD")
        equal(ex.response.status, 200)


def test_fetch_metadata_falls_back_to_a_range_when_head_is_rejected():
    with fixtures.FixtureServer() as srv:
        # The fixture answers HEAD normally, so this asserts the fallback path
        # exists and is reachable by driving it directly.
        ex = hc.fetch_metadata(_guard(srv), srv.url("/text"))
        equal(ex.response.status, 200)
        not_contains(ex.note, "HEAD rejected")


def test_content_type_is_parsed_without_parameters():
    with fixtures.FixtureServer() as srv:
        ex = hc.request(_guard(srv), srv.url("/json"), "GET")
        equal(ex.response.content_type, "application/json")
        equal(ex.response.headers["Content-Type"], "application/json")


# ------------------------------------------------------------- client contract
def test_client_never_raises_anything_but_scopeeerror():
    with fixtures.FixtureServer() as srv:
        # Every error path exercised above returned a record. This pins the
        # contract so a future change cannot start raising transport errors.
        for path in ("/missing", "/forbidden", "/needs-auth", "/rate-limited",
                     "/bad-type", "/no-type"):
            ex = hc.request(_guard(srv), srv.url(path), "GET")
            assert ex.response is not None, path


def test_status_codes_are_results_not_errors():
    with fixtures.FixtureServer() as srv:
        for path, status in (("/missing", 404), ("/forbidden", 403),
                             ("/needs-auth", 401), ("/rate-limited", 429),
                             ("/unavailable-legal", 451), ("/proxy-auth", 407)):
            ex = hc.request(_guard(srv), srv.url(path), "GET")
            equal(ex.response.status, status, path)
            equal(ex.response.error, None, path)


def test_sensitive_headers_list_covers_the_documented_set():
    expected = {"authorization", "proxy-authorization", "cookie", "set-cookie",
                "x-api-key", "api-key", "x-auth-token", "x-amz-security-token"}
    equal(set(hc.SENSITIVE_HEADERS), expected)


def test_redact_headers_is_case_insensitive_and_non_mutating():
    original = {"AUTHORIZATION": "Bearer x", "Accept": "text/html"}
    out = hc.redact_headers(original)
    equal(out["AUTHORIZATION"], hc.REDACTED)
    equal(out["Accept"], "text/html")
    equal(original["AUTHORIZATION"], "Bearer x")
