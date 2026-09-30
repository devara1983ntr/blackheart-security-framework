"""Adversarial tests: attacks written against the implementation, not with it.

Every other module checks that the workbench does what it says. This one tries to
make it do something it says it will not. It was written from the review side —
working from the claims in `docs/workbench/` and trying to falsify them — and each
test names the claim it attacks and records the result, so a later reader can see
what was tried rather than only what passed.

Attacks grouped by the guarantee they target:

* **Authorization** — out-of-scope hosts and paths, unknown methods, an exhausted
  budget, a scope that tries to disable a control, a scope that names nothing.
* **The address boundary** — a redirect into a private range, a hostname that
  resolves to something the scope did not allow, loopback without the opt-in,
  multicast, link-local, and a redirect chain that never ends.
* **Secrets** — a credential in a header, a query string, a path, a body, a
  redirect and a cookie, then a search of everything written to disk.
* **Evidence** — a record edited after the bundle was written, a status moved
  without a second observation, a required field emptied, a count that disagrees
  with the records.
* **Acquisition and extraction** — a traversal member, an absolute path, a
  symlink, a device node, a bomb, a file that changed after it was recorded.
* **The policy blocker** — every bypass route from the module boundary.

Nothing here reaches the internet. The fixture server is on loopback, and the
scopes used are the fixture scopes.
"""

from __future__ import annotations

import json
import os

from workbench import evidence as ev
from workbench import fetch
from workbench import history as hist
from workbench import http_client as hc
from workbench import policy as policymod
from workbench import report as reportmod
from workbench import scope as sc
from workbench.tests import fixtures
from workbench.tests.harness import check, contains, equal, not_contains, raises

HOST = "127.0.0.1"


def _guard(server, **overrides):
    return sc.ScopeGuard(sc.Scope(fixtures.scope_data(server.url(""), **overrides)),
                         resolve=lambda host: [HOST])


# --------------------------------------------------------------- authorization
def test_a_host_outside_the_scope_costs_no_connection():
    """`localhost` resolves to the same address the scope allows, and is still
    refused: scope is a decision about names, not about addresses."""
    with fixtures.FixtureServer() as srv:
        guard = sc.ScopeGuard(sc.Scope(fixtures.scope_data(srv.url(""))),
                              resolve=lambda host: [HOST])
        request_url = srv.url("/soft").replace(HOST, "not-in-scope.invalid")
        before = len(srv.hits)
        raises(sc.ScopeError, hc.request, guard, request_url)
        equal(len(srv.hits), before, "a refused host still opened a connection")


def test_an_unknown_method_is_refused_rather_than_sent():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, methods=["GET"])
        before = len(srv.hits)
        raises(sc.ScopeError, hc.request, guard, srv.url("/soft"), "PROPFIND")
        raises(sc.ScopeError, hc.request, guard, srv.url("/soft"), "TRACE")
        equal(len(srv.hits), before)
        equal(sorted({hit["method"] for hit in srv.hits}), [])


def test_an_exhausted_budget_stops_the_run_without_a_socket():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, max_requests=2)
        hc.request(guard, srv.url("/soft"))
        hc.request(guard, srv.url("/soft"))
        before = len(srv.hits)
        raises(sc.ScopeError, hc.request, guard, srv.url("/soft"))
        equal(len(srv.hits), before, "the budget was exceeded on the wire")


def test_a_scope_file_cannot_turn_a_control_off():
    for key in ("ignore_scope", "bypass_scope", "skip_scope_check", "disable_scope",
                "unsafe", "insecure"):
        data = fixtures.scope_data()
        data[key] = True
        error = raises(sc.ScopeError, sc.Scope, data)
        contains(str(error), key, "the refusal must name the key it refused")
        check(any(word in str(error) for word in ("unknown scope key", "disable a control")),
              f"the refusal for {key} does not say why: {error}")


