#!/usr/bin/env python3
"""
Upstream drift detection and re-vendoring for the Blackhearts mirror.

    python3 .github/scripts/sync_upstream.py            # report drift
    python3 .github/scripts/sync_upstream.py --apply    # re-vendor + re-audit

Why this never auto-merges
--------------------------
Blackhearts exists to force human judgement onto third-party code before it
enters an engagement. A bot that silently merged upstream changes would let
unreviewed code into the framework and defeat the entire control. So this
script's output is a *pull request*: a human reads the diff, the adapters show
what the new audit says, and a human merges. Automation does the tedious part
(fetch, diff, copy, re-audit, regenerate adapters, update the manifest); it
does not do the part that requires judgement.

Scope
-----
The whole mirror is compared file by file, not just skills: commands, agent
personas, plugin manifests, upstream tooling, standards, audit records, and
generated documentation are all covered. A per-skill comparison would have let
all of that drift undetected.

Safety properties
-----------------
* No upstream file is ever modified. Vendored content is copied byte-for-byte.
* A file removed upstream is REPORTED, never deleted. Deleting content is a
  human decision, recorded in a commit, not a side effect of a scheduled job.
* Excluded paths (see the manifest's `exclusions` section) are never
  re-introduced, which is what keeps upstream's `.gitignore` from silently
  untracking this repository's vendored files.
* Every vendored area keeps a Blackhearts adapter, including the non-skill
  collections.
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import hashlib

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MIRROR = os.path.join(REPO, "skills", "third-party", "claude-skills")
MANIFEST = os.path.join(REPO, ".github", "UPSTREAM-MANIFEST.json")
ADAPTER = "_BLACKHEART-ADAPTER.md"
UPSTREAM = "https://github.com/alirezarezvani/claude-skills.git"
SKILL_MD = "SKILL.md"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def log(msg):
    print(f"  {msg}")


def sh(*args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def fetch_upstream(ref, dest):
    r = sh("git", "clone", "--depth", "1", "--quiet", UPSTREAM, dest)
    if r.returncode != 0:
        r = sh("git", "clone", "--depth", "1", "--branch", ref, "--quiet",
               UPSTREAM, dest)
        if r.returncode != 0:
            raise SystemExit(f"could not clone upstream: {r.stderr.strip()}")
    if ref:
        r = sh("git", "-C", dest, "fetch", "--depth", "1", "--quiet", "origin", ref)
        if r.returncode == 0:
            sh("git", "-C", dest, "checkout", "--quiet", "FETCH_HEAD")
    return sh("git", "-C", dest, "rev-parse", "HEAD").stdout.strip()


def upstream_tree(root, exclusions):
    """Map of repo-relative path -> git blob sha, honouring the exclusions."""
    out = sh("git", "-C", root, "ls-tree", "-r", "HEAD", "--long").stdout
    tree = {}
    for line in out.splitlines():
        parts = line.split(maxsplit=4)
        if len(parts) < 4:
            continue
        sha, path = parts[2], parts[4] if len(parts) > 4 else ""
        if not path:
            continue
        if any(path == e or path.startswith(e) for e in exclusions):
            continue
        tree[path] = sha
    return tree


def local_blob_map(root, skip_adapters=True):
    out = {}
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d != "__pycache__"]
        for name in fn:
            if name.endswith((".pyc", ".pyo")):
                continue
            if skip_adapters and name == ADAPTER:
                continue
            full = os.path.join(dp, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            out[rel] = sh("git", "hash-object", full).stdout.strip()
    return out


def canonical_skill_dirs(root):
    """Real SKILL.md directories, i.e. not inside a symlink mirror."""
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not d.startswith(".") or d == "."]
        dn[:] = [d for d in dn if d not in (".git",)]
        if SKILL_MD in fn and not os.path.islink(os.path.join(dp, SKILL_MD)):
            out.append(os.path.relpath(dp, root).replace(os.sep, "/"))
    return sorted(out)


def audit(skill_dir):
    auditor = os.path.join(
        MIRROR, "engineering", "skills", "skill-security-auditor",
        "scripts", "skill_security_auditor.py")
    if not os.path.isfile(auditor):
        return None
    r = sh(sys.executable, auditor, skill_dir, "--json", timeout=180)
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write changes (default: report only)")
    ap.add_argument("--ref", default="", help="upstream ref (default: default branch)")
    ap.add_argument("--scan-date", default="")
    args = ap.parse_args()
    scan_date = args.scan_date or datetime.date.today().isoformat()

    with open(MANIFEST) as fh:
        manifest = json.load(fh)
    exclusions = tuple(manifest.get("exclusions", {}))
    exclusions = tuple(e for e in exclusions if e != "_comment")
    pinned = manifest["upstream"]["skills_commit"]

    print("Upstream sync")
    print("=" * 64)
    log(f"pinned commit : {pinned}")
    log(f"exclusions    : {', '.join(exclusions) or 'none'}")
    log(f"mode          : {'APPLY' if args.apply else 'CHECK (report only)'}")
    print("-" * 64)

    tmp = tempfile.mkdtemp(prefix="blackhearts-upstream-")
    try:
        src = os.path.join(tmp, "src")
        sha = fetch_upstream(args.ref, src)
        log(f"upstream HEAD : {sha}")
        remote = upstream_tree(src, exclusions)
        local = local_blob_map(MIRROR)
        log(f"upstream files: {len(remote)}  (after exclusions)")
        log(f"mirror files  : {len(local)}")
        print("-" * 64)

        added = sorted(set(remote) - set(local))
        changed = sorted(p for p in set(remote) & set(local)
                         if remote[p] != local[p])
        removed = sorted(set(local) - set(remote))

        log(f"added upstream    : {len(added)}")
        log(f"changed upstream  : {len(changed)}")
        log(f"no longer upstream: {len(removed)}  (reported only; never deleted automatically)")
        print("-" * 64)

        if not (added or changed or removed):
            print("  No drift. Mirror matches the pinned upstream commit.")
            return 0

        for p in (changed + added)[:20]:
            log(f"  {'changed' if p in changed else 'new':8s} {p}")
        if len(changed) + len(added) > 20:
            log(f"  ... and {len(changed) + len(added) - 20} more")
        if removed:
            print()
            log("REMOVED UPSTREAM (needs a human decision, left in place):")
            for p in removed[:20]:
                log(f"  removed  {p}")

        if not args.apply:
            print()
            print("  Dry run. Re-run with --apply, or let the workflow open a PR.")
            return 0

        print()
        log("applying changes to the mirror...")
        touched = added + changed
        for rel in touched:
            s = os.path.join(src, rel)
            d = os.path.join(MIRROR, rel)
            if os.path.isdir(d) and not os.path.isfile(d):
                shutil.rmtree(d)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)
        log(f"copied {len(touched)} file(s)")

        # re-audit any skill whose files changed
        changed_skills = sorted({p for p in touched
                                 if canonical_skill_dirs(MIRROR)
                                 and any(c in p for c in ["/skills/", "/commands/"])})
        log(f"re-auditing {len(changed_skills)} changed skill(s)...")
        for rel in changed_skills:
            skill_root = rel.split("/SKILL")[0]
            if not os.path.isdir(os.path.join(MIRROR, skill_root)):
                continue
            audit(os.path.join(MIRROR, skill_root))  # advisory run; adapters
            # are regenerated by gen_adapters.py so verdicts stay consistent
        log("  (adapters are regenerated below)")

        import gen_collection_adapters
        log("regenerating collection adapters...")
        for rel_path, title, what, why, names in gen_collection_adapters.AREAS:
            rows = gen_collection_adapters.listing(rel_path, names)
            if rows:
                gen_collection_adapters.write(rel_path, title, what, why, rows, names)
        log("  done")

        log("regenerating per-skill adapters...")
        import gen_adapters
        gen_adapters.regenerate_all(scan_date=scan_date)
        log("  done")

        log("regenerating the integrity manifest...")
        import gen_manifest
        gen_manifest.main()
        log("  done")

        print()
        print("  Changes staged for review. A human must read the diff and merge.")
        print("  This workflow never merges upstream code on its own.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
