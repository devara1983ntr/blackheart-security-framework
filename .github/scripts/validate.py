#!/usr/bin/env python3
"""
Blackhearts repository validator.

Run locally:      python3 .github/scripts/validate.py
Run in CI:        python3 .github/scripts/validate.py

Every check is a hard gate. The script exits non-zero if any check fails, so a
failing check fails the build. Checks are deliberately independent: one failing
check never masks another.

What is checked, and why:

  adapters     Every vendored skill carries a Blackhearts adapter. A vendored
               skill without one is unaudited third-party content inside the
               framework, which is exactly what the framework exists to prevent.
  integrity    Vendored files are byte-identical to the pinned upstream commit,
               per .github/UPSTREAM-MANIFEST.json. Catches local edits to
               vendored files and incomplete syncs.
  links        Markdown links resolve. Documentation that lies about where
               things are is a real defect in a security framework.
  index        FILE-INDEX.txt lists every file and every entry exists.
  secrets      No credential material is committed.
  config       The example OpenClaw config parses as JSON5 and references only
               skills that actually exist.

Exit codes:  0 = all pass, 1 = one or more failures.
"""

import hashlib
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MIRROR = os.path.join(REPO, "skills", "third-party", "claude-skills")
MANIFEST = os.path.join(REPO, ".github", "UPSTREAM-MANIFEST.json")
ADAPTER = "_BLACKHEART-ADAPTER.md"
CONFIG = os.path.join(REPO, "skills", "openclaw.example.json5")
FILE_INDEX = os.path.join(REPO, "FILE-INDEX.txt")

MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")


class Result:
    def __init__(self):
        self.checks = []

    def add(self, name, ok, detail=""):
        self.checks.append((name, ok, detail))
        return ok

    @property
    def failed(self):
        return [c for c in self.checks if not c[1]]


def walk_files(root):
    """Yield repo-relative paths of every tracked file, deterministically."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            yield os.path.relpath(full, REPO).replace(os.sep, "/")


def skill_dirs(include_nested=False):
    """Every directory in the mirror that holds a real SKILL.md.

    A skill nested inside another skill's tree (for example
    `engineering/skills/skill-tester/assets/sample-skill`) is a *test fixture*
    belonging to its parent skill, not a separately vendored skill. It gets no
    adapter of its own; its parent skill's adapter covers it. Pass
    include_nested=True to see those too.
    """
    out = []
    for dirpath, dirnames, filenames in os.walk(MIRROR):
        if "SKILL.md" in filenames:
            out.append(os.path.relpath(dirpath, MIRROR).replace(os.sep, "/"))
    out.sort()
    if include_nested:
        return out
    nested = set()
    for rel in out:
        parts = rel.split("/")
        for i in range(1, len(parts)):
            if "/".join(parts[:i]) in out:
                nested.add(rel)
                break
    return [r for r in out if r not in nested]


def skill_digest(root):
    """SHA-256 over the vendored file set, excluding the local adapter."""
    h = hashlib.sha256()
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            if name == ADAPTER:
                continue
            full = os.path.join(dirpath, name)
            h.update(os.path.relpath(full, root).encode())
            with open(full, "rb") as fh:
                h.update(hashlib.sha256(fh.read()).digest())
            count += 1
    return h.hexdigest(), count


def check_adapters(r):
    skills = skill_dirs()
    nested = skill_dirs(include_nested=True)
    fixtures = len(nested) - len(skills)
    missing = [s for s in skills if not os.path.isfile(os.path.join(MIRROR, s, ADAPTER))]
    detail = (f"{len(skills)} skills have an adapter"
              + (f" (+{fixtures} nested test fixture(s) covered by their parent)" if fixtures else ""))
    if missing:
        detail += f"; missing: {missing[:5]}"
    r.add("adapters", not missing, detail)


def check_integrity(r):
    with open(MANIFEST) as fh:
        man = json.load(fh)
    expected = man["skills"]
    drift, missing = [], []
    for rel, meta in expected.items():
        root = os.path.join(MIRROR, rel)
        if not os.path.isdir(root):
            missing.append(rel)
            continue
        digest, count = skill_digest(root)
        if digest != meta["sha256"] or count != meta["files"]:
            drift.append(rel)
    on_disk = set(skill_dirs(include_nested=True))
    extra = sorted(on_disk - set(expected))
    ok = not (drift or missing or extra)
    detail = (f"{len(expected)} skills verified byte-identical to "
              f"{man['upstream_commit'][:7]}")
    if drift:
        detail += f"; DRIFT: {drift[:5]}"
    if missing:
        detail += f"; MISSING: {missing[:5]}"
    if extra:
        detail += f"; UNEXPECTED: {extra[:5]}"
    r.add("integrity", ok, detail)


def check_links(r):
    broken = []
    total = 0
    for rel in walk_files(REPO):
        if not rel.endswith(".md"):
            continue
        full = os.path.join(REPO, rel)
        # Only documentation this project authored is a link-integrity
        # obligation. Vendored upstream markdown is left unmodified, so its
        # broken links are reported as defects rather than silently fixed.
        vendored = rel.startswith("skills/third-party/claude-skills/")
        with open(full, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        for _, target in MD_LINK.findall(body):
            if target.startswith(("http://", "https://", "#", "mailto:", "data:")):
                continue
            clean = target.split("#")[0]
            if not clean:
                continue
            # A bare `path` is a documentation template placeholder, not a link.
            if clean.lower() == "path":
                continue
            total += 1
            if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(full), clean))):
                broken.append((rel, target, vendored))
    ours = [b for b in broken if not b[2]]
    theirs = [b for b in broken if b[2]]
    detail = f"{total} local links checked; {len(ours)} broken in Blackhearts-authored docs"
    if theirs:
        detail += f"; {len(theirs)} in vendored upstream content (documented, unmodified)"
    r.add("links", not ours, detail + (f"; e.g. {ours[:3]}" if ours else ""))


def check_index(r):
    if not os.path.isfile(FILE_INDEX):
        r.add("index", False, "FILE-INDEX.txt missing")
        return
    entries = set()
    with open(FILE_INDEX) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                entries.add(line)
    on_disk = set(walk_files(REPO)) - {"FILE-INDEX.txt"}
    unindexed = sorted(p for p in on_disk if p not in entries)
    dangling = sorted(e for e in entries if e not in on_disk)
    ok = not (unindexed or dangling)
    detail = f"{len(entries)} entries; {len(unindexed)} unindexed; {len(dangling)} dangling"
    r.add("index", ok, detail + (f"; e.g. unindexed {unindexed[:3]}" if unindexed else ""))


SECRET_PATTERNS = [
    (r"ghp_[A-Za-z0-9]{36}", "GitHub personal access token"),
    (r"github_pat_[A-Za-z0-9_]{50,}", "GitHub fine-grained PAT"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key id"),
    (r"AIza[0-9A-Za-z_\-]{35}", "Google API key"),
    (r"sk-ant-[A-Za-z0-9\-_]{20,}", "Anthropic API key"),
    (r"sk-[A-Za-z0-9]{32,}", "OpenAI-style API key"),
    (r"xox[baprs]-[A-Za-z0-9\-]{10,}", "Slack token"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key"),
    (r"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}", "JWT"),
]


SECRET_ALLOWLIST = os.path.join(REPO, ".github", "secret-allowlist.json")


def load_allowlist():
    """Verified placeholders. Every entry is a specific literal, not a pattern
    relaxation, so an unrecognised credential still fails the build."""
    try:
        with open(SECRET_ALLOWLIST) as fh:
            return {e["literal"] for e in json.load(fh)["entries"]}
    except Exception:
        return set()


def check_secrets(r):
    allow = load_allowlist()
    hits, allowed = [], []
    for rel in walk_files(REPO):
        if rel.endswith((".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip")):
            continue
        # The allowlist necessarily contains the literals it suppresses; scanning
        # it would report every entry against itself.
        if os.path.abspath(os.path.join(REPO, rel)) == os.path.abspath(SECRET_ALLOWLIST):
            continue
        full = os.path.join(REPO, rel)
        try:
            with open(full, encoding="utf-8", errors="strict") as fh:
                text = fh.read()
        except (UnicodeDecodeError, OSError):
            continue
        for pattern, label in SECRET_PATTERNS:
            for m in re.finditer(pattern, text):
                literal = m.group(0)
                line = text[:m.start()].count("\n") + 1
                if literal in allow:
                    allowed.append(f"{rel}:{line}")
                else:
                    hits.append(f"{rel}:{line} {label}")
    r.add("secrets", not hits,
          f"no unrecognised credential material ({len(allowed)} allowlisted placeholders suppressed)"
          if not hits else f"{len(hits)} potential secret(s): {hits[:3]}")


def frontmatter_name(skill_dir):
    """Read the `name:` field from a skill's YAML frontmatter."""
    path = os.path.join(MIRROR, skill_dir, "SKILL.md")
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
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


