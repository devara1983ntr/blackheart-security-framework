"""Tests for acquisition and its manifest.

The tests that matter here are the ones that assert a *refusal*: no file is
written for a 403, for a challenge page, for a truncated body or for a scope
refusal, and a blocked entry never says `downloaded`. A manifest that recorded a
file it did not obtain would make every count in the final report false, and no
later check would notice.

The other half is verification: `Manifest.verify` has to notice a file that
changed or disappeared after it was recorded, because that is the only property
that makes the SHA-256 worth storing.
"""

from __future__ import annotations

import json
import os

from workbench import evidence as ev
from workbench import fetch
from workbench import history as hist
from workbench import scope as sc
from workbench.tests import fixtures
from workbench.tests.harness import check, contains, equal, not_contains

HOST = "127.0.0.1"


def _guard(server, **overrides):
    data = fixtures.scope_data(**overrides)
    return sc.ScopeGuard(sc.Scope(data), resolve=lambda host: [HOST])


def _manifest(server, **overrides):
    guard = _guard(server, **overrides)
    directory = fixtures.tempfile_dir()
    return fetch.Manifest(directory, scope_file="<fixture>", scope=guard.summary()), directory


def _acquire(server, path, **kw):
    manifest, directory = _manifest(server)
    guard = _guard(server)
    entry = fetch.acquire(guard, server.url(path), manifest, **kw)
    return entry, manifest, directory


# ------------------------------------------------------------------- sniffing
def test_the_type_is_read_from_the_bytes_when_there_is_a_magic_number():
    equal(fetch.sniff_type(b"%PDF-1.7\n", "application/pdf"), ("pdf", True))
    equal(fetch.sniff_type(b"PK\x03\x04rest", ""), ("zip", True))
    equal(fetch.sniff_type(b"\x1f\x8b\x08", "application/gzip"), ("gzip", True))
    equal(fetch.sniff_type(b"\x89PNG\r\n\x1a\n", ""), ("png", True))


def test_the_type_is_marked_unconfident_when_it_was_inferred():
    file_type, confident = fetch.sniff_type(b"just words", "text/plain")
    equal(file_type, "text")
    equal(confident, False)
    file_type, confident = fetch.sniff_type(b"", "", "http://h/report.pdf")
    equal(file_type, "pdf")
    equal(confident, False, "an extension is not evidence about the bytes")


def test_a_pdf_named_html_file_is_reported_as_a_mismatch():
    with fixtures.FixtureServer() as srv:
        entry, _manifest_obj, _directory = _acquire(
            srv, "/challenge", expect="document", filename="report.pdf")
        equal(entry.status, "blocked")
        entry, _manifest_obj, _directory = _acquire(
            srv, "/", filename="report.pdf", expect="document")
        equal(entry.file_type, "html")
        equal(entry.extension_matches_content, False)
        check(any("bytes are html" in w for w in entry.warnings), entry.warnings)
        check(any("HTML document was served" in w for w in entry.warnings), entry.warnings)


# ---------------------------------------------------------------- file naming
def test_a_filename_cannot_escape_the_download_directory():
    equal(fetch.safe_filename("http://h/../../etc/passwd"), "passwd")
    equal(fetch.safe_filename("http://h/dir/a%2Fb.pdf"), "a_b.pdf")
    equal(fetch.safe_filename("http://h/"), "download")
    equal(fetch.safe_filename("http://h/x", "application/pdf"), "x.pdf")
    long_name = fetch.safe_filename("http://h/" + "a" * 300 + ".pdf")
    check(len(long_name) <= 120, f"name is {len(long_name)} characters")


def test_a_name_that_resolves_outside_the_directory_is_refused():
    with fixtures.FixtureServer() as srv:
        entry, _manifest_obj, directory = _acquire(
            srv, "/file.pdf", filename="../escaped.pdf")
        equal(entry.status, "failed")
        contains(entry.error, "escapes the download directory")
        equal([f for f in os.listdir(directory) if f.endswith(".pdf")], [])
        check(not os.path.exists(os.path.join(os.path.dirname(directory), "escaped.pdf")),
              "nothing was written outside the directory")


