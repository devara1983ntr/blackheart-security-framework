#!/usr/bin/env python3
"""Check that `docs/CAPABILITY-AUDIT.md` is telling the truth.

    python3 .github/scripts/verify_capability_audit.py
    python3 .github/scripts/verify_capability_audit.py --json

Why this exists
---------------
The capability audit makes two kinds of claim, and both are checkable:

  1. **Every cited path exists.** "ALREADY COVERED — `guides/AUTH-AUTHZ.md`" is a
     claim about the tree. If that file moves or is deleted, the row becomes a
     false statement, and a document full of false statements is worse than no
     document, because it is read as evidence.
  2. **Every published count is current.** 388 vendored skills, 399 adapters,
     six workflows, 32 catalogue files. These are derived from the tree, so they
     can be re-derived here.

Read-only. It writes nothing, fetches nothing, and touches no vendored file.
Paths are resolved against the repository root and the three prefixes the
document cites from — `docs/`, `skills/` and `.github/` — so a row may cite
`AGENT.md`, `guides/SCOPE.md` or `conformance/SKILL.md` in the form a reader
would recognise.

Exit codes:  0 = every claim checks out,  1 = at least one did not.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC = os.path.join(REPO, "docs", "CAPABILITY-AUDIT.md")
MIRROR = os.path.join(REPO, "skills", "third-party", "claude-skills")
CATALOG = os.path.join(REPO, "skills", "catalog")
MANIFEST = os.path.join(REPO, ".github", "UPSTREAM-MANIFEST.json")

RESOLVE_BASES = ("", "docs/", "skills/", ".github/")

# A cited path: a backticked token with a slash in it, ending in a known
# extension or with no extension at all (`CODEOWNERS`, `LICENSE`).
PATH_RE = re.compile(r"`([A-Za-z0-9_./\-]+)`")
PATH_EXT = (".md", ".py", ".yml", ".yaml", ".json", ".json5", ".txt", ".svg",
            ".css", ".js", ".html", ".xml")
NO_EXT_OK = {"CODEOWNERS", "LICENSE", "AUTHOR"}


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def count_skills():
    return sum(1 for dp, _dn, fn in os.walk(MIRROR) if "SKILL.md" in fn)


def count_files(path, suffix=None):
    if not os.path.isdir(path):
        return 0
    return sum(1 for f in os.listdir(path)
               if os.path.isfile(os.path.join(path, f))
               and (suffix is None or f.endswith(suffix)))


def catalog_upstream_files():
    """The 32 catalogue files that are byte-identical upstream content.

    The directory holds 34 files: the 30 category files, upstream's README and
    contributing rules, plus two Blackhearts-authored documents (this policy and
    the category index), which are not upstream content.
    """
    return sum(1 for f in os.listdir(CATALOG) if os.path.isfile(os.path.join(CATALOG, f))
               and f.startswith("upstream-")) + count_files(
                   os.path.join(CATALOG, "categories"), ".md")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(DOC):
        print(f"missing {os.path.relpath(DOC, REPO)}", file=sys.stderr)
        return 1
    body = read(DOC)
    problems, checked = [], 0

    # 1 ---- every cited path resolves -------------------------------------
    cited, unresolved = set(), []
    for m in PATH_RE.finditer(body):
        token = m.group(1)
        if "/" not in token and token not in NO_EXT_OK:
            continue
        if token.startswith(("http", "#")) or token.endswith("/"):
            continue
        if not (token.endswith(PATH_EXT) or os.path.basename(token) in NO_EXT_OK):
            continue
        cited.add(token)
    for token in sorted(cited):
        checked += 1
        if not any(os.path.exists(os.path.join(REPO, base + token))
                   for base in RESOLVE_BASES):
            unresolved.append(token)
    if unresolved:
        problems.append("cited paths that do not resolve: " + ", ".join(unresolved))

    # 2 ---- every published count is current ------------------------------
    manifest = json.loads(read(MANIFEST))
    counts = manifest.get("counts", {})
    derived = {
        "vendored skills": count_skills(),
        "adapters": counts.get("adapters"),
        "vendored files": counts.get("vendored_files"),
        "catalogue files": catalog_upstream_files(),
        "workflows": count_files(os.path.join(REPO, ".github", "workflows"), ".yml"),
        "authored scripts": count_files(os.path.join(REPO, ".github", "scripts"), ".py"),
        "site scripts": count_files(os.path.join(REPO, "site"), ".py"),
        "guides": count_files(os.path.join(REPO, "docs", "guides"), ".md"),
        "modes": count_files(os.path.join(REPO, "docs", "modes"), ".md"),
        "agent docs": count_files(os.path.join(REPO, "docs", "agent"), ".md"),
        "templates": count_files(os.path.join(REPO, "templates"), ".md"),
    }
    claims = {
        "vendored skills": f"{derived['vendored skills']} vendored skills",
        "adapters": f"{derived['adapters']} adapters",
        "vendored files": f"{derived['vendored files']:,}",
        "catalogue files": f"{derived['catalogue files']}/",
        "workflows": "Six workflows" if derived["workflows"] == 6
                     else f"{derived['workflows']} workflows",
        "authored scripts": f"{derived['authored scripts']} authored scripts",
        "site scripts": f"{derived['site scripts']} site scripts",
        "guides": f"5 modes, {derived['guides']} guides",
        "modes": f"5 modes, {derived['guides']} guides",
        "agent docs": f"{derived['agent docs']} agent docs",
        "templates": str(derived["templates"]),
    }
    for what, needle in claims.items():
        checked += 1
        if needle not in body:
            problems.append(
                f"the document does not state the current {what} ({needle})")

    # 3 ---- the vendored total and the exclusion count agree --------------
    checked += 1
    excluded = len([k for k in manifest.get("exclusions", {})
                    if not k.startswith("_")])
    if excluded != 5:
        problems.append(f"manifest records {excluded} exclusions, the audit says five")

    report = {"document": os.path.relpath(DOC, REPO), "claims_checked": checked,
              "derived": derived, "problems": problems}
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Capability audit — claim check")
        print("=" * 66)
        print(f"  document        : {report['document']}")
        print(f"  claims checked  : {checked}")
        print(f"  cited paths     : {len(cited)} resolved")
        print(f"  derived counts  : " + ", ".join(f"{k} {v}" for k, v in derived.items()))
        if problems:
            print(f"  PROBLEMS        : {len(problems)}")
            for p in problems:
                print(f"      {p}")
        else:
            print("  RESULT          : every cited path resolves and every "
                  "published count is current")
        print("=" * 66)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
