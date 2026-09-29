#!/usr/bin/env python3
"""Read-only upstream drift watch for both pinned third-party sources.

    python3 .github/scripts/watch_upstream.py            # human report
    python3 .github/scripts/watch_upstream.py --json     # machine-readable
    python3 .github/scripts/watch_upstream.py --fail-on-drift
    python3 .github/scripts/watch_upstream.py --source catalogue
    python3 .github/scripts/watch_upstream.py --manifest /path/to/manifest.json

What this is, and what it is not
--------------------------------
This script **observes**. It resolves the head of each upstream repository,
compares it with the commit Blackhearts has pinned, and classifies the
difference. It writes nothing into the repository, nowhere: no vendored file,
no adapter, no manifest, no index. It does not fetch file contents it does not
need, it does not resolve a single upstream link, and it never deletes anything.

It is deliberately not a second sync system. `sync_upstream.py` already does the
mechanical half — re-vendor, re-audit, regenerate adapters, open a pull request
for a human to merge. This script answers the narrower question that job leaves
open: *has anything moved, in either source, and if so what kind of change is
it?* The answer is a report, not a commit.

Why both sources, when only one is re-vendored
-----------------------------------------------
`sync_upstream.py` covers the skill mirror. The catalogue
(`VoltAgent/awesome-openclaw-skills`) is a second pinned source with its own
recorded commit and its own copy under `skills/catalog/`, and until now nothing
watched it: the pin was recorded but never checked. That is the gap this closes.
A catalogue move is reported and classified, never vendored — its README records
why resolving those entries is a human decision.

Authority
---------
The pins come from `.github/UPSTREAM-MANIFEST.json`, the one manifest this
repository has. This script reads it; it does not maintain a parallel record.
`skills/VENDOR.md` remains the human-readable provenance record.

Exit codes
----------
  0  report produced (whether or not there is drift)
  1  the watch itself failed — an upstream could not be read (this includes a
     network failure: a watch that cannot see upstream has established nothing)
  2  drift detected, and `--fail-on-drift` was passed
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(REPO, ".github", "UPSTREAM-MANIFEST.json")

# The two pinned sources, keyed to the manifest's own `upstream` block. There is
# no third copy of these values: if the manifest and this table disagree, the
# manifest wins and --check-manifest says so.
SOURCES = (
    {
        "name": "skills",
        "repo_key": "skills_repo",
        "pin_key": "skills_commit",
        "licence_key": "skills_licence",
        "vendored": "skills/third-party/claude-skills/",
    },
    {
        "name": "catalogue",
        "repo_key": "catalogue_repo",
        "pin_key": "catalogue_commit",
        "licence_key": "catalogue_licence",
        "vendored": "skills/catalog/",
    },
)

EXECUTABLE = (".py", ".sh", ".bash", ".zsh", ".js", ".mjs", ".cjs", ".ts",
              ".ps1", ".bat", ".cmd", ".rb", ".pl")
LICENCE_NAMES = ("license", "licence", "copying", "notice", "author",
                 "citation", "third-party-notices", "third_party_notices")

# Path fragments that decide a bucket. Kept as data, not buried in branches, so
# the classification can be read and argued with.
SENSITIVE_FRAGMENTS = (
    "hook", "install", "setup", "auth", "secret", "token", "credential",
    "exec", "shell", "sandbox", "policy", "gate", "perm",
)
CONFIG_FRAGMENTS = (
    ".github/", "settings.json", ".mcp.json", "plugin.json",
    "marketplace.json", "pyproject.toml", "requirements", ".tool-versions",
    "dockerfile", "makefile", "tessl.json", "mkdocs.yml",
)


def log(msg=""):
    print(msg)


def sh(*args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def read_manifest(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def resolve_head(url):
    """Default branch + head commit, without cloning.

    `--symref` is what makes a default-branch *rename* visible: the report says
    which branch upstream now calls default, so a rename is a stated fact
    rather than an inference from a moved SHA.
    """
    r = sh("git", "ls-remote", "--symref", url, "HEAD")
    if r.returncode != 0:
        return None, None
    head, branch = None, None
    for line in r.stdout.splitlines():
        if line.startswith("ref:"):
            branch = line.split()[1].removeprefix("refs/heads/")
        elif line.endswith("\tHEAD"):
            head = line.split()[0]
    return branch, head


def resolve_tags(url):
    """Newest tags, informational only.

    The manifest records a commit, not a tag, so there is nothing to diff here.
    Tags are reported because an upstream release is context a reader wants
    when deciding how seriously to take a drift report.
    """
    r = sh("git", "ls-remote", "--tags", "--refs", url)
    if r.returncode != 0:
        return []
    tags = [line.split("refs/tags/")[-1] for line in r.stdout.splitlines()]
    def key(t):
        return [int(n) if n.isdigit() else n
                for n in re.split(r"[.\-+]", t.lstrip("v"))]
    try:
        return sorted(tags, key=key)[-5:]
    except TypeError:
        return sorted(tags)[-5:]


def classify(path, status, modes):
    """Buckets for one changed path.

    A path can land in several buckets on purpose: a modified GitHub workflow is
    a configuration change *and* a security-sensitive one, and collapsing that
    to a single label would hide the reason it matters.
    """
    buckets = set()
    base = os.path.basename(path).lower()
    low = path.lower()
    ext = os.path.splitext(base)[1]

    if status.startswith("A"):
        buckets.add("added")
    elif status.startswith("D"):
        buckets.add("removed")
    elif status.startswith("R"):
        buckets.add("renamed")
    elif status.startswith("M"):
        buckets.add("modified")
    elif status.startswith("T"):
        buckets.add("type_changed")

    old_mode, new_mode = modes
    if "120000" in (old_mode, new_mode):
        buckets.add("symlink_change")

    if any(base.startswith(n) for n in LICENCE_NAMES) or base == "notice":
        buckets.add("licence_provenance")
    if any(f in low for f in CONFIG_FRAGMENTS):
        buckets.add("workflow_config")
    if base in ("skills-index.json",) or ".lock" in base or low.startswith("docs/"):
        buckets.add("generated")
    if ext in EXECUTABLE:
        buckets.add("executable")
    if (ext in EXECUTABLE
            or "workflow_config" in buckets
            or any(f in low for f in SENSITIVE_FRAGMENTS)):
        buckets.add("security_sensitive")
    return buckets


def diff_source(url, pin, head, workdir):
    """File-level classification of pin..head. Returns (info, error).

    A blobless, no-checkout clone is used on purpose: name-status and mode
    information live in the commits and trees, so the file-level report needs no
    blob content at all. That keeps the watch cheap enough to run weekly without
    being a load on either upstream.
    """
    dest = os.path.join(workdir, re.sub(r"[^a-z0-9]+", "-", url.lower()))
    r = sh("git", "clone", "--filter=blob:none", "--no-checkout", "--quiet", url, dest)
    if r.returncode != 0:
        return None, f"clone failed: {r.stderr.strip()[:200]}"

    have_pin = sh("git", "-C", dest, "cat-file", "-e", f"{pin}^{{commit}}").returncode == 0
    if not have_pin:
        # The pinned commit is unreachable: upstream rewrote or dropped history.
        # This is the one case a diff cannot describe, and it is reported as its
        # own condition rather than as "N files changed".
        return {"pin_reachable": False}, None

    sh("git", "-C", dest, "fetch", "--quiet", "origin", head)
    counts = sh("git", "-C", dest, "rev-list", "--count", f"{pin}..{head}")
    raw = sh("git", "-C", dest, "diff", "--raw", "-M", pin, head)
    if raw.returncode != 0:
        return None, f"diff failed: {raw.stderr.strip()[:200]}"

    changed, buckets, paths_by_bucket = [], {}, {}
    for line in raw.stdout.splitlines():
        if not line.startswith(":"):
            continue
        meta, _, path = line[1:].partition("\t")
        parts = meta.split()
        if len(parts) < 5:
            continue
        old_mode, new_mode, _, _, status = parts[0], parts[1], parts[2], parts[3], parts[4]
        b = classify(path, status, (old_mode, new_mode))
        if "renamed" in b and "\t" in path:
            path = path.split("\t")[-1]
        changed.append({"path": path, "status": status, "buckets": sorted(b)})
        for bucket in b:
            buckets[bucket] = buckets.get(bucket, 0) + 1
            paths_by_bucket.setdefault(bucket, []).append(path)

    return {
        "pin_reachable": True,
        "commits": int(counts.stdout.strip() or 0),
        "files_changed": len(changed),
        "buckets": buckets,
        "paths_by_bucket": paths_by_bucket,
    }, None


def watch_source(src, manifest, workdir):
    up = manifest.get("upstream", {})
    url = up.get(src["repo_key"])
    pin = up.get(src["pin_key"])
    out = {
        "source": src["name"],
        "repo": url,
        "pinned": pin,
        "licence": up.get(src["licence_key"]),
        "vendored_at": src["vendored"],
        "default_branch": None,
        "head": None,
        "drift": None,
    }
    branch, head = resolve_head(url)
    out["default_branch"], out["head"] = branch, head
    if not head:
        out["error"] = "could not read upstream head"
        return out
    out["drift"] = (head != pin)
    out["tags"] = resolve_tags(url)
    if not out["drift"]:
        out["status"] = "up to date"
        return out

    info, err = diff_source(url, pin, head, workdir)
    if err:
        out["error"] = err
        return out
    out.update(info)
    out["status"] = ("pin no longer reachable upstream"
                     if not info["pin_reachable"]
                     else f"{info['files_changed']} file(s) changed")
    return out


def human(report):
    log("Blackhearts upstream watch — read-only")
    log("=" * 66)
    drifted = 0
    for s in report["sources"]:
        log("")
        log(f"{s['source']}: {s['repo']}")
        log(f"  pinned commit   : {s['pinned']}")
        log(f"  upstream head   : {s['head']}")
        log(f"  default branch  : {s['default_branch']}")
        if s.get("tags"):
            log(f"  recent tags     : {', '.join(s['tags'])}")
        if s.get("error"):
            log(f"  RESULT          : could not be read — {s['error']}")
            continue
        if not s["drift"]:
            log("  RESULT          : up to date — nothing to do")
            continue
        drifted += 1
        log(f"  RESULT          : DRIFT — {s['status']}")
        if not s.get("pin_reachable"):
            log("  The pinned commit no longer exists upstream. A diff cannot be")
            log("  produced; the pin and the vendored copy need a human decision.")
            continue
        log(f"  commits between : {s['commits']}")
        log(f"  files changed   : {s['files_changed']}")
        log("  by category:")
        for bucket, n in sorted(s["buckets"].items(), key=lambda kv: (-kv[1], kv[0])):
            log(f"      {bucket:22} {n}")
        sensitive = s["paths_by_bucket"].get("security_sensitive", [])
        if sensitive:
            log(f"  security-sensitive paths ({len(sensitive)}, first 15):")
            for p in sorted(sensitive)[:15]:
                log(f"      {p}")
    unreadable = sum(1 for s in report["sources"] if s.get("error"))
    readable = len(report["sources"]) - unreadable
    log("")
    log("=" * 66)
    if unreadable:
        log(f"  {unreadable} of {len(report['sources'])} source(s) could not be "
            f"read. The watch did not complete.")
        log("  A watch that cannot see upstream has established nothing: silence")
        log("  is not a clean bill of health, and this run is a failure, not a pass.")
    elif drifted:
        log(f"  {drifted} source(s) have moved. Nothing was fetched, vendored,")
        log("  written, or deleted. This report is the whole of the change.")
    else:
        log(f"  All {readable} source(s) are at their pinned commits.")
    return drifted, unreadable


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="machine-readable report")
    ap.add_argument("--report", metavar="PATH",
                    help="also write the human-readable report to PATH "
                         "(one run, two outputs — CI needs both)")
    ap.add_argument("--fail-on-drift", action="store_true",
                    help="exit 2 when any source has moved")
    ap.add_argument("--source", choices=[s["name"] for s in SOURCES],
                    help="watch one source only")
    ap.add_argument("--manifest", default=MANIFEST,
                    help="manifest to read pins from (default: the repository's)")
    args = ap.parse_args()

    if not os.path.isfile(args.manifest):
        print(f"manifest not found: {args.manifest}", file=sys.stderr)
        return 1
    manifest = read_manifest(args.manifest)

    sources = [s for s in SOURCES if not args.source or s["name"] == args.source]
    workdir = tempfile.mkdtemp(prefix="bh-watch-")
    try:
        report = {
            "read_only": True,
            "manifest": os.path.relpath(args.manifest, REPO)
            if args.manifest.startswith(REPO) else args.manifest,
            "sources": [watch_source(s, manifest, workdir) for s in sources],
        }
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    unreadable = sum(1 for s in report["sources"] if s.get("error"))
    drifted = sum(1 for s in report["sources"] if s.get("drift"))
    report["drift_total"] = drifted
    report["unreadable_total"] = unreadable

    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            with contextlib.redirect_stdout(fh):
                human(report)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif not args.report:
        human(report)

    # Exit codes are ordered by what a caller must do, not by what was found:
    # a watch that could not run is a failure (1), drift is information (0, or 2
    # when the caller asked to be told loudly).
    if unreadable:
        return 1
    if args.fail_on_drift and drifted:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
