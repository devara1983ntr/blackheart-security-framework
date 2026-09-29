#!/usr/bin/env python3
"""Refuse to let a generator record a damaged tree as fact.

Generators in this repository turn the working tree into a published claim:
`gen_manifest.py` produces the file counts and hashes, `gen_index.py`
produces the file list. If either is run with `--write` while the tree is
incomplete, it does not warn — it faithfully describes the damage, and the
damage becomes the committed truth. That is the worst possible failure mode
for a project whose entire argument is that its published numbers are real.

This has happened here: a working tree was missing two vendored files, a
manifest was regenerated over it, and the counts dropped from 3,864 to
3,863 with nothing but a diff line to show for it.

So: before any generator writes, confirm the working tree still matches the
commit it is supposed to be describing. A dirty tree is refused, and the
operator is told to restore it first. `--allow-dirty` exists for the
legitimate case of generating an index that must include a file being added
right now.

    python3 .github/scripts/guard_clean.py <repo-root>
"""
import os
import subprocess
import sys

MIRROR = "skills/third-party/claude-skills"
CATALOG = "skills/catalog"


def dirty_paths(repo):
    """Paths that differ from HEAD, limited to the generated-source tree.

    Scoped deliberately: unrelated edits elsewhere must not block a
    generator, but a change under the mirror or the catalogue means the
    generated facts would no longer describe the committed state.
    """
    out = subprocess.run(
        ["git", "status", "--porcelain", "--", MIRROR, CATALOG],
        cwd=repo, capture_output=True, text=True,
    ).stdout
    return [l[3:].strip().strip('"') for l in out.splitlines() if l.strip()]


def check(repo, allow_dirty=False):
    try:
        paths = dirty_paths(repo)
    except Exception as exc:                      # git missing, not a repo
        sys.stderr.write(f"guard: could not read git status ({exc}); "
                         f"refusing to generate.\n")
        return 1
    if not paths:
        return 0
    if allow_dirty:
        sys.stderr.write(f"guard: --allow-dirty given; {len(paths)} path(s) "
                         f"under the mirror differ from HEAD\n")
        return 0
    sys.stderr.write(
        "guard: refusing to generate — the tree is not in the state it would\n"
        "       be describing. Regenerating now would record the difference\n"
        "       as fact instead of reporting it.\n\n"
        f"         {len(paths)} path(s) under {MIRROR}/ or {CATALOG}/ differ "
        f"from HEAD:\n")
    for p in paths[:10]:
        sys.stderr.write(f"           {p}\n")
    if len(paths) > 10:
        sys.stderr.write(f"           … and {len(paths) - 10} more\n")
    sys.stderr.write(
        "\n         Restore them first:\n"
        f"           git checkout -- {MIRROR}/ {CATALOG}/\n"
        "\n         If the difference is real and intended, stage or commit it,\n"
        "         then regenerate. Only pass --allow-dirty if you are certain.\n")
    return 1


if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    sys.exit(check(repo, "--allow-dirty" in sys.argv[2:]))
