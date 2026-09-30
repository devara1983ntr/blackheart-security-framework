"""The whole chain, once, against the fixture server — including its failures.

Every other module tests a piece. This one runs the sequence an operator would
actually run, with the state passing between commands the way it does in
practice: a scope file, a history file, a downloads directory, an evidence
bundle, a report. The pieces that matter here are the joins — that the crawl's
scope decisions reach the report, that a blocked acquisition does not become a
file, that an extracted archive does not write outside its directory, and that
the deliberate failures stop where they are supposed to stop.

The deliberate failure paths, all asserted:

* a URL outside the scope file: refused, nothing requested, exit code 3;
* a state-changing method without confirmation: refused, exit code 3;
* a resource behind a 403: recorded as blocked with no file written, exit code 0;
* an archive that expands past its ratio: refused with nothing extracted;
* an API description in a format the reader does not parse: exit code 1;
* an evidence bundle edited after the run: reported as a problem in the report,
  and its records are still counted for what they are.

Throughout, the fixture server's own request log is the record of what was sent:
the test asserts on the server's view, not on the tool's account of itself.
"""

from __future__ import annotations

import contextlib
import io
import json
import os

from workbench import cli
from workbench.tests import fixtures
from workbench.tests.harness import check, contains, equal, not_contains


def _run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main([str(item) for item in argv])
    return code, out.getvalue(), err.getvalue()


