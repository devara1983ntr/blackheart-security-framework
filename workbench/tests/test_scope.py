"""Scope enforcement tests.

This is the module that decides whether Phase 5 is allowed to exist. If the gate
can be walked around, the workbench is an unauthorized scanner with a
configuration file, so the negative cases outnumber the positive ones here on
purpose: every test that proves a request is *allowed* is paired with one
proving the same request is refused when anything about the authorization
changes.
"""

from __future__ import annotations

import datetime as dt
import json
import os

from workbench import scope as sc
from workbench.tests.harness import contains, equal, raises, temp_dir
from workbench.tests import fixtures

FUTURE = "2099-12-31"
PAST = "2020-01-01"


def _scope(**overrides):
    return sc.Scope(fixtures.scope_data(**overrides))


def _guard(**overrides):
    data = fixtures.scope_data(**overrides)
    return sc.ScopeGuard(sc.Scope(data), resolve=lambda host: ["93.184.216.34"])


# --------------------------------------------------------------- loading rules
def test_missing_scope_file_is_refused():
    raises(sc.ScopeError, sc.load_scope, "/nonexistent/scope.json")


def test_empty_scope_file_is_refused():
    d = temp_dir()
    path = os.path.join(d, "scope.json")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("{}")
    raises(sc.ScopeError, sc.load_scope, path)