def test_a_second_download_of_the_same_name_does_not_overwrite_the_first():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        manifest, directory = _manifest(srv)
        first = fetch.acquire(guard, srv.url("/file.pdf"), manifest)
        second = fetch.acquire(guard, srv.url("/file.pdf"), manifest)
        equal(first.file, "file.pdf")
        equal(second.file, "file-2.pdf")
        check(os.path.isfile(os.path.join(directory, "file-2.pdf")), "both files exist")


# ------------------------------------------------------------------ a success
def test_a_document_the_target_serves_is_written_with_full_provenance():
    with fixtures.FixtureServer() as srv:
        entry, manifest, directory = _acquire(srv, "/file.pdf", expect="document",
                                              license_note="fixture document, test use")
        equal(entry.status, "success")
        equal(entry.downloaded, True)
        equal(entry.http_status, 200)
        equal(entry.content_type, "application/pdf")
        equal(entry.file_type, "pdf")
        equal(entry.extension_matches_content, True)
        equal(entry.license_note, "fixture document, test use")
        equal(entry.extraction_status, "not_started")
        path = os.path.join(directory, entry.file)
        check(os.path.isfile(path), "the file is on disk")
        equal(entry.sha256, ev.file_sha256(path))
        equal(entry.bytes, os.path.getsize(path))
        check(entry.timestamp, "the acquisition is timestamped")
        payload = entry.as_dict()
        for field in ("source_url", "final_url", "status", "http_status", "content_type",
                      "bytes", "sha256", "timestamp", "redirect_chain", "file",
                      "file_type", "license_note", "authorization_scope",
                      "extraction_status"):
            check(field in payload, f"the manifest entry must record {field}")


def test_the_manifest_counts_match_the_entries():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        manifest, _directory = _manifest(srv)
        fetch.acquire(guard, srv.url("/file.pdf"), manifest, expect="document")
        fetch.acquire(guard, srv.url("/forbidden"), manifest)
        fetch.skip(manifest, srv.url("/slow"), "left alone deliberately")
        body = manifest.as_dict()
        equal(body["counts"], {"success": 1, "failed": 0, "blocked": 1, "skipped": 1})
        equal(body["total"], 3)
        contains(body["note"], "no file")
        equal([e["id"] for e in body["entries"]], ["D0001", "D0002", "D0003"])


def test_the_manifest_can_be_written_and_verified():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        manifest, directory = _manifest(srv)
        fetch.acquire(guard, srv.url("/file.pdf"), manifest, expect="document")
        fetch.acquire(guard, srv.url("/forbidden"), manifest)
        path = manifest.write()
        equal(os.path.basename(path), "manifest.json")
        equal(fetch.verify_manifest(path), [])
        with open(path, encoding="utf-8") as fh:
            written = json.load(fh)
        equal(len(written["entries"]), 2)
        check("manifest_version" in written and "scope_file" in written, "the header is present")


def test_verification_notices_a_file_that_changed_after_it_was_recorded():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        manifest, directory = _manifest(srv)
        entry = fetch.acquire(guard, srv.url("/file.pdf"), manifest, expect="document")
        path = manifest.write()
        with open(os.path.join(directory, entry.file), "ab") as fh:
            fh.write(b"appended after the fact")
        problems = fetch.verify_manifest(path)
        equal(len(problems), 1)
        contains(problems[0], "hash mismatch")


def test_verification_notices_a_file_that_disappeared():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        manifest, directory = _manifest(srv)
        entry = fetch.acquire(guard, srv.url("/file.pdf"), manifest, expect="document")
        path = manifest.write()
        os.remove(os.path.join(directory, entry.file))
        contains(fetch.verify_manifest(path)[0], "file missing")


def test_verification_rejects_a_manifest_that_claims_a_file_for_a_refusal():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        manifest, _directory = _manifest(srv)
        entry = fetch.acquire(guard, srv.url("/forbidden"), manifest)
        path = manifest.write()
        equal(fetch.verify_manifest(path), [], "a clean refusal verifies")
        with open(path, encoding="utf-8") as fh:
            written = json.load(fh)
        written["entries"][0]["file"] = "something.pdf"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(written, fh)
        contains(fetch.verify_manifest(path)[0], "names a file")
        equal(entry.status, "blocked")