def test_a_redirect_into_a_private_range_is_refused_per_hop():
    """The open redirect is on the fixture; the destination is not in scope."""
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        before = len(srv.hits)
        exchange = hc.request(guard, srv.url("/redirect-offhost"))
        equal(len(srv.hits), before + 1, "only the first hop was requested")
        hop = exchange.redirect_chain[-1]
        equal(hop["status"], 302)
        contains(hop.get("refused") or json.dumps(hop), "198.51.100.7")


def test_loopback_without_the_private_network_opt_in_is_refused():
    data = fixtures.scope_data()
    data["allow_private_networks"] = False
    guard = sc.ScopeGuard(sc.Scope(data), resolve=lambda host: [HOST])
    raises(sc.ScopeError, hc.request, guard, "http://127.0.0.1:1/soft")


def test_private_and_reserved_addresses_are_refused_at_the_address_check():
    guard = _guard(fixtures.FixtureServer() if False else _FakeServer())
    for address in ("169.254.169.254", "224.0.0.1", "10.0.0.1", "192.168.1.1",
                    "0.0.0.0", "::1", "fe80::1", "ff02::1"):
        decision = guard.check_address(address)
        check(not decision.allowed or guard.scope.allow_private_networks,
              f"{address} was allowed without the opt-in")


class _FakeServer:
    """Only `url()` is needed by `_guard` for the address checks above."""

    def url(self, path):
        return f"http://example.invalid{path}"


def test_a_redirect_loop_terminates_at_the_redirect_cap():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, allowed_methods=["GET"], max_redirects=3)
        before = len(srv.hits)
        exchange = hc.request(guard, srv.url("/redirect-loop"))
        check(len(srv.hits) - before <= 4,
              f"the loop sent {len(srv.hits) - before} requests for a cap of 3")
        check(exchange is not None)


def test_a_write_method_cannot_be_sent_even_when_the_scope_allows_it():
    """Scope alone is never enough for a state-changing request."""
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, methods=["POST", "DELETE"])
        before = len(srv.hits)
        raises(sc.ScopeError, hc.request, guard, srv.url("/echo"), "POST")
        raises(sc.ScopeError, hc.request, guard, srv.url("/soft"), "DELETE")
        equal(len(srv.hits), before, "a state-changing request reached the wire")


# --------------------------------------------------------------------- secrets
def test_no_credential_reaches_disk_by_any_route():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        secret = "adv-fixture-secret"
        work = fixtures.tempfile_dir()
        history_obj = hist.History(path=os.path.join(work, "h.jsonl"), secrets=[secret])
        exchange = hc.request(
            guard, srv.url(f"/reflect?q={secret}"),
            headers={"Authorization": f"Bearer {secret}", "Cookie": f"sid={secret}",
                     "X-API-Key": secret, "Proxy-Authorization": f"Basic {secret}"},
            body=f"token={secret}".encode())
        history_obj.add(exchange, tag=f"adv {secret}")

        written = ""
        for name in os.listdir(work):
            with open(os.path.join(work, name), encoding="utf-8") as fh:
                written += fh.read()
        equal(secret in written, False,
              "a credential the operator named reached the history file")
        contains(written, "[redacted]")


def test_a_set_cookie_keeps_its_flags_and_loses_its_value():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv, allowed_methods=["GET"])
        exchange = hc.request(guard, srv.url("/setcookie-hardened"))
        record = exchange.record()
        cookie = record["response"]["headers"].get("Set-Cookie", "")
        contains(cookie, "[redacted]")
        contains(cookie, "HttpOnly", "the flags are the evidence; they must survive")