def test_scope_that_is_not_an_object_is_refused():
    d = temp_dir()
    path = os.path.join(d, "scope.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([1, 2, 3], fh)
    raises(sc.ScopeError, sc.load_scope, path)


def test_scope_that_is_not_json_is_refused():
    d = temp_dir()
    path = os.path.join(d, "scope.json")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("allowed_hosts: everything")
    raises(sc.ScopeError, sc.load_scope, path)


def test_unknown_key_is_refused_rather_than_ignored():
    # Ignoring an unknown key is how a typo becomes a silent widening.
    exc = raises(sc.ScopeError, _scope, alowed_hosts=["example.com"])
    sc_msg = str(exc)
    assert "unknown scope key" in sc_msg, sc_msg


def test_bypass_keys_are_named_in_the_error():
    for key in ("ignore_scope", "bypass", "disable_scope", "allow_all", "force"):
        exc = raises(sc.ScopeError, _scope, **{key: True})
        assert "no bypass" in str(exc).lower(), (key, str(exc))


def test_empty_host_list_authorizes_nothing():
    raises(sc.ScopeError, _scope, allowed_hosts=[])


def test_empty_method_list_authorizes_nothing():
    raises(sc.ScopeError, _scope, allowed_methods=[])


def test_zero_request_budget_is_refused():
    # An unbounded budget is not a scope. Refusing 0 keeps "I forgot" from
    # becoming "unlimited".
    raises(sc.ScopeError, _scope, max_requests=0)


def test_negative_numbers_are_refused():
    for key in ("max_requests", "max_concurrency", "max_redirects", "timeout_s",
                "max_response_bytes", "min_interval_s"):
        raises(sc.ScopeError, _scope, **{key: -1})


def test_boolean_is_not_accepted_as_a_number():
    raises(sc.ScopeError, _scope, max_requests=True)


def test_invalid_lists_are_refused():
    raises(sc.ScopeError, _scope, allowed_hosts="example.com")
    raises(sc.ScopeError, _scope, allowed_methods=[1, 2])
    raises(sc.ScopeError, _scope, excluded_paths="admin")


def test_invalid_method_names_are_refused():
    raises(sc.ScopeError, _scope, allowed_methods=["GET", "DROP TABLE"])


def test_allow_private_networks_must_be_boolean():
    raises(sc.ScopeError, _scope, allow_private_networks="yes")


# ------------------------------------------------------------- expiry / clock
def test_authorized_until_date_is_end_of_day():
    s = _scope(authorized_until="2030-06-15")
    equal(s.authorized_until.hour, 23, "date form should mean end of that day")


def test_authorized_until_accepts_a_timestamp():
    s = _scope(authorized_until="2030-06-15T10:30:00Z")
    equal(s.authorized_until.minute, 30)


def test_authorized_until_rejects_nonsense():
    raises(sc.ScopeError, _scope, authorized_until="next tuesday")


def test_expired_authorization_refuses_requests():
    guard = sc.ScopeGuard(sc.Scope(fixtures.scope_data(authorized_until=PAST)),
                          resolve=lambda host: ["93.184.216.34"])
    decision = guard.check("http://127.0.0.1/text")
    assert not decision, "an expired scope must refuse"
    equal(decision.rule, "expired")


def test_future_authorization_allows_requests():
    guard = sc.ScopeGuard(sc.Scope(fixtures.scope_data(authorized_until=FUTURE)),
                          resolve=lambda host: ["93.184.216.34"])
    assert guard.check("http://127.0.0.1/text")


def test_clock_is_injectable_so_expiry_is_testable():
    frozen = [dt.datetime(2030, 1, 1, tzinfo=dt.timezone.utc)]
    guard = sc.ScopeGuard(sc.Scope(fixtures.scope_data(authorized_until="2030-06-15")),
                          utcnow=lambda: frozen[0], resolve=lambda host: ["93.184.216.34"])
    assert guard.check("http://127.0.0.1/text")
    frozen[0] = dt.datetime(2031, 1, 1, tzinfo=dt.timezone.utc)
    assert not guard.check("http://127.0.0.1/text")


# --------------------------------------------------------------- host matching
def test_exact_host_matches():
    assert _scope(allowed_hosts=["example.com"]).host_allowed("example.com")


def test_unlisted_host_does_not_match():
    assert not _scope(allowed_hosts=["example.com"]).host_allowed("other.com")


def test_wildcard_matches_subdomains():
    s = _scope(allowed_hosts=["*.example.com"])
    assert s.host_allowed("api.example.com")
    assert s.host_allowed("deep.api.example.com")


def test_wildcard_does_not_match_the_bare_suffix():
    # `*.example.com` must not authorise `notexample.com`; a substring match is
    # the classic way this control fails.
    s = _scope(allowed_hosts=["*.example.com"])
    assert not s.host_allowed("notexample.com")
    assert not s.host_allowed("example.com.evil.net")


def test_wildcard_does_not_match_the_apex():
    assert not _scope(allowed_hosts=["*.example.com"]).host_allowed("example.com")


def test_host_matching_is_case_insensitive_and_ignores_trailing_dot():
    s = _scope(allowed_hosts=["example.com"])
    assert s.host_allowed("EXAMPLE.COM")
    assert s.host_allowed("example.com.")


def test_exclusion_beats_inclusion_for_hosts():
    s = _scope(allowed_hosts=["example.com", "admin.example.com"],
               excluded_hosts=["admin.example.com"])
    assert s.host_allowed("example.com")
    assert not s.host_allowed("admin.example.com")


def test_wildcard_exclusion_beats_exact_inclusion():
    s = _scope(allowed_hosts=["api.example.com"], excluded_hosts=["*.example.com"])
    assert not s.host_allowed("api.example.com")


# --------------------------------------------------------------- path matching
def test_path_prefix_matching():
    s = _scope(allowed_paths=["/api"])
    assert s.path_allowed("/api")
    assert s.path_allowed("/api/items/1")
    assert not s.path_allowed("/admin")


def test_path_wildcard_matching():
    s = _scope(allowed_paths=["/api/v*/items"])
    assert s.path_allowed("/api/v1/items")
    assert s.path_allowed("/api/v2/items")
    assert not s.path_allowed("/api/items")


def test_empty_path_list_means_host_scoped():
    assert _scope(allowed_paths=[]).path_allowed("/anything")


def test_excluded_path_beats_allowed_path():
    s = _scope(allowed_paths=["/api"], excluded_paths=["/api/admin"])
    assert s.path_allowed("/api/items")
    assert not s.path_allowed("/api/admin")
    assert not s.path_allowed("/api/admin/users")


def test_path_exclusion_applies_even_with_no_path_allowlist():
    s = _scope(allowed_paths=[], excluded_paths=["/private"])
    assert not s.path_allowed("/private")
    assert s.path_allowed("/public")


# ------------------------------------------------------------------ the guard
def test_guard_allows_an_in_scope_request():
    assert _guard().check("http://127.0.0.1/text", "GET")


def test_guard_refuses_a_non_http_scheme():
    guard = _guard()
    for url in ("ftp://127.0.0.1/file", "file:///etc/passwd",
                "gopher://127.0.0.1/", "javascript:alert(1)", "data:text/html,x"):
        decision = guard.check(url, "GET")
        assert not decision, url
        equal(decision.rule, "scheme", url)


def test_guard_refuses_credentials_in_the_url():
    decision = _guard().check("http://user:pass@127.0.0.1/text")
    assert not decision
    equal(decision.rule, "credentials")


def test_guard_refuses_a_url_without_a_host():
    decision = _guard().check("http:///text")
    assert not decision


def test_guard_refuses_an_out_of_scope_host():
    decision = _guard().check("http://example.com/text")
    assert not decision
    equal(decision.rule, "host")


def test_guard_refuses_an_excluded_host():
    guard = _guard(allowed_hosts=["127.0.0.1", "example.com"],
                   excluded_hosts=["example.com"])
    decision = guard.check("http://example.com/text")
    assert not decision
    equal(decision.rule, "host")


def test_guard_refuses_an_excluded_path():
    decision = _guard().check("http://127.0.0.1/private/notes")
    assert not decision
    equal(decision.rule, "path")


def test_guard_refuses_a_method_not_in_scope():
    decision = _guard().check("http://127.0.0.1/text", "DELETE")
    assert not decision
    equal(decision.rule, "method")


def test_guard_method_check_is_case_insensitive():
    assert _guard(methods=("get", "HEAD")).check("http://127.0.0.1/text", "get")


def test_guard_refuses_private_addresses_by_default():
    # The same URL, the same host list, only the opt-in differs.
    guard = sc.ScopeGuard(sc.Scope(fixtures.scope_data(allow_private_networks=False)),
                          resolve=lambda host: ["10.0.0.5"])
    decision = guard.check("http://127.0.0.1/text")
    assert not decision
    equal(decision.rule, "address")


def test_guard_allows_loopback_only_with_the_explicit_opt_in():
    guard = sc.ScopeGuard(sc.Scope(fixtures.scope_data(allow_private_networks=True)),
                          resolve=lambda host: ["127.0.0.1"])
    assert guard.check("http://127.0.0.1/text")


def test_private_opt_in_does_not_widen_the_host_list():
    # Opting into private address space must not authorise a host that was
    # never named, even if it resolves privately.
    guard = sc.ScopeGuard(
        sc.Scope(fixtures.scope_data(allowed_hosts=["127.0.0.1"],
                                     allow_private_networks=True)),
        resolve=lambda host: ["10.0.0.5"])
    decision = guard.check("http://internal.example/text")
    assert not decision


def test_guard_refuses_private_ip_literals():
    # Each of these is an address the workbench must refuse; naming one here
    # authorises nothing, because the opt-in below is false. The wildcard-address
    # literal is data in a deny-test, not a bind address.
    guard = sc.ScopeGuard(sc.Scope(fixtures.scope_data(
        allowed_hosts=["10.0.0.1", "169.254.169.254", "192.168.1.1", "::1",
                       "fd00::1", "fe80::1", "0.0.0.0"],  # nosec B104
        allow_private_networks=False)))
    for host in ("10.0.0.1", "169.254.169.254", "192.168.1.1",  # nosec B104
                 "0.0.0.0", "[fd00::1]", "[::1]", "[fe80::1]"):
        decision = guard.check(f"http://{host}/")
        assert not decision, host
        equal(decision.rule, "address", host)


def test_cloud_metadata_address_is_refused_by_name_too():
    # Naming it does not help while the private-network opt-in is absent: this
    # is the address an SSRF reaches for and it is link-local, not public.
    decision = _guard(allowed_hosts=["169.254.169.254"],
                      allow_private_networks=False).check("http://169.254.169.254/")
    assert not decision
    equal(decision.rule, "address")


def test_named_private_host_is_allowed_only_with_the_opt_in():
    # The documented boundary: `allow_private_networks` widens the address
    # space for a host that was already named, and never widens the host list.
    allowed = _guard(allowed_hosts=["169.254.169.254"],
                     allow_private_networks=True).check("http://169.254.169.254/")
    assert allowed is not None and allowed


def test_guard_refuses_when_dns_fails():
    # A name is used deliberately: an IP literal is never resolved, so it could
    # not exercise this path (that is itself worth knowing, and is why the
    # resolver is injectable).
    guard = sc.ScopeGuard(
        sc.Scope(fixtures.scope_data(allowed_hosts=["fixture.invalid"])),
        resolve=lambda host: (_ for _ in ()).throw(OSError("no dns")))
    decision = guard.check("http://fixture.invalid/text")
    assert not decision
    equal(decision.rule, "dns")


def test_guard_refuses_when_dns_returns_nothing():
    guard = sc.ScopeGuard(
        sc.Scope(fixtures.scope_data(allowed_hosts=["fixture.invalid"])),
        resolve=lambda host: [])
    decision = guard.check("http://fixture.invalid/text")
    assert not decision
    equal(decision.rule, "dns")


def test_ip_literals_are_not_resolved():
    calls = []

    def resolver(host):
        calls.append(host)
        return ["93.184.216.34"]

    guard = sc.ScopeGuard(sc.Scope(fixtures.scope_data()), resolve=resolver)
    guard.check("http://127.0.0.1/text")
    equal(calls, [], "an IP literal must not be sent to the resolver")


def test_guard_refuses_a_host_that_resolves_to_public_and_private():
    # Half-public resolution is not authorisation for the private half.
    guard = sc.ScopeGuard(
        sc.Scope(fixtures.scope_data(allowed_hosts=["mixed.example"],
                                     allow_private_networks=False)),
        resolve=lambda host: ["93.184.216.34", "127.0.0.1"])
    decision = guard.check("http://mixed.example/")
    assert not decision
    equal(decision.rule, "address")


# --------------------------------------------------------------------- budget
def test_budget_is_enforced_and_reported():
    guard = _guard(max_requests=3)
    for _ in range(3):
        assert guard.check("http://127.0.0.1/text")
        guard.note_request()
    decision = guard.check("http://127.0.0.1/text")
    assert not decision
    equal(decision.rule, "budget")
    equal(guard.requests_made, 3)


def test_denials_are_recorded_with_a_rule():
    guard = _guard()
    guard.check("http://example.com/")
    guard.check("http://127.0.0.1/text", "DELETE")
    equal(len(guard.denials), 2)
    equal(sorted(d["rule"] for d in guard.denials), ["host", "method"])


def test_rate_limit_waits_the_configured_interval():
    slept = []
    guard = sc.ScopeGuard(sc.Scope(fixtures.scope_data(min_interval_s=0.5)),
                          clock=lambda: 1.0, resolve=lambda h: ["93.184.216.34"])
    guard._last_request_at = 0.6
    waited = guard.wait_for_rate_limit(sleeper=slept.append)
    assert slept and abs(waited - 0.1) < 1e-6, (slept, waited)


# --------------------------------------------------------- require() semantics
def test_require_raises_instead_of_returning_falsy():
    # A falsy return is something a caller can forget to check. An exception is
    # not. This is the whole reason `require` exists next to `check`.
    raises(sc.ScopeError, sc.require, _guard(), "http://example.com/")


def test_require_refuses_write_methods_without_confirmation():
    guard = _guard(methods=("GET", "DELETE"))
    raises(sc.ScopeError, sc.require, guard, "http://127.0.0.1/text", "DELETE")


def test_require_allows_write_methods_when_confirmed():
    guard = _guard(methods=("GET", "DELETE"))
    decision = sc.require(guard, "http://127.0.0.1/text", "DELETE", confirm_write=True)
    assert decision


def test_require_still_refuses_unscoped_write_methods_when_confirmed():
    guard = _guard(methods=("GET",))
    raises(sc.ScopeError, sc.require, guard, "http://127.0.0.1/text", "DELETE",
           confirm_write=True)


# ------------------------------------------------------- structural (no bypass)
def test_guard_exposes_no_way_to_disable_itself():
    guard = _guard()
    forbidden = ("ignore", "bypass", "disable", "force", "unsafe", "override",
                 "skip", "allow_all")
    for name in dir(guard):
        if name.startswith("__"):
            continue
        lowered = name.lower()
        for word in forbidden:
            assert word not in lowered, f"ScopeGuard.{name} looks like a bypass hook"
        assert not name.startswith("_") or name in (
            "_clock", "_utcnow", "_resolve", "_last_request_at", "_deny",
        ), f"unexpected private attribute {name}"


def test_scope_object_exposes_no_way_to_disable_itself():
    s = _scope()
    for name in dir(s):
        if name.startswith("__"):
            continue
        for word in ("ignore", "bypass", "disable", "override", "unlimited"):
            assert word not in name.lower(), f"Scope.{name} looks like a bypass"


def test_private_api_is_the_only_private_surface():
    # Private members are reachable, so the guard against accidental bypass is
    # the name check above. This test pins the surface so a new private back
    # door cannot be added without a reviewer noticing.
    guard = _guard()
    private = {n for n in dir(guard) if n.startswith("_") and not n.startswith("__")}
    equal(private, {"_clock", "_utcnow", "_resolve", "_last_request_at", "_deny"})


# ------------------------------------------------------------- address policy
def test_documentation_and_reserved_ranges_are_not_global():
    # Asserting refusal, so the wildcard-address literal is test data.
    for addr in ("198.51.100.7", "203.0.113.9", "192.0.2.1",  # nosec B104
                 "0.0.0.0", "224.0.0.1", "255.255.255.255", "::", "ff02::1"):
        assert sc.address_is_private(addr), addr


def test_public_addresses_are_global():
    for addr in ("93.184.216.34", "8.8.8.8", "2606:4700::1111"):
        assert not sc.address_is_private(addr), addr


def test_unparseable_address_is_treated_as_unsafe():
    assert sc.address_is_private("not-an-address")
    assert sc.address_is_private("")


def test_summary_reports_the_controls_in_force():
    guard = _guard()
    guard.check("http://example.com/")
    summary = guard.summary()
    equal(summary["max_requests"], 200)
    equal(summary["denials"], 1)
    assert summary["allowed_hosts"] == ["127.0.0.1", "localhost"]
    assert isinstance(summary["scope_file"], str)


def test_decision_serialises():
    d = _guard().check("http://example.com/")
    payload = d.as_dict()
    equal(payload["allowed"], False)
    equal(payload["rule"], "host")
    assert payload["reason"]


def test_decisions_are_deterministic():
    a = _guard().check("http://127.0.0.1/text").as_dict()
    b = _guard().check("http://127.0.0.1/text").as_dict()
    equal(a, b)