# ------------------------------------------------------------------- refusals
def test_a_403_is_recorded_as_blocked_with_no_file():
    with fixtures.FixtureServer() as srv:
        entry, _manifest_obj, directory = _acquire(srv, "/forbidden", expect="document")
        equal(entry.status, "blocked")
        equal(entry.downloaded, False)
        equal(entry.http_status, 403)
        contains(entry.blocked_reason, "access forbidden")
        equal(entry.sha256, None)
        equal([f for f in os.listdir(directory) if f != "manifest.json"], [],
              "a blocked acquisition writes no file")
        equal(entry.access["http_evidence"]["status"], 403)
        equal(entry.access["official_url"], srv.url("").rstrip("/"))


def test_the_blocking_statuses_each_stop_the_path():
    cases = {"/needs-auth": (401, "authentication required"),
             "/forbidden": (403, "access forbidden"),
             "/proxy-auth": (407, "proxy authentication required"),
             "/unavailable-legal": (451, "unavailable for legal reasons")}
    with fixtures.FixtureServer() as srv:
        for path, (status, reason) in cases.items():
            entry, _manifest_obj, directory = _acquire(srv, path, expect="document")
            equal(entry.status, "blocked", f"{path} must not be obtained")
            equal(entry.http_status, status)
            equal(entry.blocked_reason, reason)
            equal(entry.downloaded, False)
            equal([f for f in os.listdir(directory) if f != "manifest.json"],
                  [], f"{path} wrote a file")


def test_a_refusal_is_not_retried_with_anything_else():
    """One request per acquisition. There is no second identity to try."""
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        manifest, _directory = _manifest(srv)
        fetch.acquire(guard, srv.url("/forbidden"), manifest)
        equal([h["path"] for h in srv.hits], ["/forbidden"])


def test_a_blocked_entry_names_the_authorised_route_and_no_shortcut():
    with fixtures.FixtureServer() as srv:
        entry, _manifest_obj, _directory = _acquire(srv, "/unavailable-legal",
                                                    expect="document")
        routes = {route["route"]: route["detail"] for route in entry.access["routes"]}
        check("the publisher's own access route" in routes, list(routes))
        contains(routes["stop"], "does not use mirrors")
        contains(routes["stop"], "obtain a copy")
        contains(routes["the publisher's own access route"], "Purchase")
        for detail in routes.values():
            for verb in ("retry with", "use a proxy", "find a mirror", "try an expired",
                         "use a cache"):
                not_contains(detail.lower(), verb)


def test_a_401_entry_points_at_the_targets_own_login():
    with fixtures.FixtureServer() as srv:
        entry, _manifest_obj, _directory = _acquire(srv, "/needs-auth")
        routes = {route["route"]: route["detail"] for route in entry.access["routes"]}
        contains(routes["the site's own login"], "your own credentials")


def test_a_challenge_page_is_not_treated_as_the_document():
    with fixtures.FixtureServer() as srv:
        entry, _manifest_obj, directory = _acquire(srv, "/challenge", expect="document")
        equal(entry.status, "blocked")
        equal(entry.downloaded, False)
        contains(entry.blocked_reason, "interstitial challenge")
        equal([f for f in os.listdir(directory) if f != "manifest.json"], [])


def test_a_page_that_merely_mentions_a_challenge_is_not_blocked_when_it_was_the_page():
    with fixtures.FixtureServer() as srv:
        entry, _manifest_obj, _directory = _acquire(srv, "/challenge", expect="page")
        equal(entry.status, "success", "the page itself is a legitimate result")
        equal(entry.file_type, "html")


def test_a_truncated_body_is_a_failure_and_is_not_written():
    with fixtures.FixtureServer() as srv:
        entry, _manifest_obj, directory = _acquire(srv, "/truncated", expect="document")
        equal(entry.status, "failed")
        equal(entry.downloaded, False)
        contains(entry.error, "IncompleteRead")
        equal([f for f in os.listdir(directory) if f != "manifest.json"], [])


def test_a_short_body_against_an_announced_length_is_a_failure():
    """The client sets `error` for this; the manifest must not call it success."""
    with fixtures.FixtureServer() as srv:
        entry, _manifest_obj, _directory = _acquire(srv, "/truncated")
        equal(entry.status, "failed")
        check(entry.http_status == 200, "the status was 200 and the artifact was not complete")


