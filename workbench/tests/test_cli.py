"""Tests for the command surface.

These are the tests that keep the surface honest. They assert the properties a
reader has to be able to rely on without reading every line:

* every documented command exists, and no command exists that is not documented;
* a command that sends requests refuses to run without a scope file, and no flag
  anywhere in the surface is named after a control it disables;
* `--json` puts one parseable object on stdout and keeps human output on stderr;
* exit codes mean what they say: 0 ran, 1 could not run, 2 misused, 3 refused;
* commands that read local files send nothing, and a command that only plans
  something reaches no network at all — asserted against the fixture server's own
  request log rather than against the tool's own report of what it did.

Everything runs in-process against the local fixture server. Nothing here touches
a network address that is not loopback.
"""

from __future__ import annotations

import contextlib
import io
import json
import os

from workbench import cli
from workbench.tests import fixtures
from workbench.tests.harness import check, contains, equal, not_contains

WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")
FORBIDDEN_FLAG_WORDS = ("ignore", "bypass", "skip", "unsafe", "insecure", "disable")


def _run(*argv):
    """Run the CLI in-process, returning (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main([str(item) for item in argv])
    return code, out.getvalue(), err.getvalue()


def _scope_file(work, base_url="", **overrides):
    """Write a fixture scope file into `work` and return its path."""
    path = os.path.join(work, "scope.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(fixtures.scope_data(base_url, **overrides), fh, indent=2)
    return path


# ------------------------------------------------------------------- surface
def test_the_documented_commands_are_exactly_the_commands_that_exist():
    equal(cli.command_paths(), tuple(sorted(cli.COMMANDS)))
    equal(len(cli.COMMANDS), len(set(cli.COMMANDS)), "a command is listed twice")


def test_no_flag_in_the_surface_is_named_after_a_control_it_switches_off():
    offenders = []
    for flag in _flag_strings(cli.build_parser()):
        for word in FORBIDDEN_FLAG_WORDS:
            if word in flag.lower():
                offenders.append(flag)
    equal(sorted(set(offenders)), [], "a flag name suggests a control can be turned off")


def test_the_help_output_lists_every_command_group():
    code, out, _err = _run("--help")
    equal(code, 0)
    for group in ("scope", "http", "api", "web", "resource", "emergency", "report"):
        contains(out, group)


def _flag_strings(parser):
    """Every option string anywhere in the parser tree."""
    flags = []
    nodes = [parser]
    while nodes:
        node = nodes.pop()
        flags.extend(action.option_strings for action in node._actions)
        group = getattr(node, "_subparsers", None)
        if group is None:
            continue
        for action in group._group_actions:
            nodes.extend((getattr(action, "choices", None) or {}).values())
    return [flag for group in flags for flag in group]


# --------------------------------------------------------------------- scope
def test_every_command_that_sends_a_request_requires_a_scope_file():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        history = os.path.join(work, "h.jsonl")
        for argv in (
            ("http", "inspect", "--url", srv.url("/soft")),
            ("http", "replay", "--history", history, "--id", "H0001"),
            ("http", "fuzz", "--history", history, "--id", "H0001"),
            ("api", "discover", "--url", srv.url("/")),
            ("api", "inspect", "--url", srv.url("/openapi.json")),
            ("web", "crawl", "--url", srv.url("/")),
            ("web", "scan", "--url", srv.url("/soft")),
            ("resource", "download", "--url", srv.url("/file.pdf")),
            ("emergency", "collect", "--url", srv.url("/soft")),
        ):
            code, out, err = _run(*argv)
            equal(code, cli.EXIT_USAGE, f"{' '.join(argv[:2])}: exit code")
            contains(err, "--scope", f"{' '.join(argv[:2])}: says what is missing")
            equal(srv.hits, [], f"{' '.join(argv[:2])}: nothing was requested")


def test_commands_that_read_local_files_do_not_ask_for_a_scope_file():
    work = fixtures.tempfile_dir()
    history = os.path.join(work, "h.jsonl")
    with open(history, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"id": "H0001", "url": "http://127.0.0.1/x", "method": "GET",
                             "request_headers": {}, "response": {"status": 200}}) + "\n")
    for argv in (
        ("http", "diff", "--history", history, "--from", "H0001", "--to", "H0001"),
        ("http", "mutate", "--history", history, "--id", "H0001"),
        ("evidence", "hash", os.path.join(work, "h.jsonl")),
        ("evidence", "manifest", "--directory", work),
        ("report", "generate", "--out", os.path.join(work, "r.md")),
    ):
        code, _out, err = _run(*argv)
        not_contains(err, "--scope", f"{' '.join(argv[:2])} should not need a scope file")


def test_a_scope_file_that_would_disable_a_control_is_refused():
    work = fixtures.tempfile_dir()
    path = os.path.join(work, "scope.json")
    data = fixtures.scope_data()
    data["ignore_scope"] = True
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    code, out, _err = _run("scope", "validate", "--scope", path)
    equal(code, cli.EXIT_USAGE)
    contains(out, "no bypass")


def test_a_target_outside_the_scope_file_is_refused_with_the_scope_exit_code():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = os.path.join(work, "scope.json")
        # A scope that authorises somebody else's host entirely.
        data = fixtures.scope_data()
        data["allowed_hosts"] = ["example.invalid"]
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        code, _out, err = _run("http", "inspect", "--scope", path, "--url", srv.url("/soft"))
        equal(code, cli.EXIT_SCOPE)
        contains(err, "refused")
        equal(srv.hits, [], "a refused request never reaches the target")


def test_a_write_method_is_refused_unless_the_operator_confirms_it():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""), methods=["GET", "POST"])
        history = os.path.join(work, "h.jsonl")
        code, _out, _err = _run("http", "inspect", "--scope", path, "--url", srv.url("/soft"),
                                "--history", history)
        equal(code, cli.EXIT_OK)
        for method in WRITE_METHODS:
            code, _out, err = _run("http", "replay", "--scope", path, "--history", history,
                                   "--id", "H0001", "--method", method)
            equal(code, cli.EXIT_SCOPE, f"{method} without --confirm-write")
        sent = [hit["method"] for hit in srv.hits]
        equal(sent, ["GET"], "only the read was sent")


# ------------------------------------------------------------------- history
def test_two_runs_against_one_history_file_do_not_reuse_ids():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""))
        history = os.path.join(work, "h.jsonl")
        for _ in range(2):
            code, out, _err = _run("http", "inspect", "--scope", path,
                                   "--url", srv.url("/soft"), "--history", history)
            equal(code, cli.EXIT_OK)
        contains(out, "history id    : H0002")
        with open(history, encoding="utf-8") as fh:
            entries = [json.loads(line) for line in fh if line.strip()]
        equal([entry["id"] for entry in entries], ["H0001", "H0002"])


def test_a_credential_passed_on_the_command_line_is_not_written_to_the_history():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""))
        history = os.path.join(work, "h.jsonl")
        token = "fixture-not-a-real-token"
        code, _out, _err = _run("http", "inspect", "--scope", path, "--url", srv.url("/soft"),
                                "--header", f"Authorization: Bearer {token}",
                                "--history", history)
        equal(code, cli.EXIT_OK)
        with open(history, encoding="utf-8") as fh:
            written = fh.read()
        not_contains(written, token, "the token reached the history file")
        contains(written, "[redacted]")
        contains(srv.hits[0]["headers"].get("Authorization", ""), token,
                 "the header was sent as given; the fixture server is the record of that")


def test_mutate_sends_nothing_even_when_asked_to_show_a_request():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""))
        history = os.path.join(work, "h.jsonl")
        _run("http", "inspect", "--scope", path, "--url", srv.url("/json?page=1"),
             "--history", history)
        before = len(srv.hits)
        code, out, _err = _run("http", "mutate", "--history", history, "--id", "H0001",
                               "--apply", "0", "--json")
        equal(code, cli.EXIT_OK)
        equal(len(srv.hits), before, "mutate must not send anything")
        payload = json.loads(out)
        equal(payload["result"]["sent"], 0)
        check(payload["result"]["mutations"], "the catalogue should not be empty")


# --------------------------------------------------------------------- json
def test_json_output_is_one_object_and_human_lines_go_to_stderr():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""))
        code, out, err = _run("http", "inspect", "--scope", path, "--url", srv.url("/soft"),
                              "--json")
        equal(code, cli.EXIT_OK)
        payload = json.loads(out)
        equal(payload["command"], "http inspect")
        equal(payload["status"], "ok")
        equal(payload["exit_code"], 0)
        equal(payload["result"]["record"]["response"]["status"], 200)
        contains(err, "status        : 200", "the human lines moved to stderr")


def test_a_command_that_could_not_run_reports_the_failure_in_its_exit_code():
    work = fixtures.tempfile_dir()
    code, out, _err = _run("evidence", "hash", os.path.join(work, "absent.bin"))
    equal(code, cli.EXIT_FAILED)
    contains(out, "absent.bin", "the human output says which file was not there")


def test_a_missing_history_file_is_a_usage_error_not_a_traceback():
    work = fixtures.tempfile_dir()
    code, _out, err = _run("http", "diff", "--history", os.path.join(work, "nope.jsonl"),
                           "--from", "H0001", "--to", "H0002")
    equal(code, cli.EXIT_USAGE)
    contains(err, "not found")


# ---------------------------------------------------------------- evidence
def test_evidence_manifest_will_not_overwrite_a_manifest_that_is_already_there():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""))
        directory = os.path.join(work, "evidence")
        code, _out, _err = _run("web", "scan", "--scope", path, "--url", srv.url("/soft"),
                                "--out", directory)
        equal(code, cli.EXIT_OK)
        code, _out, err = _run("evidence", "manifest", "--directory", directory)
        equal(code, cli.EXIT_USAGE)
        contains(err, "--out")
        code, out, _err = _run("evidence", "manifest", "--directory", directory, "--verify")
        equal(code, cli.EXIT_OK)
        contains(out, "verified")


def test_evidence_manifest_reports_a_tampered_bundle_through_its_exit_code():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""))
        directory = os.path.join(work, "evidence")
        _run("web", "scan", "--scope", path, "--url", srv.url("/soft"), "--out", directory)
        with open(os.path.join(directory, "manifest.json"), encoding="utf-8") as fh:
            record_id = json.load(fh)["records"][0]["id"]
        with open(os.path.join(directory, f"{record_id}.json"), encoding="utf-8") as fh:
            record = json.load(fh)
        record["observed"] = "edited after the run"
        with open(os.path.join(directory, f"{record_id}.json"), "w", encoding="utf-8") as fh:
            json.dump(record, fh, sort_keys=True)
        code, out, _err = _run("evidence", "manifest", "--directory", directory, "--verify")
        equal(code, cli.EXIT_FAILED)
        contains(out, "hash mismatch")


def test_evidence_hash_reports_a_digest_for_every_file_and_fails_if_one_is_absent():
    work = fixtures.tempfile_dir()
    present = os.path.join(work, "a.txt")
    with open(present, "w", encoding="utf-8") as fh:
        fh.write("fixture bytes")
    code, out, _err = _run("evidence", "hash", present, "--json")
    equal(code, cli.EXIT_OK)
    digest = json.loads(out)["result"]["hashes"][present]["sha256"]
    equal(len(digest), 64)
    code, _out, _err = _run("evidence", "hash", present, os.path.join(work, "missing.txt"))
    equal(code, cli.EXIT_FAILED)


# --------------------------------------------------------------- acquisition
def test_a_download_manifest_accumulates_across_invocations():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""))
        directory = os.path.join(work, "downloads")
        for target in ("/file.pdf", "/data.zip"):
            code, out, _err = _run("resource", "download", "--scope", path,
                                   "--url", srv.url(target), "--out", directory, "--yes")
            equal(code, cli.EXIT_OK, f"{target}: {out}")
        with open(os.path.join(directory, "manifest.json"), encoding="utf-8") as fh:
            manifest = json.load(fh)
        equal([entry["id"] for entry in manifest["entries"]], ["D0001", "D0002"])
        equal(manifest["counts"]["success"], 2)


def test_a_download_plans_before_it_acts_and_sends_nothing_without_confirmation():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""))
        code, out, _err = _run("resource", "download", "--scope", path,
                               "--url", srv.url("/file.pdf"),
                               "--out", os.path.join(work, "downloads"))
        equal(code, cli.EXIT_OK)
        contains(out, "--yes")
        equal(srv.hits, [], "a plan is not a request")


def test_a_blocked_download_is_recorded_with_the_route_that_is_allowed():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""))
        directory = os.path.join(work, "downloads")
        code, out, _err = _run("resource", "download", "--scope", path,
                               "--url", srv.url("/forbidden"), "--out", directory, "--yes")
        equal(code, cli.EXIT_OK, "a refusal is a result, not a failure of the command")
        contains(out, "blocked")
        contains(out, "authorized route")
        with open(os.path.join(directory, "manifest.json"), encoding="utf-8") as fh:
            entry = json.load(fh)["entries"][0]
        equal(entry["downloaded"], False)
        check(entry["file"] is None, "a blocked entry must not name a file")


# ---------------------------------------------------------------- emergency
def test_emergency_collection_is_read_only_and_plans_first():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""))
        directory = os.path.join(work, "emergency")
        code, out, _err = _run("emergency", "collect", "--scope", path,
                               "--url", srv.url("/soft"), "--out", directory)
        equal(code, cli.EXIT_OK)
        contains(out, "GET, HEAD only")
        contains(out, "no writes")
        equal(srv.hits, [], "the plan phase sends nothing")

        code, out, _err = _run("emergency", "collect", "--scope", path,
                               "--url", srv.url("/soft"), "--out", directory, "--yes")
        equal(code, cli.EXIT_OK)
        methods = {hit["method"] for hit in srv.hits}
        equal(methods <= {"GET", "HEAD"}, True, f"methods sent: {sorted(methods)}")
        check(os.path.isfile(os.path.join(directory, "manifest.json")))
        with open(os.path.join(directory, "emergency.json"), encoding="utf-8") as fh:
            collection = json.load(fh)
        equal(collection["summary"]["read_only"], True)


# ---------------------------------------------------------------------- api
def test_api_inspect_reads_a_description_and_calls_none_of_its_operations():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""))
        code, out, _err = _run("api", "inspect", "--scope", path,
                               "--url", srv.url("/openapi.json"))
        equal(code, cli.EXIT_OK)
        contains(out, "none of them was called")
        contains(out, "GET")
        equal([hit["path"] for hit in srv.hits], ["/openapi.json"],
              "only the description itself was requested")


def test_api_inspect_refuses_a_description_format_it_cannot_read():
    work = fixtures.tempfile_dir()
    path = os.path.join(work, "api.yaml")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("openapi: 3.0.0\npaths:\n  /items:\n    get: {}\n")
    code, out, _err = _run("api", "inspect", "--file", path)
    equal(code, cli.EXIT_FAILED)
    contains(out, "not JSON")


# ------------------------------------------------------------------- report
def test_report_generate_writes_markdown_and_json_from_a_supplied_bundle():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""))
        directory = os.path.join(work, "evidence")
        _run("web", "scan", "--scope", path, "--url", srv.url("/soft"), "--out", directory)

        code, out, _err = _run("report", "generate", "--bundle", directory,
                               "--out", os.path.join(work, "report.md"))
        equal(code, cli.EXIT_OK)
        contains(out, "report written")
        with open(os.path.join(work, "report.md"), encoding="utf-8") as fh:
            text = fh.read()
        contains(text, "## What this report does not establish")
        contains(text, "This framework does not bypass authentication, authorization, "
                       "paywalls, DRM, licensing controls, or other access restrictions.")

        code, out, _err = _run("report", "generate", "--bundle", directory,
                               "--out", os.path.join(work, "report.json"))
        equal(code, cli.EXIT_OK)
        with open(os.path.join(work, "report.json"), encoding="utf-8") as fh:
            body = json.load(fh)
        equal(body["counts"]["records"], 2)
        equal(body["verification"]["evidence_bundle"]["problems"], [])


def test_a_report_over_a_bundle_that_was_edited_reports_the_problem():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""))
        directory = os.path.join(work, "evidence")
        _run("web", "scan", "--scope", path, "--url", srv.url("/soft"), "--out", directory)
        with open(os.path.join(directory, "manifest.json"), encoding="utf-8") as fh:
            record_id = json.load(fh)["records"][0]["id"]
        os.remove(os.path.join(directory, f"{record_id}.json"))
        code, out, _err = _run("report", "generate", "--bundle", directory,
                               "--out", os.path.join(work, "report.md"))
        equal(code, cli.EXIT_OK)
        contains(out, "problem(s)")
        contains(out, "record file missing")
        with open(os.path.join(work, "report.md"), encoding="utf-8") as fh:
            text = fh.read()
        contains(text, "record file missing")


def test_a_file_that_changed_after_it_was_recorded_is_refused_before_it_is_read():
    """The hash gate belongs before the parser, not after it.

    Reading first and refusing afterwards produced a report that said the file
    "was not read" while printing the page and member counts that reading it had
    produced. The refusal has to come first, so nothing describes the file.
    """
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        path = _scope_file(work, srv.url(""))
        directory = os.path.join(work, "downloads")
        code, _out, _err = _run("resource", "download", "--scope", path,
                                "--url", srv.url("/data.zip"), "--out", directory, "--yes")
        equal(code, cli.EXIT_OK)
        archive = os.path.join(directory, "data.zip")
        before = os.path.getsize(archive)
        with open(archive, "ab") as fh:
            fh.write(b"tamper")

        into = os.path.join(work, "extracted")
        code, out, _err = _run("resource", "extract", "--out", into, "--json",
                               "--manifest", os.path.join(directory, "manifest.json"))
        equal(code, cli.EXIT_OK, "a refusal is a result, not a failure of the command")
        payload = json.loads(out)
        extraction = payload["result"]["extractions"][0]["extraction"]
        equal(extraction["status"], "refused")
        equal(len(extraction["refusal_reasons"]), 1)
        contains(extraction["refusal_reasons"][0], "does not match the manifest hash")
        equal(extraction["members"], 0, "the archive was not listed")
        equal(extraction["pages"], 0)
        check(os.path.getsize(archive) > before, "the fixture did change the file")
        check(not os.path.exists(into), "nothing was extracted from the changed file")
        with open(os.path.join(directory, "manifest.json"), encoding="utf-8") as fh:
            entry = json.load(fh)["entries"][0]
        equal(entry["extraction_status"], "refused")
