"""The command surface.

    blackheart scope     validate
    blackheart http      inspect | replay | diff | mutate | fuzz
    blackheart api       discover | inspect
    blackheart web       crawl | scan
    blackheart resource  inspect | download | extract
    blackheart evidence  hash | manifest
    blackheart emergency collect
    blackheart report    generate

House rules, applied to every command in that list:

* **`--scope` is required for anything that sends a request.** There is no
  default scope, no in-memory bypass, and no flag that skips the check. A
  command that would send traffic without an authorisation file exits with the
  scope exit code instead. `http diff`, `http mutate`, `resource inspect`,
  `resource extract`, `evidence hash`, `evidence manifest` and `report generate`
  read local files only and take no scope.
* **Safe defaults, bounded execution.** Every command that can send many requests
  takes `--budget`, `--limit`, `--max-pages` or `--max-depth`, with a
  conservative default. `resource download` and `emergency collect` show what
  they will do and do nothing until `--yes` is given.
* **Structured output.** `--json` prints one JSON object on stdout: the command,
  its status, its exit code and its payload. Human-readable lines go to stderr
  in that mode, so a pipeline parses stdout without filtering progress text.
* **Deterministic exit codes.** 0 ran and produced output; 1 could not run; 2 the
  arguments were wrong; 3 the scope file refused something. A command that
  observes something worrying and reports it exits 0: the exit code says whether
  the command ran, not whether the target looked healthy.

Nothing here writes credentials, and no flag is named as if it skipped a control.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import checks
from . import diff as diffmod
from . import discover as discovermod
from . import emergency as emergencymod
from . import evidence as ev
from . import extract as extractmod
from . import fetch as fetchmod
from . import fuzz as fuzzmod
from . import history as hist
from . import http_client as hc
from . import mutate as mutatemod
from . import report as reportmod
from . import scope as sc

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_SCOPE = 3

PROGRAM = "blackheart"

#: The documented surface, and the list `command_paths()` is checked against so
#: that a command cannot exist in the code and be missing from the documentation
#: (or the other way round).
COMMANDS = (
    ("scope", "validate"),
    ("http", "inspect"), ("http", "replay"), ("http", "diff"),
    ("http", "mutate"), ("http", "fuzz"),
    ("api", "discover"), ("api", "inspect"),
    ("web", "crawl"), ("web", "scan"),
    ("resource", "inspect"), ("resource", "download"), ("resource", "extract"),
    ("evidence", "hash"), ("evidence", "manifest"),
    ("emergency", "collect"),
    ("report", "generate"),
)


class Usage(Exception):
    """An argument problem, reported as a usage error rather than a traceback."""


class Result:
    """What a command produced: a payload, human lines and an exit code."""

    def __init__(self, command, payload=None, lines=(), exit_code=EXIT_OK):
        self.command = command
        self.payload = payload or {}
        self.lines = list(lines)
        self.exit_code = exit_code

    def as_dict(self):
        return {
            "command": self.command,
            "tool": "blackheart-workbench",
            "tool_version": ev.provenance_for({})["tool_version"],
            "status": "ok" if self.exit_code == EXIT_OK else "failed",
            "exit_code": self.exit_code,
            "result": self.payload,
        }


# ------------------------------------------------------------------ plumbing
def _guard(args):
    """Load the scope file and build a guard. The only way a command gets one."""
    scope_path = getattr(args, "scope", None)
    if not scope_path:
        raise Usage(f"{args.command_name} sends requests and requires --scope <file>")
    try:
        return sc.ScopeGuard(sc.load_scope(scope_path))
    except FileNotFoundError:
        raise Usage(f"scope file not found: {scope_path}") from None
    except sc.ScopeError as exc:
        raise Usage(f"the scope file was refused: {exc}") from None


def _open_history(path, secrets=(), *, create=True):
    """Open a history file for reading and appending.

    `History.load` sets the next id from what is already on disk; assigning the
    path afterwards makes `add` append to the same file. Loading and appending
    through two separate objects is how a run ends up reusing ids.

    `create=False` is for the commands that read a history: a mistyped path must
    be an error, because an empty history and an absent file otherwise look
    identical to the operator.
    """
    if not path:
        return hist.History(secrets=secrets), None
    try:
        history_obj = hist.History.load(path, secrets=secrets)
    except FileNotFoundError:
        if not create:
            raise Usage(f"history file not found: {path}") from None
        return hist.History(path=path, secrets=secrets), path
    history_obj.path = path
    return history_obj, path


def _needs_history(args):
    path = getattr(args, "history", None)
    if not path:
        raise Usage(f"{args.command_name} needs --history <file>")
    return _open_history(path, secrets=list(getattr(args, "secret", None) or []),
                         create=False)


def _record_by_id(history_obj, entry_id):
    record = history_obj.get(entry_id) if entry_id else history_obj.last()
    if record is None:
        raise Usage(f"no history entry {entry_id!r} in {history_obj.path or 'the history'}")
    return record


def _headers(args):
    headers = {}
    for item in getattr(args, "header", None) or []:
        if ":" not in item:
            raise Usage(f"--header expects 'Name: value', got {item!r}")
        name, _, value = item.partition(":")
        headers[name.strip()] = value.strip()
    return headers


def _write(path, content):
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def _emit(result, args):
    if getattr(args, "json", False):
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
        for line in result.lines:
            print(line, file=sys.stderr)
    else:
        for line in result.lines:
            print(line)
        if result.exit_code != EXIT_OK:
            print(f"exit {result.exit_code}", file=sys.stderr)
    return result.exit_code


# -------------------------------------------------------------------- scope
def cmd_scope_validate(args):
    try:
        scope_obj = sc.load_scope(args.scope)
    except FileNotFoundError:
        raise Usage(f"scope file not found: {args.scope}") from None
    except sc.ScopeError as exc:
        return Result("scope validate",
                      {"scope_file": args.scope, "valid": False, "reason": str(exc)},
                      [f"scope file refused: {exc}"], EXIT_USAGE)
    summary = sc.ScopeGuard(scope_obj).summary()
    lines = [f"scope file: {args.scope}", "valid: yes"]
    for key in sorted(summary):
        lines.append(f"  {key}: {summary[key]}")
    lines.append("  there is no bypass: every request is checked against this file")
    return Result("scope validate",
                  {"scope_file": args.scope, "valid": True, "summary": summary}, lines)


# --------------------------------------------------------------------- http
def cmd_http_inspect(args):
    guard = _guard(args)
    history_obj, _path = _open_history(getattr(args, "history", None),
                                       secrets=list(getattr(args, "secret", None) or []))
    exchange = hc.request(guard, args.url, args.method, headers=_headers(args),
                          timeout=args.timeout, note="cli:inspect")
    entry_id = history_obj.add(exchange, tag="cli:inspect")
    record = history_obj.get(entry_id)
    response = record.get("response") or {}
    lines = [f"{args.method} {record['url']}",
             f"  history id    : {entry_id}",
             f"  status        : {str(response.get('status'))} "
             f"{response.get('reason') or ''}".rstrip(),
             f"  final url     : {record.get('final_url')}",
             f"  content type  : {response.get('content_type')}",
             f"  bytes         : {response.get('bytes')}",
             f"  elapsed ms    : {response.get('elapsed_ms')}",
             f"  scope decision: {(record.get('scope_decision') or {}).get('rule')}"]
    if response.get("error"):
        lines.append(f"  error         : {response['error']}")
    for name, value in (response.get("headers") or {}).items():
        lines.append(f"  header        : {name}: {value}")
    for hop in record.get("redirect_chain") or []:
        lines.append(f"  redirect      : {hop['status']} -> {hop['location']}")
    if not history_obj.path:
        lines.append("  note          : no --history given, so this exchange is not on disk")
    return Result("http inspect",
                  {"record": record, "history_id": entry_id,
                   "history_path": history_obj.path}, lines)


def cmd_http_replay(args):
    guard = _guard(args)
    history_obj, _path = _needs_history(args)
    original = _record_by_id(history_obj, args.id)
    entry_id, exchange = hist.replay_from_record(
        guard, history_obj, args.id, headers=_headers(args), body=args.body,
        method=args.method, confirm_write=bool(args.confirm_write),
        tag="cli:replay", timeout=args.timeout)
    record = history_obj.get(entry_id)
    comparison = diffmod.compare_records(original, record)
    response = record.get("response") or {}
    lines = [f"replayed {args.id} as {entry_id}",
             f"  status        : {response.get('status')}",
             f"  differences   : {comparison['difference_count']} section(s) against {args.id}",
             f"  interpretation: {comparison['interpretation']}"]
    return Result("http replay",
                  {"source_id": args.id, "history_id": entry_id, "record": record,
                   "difference": comparison}, lines)


def cmd_http_diff(args):
    history_obj, _path = _needs_history(args)
    first = _record_by_id(history_obj, args.from_id)
    second = _record_by_id(history_obj, args.to_id)
    result = diffmod.compare_records(first, second)
    lines = [f"comparing {first.get('id')} against {second.get('id')}",
             f"  differences   : {result['difference_count']} section(s)",
             f"  interpretation: {result['interpretation']}"]
    lines.extend(diffmod.as_text(result).splitlines())
    return Result("http diff", result, lines)


def cmd_http_mutate(args):
    history_obj, _path = _needs_history(args)
    record = _record_by_id(history_obj, args.id)
    kinds = [kind.strip() for kind in args.kinds.split(",")] if args.kinds else None
    mutations = mutatemod.catalogue(record, kinds)
    lines = [f"{len(mutations)} mutation(s) for {record.get('id')}",
             "  none of them is sent by this command"]
    for index, mutation in enumerate(mutations):
        payload = mutation.as_dict()
        lines.append(f"  [{index:02d}] {payload['kind']:12} {payload['target']:22} "
                     f"{payload['mode']:7} {payload['note']}")
    if args.apply is not None:
        if args.apply < 0 or args.apply >= len(mutations):
            raise Usage(f"--apply must be between 0 and {len(mutations) - 1}")
        url, method, headers, body, conflict = mutatemod.apply(record, mutations[args.apply])
        if conflict:
            lines.append(f"  mutation {args.apply} cannot be applied: {conflict}")
        else:
            lines.append(f"  mutation {args.apply} would send:")
            lines.append(f"    {method} {url}")
            for name, value in headers.items():
                lines.append(f"    {name}: {value}")
            if body:
                lines.append(f"    body: {body}")
    write_verbs = mutatemod.state_changing_methods(record)
    if write_verbs:
        lines.append(f"  write verbs that would need a deliberate decision: "
                     f"{', '.join(write_verbs)}")
    return Result("http mutate",
                  {"mutations": [m.as_dict() for m in mutations],
                   "write_verbs_not_generated": write_verbs, "sent": 0}, lines)


def cmd_http_fuzz(args):
    guard = _guard(args)
    history_obj, _path = _needs_history(args)
    record = _record_by_id(history_obj, args.id)
    kinds = [kind.strip() for kind in args.kinds.split(",")] if args.kinds else None
    state = fuzzmod.run(guard, record, kinds=kinds, budget=args.budget, limit=args.limit,
                        history=history_obj, tag="cli:fuzz",
                        allow_state_changing=bool(args.confirm_write))
    lines = [fuzzmod.report_lines(state)]
    return Result("http fuzz",
                  {"summary": state.summary(),
                   "results": [result.as_dict() for result in state.results]}, lines)


# ---------------------------------------------------------------------- api
def cmd_api_discover(args):
    guard = _guard(args)
    history_obj, _path = _open_history(getattr(args, "history", None),
                                       secrets=list(getattr(args, "secret", None) or []))
    discovery = discovermod.discover(guard, args.url, history=history_obj,
                                     max_pages=args.max_pages, max_depth=args.max_depth,
                                     budget=args.budget)
    documents = [f for f in discovery.findings if f.kind == "api-description"]
    graphql = discovermod.graphql_references(discovery)
    lines = ["API description documents found:" if documents else
             "No API description document was found at the conventional paths."]
    for finding in documents:
        operations = (finding.detail or {}).get("operations") or []
        lines.append(f"  {finding.url} (status {finding.status})")
        lines.append(f"    declares {len(operations)} operation(s)")
        for operation in operations[:50]:
            lines.append(f"      {operation['method']:6} {operation['path']}"
                         f"{' [write]' if operation['declares_write'] else ''}")
    if graphql:
        lines.append("  GraphQL endpoints the target referenced:")
        for url in graphql:
            lines.append(f"    {url} (referenced, not queried)")
    lines.append("  no operation found this way was called")
    return Result("api discover",
                  {"discovery": discovery.summary(),
                   "api_documents": [f.as_dict() for f in documents],
                   "graphql_references": graphql}, lines)


def cmd_api_inspect(args):
    if bool(args.url) == bool(args.file):
        raise Usage("api inspect takes exactly one of --url or --file")
    text, source, status = "", "", None
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            text = fh.read()
        source = args.file
    else:
        guard = _guard(args)
        history_obj, _path = _open_history(getattr(args, "history", None),
                                           secrets=list(getattr(args, "secret", None) or []))
        exchange = hc.request(guard, args.url, "GET", note="cli:api-inspect")
        entry_id = history_obj.add(exchange, tag="cli:api-inspect")
        record = history_obj.get(entry_id)
        status = (record.get("response") or {}).get("status")
        text = (record.get("response") or {}).get("body_text") or ""
        source = args.url
    try:
        document = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return Result("api inspect", {"source": source, "parsed": False},
                      [f"{source}: not JSON, so no operations were read",
                       "  a YAML description is not parsed by this reader"],
                      EXIT_FAILED)
    parsed = discovermod.parse_openapi(document)
    lines = [f"{source}" + (f" (status {status})" if status else ""),
             f"  format        : {parsed['version'] or 'unrecognised'}",
             f"  operations    : {len(parsed['operations'])}",
             "  none of them was called"]
    for operation in parsed["operations"]:
        lines.append(f"    {operation['method']:6} {operation['path']}"
                     f"{' [write]' if operation['declares_write'] else ''}"
                     f"{' [auth]' if operation['declares_auth'] else ''}")
    if parsed["servers"]:
        lines.append(f"  declared servers: {', '.join(parsed['servers'])}")
        lines.append("  those servers were not contacted")
    return Result("api inspect",
                  {"source": source, "http_status": status, "parsed": parsed["valid"],
                   "openapi": parsed},
                  lines, EXIT_OK if parsed["valid"] else EXIT_FAILED)


# ---------------------------------------------------------------------- web
def cmd_web_crawl(args):
    guard = _guard(args)
    history_obj, _path = _open_history(getattr(args, "history", None),
                                       secrets=list(getattr(args, "secret", None) or []))
    discovery = discovermod.discover(guard, args.url, history=history_obj,
                                     max_pages=args.max_pages, max_depth=args.max_depth,
                                     budget=args.budget, include_assets=not args.no_assets)
    return Result("web crawl",
                  {"discovery": discovery.summary(),
                   "findings": [f.as_dict() for f in discovery.findings],
                   "refused": discovery.refused,
                   "not_followed": discovery.not_followed},
                  [discovery.report_lines()])


def cmd_web_scan(args):
    """Capture the given URLs and run the observable checks over the responses."""
    guard = _guard(args)
    history_obj, _path = _open_history(getattr(args, "history", None),
                                       secrets=list(getattr(args, "secret", None) or []))
    bundle = ev.Bundle("web-scan", scope_file=args.scope)
    urls = [args.url] + list(args.extra_url or [])
    for url in urls:
        exchange = hc.request(guard, url, "GET", note="cli:scan")
        history_obj.add(exchange, tag="cli:scan")
    produced = checks.run_checks(history_obj.entries, bundle=bundle,
                                 scope_summary=guard.summary())
    directory = args.out or os.path.join(os.getcwd(), "evidence")
    manifest = bundle.write(directory)
    lines = [f"{len(urls)} response(s), {len(produced)} record(s)",
             "  records are observations; none of them is a validated finding"]
    for record in produced:
        lines.append(f"  {record.status:10} {record.severity:13} {record.id:26} "
                     f"{record.title[:60]}")
    lines.append(f"  written to {directory}: {manifest['count']} record(s), "
                 f"manifest {manifest['manifest_sha256'][:12]}...")
    if len(urls) < 3:
        lines.append("  note: a handful of responses is a spot check, not coverage")
    return Result("web scan",
                  {"urls": urls, "records": [r.as_dict() for r in produced],
                   "counts": manifest["by_status"], "directory": directory}, lines)


# ----------------------------------------------------------------- resource
def cmd_resource_inspect(args):
    limits_used = extractmod.limits(max_bytes=args.max_bytes, max_depth=args.max_depth)
    report_obj = extractmod.inspect_file(args.path, limits_used,
                                         quarantine_dir=args.quarantine)
    return Result("resource inspect", report_obj.as_dict(), report_obj.report_lines())


def cmd_resource_download(args):
    guard = _guard(args)
    history_obj, _path = _open_history(getattr(args, "history", None),
                                       secrets=list(getattr(args, "secret", None) or []))
    directory = args.out or os.path.join(os.getcwd(), "downloads")
    manifest_path = os.path.join(directory, "manifest.json")
    # A second acquisition must extend the record, not replace it: the manifest is
    # the only account of what was asked for and what came back.
    manifest = fetchmod.Manifest.load(manifest_path, directory=directory,
                                      scope_file=args.scope, scope=guard.summary())
    prior = len(manifest.entries)
    if not args.yes:
        return Result("resource download",
                      {"planned": True, "url": args.url, "directory": directory,
                       "requests": 1},
                      [f"plan: one GET to {args.url}",
                       f"  saved under: {directory}",
                       f"  expect     : {args.expect}",
                       f"  a 401, 402, 403, 407 or 451 ends the path and no file is written",
                       "  re-run with --yes to perform it"])
    entry = fetchmod.acquire(guard, args.url, manifest, history=history_obj,
                             expected_sha256=args.sha256,
                             license_note=args.license or "", note=args.note or "",
                             expect=args.expect, allow_partial=bool(args.allow_partial))
    manifest_path = manifest.write()
    problems = fetchmod.verify_manifest(manifest_path)
    lines = [entry.summary_line(), f"  manifest: {manifest_path}",
             f"  verified: {'clean' if not problems else problems}"]
    if prior:
        lines.append(f"  this manifest already held {prior} acquisition(s); "
                     f"the new entry is {entry.id}")
    if entry.status == "blocked":
        for route in (entry.access or {}).get("routes", []):
            lines.append(f"  authorized route: {route['route']}: {route['detail']}")
    exit_code = EXIT_SCOPE if (entry.status == "blocked"
                               and "scope" in (entry.blocked_reason or "")) else EXIT_OK
    return Result("resource download",
                  {"entry": entry.as_dict(), "manifest": manifest_path,
                   "verification": problems}, lines, exit_code)


def cmd_resource_extract(args):
    with open(args.manifest, encoding="utf-8") as fh:
        manifest_data = json.load(fh)
    directory = os.path.dirname(os.path.abspath(args.manifest))
    wanted = [entry for entry in manifest_data.get("entries", [])
              if entry.get("status") == "success" and (not args.id or entry.get("id") == args.id)]
    if not wanted:
        raise Usage("no successful acquisition in this manifest matches")
    limits_used = extractmod.limits(max_bytes=args.max_bytes, max_depth=args.max_depth)
    lines, results = [], []
    for entry in wanted:
        path = os.path.join(directory, entry["file"])
        digest = ev.file_sha256(path)
        if not entry.get("sha256") or digest != entry["sha256"]:
            # The hash is checked before the file is parsed. Reading first and
            # refusing afterwards meant the page and member counts in the report
            # came from a file the manifest did not describe — the report said
            # "was not read" while showing what had been read out of it.
            report_obj = extractmod.Extraction(
                path, entry.get("file_type") or "unknown", os.path.getsize(path),
                limits_used)
            report_obj.sha256 = digest
            report_obj.refuse(
                f"the file on disk does not match the manifest hash: the manifest "
                f"records {str(entry.get('sha256'))[:12]}... and the file is "
                f"{digest[:12]}...")
            report_obj.notes.append("not parsed: the manifest does not describe this file")
        else:
            report_obj = extractmod.inspect_file(path, limits_used, extract_into=args.out)
        entry["extraction_status"] = extractmod.extraction_status(report_obj)
        results.append({"id": entry["id"], "file": entry["file"],
                        "extraction": report_obj.summary()})
        lines.append(report_obj.report_lines())
        lines.append("")
    manifest_path = _write(args.manifest,
                           json.dumps(manifest_data, indent=2, sort_keys=True))
    lines.append(f"manifest updated: {manifest_path}")
    lines.append("  a file whose hash no longer matches the manifest was not read")
    return Result("resource extract",
                  {"extractions": results, "manifest": manifest_path}, lines)


# ---------------------------------------------------------------- evidence
def cmd_evidence_hash(args):
    hashes, lines = {}, []
    for path in args.path:
        if not os.path.isfile(path):
            lines.append(f"{path}: not a file")
            continue
        digest = ev.file_sha256(path)
        hashes[path] = {"sha256": digest, "bytes": os.path.getsize(path)}
        lines.append(f"{digest}  {os.path.getsize(path):>10}  {path}")
    exit_code = EXIT_OK if len(hashes) == len(args.path) else EXIT_FAILED
    return Result("evidence hash", {"hashes": hashes}, lines, exit_code)


def cmd_evidence_manifest(args):
    if args.verify:
        problems = ev.Bundle.verify(args.directory)
        lines = [f"{args.directory}: "
                 f"{'verified, every record hashes to what the manifest says' if not problems else 'problems found'}"]
        lines.extend(f"  {problem}" for problem in problems)
        return Result("evidence manifest",
                      {"directory": args.directory, "problems": problems}, lines,
                      EXIT_OK if not problems else EXIT_FAILED)
    if not os.path.isdir(args.directory):
        raise Usage(f"not a directory: {args.directory}")
    target_path = args.out or os.path.join(args.directory, "manifest.json")
    if not args.out and os.path.exists(target_path):
        # Bundle and download manifests are written by the run that produced
        # them. Overwriting one with an index would replace the record of what
        # happened with a list of the files that happen to be in the directory.
        raise Usage(f"{target_path} already exists; pass --out <file> to write the "
                    f"index elsewhere, or --verify to check the manifest that is there")
    entries = []
    for name in sorted(os.listdir(args.directory)):
        if not name.endswith(".json") or name == "manifest.json":
            continue
        with open(os.path.join(args.directory, name), encoding="utf-8") as fh:
            data = json.load(fh)
        entries.append({"id": data.get("id", os.path.splitext(name)[0]),
                        "title": data.get("title", ""),
                        "status": data.get("status", ""),
                        "severity": data.get("severity", ""),
                        "target": data.get("target", ""),
                        "sha256": (data.get("hashes") or {}).get("record_sha256")})
    payload = {"bundle": os.path.basename(os.path.normpath(args.directory)),
               "created_at": fetchmod.now(), "tool": "blackheart-workbench",
               "scope_file": None, "records": entries, "count": len(entries),
               "by_status": _counts(entries, "status"),
               "by_severity": _counts(entries, "severity")}
    payload["manifest_sha256"] = ev.sha256_text(ev.canonical_json(payload))
    path = _write(os.path.join(args.directory, "manifest.json"),
                  json.dumps(payload, indent=2, sort_keys=True))
    problems = ev.Bundle.verify(args.directory)
    return Result("evidence manifest",
                  {"manifest": path, "count": len(entries), "problems": problems},
                  [f"{len(entries)} record(s) indexed", f"manifest: {path}",
                   f"verified: {'clean' if not problems else problems}"])


def _counts(entries, field):
    counts = {}
    for entry in entries:
        counts[entry[field]] = counts.get(entry[field], 0) + 1
    return counts


# --------------------------------------------------------------- emergency
def cmd_emergency_collect(args):
    guard = _guard(args)
    history_obj, _path = _open_history(getattr(args, "history", None),
                                       secrets=list(getattr(args, "secret", None) or []))
    directory = args.out or os.path.join(os.getcwd(), "emergency")
    if not args.yes:
        return Result("emergency collect",
                      {"planned": True, "url": args.url, "directory": directory},
                      [emergencymod.plan_lines(guard, args.url, args.budget),
                       "  re-run with --yes to perform it"])
    bundle = ev.Bundle("emergency", scope_file=args.scope)
    collection = emergencymod.collect(guard, args.url, history=history_obj,
                                      bundle=bundle, budget=args.budget)
    manifest = bundle.write(directory)
    _write(os.path.join(directory, "emergency.json"),
           json.dumps(collection.as_dict(), indent=2, sort_keys=True))
    lines = [collection.report_lines(),
             f"  evidence: {directory} ({manifest['count']} record(s))"]
    return Result("emergency collect",
                  {"collection": collection.as_dict(), "directory": directory}, lines)


# ------------------------------------------------------------------- report
def cmd_report_generate(args):
    report_obj = reportmod.build(bundle_dir=args.bundle, manifest_path=args.manifest,
                                 scope_file=args.scope, title=args.title,
                                 notes=args.note or [])
    if args.scope and os.path.isfile(args.scope):
        try:
            report_obj.scope_summary = sc.ScopeGuard(sc.load_scope(args.scope)).summary()
        except sc.ScopeError:
            pass
    path = report_obj.write(args.out)
    counts = report_obj.counts()
    lines = [f"report written: {path}",
             f"  records       : {counts['records']}",
             f"  validated     : {counts['reproduced']}",
             f"  not validated : {counts['not_established']}",
             f"  acquisitions  : {report_obj.acquisition_counts() or 'none supplied'}"]
    for name, detail in sorted(report_obj.verification.items()):
        problems = detail.get("problems") or []
        lines.append(f"  verification  : {name}: "
                     f"{'clean' if not problems else f'{len(problems)} problem(s)'}")
        for problem in problems[:5]:
            lines.append(f"    {problem}")
    return Result("report generate", {"path": path, "counts": counts}, lines)


# --------------------------------------------------------------------- parser
def build_parser():
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Blackhearts workbench: authorized HTTP, API and resource "
                    "assessment tooling. It does not bypass access controls and it "
                    "does not attack anything you are not authorized to test.")
    groups = parser.add_subparsers(dest="group")

    def with_scope(sub, name, needs_scope=True, scope_optional=False):
        """Add the shared output flags, and the scope flags where they apply.

        `scope_optional` is for the two commands that can work from a local file
        instead of a request (`api inspect` with `--file`, `resource inspect` with
        a path). The flag is accepted but not required, and the branch that sends
        a request calls `_guard`, which refuses without it.
        """
        sub.add_argument("--json", action="store_true",
                         help="print one JSON object on stdout")
        if needs_scope or scope_optional:
            sub.add_argument("--scope", required=needs_scope,
                             help="authorization scope file; required, with no default"
                                  + ("" if needs_scope else " for a request"))
            sub.add_argument("--secret", action="append", default=[],
                             help="a value to redact from recorded bodies and URLs (repeatable)")
        sub.set_defaults(command_name=name)
        return sub

    # scope
    scope_group = groups.add_parser("scope").add_subparsers(dest="command", required=True)
    scope_validate = scope_group.add_parser("validate", help="check a scope file")
    scope_validate.add_argument("--scope", required=True)
    scope_validate.add_argument("--json", action="store_true")
    scope_validate.set_defaults(handler=cmd_scope_validate, command_name="scope validate")

    # http
    http = groups.add_parser("http").add_subparsers(dest="command", required=True)
    inspect_parser = with_scope(http.add_parser("inspect", help="one request, in full"),
                                "http inspect")
    inspect_parser.add_argument("--url", required=True)
    inspect_parser.add_argument("--method", default="GET")
    inspect_parser.add_argument("--header", action="append", default=[])
    inspect_parser.add_argument("--history", help="append the exchange to this file")
    inspect_parser.add_argument("--timeout", type=float, default=None)
    inspect_parser.set_defaults(handler=cmd_http_inspect)

    replay_parser = with_scope(http.add_parser("replay", help="replay a stored request"),
                               "http replay")
    replay_parser.add_argument("--history", required=True)
    replay_parser.add_argument("--id", required=True)
    replay_parser.add_argument("--method")
    replay_parser.add_argument("--header", action="append", default=[])
    replay_parser.add_argument("--body")
    replay_parser.add_argument("--timeout", type=float, default=None)
    replay_parser.add_argument("--confirm-write", action="store_true",
                               help="required before a write method is sent")
    replay_parser.set_defaults(handler=cmd_http_replay)

    diff_parser = with_scope(http.add_parser("diff", help="compare two stored exchanges"),
                             "http diff", needs_scope=False)
    diff_parser.add_argument("--history", required=True)
    diff_parser.add_argument("--from", dest="from_id", required=True)
    diff_parser.add_argument("--to", dest="to_id", required=True)
    diff_parser.set_defaults(handler=cmd_http_diff)

    mutate_parser = with_scope(http.add_parser("mutate", help="show the mutation catalogue"),
                               "http mutate", needs_scope=False)
    mutate_parser.add_argument("--history", required=True)
    mutate_parser.add_argument("--id", required=True)
    mutate_parser.add_argument("--kinds", help="comma-separated mutation kinds")
    mutate_parser.add_argument("--apply", type=int, default=None,
                               help="print the request one mutation would send; sends nothing")
    mutate_parser.set_defaults(handler=cmd_http_mutate)

    fuzz_parser = with_scope(http.add_parser("fuzz", help="bounded mutation run"),
                             "http fuzz")
    fuzz_parser.add_argument("--history", required=True)
    fuzz_parser.add_argument("--id", required=True)
    fuzz_parser.add_argument("--kinds")
    fuzz_parser.add_argument("--limit", type=int, default=25)
    fuzz_parser.add_argument("--budget", type=int, default=None)
    fuzz_parser.add_argument("--confirm-write", action="store_true",
                             help="allow a state-changing request if the scope permits it")
    fuzz_parser.set_defaults(handler=cmd_http_fuzz)

    # api
    api = groups.add_parser("api").add_subparsers(dest="command", required=True)
    api_discover = with_scope(api.add_parser("discover", help="find API descriptions"),
                              "api discover")
    api_discover.add_argument("--url", required=True)
    api_discover.add_argument("--max-pages", type=int, default=5)
    api_discover.add_argument("--max-depth", type=int, default=1)
    api_discover.add_argument("--budget", type=int, default=None)
    api_discover.add_argument("--history")
    api_discover.set_defaults(handler=cmd_api_discover)

    api_inspect = with_scope(api.add_parser("inspect", help="read one API description"),
                             "api inspect", needs_scope=False, scope_optional=True)
    api_inspect.add_argument("--url", help="fetch the description from here")
    api_inspect.add_argument("--file", help="or read a local description file")
    api_inspect.add_argument("--history")
    api_inspect.set_defaults(handler=cmd_api_inspect)

    # web
    web = groups.add_parser("web").add_subparsers(dest="command", required=True)
    crawl = with_scope(web.add_parser("crawl", help="bounded discovery"), "web crawl")
    crawl.add_argument("--url", required=True)
    crawl.add_argument("--max-pages", type=int, default=25)
    crawl.add_argument("--max-depth", type=int, default=2)
    crawl.add_argument("--budget", type=int, default=None)
    crawl.add_argument("--no-assets", action="store_true")
    crawl.add_argument("--history")
    crawl.set_defaults(handler=cmd_web_crawl)

    scan = with_scope(web.add_parser("scan", help="observable checks over responses"),
                      "web scan")
    scan.add_argument("--url", required=True)
    scan.add_argument("--extra-url", action="append", default=[])
    scan.add_argument("--history")
    scan.add_argument("--out", help="evidence directory")
    scan.set_defaults(handler=cmd_web_scan)

    # resource
    resource = groups.add_parser("resource").add_subparsers(dest="command", required=True)
    res_inspect = with_scope(resource.add_parser("inspect", help="read a local file safely"),
                             "resource inspect", needs_scope=False)
    res_inspect.add_argument("--path", required=True)
    res_inspect.add_argument("--max-bytes", type=int, default=None)
    res_inspect.add_argument("--max-depth", type=int, default=None)
    res_inspect.add_argument("--quarantine", help="move flagged files here")
    res_inspect.set_defaults(handler=cmd_resource_inspect)

    res_download = with_scope(resource.add_parser("download", help="acquire one resource"),
                              "resource download")
    res_download.add_argument("--url", required=True)
    res_download.add_argument("--out")
    res_download.add_argument("--expect", choices=("document", "page"), default="document")
    res_download.add_argument("--sha256", help="refuse the file unless it hashes to this")
    res_download.add_argument("--license", help="a note about the resource's licence")
    res_download.add_argument("--note")
    res_download.add_argument("--allow-partial", action="store_true")
    res_download.add_argument("--history")
    res_download.add_argument("--yes", action="store_true", help="confirm the request")
    res_download.set_defaults(handler=cmd_resource_download)

    res_extract = with_scope(resource.add_parser("extract",
                                                 help="read files a manifest names"),
                             "resource extract", needs_scope=False)
    res_extract.add_argument("--manifest", required=True)
    res_extract.add_argument("--id")
    res_extract.add_argument("--out", help="extract archive members here")
    res_extract.add_argument("--max-bytes", type=int, default=None)
    res_extract.add_argument("--max-depth", type=int, default=None)
    res_extract.set_defaults(handler=cmd_resource_extract)

    # evidence
    evidence = groups.add_parser("evidence").add_subparsers(dest="command", required=True)
    ev_hash = with_scope(evidence.add_parser("hash", help="sha256 of files on disk"),
                         "evidence hash", needs_scope=False)
    ev_hash.add_argument("path", nargs="+")
    ev_hash.set_defaults(handler=cmd_evidence_hash)

    ev_manifest = with_scope(evidence.add_parser("manifest",
                                                 help="index or verify a bundle"),
                             "evidence manifest", needs_scope=False)
    ev_manifest.add_argument("--directory", required=True)
    ev_manifest.add_argument("--out", help="write the index here instead")
    ev_manifest.add_argument("--verify", action="store_true")
    ev_manifest.set_defaults(handler=cmd_evidence_manifest)

    # emergency
    emergency_parser = groups.add_parser("emergency").add_subparsers(dest="command",
                                                                     required=True)
    ecollect = with_scope(emergency_parser.add_parser("collect",
                                                      help="read-only snapshot"),
                          "emergency collect")
    ecollect.add_argument("--url", required=True)
    ecollect.add_argument("--out")
    ecollect.add_argument("--budget", type=int, default=None)
    ecollect.add_argument("--history")
    ecollect.add_argument("--yes", action="store_true", help="confirm the request")
    ecollect.set_defaults(handler=cmd_emergency_collect)

    # report
    report_group = groups.add_parser("report").add_subparsers(dest="command", required=True)
    rgenerate = with_scope(report_group.add_parser("generate", help="write a report"),
                           "report generate", needs_scope=False)
    rgenerate.add_argument("--bundle", help="an evidence bundle directory")
    rgenerate.add_argument("--manifest", help="a downloads manifest")
    rgenerate.add_argument("--scope", help="the scope file the run used")
    rgenerate.add_argument("--out", required=True)
    rgenerate.add_argument("--title", default="Assessment report")
    rgenerate.add_argument("--note", action="append", default=[])
    rgenerate.set_defaults(handler=cmd_report_generate)
    return parser


def command_paths(parser=None):
    """Every `group command` path the parser defines.

    argparse keeps child parsers on the subparser action, which is private but
    stable. Walking it here means a test can compare the surface that exists
    against the surface that is documented, and a difference fails the suite
    instead of being noticed by a reader who could not find a command.
    """
    parser = parser or build_parser()

    def walk(node, prefix):
        group = getattr(node, "_subparsers", None)
        if group is None:
            return [prefix] if prefix else []
        paths = []
        for action in group._group_actions:
            for name, child in (getattr(action, "choices", None) or {}).items():
                paths.extend(walk(child, (prefix + (name,)) if prefix else (name,)))
        return paths

    return tuple(sorted(walk(parser, ())))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if not argv:
        parser.print_help()
        return EXIT_USAGE
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:                     # argparse exits 2 on bad usage
        return exc.code if isinstance(exc.code, int) else EXIT_USAGE
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return EXIT_USAGE
    try:
        result = handler(args)
    except Usage as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except sc.ScopeError as exc:
        print(f"{PROGRAM}: refused by the scope file: {exc}", file=sys.stderr)
        return EXIT_SCOPE
    except FileNotFoundError as exc:
        print(f"{PROGRAM}: not found: {exc}", file=sys.stderr)
        return EXIT_FAILED
    except KeyboardInterrupt:
        print(f"{PROGRAM}: interrupted", file=sys.stderr)
        return EXIT_FAILED
    except (OSError, KeyError, ValueError) as exc:
        print(f"{PROGRAM}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_FAILED
    return _emit(result, args)


if __name__ == "__main__":
    sys.exit(main())