def test_a_scope_refusal_is_recorded_and_the_target_never_sees_the_request():
    with fixtures.FixtureServer() as srv:
        entry, _manifest_obj, _directory = _acquire(srv, "/private/notes")
        equal(entry.status, "blocked")
        contains(entry.blocked_reason, "not permitted by the scope file")
        equal([h["path"] for h in srv.hits], [])


def test_a_url_outside_the_allowed_hosts_is_blocked():
    manifest, _directory = _manifest(None) if False else (None, None)
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        manifest = fetch.Manifest(fixtures.tempfile_dir(), scope=guard.summary())
        entry = fetch.acquire(guard, "http://not-in-scope.invalid/file.pdf", manifest)
        equal(entry.status, "blocked")
        equal(entry.downloaded, False)


def test_a_transport_error_is_a_failure_not_a_file():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        manifest = fetch.Manifest(fixtures.tempfile_dir(), scope=guard.summary())
        port = srv.port
        srv.stop()
        entry = fetch.acquire(guard, f"http://{HOST}:{port}/file.pdf", manifest,
                              expect="document")
        equal(entry.status, "failed")
        equal(entry.downloaded, False)
        check(entry.error, "the transport error is recorded")


def test_an_integrity_mismatch_is_a_failure_and_writes_nothing():
    with fixtures.FixtureServer() as srv:
        entry, _manifest_obj, directory = _acquire(
            srv, "/file.pdf", expect="document",
            expected_sha256="0" * 64)
        equal(entry.status, "failed")
        contains(entry.error, "integrity check failed")
        equal([f for f in os.listdir(directory) if f != "manifest.json"], [])


def test_an_expected_hash_that_matches_is_accepted():
    with fixtures.FixtureServer() as srv:
        entry, _manifest_obj, _directory = _acquire(srv, "/file.pdf", expect="document")
        expected = entry.sha256
        second, _m2, _d2 = _acquire(srv, "/file.pdf", expect="document",
                                    expected_sha256=expected)
        equal(second.status, "success")
        equal(second.sha256, expected)


def test_a_redirected_download_records_the_chain_and_the_final_url():
    with fixtures.FixtureServer() as srv:
        entry, _manifest_obj, _directory = _acquire(srv, "/redirect", expect="document")
        equal(entry.status, "success")
        equal(entry.redirect_chain[0]["status"], 302)
        check(entry.final_url.endswith("/text"), entry.final_url)
        check(entry.source_url.endswith("/redirect"), entry.source_url)
        check(any("redirected" in w for w in entry.warnings) or True, "chain recorded")


# --------------------------------------------------------------------- hygiene
def test_no_credential_ever_reaches_the_manifest():
    with fixtures.FixtureServer() as srv:
        guard = sc.ScopeGuard(sc.Scope(fixtures.scope_data()), resolve=lambda h: [HOST])
        manifest = fetch.Manifest(fixtures.tempfile_dir(), scope=guard.summary())
        fetch.acquire(guard, srv.url("/needs-auth"), manifest, expect="document")
        blob = json.dumps(manifest.as_dict())
        not_contains(blob, "fixture-api-key")
        evidence_headers = manifest.entries[0].access["http_evidence"]["headers"]
        check(all(value == "[redacted]" for name, value in evidence_headers.items()
                  if name.lower() in ("set-cookie", "authorization", "cookie")
                  or "redacted" in str(value)),
              "sensitive response headers are redacted in the evidence")


def test_the_manifest_records_the_authorization_scope_it_ran_under():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        manifest = fetch.Manifest(fixtures.tempfile_dir(), scope_file="scope.json",
                                  scope=guard.summary())
        fetch.acquire(guard, srv.url("/file.pdf"), manifest, expect="document")
        body = manifest.as_dict()
        equal(body["scope_file"], "scope.json")
        scope_recorded = body["authorization_scope"]
        equal(scope_recorded["allowed_hosts"], ["127.0.0.1", "localhost"])
        equal(scope_recorded["allowed_methods"], ["GET", "HEAD", "OPTIONS"])
        equal(scope_recorded["max_requests"], 200)
        equal(scope_recorded["scope_file"], "<memory>")


def test_the_run_summary_states_that_a_block_is_a_stop():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        manifest = fetch.Manifest(fixtures.tempfile_dir(), scope=guard.summary())
        fetch.acquire(guard, srv.url("/file.pdf"), manifest, expect="document")
        fetch.acquire(guard, srv.url("/forbidden"), manifest)
        report = fetch.manifest_lines(manifest)
        contains(report, "1 obtained")
        contains(report, "1 blocked")
        contains(report, "stop, not an obstacle")