def check_config(r):
    try:
        import json5
        with open(CONFIG) as fh:
            cfg = json5.load(fh)
    except Exception as exc:
        r.add("config", False, f"cannot parse {os.path.basename(CONFIG)} as JSON5: {exc}")
        return

    skills_cfg = cfg.get("skills") or {}
    entries = skills_cfg.get("entries") or {}
    load = skills_cfg.get("load") or {}

    # every declared skill must exist in the mirror (or be the conformance skill)
    unknown = []
    for name in entries:
        if name == "blackheart-conformance":
            continue
        if not any(frontmatter_name(d) == name for d in skill_dirs()):
            unknown.append(name)

    # every extraDir must exist
    bad_dirs = [d for d in (load.get("extraDirs") or [])
                if not os.path.isdir(os.path.join(REPO, d))]

    known = {frontmatter_name(d) for d in skill_dirs()} | {"blackheart-conformance"}
    covered = len(known & set(entries))
    ok = not unknown and not bad_dirs
    detail = (f"parses as JSON5; {covered} skills declared of {len(known)} available")
    if unknown:
        detail += f"; unknown skill(s): {unknown[:5]}"
    if bad_dirs:
        detail += f"; missing extraDir(s): {bad_dirs[:5]}"
    r.add("config", ok, detail)


def main():
    r = Result()
    check_adapters(r)
    check_integrity(r)
    check_links(r)
    check_index(r)
    check_secrets(r)
    check_config(r)

    width = max(len(n) for n, _, _ in r.checks)
    print("Blackhearts validation")
    print("=" * (width + 30))
    for name, ok, detail in r.checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
    print("=" * (width + 30))
    failed = r.failed
    if failed:
        print(f"  {len(failed)} check(s) FAILED: {', '.join(n for n, _, _ in failed)}")
        return 1
    print(f"  all {len(r.checks)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
