#!/usr/bin/env python3
"""
Regenerate .github/UPSTREAM-MANIFEST.json from the current mirror.

The manifest is the integrity record for **every vendored file**, not just
skills. Anything in the mirror that is not listed, or whose SHA-256 differs,
fails the validation gate.

Blackhearts-local files (the `_BLACKHEART-ADAPTER.md` files) are listed in a
separate section so that "extra file" means "unaccounted for", never "expected".
"""
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MIRROR = os.path.join(REPO, "skills", "third-party", "claude-skills")
CATALOG = os.path.join(REPO, "skills", "catalog")
MANIFEST = os.path.join(REPO, ".github", "UPSTREAM-MANIFEST.json")
ADAPTER = "_BLACKHEART-ADAPTER.md"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk(root, skip=()):
    for dp, dn, fn in os.walk(root):
        dn[:] = sorted(d for d in dn if d not in skip)
        for name in sorted(fn):
            full = os.path.join(dp, name)
            yield os.path.relpath(full, root).replace(os.sep, "/"), full


def main():
    # Refuse to describe a tree that does not match the commit it is
    # describing. See guard_clean.py: regenerating over an incomplete tree
    # turns a transient damage into a committed, and false, fact.
    if "--allow-dirty" not in sys.argv:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from guard_clean import check
        if check(REPO):
            return 1

    vendored, adapters = {}, {}
    for rel, full in walk(MIRROR):
        rec = {"sha256": sha(full), "bytes": os.path.getsize(full)}
        if os.path.basename(rel) == ADAPTER:
            adapters[rel] = rec
        else:
            vendored[rel] = rec

    catalog = {}
    for rel, full in walk(CATALOG):
        if rel in ("README.md", "CATEGORY-INDEX.md"):
            continue  # Blackhearts-authored policy documents
        catalog[f"skills/catalog/{rel}"] = {
            "sha256": sha(full), "bytes": os.path.getsize(full)}

    manifest = {
        "_comment": (
            "Integrity record for all third-party content vendored into this "
            "repository. Regenerate with: python3 .github/scripts/gen_manifest.py  "
            "Verify with:      python3 .github/scripts/validate.py"),
        "upstream": {
            "skills_repo": "https://github.com/alirezarezvani/claude-skills",
            "skills_commit": "19392f7a08264ed00486a251f5b2098321771f94",
            "skills_licence": "MIT (c) 2025 Alireza Rezvani",
            "catalogue_repo": "https://github.com/VoltAgent/awesome-openclaw-skills",
            "catalogue_commit": "f274daa9d24c0803c8f94a4630aa4922ca4b950e",
            "catalogue_licence": "MIT (c) 2026 VoltAgent",
        },
        "exclusions": {
            "_comment": (
                "Upstream paths deliberately NOT vendored, and why. Removing an entry "
                "here without re-vendoring will fail the integrity gate."),
            ".gemini/": "458 symlinks re-exposing the same skills in another tool's layout",
            ".codex/": "374 symlinks re-exposing the same skills in another tool's layout",
            ".vibe/": "371 symlinks re-exposing the same skills in another tool's layout",
            ".hermes/": "371 symlinks re-exposing the same skills in another tool's layout",
            ".gitignore": (
                "Would apply to this repository's own git behaviour across the whole "
                "mirror subtree, silently untracking vendored files and breaking the "
                "index and integrity checks"),
        },
        "counts": {
            "vendored_files": len(vendored),
            "adapters": len(adapters),
            "catalogue_files": len(catalog),
        },
        "vendored": vendored,
        "adapters": adapters,
        "catalogue": catalog,
    }

    with open(MANIFEST, "w") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
    print(f"  vendored files : {len(vendored)}")
    print(f"  adapters       : {len(adapters)}")
    print(f"  catalogue files: {len(catalog)}")
    print(f"  manifest       : {os.path.relpath(MANIFEST, REPO)}")


if __name__ == "__main__":
    # sys.exit, not a bare call: this script always returns 1 when the guard
    # refuses, and a discarded return value would report success to CI while
    # having written nothing.
    sys.exit(main())
