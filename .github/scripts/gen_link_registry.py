#!/usr/bin/env python3
"""
Register every broken link inside byte-identical vendored content.

Run:      python3 .github/scripts/gen_link_registry.py
Verify:   python3 .github/scripts/gen_link_registry.py --check
Write:    python3 .github/scripts/gen_link_registry.py --write

Why this exists.

The mirror is a mirror. Vendored files are byte-identical to upstream, and
that is the property the whole integrity guarantee rests on: if Blackhearts
edits upstream content, the integrity check can no longer prove that the
Blackhearts side added nothing of its own to a third-party instruction.

Upstream ships broken relative links. There are a lot of them. The tempting
response is to "fix" them, and that response is wrong: editing them would
break the integrity check, and more importantly it would put Blackhearts
words inside a document that claims to be someone else's.

So they are not fixed. They are REGISTERED.

Before this script, the repository said "159 in vendored upstream content
(documented, unmodified)" -- a number in a sentence, with no way to check it,
no way to see which links they were, and no way for a NEW broken link to be
noticed. A count is not accounting.

This turns that sentence into a machine-checked registry. Every broken link
inside vendored content gets an entry with its file, line, target, and a
reason. validate.py then requires that every detected broken link is
registered, which means:

  * a new upstream broken link fails CI until someone explains it, and
  * a Blackhearts-authored broken link fails CI always, because adapters are
    excluded from this registry by construction.

That is the difference between a documented defect and a known-and-tolerated
defect. The second one is a control.

Exit codes:  0 = in sync (or written), 1 = drift, 2 = bad usage.
"""

import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The link grammar, the vendored-path test, the skip rules and the file walk
# are imported from validate.py rather than reimplemented. An earlier version
# of this script had its own copy and disagreed with the validator by 4 links
# -- two implementations of "a broken link" is two answers, and the registry is
# worthless if it does not cover exactly what the gate detects.
import validate
MIRROR = os.path.join(REPO, "skills", "third-party", "claude-skills")
CATALOG = os.path.join(REPO, "skills", "catalog")
ADAPTER = "_BLACKHEART-ADAPTER.md"
REGISTRY = os.path.join(REPO, ".github", "upstream-link-defects.json")

LINK = validate.MD_LINK


def is_vendored(rel):
    return validate.is_vendored(rel)


def classify(rel, target):
    """A reason a link is dead, derived from shape, not from opinion."""
    if target.startswith(("http://", "https://", "#", "mailto:")):
        return "external-or-anchor", "external or in-document reference"
    if any(t in target for t in ("<", ">", "skill-name", "/url", "domain/",
                                 "your-", "example", "path/to")):
        return "upstream-placeholder", "upstream template placeholder, never a real path"
    if target.endswith(("/", "#")):
        return "upstream-directory", "upstream links a directory, not a file"
    if re.search(r"[^/]/$", target):
        return "upstream-directory", "upstream links a directory, not a file"
    return "upstream-missing-path", "target does not exist at this path upstream"


def detect():
    """Every broken local link in vendored content.

    Semantics are byte-for-byte validate.py's: same regex, same skip rules
    (external, anchor, mailto, data:, and the bare `path` template
    placeholder), same normalisation, same walk. Adapters are excluded, so a
    Blackhearts-authored broken link can never be registered away.
    """
    # A list, not a dict: two identical links can sit on one line, and a dict
    # keyed on (file, line, target) would silently collapse them. That hid 2
    # occurrences -- the registry reported 109 for 111 detected.
    found = []
    for rel in validate.walk_files(REPO):
        if not rel.endswith(".md") or not is_vendored(rel):
            continue
        if os.path.basename(rel) == ADAPTER:
            continue
        full = os.path.join(REPO, rel)
        with open(full, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        for m in LINK.finditer(body):
            target = m.group(2)
            if target.startswith(("http://", "https://", "#", "mailto:", "data:")):
                continue
            clean = target.split("#")[0]
            if not clean or clean.lower() == "path":
                continue
            if os.path.exists(os.path.normpath(os.path.join(os.path.dirname(full), clean))):
                continue
            lineno = body[:m.start()].count("\n") + 1
            found.append((rel, lineno, target, classify(rel, target)[0]))
    return found


def build():
    found = detect()
    entries = []
    for i, (rel, lineno, target, cat) in enumerate(sorted(found), 1):
        reason = classify(rel, target)[1]
        entries.append({
            "id": f"UL-{i:04d}",
            "file": rel,
            "line": lineno,
            "target": target,
            "category": cat,
            "reason": reason,
        })
    by_cat = {}
    for e in entries:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + 1
    return {
        "_comment": [
            "Broken relative links inside byte-identical vendored upstream content.",
            "These are NOT fixed, because vendored files must remain byte-identical to",
            "upstream or the integrity guarantee is meaningless. They are registered here",
            "so that:",
            "  1. a NEW broken link fails CI until a human registers and explains it;",
            "  2. a Blackhearts-authored broken link always fails CI (adapters are",
            "     excluded from this registry by construction);",
            "  3. the count is verifiable rather than a claim in a sentence.",
            "",
            "Regenerate:  python3 .github/scripts/gen_link_registry.py --write",
            "Verified by: python3 .github/scripts/validate.py   (check: links)",
            "",
            "Fixing these in place is possible but is refused by policy. It would put",
            "Blackhearts text inside documents that claim to be another author's, and",
            "would make the integrity check unable to prove what the mirror contains.",
        ],
        "upstream": {
            "repository": "https://github.com/alirezarezvani/claude-skills",
            "commit": "19392f7a08264ed00486a251f5b2098321771f94",
            "license": "MIT (c) 2025 Alireza Rezvani",
        },
        "policy": {
            "modified_in_vendored_content": False,
            "rationale": ("a mirror that edits its source stops being a mirror and "
                          "stops being evidence"),
            "blackhearts_authored_broken_links_allowed": 0,
        },
        "totals": {
            "broken_links": len(entries),
            "by_category": by_cat,
        },
        "entries": entries,
    }


def render(data):
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def main(argv):
    args = argv[1:]
    if not args:
        args = ["--check"]
    if len(args) > 1 or args[0] not in ("--check", "--write"):
        sys.stderr.write(__doc__)
        return 2

    want = render(build())
    have = ""
    if os.path.isfile(REGISTRY):
        with open(REGISTRY, encoding="utf-8") as fh:
            have = fh.read()

    if have == want:
        n = json.loads(want)["totals"]["broken_links"]
        print(f"  link defect registry in sync ({n} registered)")
        return 0

    if args[0] == "--write":
        with open(REGISTRY, "w", encoding="utf-8") as fh:
            fh.write(want)
        print(f"  link defect registry written ({json.loads(want)['totals']['broken_links']} registered)")
        return 0

    old = json.loads(have)["totals"]["broken_links"] if have else 0
    new = json.loads(want)["totals"]["broken_links"]
    print(f"  FAIL  links      registry is stale: {old} registered, {new} detected")
    print("        run:  python3 .github/scripts/gen_link_registry.py --write")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
