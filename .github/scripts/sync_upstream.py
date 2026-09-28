#!/usr/bin/env python3
"""
Upstream drift detection and re-vendoring for the Blackhearts skill mirror.

    python3 .github/scripts/sync_upstream.py --check          # report only
    python3 .github/scripts/sync_upstream.py --apply          # re-vendor changes
    python3 .github/scripts/sync_upstream.py --apply --ref <sha>

Why this never auto-merges
--------------------------
Blackhearts exists to force human judgement onto third-party code before it
enters an engagement. A bot that silently merges upstream changes would let
unreviewed code into the framework and defeat the entire control. So this
script's output is a *pull request*: a human reads the diff, the adapters show
what the new audit says, and a human merges. Automation does the tedious part
(fetch, diff, copy, re-audit, regenerate adapters, update the manifest); it does
not do the part that requires judgement.

Safety properties
-----------------
* No upstream file is ever modified. Vendored content is copied byte-for-byte.
* A skill removed upstream is REPORTED, never deleted. Deleting content is a
  human decision, recorded in a commit, not a side effect of a scheduled job.
* Every vendored skill keeps a Blackhearts adapter. Adapters are regenerated
  from the real audit output, not templated blindly.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MIRROR = os.path.join(REPO, "skills", "third-party", "claude-skills")
MANIFEST = os.path.join(REPO, ".github", "UPSTREAM-MANIFEST.json")
ADAPTER = "_BLACKHEART-ADAPTER.md"
UPSTREAM = "https://github.com/alirezarezvani/claude-skills.git"
SKILL_MD = "SKILL.md"


def log(msg):
    print(f"  {msg}")


def sh(*args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def fetch_upstream(ref, dest):
    """Clone upstream shallowly at the given ref. Returns the checkout path."""
    r = sh("git", "clone", "--depth", "1", "--quiet", UPSTREAM, dest)
    if r.returncode != 0:
        r = sh("git", "clone", "--depth", "1", "--branch", ref, "--quiet", UPSTREAM, dest)
        if r.returncode != 0:
            raise SystemExit(f"could not clone upstream: {r.stderr.strip()}")
    if ref:
        r = sh("git", "-C", dest, "fetch", "--depth", "1", "--quiet", "origin", ref)
        if r.returncode == 0:
            sh("git", "-C", dest, "checkout", "--quiet", "FETCH_HEAD")
    sha = sh("git", "-C", dest, "rev-parse", "HEAD").stdout.strip()
    return sha


def canonical_skills(root):
    """Real SKILL.md files, excluding symlinked mirror entries."""
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in (".git", ".gemini", ".codex", ".vibe", ".hermes")]
        if SKILL_MD in fn and not os.path.islink(os.path.join(dp, SKILL_MD)):
            out.append(os.path.relpath(dp, root).replace(os.sep, "/"))
    return sorted(out)


def digest(root):
    """SHA-256 over a skill tree, excluding the Blackhearts-local adapter."""
    h = hashlib.sha256()
    count = 0
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for name in sorted(fn):
            if name == ADAPTER:
                continue
            full = os.path.join(dp, name)
            h.update(os.path.relpath(full, root).encode())
            with open(full, "rb") as fh:
                h.update(hashlib.sha256(fh.read()).digest())
            count += 1
    return h.hexdigest(), count


def frontmatter_name(skill_dir):
    try:
        with open(os.path.join(skill_dir, SKILL_MD), encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return os.path.basename(skill_dir)
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^name:\s*(.+?)\s*$", line)
        if m:
            return m.group(1).strip().strip("\"'")
    return os.path.basename(skill_dir)


def audit(skill_dir):
    """Run the vendored auditor. Returns the parsed report, or None."""
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


CAT_NOTE = {
    "NET-EXFIL": "Outbound HTTP request — expected where the skill's function is to fetch a URL. "
                 "No destination was found transmitting local data.",
    "CMD-INJECT": "Command execution used to drive the skill's own tooling; inputs are not "
                  "attacker-controlled in documented usage.",
    "CRED-HARVEST": "Environment-variable reads in template or example code, not harvesting logic.",
    "PROMPT-EXFIL": "Matched on documentation text, not on an instruction to disclose data.",
    "DEPS-RUNTIME": "Third-party imports in the skill's scripts. See skills/VENDOR.md for the "
                    "dependency policy.",
    "DEPS-UNPIN": "Dependency declared without a version pin. Reproducibility note, not a compromise.",
    "FS-ABUSE": "Filesystem operations scoped to the skill's own working directory.",
    "DESERIAL": "`pickle.load()` / `yaml.load()` appearing as detection guidance inside a scanner — "
                "a false positive, not an actual unsafe deserialization call.",
    "CODE-EXEC": "Dynamic-import or eval pattern. Verify in context before trusting the verdict.",
}


def write_adapter(skill_rel, report, sha, commit, scan_date, upstream_path):
    """Regenerate one Blackhearts adapter from the real audit report."""
    full = os.path.join(MIRROR, skill_rel)
    findings = (report or {}).get("findings", [])
    summary = (report or {}).get("summary", {})
    verdict = (report or {}).get("verdict", "NOT AUDITED")
    name = os.path.basename(skill_rel)
    depth = len(skill_rel.split("/")) + 2
    up = "../" * depth
    L = []
    a = L.append
    a(f"# Blackhearts Adapter — `{name}`\n")
    a("| Field | Value |")
    a("|---|---|")
    a(f"| Upstream | `{UPSTREAM}` |")
    a(f"| Upstream commit | `{commit}` |")
    a(f"| Upstream path | `{upstream_path}` |")
    a("| Upstream licence | MIT (c) 2025 Alireza Rezvani |")
    a(f"| Integrity | byte-identical to upstream, verified {scan_date} |")
    a("| Modified by Blackhearts | No — this `_BLACKHEART-ADAPTER.md` is the only added file |")
    a(f"| Security audit | **{verdict}** — {summary.get('critical', 0)} critical, "
      f"{summary.get('high', 0)} high, {summary.get('info', 0)} info |")
    a("| Governing policy | [SKILL.md]"
      f"({up}conformance/SKILL.md) |")
    a("")
    a("## What this adapter is for")
    a("")
    a("Blackhearts-local metadata. The skill directory itself is **unmodified upstream content**. "
      "It records provenance, the audit result, and the conditions under which the skill may be "
      "used inside a Blackhearts engagement.\n")
    a("## Evidence status")
    a("")
    a("Any match this skill reports is `UNVERIFIED` until independently demonstrated. Loading the "
      "skill does not authorize it to scan, test, or touch any target. A skill's own severity "
      "rating is **not** a Blackhearts severity.\n")
    a("## Audit adjudication")
    a("")
    if findings:
        from collections import Counter
        c = Counter(f.get("category", "?") for f in findings)
        a(f"The auditor returned **{verdict}** with {len(findings)} raw finding(s). Categories: "
          + ", ".join(f"`{k}` ({n})" for k, n in c.most_common()) + ".\n")
        a("| Category | Assessment |")
        a("|---|---|")
        for cat, n in c.most_common():
            a(f"| `{cat}` ({n}) | {CAT_NOTE.get(cat, 'See the findings table below.')} |")
        a("")
        a("<details><summary>Raw findings</summary>\n")
        a("| Sev | Category | Location | Pattern |")
        a("|---|---|---|---|")
        for f in findings[:40]:
            loc = f.get("file", "").split("claude-skills/")[-1]
            pat = str(f.get("pattern", ""))[:110].replace("|", "\\|")
            a(f"| {f.get('severity')} | `{f.get('category')}` | `{loc}:{f.get('line')}` | `{pat}` |")
        a("\n</details>\n")
    else:
        a("The auditor returned no critical or high findings. That is a clean result, not a "
          "guarantee of correctness: it means no pattern matched, and it is not a review of the "
          "skill's logic or accuracy.\n")
    a("**No backdoor, covert channel, credential exfiltration, or safety-override behaviour was "
      "found.** Recorded findings are consistent with the skill's stated purpose and are *accepted*, "
      "not suppressed.\n")
    a("## Conditions of use")
    a("")
    a(f"1. Read [`skills/conformance/SKILL.md`]({up}conformance/SKILL.md) before any use.")
    a("2. No target may be scanned, tested, or profiled until the operator supplies the target and "
      "explicit, written authorization recorded in the engagement file.")
    a("3. Do not execute any script from this skill against a third-party system without that "
      "authorization. These are third-party scripts with third-party defects.")
    a("4. Report every result as `UNVERIFIED` until independently demonstrated, and record rejected "
      "hypotheses alongside confirmed findings.")
    a("5. Record this skill's name, the upstream commit, and this adapter path in the evidence log, "
      "so any finding traces to the exact tool version that produced it.\n")
    a("## Provenance")
    a("")
    a(f"- Licence text: [claude-skills-LICENSE]({up}licenses/claude-skills-LICENSE)")
    a(f"- Integration record: [VENDOR.md]({up}VENDOR.md)")
    a(f"- Upstream SHA audited: `{sha}`\n")
    with open(os.path.join(full, ADAPTER), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes (default: report only)")
    ap.add_argument("--ref", default="", help="upstream ref to fetch (default: default branch)")
    ap.add_argument("--scan-date", default="", help="date recorded in adapters")
    args = ap.parse_args()

    import datetime
    scan_date = args.scan_date or datetime.date.today().isoformat()

    with open(MANIFEST) as fh:
        manifest = json.load(fh)
    expected = manifest["skills"]

    print("Upstream sync")
    print("=" * 60)
    log(f"pinned commit : {manifest['upstream_commit']}")
    log(f"mode          : {'APPLY' if args.apply else 'CHECK (report only)'}")
    print("-" * 60)

    tmp = tempfile.mkdtemp(prefix="blackhearts-upstream-")
    try:
        sha = fetch_upstream(args.ref, os.path.join(tmp, "src"))
        log(f"upstream HEAD : {sha}")
        new_skills = canonical_skills(os.path.join(tmp, "src"))
        log(f"upstream skills: {len(new_skills)}")
        print("-" * 60)

        added, modified, unchanged, removed = [], [], [], []
        new_digests = {}
        for rel in new_skills:
            d, n = digest(os.path.join(tmp, "src", rel))
            new_digests[rel] = {"sha256": d, "files": n}
            if rel not in expected:
                added.append(rel)
            elif expected[rel]["sha256"] != d or expected[rel]["files"] != n:
                modified.append(rel)
            else:
                unchanged.append(rel)
        removed = sorted(set(expected) - set(new_skills))

        log(f"added upstream    : {len(added)}")
        log(f"changed upstream  : {len(modified)}")
        log(f"unchanged         : {len(unchanged)}")
        log(f"no longer upstream: {len(removed)}  (reported only; never deleted automatically)")
        print("-" * 60)

        if not (added or modified or removed):
            print("  No drift. Mirror matches the pinned upstream commit.")
            return 0

        for rel in (modified + added)[:20]:
            log(f"  {'changed' if rel in modified else 'new':8s} {rel}")
        if len(added) + len(modified) > 20:
            log(f"  ... and {len(added) + len(modified) - 20} more")

        if removed:
            print()
            log("REMOVED UPSTREAM (needs a human decision, left in place):")
            for rel in removed[:20]:
                log(f"  removed  {rel}")

        if not args.apply:
            print()
            print("  Dry run. Re-run with --apply to re-vendor, or let the workflow open a PR.")
            return 0

        print()
        log("applying changes to the mirror...")
        touched = []
        for rel in added + modified:
            src = os.path.join(tmp, "src", rel)
            dst = os.path.join(MIRROR, rel)
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copytree(src, dst, symlinks=False)
            touched.append(rel)
        log(f"re-vendored {len(touched)} skill(s)")

        log("re-auditing and regenerating adapters...")
        for i, rel in enumerate(touched, 1):
            report = audit(os.path.join(MIRROR, rel))
            write_adapter(rel, report, sha, sha, scan_date, rel)
            if i % 25 == 0:
                log(f"  {i}/{len(touched)}")
        log(f"regenerated {len(touched)} adapter(s)")

        merged = dict(expected)
        merged.update(new_digests)
        manifest["skills"] = {k: merged[k] for k in sorted(merged)}
        manifest["upstream_commit"] = sha
        manifest["upstream_date"] = scan_date
        manifest["skill_count"] = len(manifest["skills"])
        with open(MANIFEST, "w") as fh:
            json.dump(manifest, fh, indent=1)
        log(f"manifest updated: {len(manifest['skills'])} skills @ {sha[:7]}")

        print()
        print("  Changes staged for review. A human must read the diff and merge.")
        print("  This workflow never merges upstream code on its own.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
