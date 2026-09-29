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
  integrity    EVERY vendored file is byte-identical to the pinned upstream
               commit, per .github/UPSTREAM-MANIFEST.json. Covers the whole
               mirror: skills, commands, agents, scripts, plugin manifests,
               standards, audit records, and documentation. Catches local edits
               and incomplete syncs.
  catalog      The vendored discovery index is byte-identical to its source.
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
LINK_DEFECTS = os.path.join(REPO, ".github", "upstream-link-defects.json")

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
    """Yield repo-relative paths of every tracked file, deterministically.

    Bytecode caches are skipped. They are build output, not repository content,
    and a validator that trips over them trains people to ignore its output.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in (".git", "__pycache__")
        )
        for name in sorted(filenames):
            if name.endswith((".pyc", ".pyo")):
                continue
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


# Vendored areas that are not skills but are still third-party content inside
# the framework. Each needs an adapter, or it is unaudited content.
COLLECTION_DIRS = (
    "commands", "agents", "scripts", "standards", "audit", "templates",
    "orchestration", "custom-gpt", "docs",
    ".claude-plugin", ".codex-plugin", ".claude",
)


def check_adapters(r):
    skills = skill_dirs()
    nested = skill_dirs(include_nested=True)
    fixtures = len(nested) - len(skills)
    missing = [s for s in skills if not os.path.isfile(os.path.join(MIRROR, s, ADAPTER))]

    collections = sorted(
        d for d in COLLECTION_DIRS
        if os.path.isdir(os.path.join(MIRROR, d))
        and not os.path.isfile(os.path.join(MIRROR, d, ADAPTER)))

    detail = (f"{len(skills)} skills have an adapter"
              + (f" (+{fixtures} nested test fixture(s) covered by their parent)"
                 if fixtures else "")
              + f"; {len(COLLECTION_DIRS)} vendored collections")
    if missing:
        detail += f"; MISSING skill adapters: {missing[:5]}"
    if collections:
        detail += f"; MISSING collection adapters: {collections}"
    r.add("adapters", not (missing or collections), detail)


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_integrity(r):
    """Every vendored file must match the pinned upstream commit, byte for byte.

    This is file-level rather than per-skill on purpose. Per-skill digests only
    covered the 388 skill directories, which meant the commands, agents,
    scripts, plugin manifests, standards, audit records, and documentation that
    make up the rest of the mirror were vendored with nothing verifying them.
    """
    with open(MANIFEST) as fh:
        man = json.load(fh)
    expected = man["vendored"]
    expected_adapters = man.get("adapters", {})

    actual, actual_adapters = {}, {}
    for dp, dn, fn in os.walk(MIRROR):
        dn[:] = sorted(d for d in dn if d != "__pycache__")
        for name in sorted(fn):
            if name.endswith((".pyc", ".pyo")):
                continue
            full = os.path.join(dp, name)
            rel = os.path.relpath(full, MIRROR).replace(os.sep, "/")
            if name == ADAPTER:
                actual_adapters[rel] = full
            else:
                actual[rel] = full

    changed = [rel for rel, meta in expected.items()
               if rel in actual and file_sha256(actual[rel]) != meta["sha256"]]
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    ad_missing = sorted(set(expected_adapters) - set(actual_adapters))
    ad_extra = sorted(set(actual_adapters) - set(expected_adapters))
    ad_changed = [rel for rel, meta in expected_adapters.items()
                  if rel in actual_adapters
                  and file_sha256(actual_adapters[rel]) != meta["sha256"]]

    ok = not (changed or missing or extra or ad_missing or ad_extra or ad_changed)
    up = man["upstream"]["skills_commit"]
    detail = (f"{len(expected)} vendored files byte-identical to {up[:7]}"
              f"; {len(expected_adapters)} adapters")
    for label, items in (("DRIFT", changed), ("MISSING", missing),
                         ("UNEXPECTED", extra), ("ADAPTER-MISSING", ad_missing),
                         ("ADAPTER-EXTRA", ad_extra), ("ADAPTER-DRIFT", ad_changed)):
        if items:
            detail += f"; {label}: {len(items)} e.g. {items[:3]}"
    r.add("integrity", ok, detail)


# Paths holding verbatim third-party content. Links inside these are upstream's
# own repo-relative links, which do not all resolve in a partial vendoring.
# They are reported as known defects and never auto-fixed, so the copy stays
# byte-comparable to its source. Everything Blackhearts authors is enforced.
VENDORED_PREFIXES = (
    "skills/third-party/claude-skills/",
    "skills/catalog/categories/",
)
VENDORED_FILES = (
    "skills/catalog/upstream-README.md",
    "skills/catalog/upstream-CONTRIBUTING.md",
)


def is_vendored(rel):
    return rel.startswith(VENDORED_PREFIXES) or rel in VENDORED_FILES


def check_catalog(r):
    """The vendored discovery index must stay byte-identical to its source.

    It is a reference index, not executable content, but it is still third-party
    material: if it is edited locally, the record of what upstream published is
    no longer trustworthy. Same rule as the skill mirror, different source.
    """
    with open(MANIFEST) as fh:
        man = json.load(fh)
    cat = man.get("catalogue") or man.get("catalog")
    if not cat:
        r.add("catalog", False, "manifest has no catalogue section")
        return
    drift, missing = [], []
    for rel, meta in cat.items():
        full = os.path.join(REPO, rel)
        if not os.path.isfile(full):
            missing.append(rel)
        elif file_sha256(full) != meta["sha256"]:
            drift.append(rel)
    on_disk = {p for p in walk_files(REPO)
               if p.startswith("skills/catalog/categories/")
               or p in ("skills/catalog/upstream-README.md",
                        "skills/catalog/upstream-CONTRIBUTING.md")}
    extra = sorted(on_disk - set(cat))
    ok = not (drift or missing or extra)
    detail = f"{len(cat)} catalogue files verified byte-identical"
    for label, items in (("DRIFT", drift), ("MISSING", missing), ("UNEXPECTED", extra)):
        if items:
            detail += f"; {label}: {len(items)} e.g. {items[:3]}"
    r.add("catalog", ok, detail)


def load_link_registry():
    """The registered, individually explained upstream link defects."""
    if not os.path.isfile(LINK_DEFECTS):
        return None, "link defect registry missing; run gen_link_registry.py --write"
    try:
        with open(LINK_DEFECTS) as fh:
            data = json.load(fh)
        return {(e["file"], e["line"], e["target"]) for e in data["entries"]}, ""
    except Exception as exc:
        return None, f"link defect registry unreadable: {exc}"


def check_links(r):
    """Every local link resolves, and every dead vendored link is accounted for.

    Two different failures, handled differently on purpose:

      * A broken link in Blackhearts-authored content is a defect. It is
        fixed. It fails the build.

      * A broken link inside byte-identical vendored content is an upstream
        defect. It is NOT fixed, because vendored files must remain
        byte-identical or the integrity guarantee means nothing. But it must
        be registered in .github/upstream-link-defects.json with a reason.

    A count in a sentence is not accounting. Before the registry existed, a
    new dead upstream link would have been invisible, and a dead
    Blackhearts-authored link was being reported as if it were upstream's.
    """
    total = 0
    broken = []          # (rel, line, target, vendored)
    for rel in walk_files(REPO):
        if not rel.endswith(".md"):
            continue
        full = os.path.join(REPO, rel)
        vendored = is_vendored(rel)
        with open(full, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        for m in MD_LINK.finditer(body):
            target = m.group(2)
            if target.startswith(("http://", "https://", "#", "mailto:", "data:")):
                continue
            clean = target.split("#")[0]
            if not clean:
                continue
            # A bare `path` is a documentation template placeholder, not a link.
            if clean.lower() == "path":
                continue
            total += 1
            if not os.path.exists(os.path.normpath(
                    os.path.join(os.path.dirname(full), clean))):
                broken.append((rel, body[:m.start()].count("\n") + 1, target, vendored))

    ours = [b for b in broken if not b[3]]
    theirs = [b for b in broken if b[3]]

    registered, reg_err = load_link_registry()
    if registered is None:
        r.add("links", False, f"{total} local links checked; {reg_err}")
        return

    # Adapters are Blackhearts-authored even though they live inside the
    # vendored tree. They must be correct, so they are held to the same
    # standard as the rest of our documentation and can never be registered.
    unregistered = [(rel, line, t) for rel, line, t, _v in theirs
                    if (rel, line, t) not in registered
                    and not os.path.basename(rel) == ADAPTER]
    adapter_broken = [(rel, line, t) for rel, line, t, _v in theirs
                      if os.path.basename(rel) == ADAPTER]
    ours += [(rel, line, t, False) for rel, line, t in adapter_broken]

    detail = (f"{total} local links checked; {len(ours)} broken in "
              f"Blackhearts-authored docs; {len(theirs)} in vendored upstream "
              f"content ({len(theirs) - len(unregistered)} registered)")
    if unregistered:
        detail += f"; {len(unregistered)} UNREGISTERED"
    r.add("links", not ours and not unregistered, detail
          + (f"; e.g. {(ours + unregistered)[:3]}" if (ours or unregistered) else ""))


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
    except ImportError:
        r.add("config", False,
              "cannot parse the example config: the 'json5' module is not installed. "
              "Run `python3 -m pip install json5` (CI does this automatically). "
              "The config is JSON5, not JSON — stdlib json cannot read it by design.")
        return
    try:
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
    check_catalog(r)
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