def test_the_whole_chain_from_scope_file_to_report():
    work = fixtures.tempfile_dir()
    scope_path = os.path.join(work, "scope.json")
    history_path = os.path.join(work, "run", "history.jsonl")
    downloads = os.path.join(work, "run", "downloads")
    extracted = os.path.join(work, "run", "extracted")
    evidence_dir = os.path.join(work, "run", "evidence")
    emergency_dir = os.path.join(work, "run", "emergency")
    report_path = os.path.join(work, "run", "report.md")

    with fixtures.FixtureServer() as srv:
        with open(scope_path, "w", encoding="utf-8") as fh:
            json.dump(fixtures.scope_data(srv.url(""), max_requests=120), fh, indent=2)

        # 1. The scope file is checked before anything uses it.
        code, out, _err = _run("scope", "validate", "--scope", scope_path)
        equal(code, cli.EXIT_OK)
        contains(out, "valid: yes")
        contains(out, "there is no bypass")
        equal(srv.hits, [], "validating a scope file contacts nobody")

        # 2. Discovery, within caps. The fixture page links to another host and
        #    the sitemap lists an excluded path: both must be recorded, not tried.
        code, out, _err = _run("web", "crawl", "--scope", scope_path,
                               "--url", srv.url("/"), "--max-pages", "10",
                               "--max-depth", "2", "--budget", "25")
        equal(code, cli.EXIT_OK)
        contains(out, "not followed")
        fetched = [hit["path"] for hit in srv.hits]
        equal(any("example.invalid" in path for path in fetched), False,
              "an out-of-scope link was not followed")
        equal("/private/notes" in fetched, False,
              "an excluded path was not requested")
        equal(len(fetched), len(set(fetched)), "each published path was asked once")

        # 3. A request recorded by hand, then a bounded fuzz over it.
        code, out, _err = _run("http", "inspect", "--scope", scope_path,
                               "--url", srv.url("/json?page=1"), "--history", history_path)
        equal(code, cli.EXIT_OK)
        contains(out, "history id    : H0001")

        code, out, _err = _run("http", "mutate", "--history", history_path, "--id", "H0001")
        equal(code, cli.EXIT_OK)
        contains(out, "none of them is sent by this command")

        before = len(srv.hits)
        code, out, _err = _run("http", "fuzz", "--scope", scope_path,
                               "--history", history_path, "--id", "H0001",
                               "--limit", "6", "--budget", "8")
        equal(code, cli.EXIT_OK)
        sent = len(srv.hits) - before
        check(sent <= 8, f"the fuzz run sent {sent} requests, over its budget")

        # 4. Observable checks over responses, written as an evidence bundle.
        code, out, _err = _run("web", "scan", "--scope", scope_path,
                               "--url", srv.url("/soft"), "--out", evidence_dir)
        equal(code, cli.EXIT_OK)
        contains(out, "records are observations; none of them is a validated finding")

        # 5. Acquisition: one published document, and one refused resource.
        code, out, _err = _run("resource", "download", "--scope", scope_path,
                               "--url", srv.url("/file.pdf"), "--out", downloads,
                               "--license", "fixture, not a real licence", "--yes")
        equal(code, cli.EXIT_OK)
        contains(out, "success")

        code, out, _err = _run("resource", "download", "--scope", scope_path,
                               "--url", srv.url("/forbidden"), "--out", downloads, "--yes")
        equal(code, cli.EXIT_OK, "a refusal is a result")
        contains(out, "blocked")
        contains(out, "authorized route")

        manifest_path = os.path.join(downloads, "manifest.json")
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
        equal([entry["status"] for entry in manifest["entries"]], ["success", "blocked"])
        equal(manifest["entries"][1]["file"], None)
        equal(os.path.isfile(os.path.join(downloads, "file.pdf")), True)
        equal(len([name for name in os.listdir(downloads) if name != "manifest.json"]), 1,
              "the refused resource left no file behind")

        # 6. Reading what was obtained, and refusing what expands too far.
        code, _out, _err = _run("resource", "extract", "--manifest", manifest_path,
                                "--out", extracted)
        equal(code, cli.EXIT_OK)
        with open(manifest_path, encoding="utf-8") as fh:
            updated = json.load(fh)
        equal(updated["entries"][0]["extraction_status"], "extracted")
        equal(updated["entries"][1]["extraction_status"], "not_started",
              "a blocked entry is never read")

        code, out, _err = _run("resource", "download", "--scope", scope_path,
                               "--url", srv.url("/bomb.zip"), "--out", downloads, "--yes")
        equal(code, cli.EXIT_OK)
        code, out, _err = _run("resource", "extract", "--manifest", manifest_path,
                               "--id", "D0003")
        equal(code, cli.EXIT_OK)
        contains(out, "refused")
        members = os.listdir(extracted) if os.path.isdir(extracted) else []
        check(not [name for name in members if name.startswith("bomb")],
              "a refused archive wrote nothing")

        # 7. A read-only emergency collection.
        code, out, _err = _run("emergency", "collect", "--scope", scope_path,
                               "--url", srv.url("/soft"), "--out", emergency_dir, "--yes")
        equal(code, cli.EXIT_OK)
        with open(os.path.join(emergency_dir, "emergency.json"), encoding="utf-8") as fh:
            collection = json.load(fh)
        equal(collection["summary"]["read_only"], True)
        equal(collection["summary"]["methods_sent"], ["GET", "HEAD"])
        contains(collection["summary"]["note"], "It is not an assessment")

        # 8. Every bundle verifies before the report is written.
        code, out, _err = _run("evidence", "manifest", "--directory", evidence_dir,
                               "--verify")
        equal(code, cli.EXIT_OK)
        contains(out, "verified")

        # 9. The report: counts derived from the records, and the blocked path
        #    carried through with the route that is authorised.
        code, out, _err = _run("report", "generate", "--bundle", evidence_dir,
                               "--manifest", manifest_path, "--scope", scope_path,
                               "--out", report_path, "--title", "Fixture run")
        equal(code, cli.EXIT_OK)
        with open(report_path, encoding="utf-8") as fh:
            report = fh.read()
        contains(report, "# Fixture run")
        contains(report, "- Evidence records: 2")
        contains(report, "- Validated (REPRODUCED): 0")
        contains(report, "- Not validated (POTENTIAL or UNVERIFIED): 0")
        contains(report, "- Obtained: 2")
        contains(report, "- Blocked: 1")
        contains(report, "### Blocked paths, and the authorised route")
        contains(report, "This framework does not bypass authentication, authorization, "
                         "paywalls, DRM, licensing controls, or other access restrictions.")
        not_contains(report, "vulnerable", "no record may be promoted to a claim")

        # 10. Deliberate failure paths.
        code, _out, err = _run("http", "inspect", "--scope", scope_path,
                               "--url", "https://not-in-scope.invalid/")
        equal(code, cli.EXIT_SCOPE)
        contains(err, "refused")

        # A write method is refused twice over: once because the scope does not
        # allow it, and once because nobody confirmed it.
        code, _out, err = _run("http", "replay", "--scope", scope_path,
                               "--history", history_path, "--id", "H0001",
                               "--method", "POST")
        equal(code, cli.EXIT_SCOPE)
        contains(err, "refused")

        permissive = os.path.join(work, "scope-write.json")
        with open(permissive, "w", encoding="utf-8") as fh:
            json.dump(fixtures.scope_data(srv.url(""),
                                          methods=["GET", "HEAD", "POST"]), fh)
        before = len(srv.hits)
        code, _out, err = _run("http", "replay", "--scope", permissive,
                               "--history", history_path, "--id", "H0001",
                               "--method", "POST")
        equal(code, cli.EXIT_SCOPE)
        contains(err, "changes state")
        equal(len(srv.hits), before, "the unconfirmed write was never sent")

        yaml_path = os.path.join(work, "api.yaml")
        with open(yaml_path, "w", encoding="utf-8") as fh:
            fh.write("openapi: 3.0.0\n")
        code, _out, _err = _run("api", "inspect", "--file", yaml_path)
        equal(code, cli.EXIT_FAILED)

        code, _out, _err = _run("evidence", "hash", os.path.join(work, "absent.bin"))
        equal(code, cli.EXIT_FAILED)

        # 11. A bundle edited after the run is reported, not silently used.
        with open(os.path.join(evidence_dir, "manifest.json"), encoding="utf-8") as fh:
            record_id = json.load(fh)["records"][0]["id"]
        record_path = os.path.join(evidence_dir, f"{record_id}.json")
        with open(record_path, encoding="utf-8") as fh:
            record = json.load(fh)
        record["observed"] = "edited after the run"
        with open(record_path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, sort_keys=True)
        code, out, _err = _run("report", "generate", "--bundle", evidence_dir,
                               "--out", report_path)
        equal(code, cli.EXIT_OK)
        contains(out, "problem(s)")
        with open(report_path, encoding="utf-8") as fh:
            tampered = fh.read()
        contains(tampered, "hash mismatch")

        # The record of what was sent, across the whole chain: reads only, and
        # every one of them a path on the fixture server.
        methods = sorted({hit["method"] for hit in srv.hits})
        equal([method for method in methods if method not in ("GET", "HEAD")], [],
              f"a method that changes state reached the target: {methods}")
        for hit in srv.hits:
            check(hit["path"].startswith("/"), hit["path"])
        check(len(srv.hits) > 10, f"the chain sent {len(srv.hits)} requests in total")