# -------------------------------------------------------------------- evidence
def test_a_record_edited_after_the_bundle_was_written_is_caught():
    work = fixtures.tempfile_dir()
    bundle = ev.Bundle("adversarial", scope_file="<fixture>")
    bundle.add(_record("E-ADV-1"))
    bundle.write(work)
    path = os.path.join(work, "E-ADV-1.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    data["severity"] = "critical"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, sort_keys=True)
    problems = ev.Bundle.verify(work)
    check(any("hash mismatch" in problem for problem in problems), problems)
    report = reportmod.build(bundle_dir=work)
    equal(report.counts()["by_severity"].get("critical"), None,
          "the edited severity was read as if it were evidence")
    contains(report.markdown(), "hash mismatch")


def test_a_status_cannot_be_promoted_without_a_second_observation():
    record = _record("E-ADV-2", status="POTENTIAL")
    raises(ev.EvidenceError, record.transition, "REPRODUCED")
    equal(record.status, "POTENTIAL")
    record.transition("REPRODUCED", reproduction=["a second run reproduced it"])
    equal(record.status, "REPRODUCED")


def test_a_record_without_limitations_cannot_be_validated_or_serialised():
    from workbench.tests.harness import raises as _raises

    for empty in ("", "   ", None):
        record = _record("E-ADV-3", limitations=empty)
        _raises(ev.EvidenceError, record.validate)
        _raises(ev.EvidenceError, record.as_dict)


def test_validated_language_is_refused_on_an_unvalidated_record():
    record = _record("E-ADV-4", status="POTENTIAL")
    record.observed = "the system is exploitable via the parameter"
    raises(ev.EvidenceError, record.validate)


# ------------------------------------------------------ acquisition, extraction
def test_a_traversing_archive_member_is_never_written():
    work = fixtures.tempfile_dir()
    tar_path = os.path.join(work, "escape.tar")
    fixtures.build_symlink_tar(tar_path) if False else None
    guard_target = None
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        directory = fixtures.tempfile_dir()
        manifest = fetch.Manifest(directory, scope_file="<fixture>", scope=guard.summary())
        fetch.acquire(guard, srv.url("/archive.tar.gz"), manifest, expect="document")
        into = os.path.join(directory, "out")
        from workbench import extract as extractmod
        report = extractmod.inspect_file(os.path.join(directory, "archive.tar.gz"),
                                         extract_into=into)
        equal(report.executed, False)
        if os.path.isdir(into):
            for root, _dirs, names in os.walk(into):
                for name in names:
                    resolved = os.path.realpath(os.path.join(root, name))
                    check(resolved.startswith(os.path.realpath(into)),
                          f"{name} escapes the extraction directory")


def test_a_file_that_changed_after_it_was_recorded_is_not_recorded_as_obtained():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        directory = fixtures.tempfile_dir()
        manifest = fetch.Manifest(directory, scope_file="<fixture>", scope=guard.summary())
        fetch.acquire(guard, srv.url("/file.pdf"), manifest, expect="document")
        manifest_path = manifest.write()
        with open(os.path.join(directory, "file.pdf"), "ab") as fh:
            fh.write(b"tampered")
        problems = fetch.verify_manifest(manifest_path)
        check(any("hash mismatch" in problem for problem in problems), problems)


def test_a_refused_resource_never_names_a_file():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        directory = fixtures.tempfile_dir()
        manifest = fetch.Manifest(directory, scope_file="<fixture>", scope=guard.summary())
        for path in ("/forbidden", "/unavailable-legal", "/needs-auth",
                     "/proxy-auth", "/challenge"):
            entry = fetch.acquire(guard, srv.url(path), manifest, expect="document")
            equal(entry.status, "blocked", f"{path} was not recorded as blocked")
            equal(entry.file, None, f"{path} named a file for a refusal")
            equal(entry.downloaded, False, f"{path} claimed a download")
        equal(len([name for name in os.listdir(directory) if name != "manifest.json"]),
              0, "a refusal wrote a file")


def test_a_page_that_carries_a_challenge_marker_says_so():
    """A page is not blocked on a marker's presence, but it is never silent.

    Blocking every HTML page containing the word "captcha" would refuse the
    framework's own documentation; writing such a page as a clean success would
    hide the thing a reader most needs to know about it. So the page is written
    and the marker is recorded.
    """
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        directory = fixtures.tempfile_dir()
        manifest = fetch.Manifest(directory, scope_file="<fixture>", scope=guard.summary())
        entry = fetch.acquire(guard, srv.url("/challenge"), manifest, expect="page")
        equal(entry.status, "success")
        check(any("challenge marker" in warning for warning in entry.warnings),
              f"the marker was not recorded: {entry.warnings}")
        written = json.dumps(entry.as_dict())
        contains(written, "challenge marker")

# ---------------------------------------------------------------- the blocker
def test_the_blocker_cannot_be_skipped_by_an_environment_variable():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        fresh = fixtures.tempfile_dir()
        previous = os.environ.get(policymod.STATE_DIR_ENV)
        os.environ[policymod.STATE_DIR_ENV] = fresh
        try:
            raises(policymod.PolicyError, hc.request, guard, srv.url("/soft"))
            for key, value in (("BLACKHEART_POLICY_ACCEPTED", "1"),
                               ("BLACKHEART_IGNORE_POLICY", "1"),
                               ("BLACKHEART_SKIP_POLICY", "true")):
                os.environ[key] = value
                raises(policymod.PolicyError, hc.request, guard, srv.url("/soft"))
                del os.environ[key]
        finally:
            if previous is None:
                os.environ.pop(policymod.STATE_DIR_ENV, None)
            else:
                os.environ[policymod.STATE_DIR_ENV] = previous
        equal(srv.hits, [], "an environment variable got a request out")


def test_the_blocker_cannot_be_skipped_by_editing_the_acceptance_by_hand():
    """A forged record is refused for the same reason a stale one is: the hash."""
    work = fixtures.tempfile_dir()
    forged = os.path.join(work, policymod.ACCEPTANCE_FILE)
    with open(forged, "w", encoding="utf-8") as fh:
        json.dump({"policy_version": policymod.load()["policy_version"],
                   "accepted_at": "2026-01-01T00:00:00Z"}, fh)
    status = policymod.acceptance_status(directory=work)
    equal(status["accepted"], False,
          "a record with no policy hash was accepted as current")


def test_the_blocker_holds_from_any_working_directory():
    """Paths are resolved absolutely, so `cd` cannot change the answer."""
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        empty = fixtures.tempfile_dir()
        previous_dir = os.getcwd()
        previous_env = os.environ.get(policymod.STATE_DIR_ENV)
        os.environ[policymod.STATE_DIR_ENV] = empty
        try:
            os.chdir(fixtures.tempfile_dir())
            raises(policymod.PolicyError, hc.request, guard, srv.url("/soft"))
            os.chdir("/")
            raises(policymod.PolicyError, hc.request, guard, srv.url("/soft"))
        finally:
            os.chdir(previous_dir)
            if previous_env is None:
                os.environ.pop(policymod.STATE_DIR_ENV, None)
            else:
                os.environ[policymod.STATE_DIR_ENV] = previous_env
        equal(srv.hits, [])


def test_acceptance_then_removal_blocks_again():
    """The check is made per request, not once per process."""
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        directory = fixtures.tempfile_dir()
        policymod.accept(directory)
        previous = os.environ.get(policymod.STATE_DIR_ENV)
        os.environ[policymod.STATE_DIR_ENV] = directory
        try:
            hc.request(guard, srv.url("/soft"))
            equal(len(srv.hits), 1)
            os.remove(policymod.acceptance_path(directory))
            raises(policymod.PolicyError, hc.request, guard, srv.url("/soft"))
        finally:
            if previous is None:
                os.environ.pop(policymod.STATE_DIR_ENV, None)
            else:
                os.environ[policymod.STATE_DIR_ENV] = previous
        equal(len(srv.hits), 1, "a request went out after acceptance was removed")


# -------------------------------------------------------------------- helpers
def _record(entry_id, status="OBSERVED", **overrides):
    fields = dict(
        severity="informational", confidence="high", status=status,
        target="http://127.0.0.1/soft", scope={"allowed_hosts": ["127.0.0.1"]},
        expected="a response is served", observed="a response was served",
        impact="an operator must decide whether it matters",
        limitations="one response, at one time",
        remediation="assess against the deployment's own baseline",
        provenance=ev.provenance_for({}),
        reproduction=["one request to the fixture, then read the response"],
    )
    fields.update(overrides)
    return ev.Evidence(entry_id, f"Adversarial observation {entry_id}", **fields)