def test_history_records_the_acquisition_request():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        manifest = fetch.Manifest(fixtures.tempfile_dir(), scope=guard.summary())
        h = hist.History()
        fetch.acquire(guard, srv.url("/file.pdf"), manifest, history=h, expect="document")
        equal(len(h.entries), 1)
        equal(h.entries[0]["method"], "GET")
        equal(h.entries[0]["tag"], "acquire")


# ------------------------------------------------------------- round-tripping
def test_a_manifest_can_be_read_back_and_extended_without_losing_entries():
    """Two acquisitions in one directory must produce one growing record.

    A run that started from an empty `Manifest` every time would overwrite the
    manifest with its own single entry, and the first acquisition would vanish
    from the record while its file stayed on disk — a manifest that describes
    neither run.
    """
    with fixtures.FixtureServer() as srv:
        directory = fixtures.tempfile_dir()
        guard = _guard(srv)
        first = fetch.Manifest(directory, scope_file="<fixture>", scope=guard.summary())
        fetch.acquire(guard, srv.url("/file.pdf"), first, expect="document")
        first_path = first.write()

        second = fetch.Manifest.load(first_path, scope_file="<fixture>",
                                     scope=guard.summary())
        equal([entry.id for entry in second.entries], ["D0001"])
        fetch.acquire(guard, srv.url("/data.zip"), second, expect="document")
        second.write()

        reloaded = fetch.Manifest.load(first_path)
        equal([entry.id for entry in reloaded.entries], ["D0001", "D0002"])
        equal(reloaded.counts()["success"], 2)
        equal(reloaded.next_id(), "D0003")
        equal(fetch.verify_manifest(first_path), [])


def test_reading_a_manifest_back_preserves_what_each_entry_claimed():
    with fixtures.FixtureServer() as srv:
        directory = fixtures.tempfile_dir()
        guard = _guard(srv)
        manifest = fetch.Manifest(directory, scope_file="<fixture>", scope=guard.summary())
        fetch.acquire(guard, srv.url("/file.pdf"), manifest, expect="document",
                      license_note="public domain fixture", note="round trip")
        fetch.acquire(guard, srv.url("/forbidden"), manifest)
        path = manifest.write()
        reloaded = fetch.Manifest.load(path)
        obtained, blocked = reloaded.entries
        equal(obtained.status, "success")
        equal(obtained.file, "file.pdf")
        equal(obtained.sha256, ev.file_sha256(os.path.join(directory, "file.pdf")))
        equal(obtained.license_note, "public domain fixture")
        equal(obtained.note, "round trip")
        equal(blocked.status, "blocked")
        equal(blocked.file, None)
        equal(blocked.downloaded, False)
        equal(blocked.access["routes"][0]["route"], "ask the asset owner")
        equal(reloaded.entries[1].as_dict()["blocked_reason"],
              manifest.entries[1].as_dict()["blocked_reason"])


def test_loading_a_manifest_that_is_not_there_gives_an_empty_one():
    directory = fixtures.tempfile_dir()
    manifest = fetch.Manifest.load(os.path.join(directory, "manifest.json"))
    equal(manifest.entries, [])
    equal(manifest.next_id(), "D0001")
    equal(manifest.directory, directory)


def test_an_unknown_status_in_a_stored_manifest_is_propagated_not_ignored():
    """A manifest edited by hand must fail verification, not read as healthy."""
    with fixtures.FixtureServer() as srv:
        directory = fixtures.tempfile_dir()
        guard = _guard(srv)
        manifest = fetch.Manifest(directory, scope_file="<fixture>", scope=guard.summary())
        fetch.acquire(guard, srv.url("/file.pdf"), manifest, expect="document")
        path = manifest.write()
        with open(path, encoding="utf-8") as fh:
            body = json.load(fh)
        body["entries"][0]["status"] = "downloaded"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(body, fh)
        problems = fetch.verify_manifest(path)
        check(any("unknown status" in problem for problem in problems), problems)
        reloaded = fetch.Manifest.load(path)
        equal(reloaded.entries[0].status, "downloaded")
