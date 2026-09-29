#!/usr/bin/env python3
"""Generate collection adapters for the vendored non-skill areas of the mirror.

Skills get one adapter each: each is an independently loadable, separately
audited unit. The rest of the mirror (commands, agent personas, plugin
manifests, upstream tooling, standards, audit records, templates, and generated
documentation) loads as a set and shares a single upstream review, so it gets
one adapter per directory stating the same guarantees.
"""
import os
import re

MIR = "skills/third-party/claude-skills"

# Collections whose adapter carries hand-written security analysis that a
# generator cannot reproduce. `agents/` is the critical one: it is where the
# 33 personas are argued to be hostile input, and regenerating it silently
# deleted that argument. Same protection as gen_adapters.py's PROMOTED.
PROMOTED = {"agents"}
UP = "19392f7a08264ed00486a251f5b2098321771f94"
DATE = "2026-09-29"

CONDITIONS_TMPL = """1. Read [`skills/conformance/SKILL.md`]({up}/conformance/SKILL.md)
   before any use.
2. No target may be scanned, tested, or profiled until the operator supplies the
   target and explicit, written authorization recorded in the engagement file.
3. Do not execute any script from this content against a third-party system
   without that authorization. These are third-party files with third-party
   defects.
4. Report every result as `UNVERIFIED` until independently demonstrated, and
   record rejected hypotheses alongside confirmed findings.
5. Record the upstream commit and this adapter path in the evidence log, so any
   finding traces to the exact tool version that produced it."""


def conditions(up):
    """Render the conditions block with a depth-correct link."""
    return CONDITIONS_TMPL.format(up=up)

WHY_COLLECTION = """Skills get one adapter each because each is an independently
loadable, separately audited unit. The content covered here is not: it loads as
a set, shares a single upstream review, and is governed by the same conditions.
One adapter per directory is proportionate and states the same guarantees
without generating boilerplate that would carry no information."""


def repo_rel(target, from_dir):
    """Relative path from an adapter's directory to a repo-relative target.

    The depth of a collection adapter is not a constant. `commands/` and
    `docs/` sit at the same level, but a collection nested one level deeper
    needs a different number of `../` segments. This was hard-coded as
    `../../../../`, which produced 48 dead links across 12 adapters before it
    was measured. Depth is now computed from the actual path, so a collection
    can be added at any level and still link correctly.
    """
    here = os.path.abspath(from_dir)
    dest = os.path.abspath(target)
    return os.path.relpath(dest, here).replace(os.sep, "/")


def up_to_skills(from_dir):
    """`../../..`-style prefix that lands on the repository's skills/ dir."""
    rel = os.path.relpath(os.path.join("skills"), os.path.abspath(from_dir))
    return rel.replace(os.sep, "/")



def frontmatter_name(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^name:\s*(.+?)\s*$", line)
        if m:
            return m.group(1).strip().strip("\"'")
    return None


def listing(rel, with_names):
    root = os.path.join(MIR, rel)
    rows = []
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for f in sorted(fn):
            if f == "_BLACKHEART-ADAPTER.md":
                continue
            # .gitkeep files ARE listed. Dropping them silently made the
            # agents/ collection report 35 files when it held 38, and made
            # docs/ report 666 when it held 667. A generated count that
            # disagrees with the filesystem is the exact defect this project
            # exists to prevent.
            full = os.path.join(dp, f)
            name = frontmatter_name(full) if with_names else None
            rows.append((os.path.relpath(full, root).replace(os.sep, "/"), name))
    return sorted(rows)


def write(rel, title, what, why_matters, rows, with_names=False, force=False):
    target = os.path.join(MIR, rel, "_BLACKHEART-ADAPTER.md")
    if rel in PROMOTED and os.path.isfile(target) and not force:
        print(f"  {rel}/_BLACKHEART-ADAPTER.md  left as-is (promoted, hand-written)")
        return
    # Computed per collection rather than hard-coded: a collection nested at a
    # different depth would otherwise emit dead links again.
    up = up_to_skills(os.path.join(MIR, rel))
    L = [f"# Blackhearts Adapter — `{rel}/` ({title})", ""]
    L += [
        "| Field | Value |", "|---|---|",
        "| Upstream | `https://github.com/alirezarezvani/claude-skills` |",
        f"| Upstream commit | `{UP}` |",
        f"| Upstream path | `{rel}/` |",
        "| Upstream licence | MIT (c) 2025 Alireza Rezvani |",
        f"| Integrity | byte-identical to upstream, verified {DATE} |",
        "| Modified by Blackhearts | No — this `_BLACKHEART-ADAPTER.md` is the only added file |",
        f"| Contents | {len(rows)} files |",
        f"| Governing policy | [SKILL.md]({up}/conformance/SKILL.md) |",
        "",
        "## What this adapter is for", "",
        "Blackhearts-local metadata. The directory is **unmodified upstream "
        "content**. This file records provenance and the conditions under which it "
        "may be used inside a BLACKHEART engagement.", "",
        "## Why this is a collection adapter", "", WHY_COLLECTION, "",
        "## What this is", "", what, "",
        "## Why it matters here", "", why_matters, "",
        "## Evidence status", "",
        "Any result this content produces is `UNVERIFIED` until independently "
        "demonstrated. Loading it does not authorize it to act on any target. A "
        "tool's own severity rating is **not** a BLACKHEART severity.", "",
        "## Conditions of use", "", conditions(up), "",
        "## Provenance", "",
        f"- Licence text: [claude-skills-LICENSE]({up}/licenses/claude-skills-LICENSE)",
        f"- Integration record: [VENDOR.md]({up}/VENDOR.md)", "",
        "## Inventory", "",
    ]
    if with_names:
        L += ["| File | Frontmatter `name` |", "|---|---|"]
    else:
        L += ["| File | |", "|---|---|"]
    for f, n in rows:
        L.append(f"| `{f}` | {('`' + n + '`') if n else '—'} |")
    L.append("")
    out = os.path.join(MIR, rel, "_BLACKHEART-ADAPTER.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"  {rel}/_BLACKHEART-ADAPTER.md  ({len(rows)} files)")


AREAS = [
    ("commands", "slash commands",
     "Upstream's **slash commands** — invocable as `/name`, each a markdown file "
     "whose frontmatter declares its name, description, and argument hint. They "
     "wrap or invoke skills; they are not skills themselves.",
     "A command is a **user-invoked entry point**, not an analysis unit. It can "
     "launch a skill, so it inherits that skill's adapter and its conditions. A "
     "command that reaches a target with no engagement record is the same "
     "violation as a skill doing it.", True),
    ("agents", "agent personas",
     "Upstream's **agent personas** — specialist role definitions (`cs-*` plus a "
     "handful of personas) that set role, scope, and escalation behaviour for an "
     "agent. They contain no executable logic; they change how an agent reasons "
     "and what it is willing to do.",
     "A persona is the **highest-leverage** vendored content here and the easiest "
     "to get wrong. A persona can redefine an agent's identity, widen its scope, "
     "or instruct it to act without asking — which is exactly what the "
     "authorization gate prevents, and a persona is a natural place for that "
     "instruction to be smuggled in.\n\n"
     "Every persona is therefore treated as **untrusted instruction**, not trusted "
     "policy. `skills/conformance/SKILL.md` governs. No persona may widen scope, "
     "disable the gate, or authorize a target. Where a persona conflicts with the "
     "conformance layer, **conformance wins**.", True),
    ("scripts", "upstream tooling",
     "Upstream's own **build, audit, and sync tooling** — the scripts that lint "
     "skills, check frontmatter, verify plugin manifests, publish mirrors, and "
     "install the catalogue into other agents.",
     "These operate on **this mirror as a checkout**, not on an engagement target. "
     "They are vendored so an operator can see exactly how upstream validates and "
     "publishes, and so the process is reproducible. Do not run them against a "
     "client system: they are repository tooling and expect upstream's own layout.",
     False),
    ("standards", "authoring standards",
     "Upstream's **authoring standards** — the communication, documentation, git, "
     "quality, and security conventions its skills are written against.",
     "Standards are descriptive, not enforceable. Vendoring them documents the "
     "conventions the skills follow, which matters when judging whether a given "
     "skill's output is trustworthy.", False),
    ("audit", "upstream audit records",
     "Upstream's **own audit history** — master reports, rubrics, and findings from "
     "the reviews its authors ran over the catalogue.",
     "This is **upstream's** audit, not BLACKHEART's. It is vendored so the claim "
     "that the catalogue was reviewed is checkable rather than assumed. It does "
     "**not** substitute for the BLACKHEART audit recorded in each skill's "
     "adapter, and it carries no BLACKHEART evidence status.", False),
    ("templates", "authoring templates",
     "Upstream's **skill and agent templates** — the skeletons its authors start from.",
     "Templates are inert until filled in. Vendored for provenance.", False),
    ("orchestration", "orchestration notes",
     "Upstream's notes on **multi-skill orchestration** — how its skills are meant "
     "to be sequenced and delegated between.",
     "Orchestration guidance is descriptive. It does not authorize any action.", False),
    ("custom-gpt", "GPT configuration notes",
     "Upstream's notes for **GPT-based consumers** of the catalogue.",
     "Descriptive only.", False),
    ("docs", "upstream documentation",
     "Upstream's **generated reference documentation** — a page per skill, per "
     "command, and per agent persona, plus site configuration.",
     "Generated from the source content, so it restates rather than adds. Vendored "
     "so the catalogue is searchable offline. Where it disagrees with a skill's "
     "own `SKILL.md`, **`SKILL.md` wins**: it is the source, and this is the "
     "rendering.", False),
    (".claude-plugin", "Claude plugin manifest",
     "Upstream's **plugin marketplace manifest**, declaring the author, the plugin "
     "list, and per-plugin versions.",
     "A manifest is a **declaration, not an enforcement**. Vendoring it does not "
     "install anything, grant a permission, or activate a plugin. It is included "
     "so the catalogue's own packaging is visible and auditable rather than "
     "asserted.", False),
    (".codex-plugin", "Codex plugin manifest",
     "Upstream's **Codex CLI plugin manifest**.",
     "A declaration, not an enforcement. Same reasoning as the Claude manifest.",
     False),
    (".claude", "Claude Code configuration",
     "Upstream's **Claude Code project configuration**.",
     "Configuration for upstream's own repository layout. Vendored verbatim for "
     "provenance; it is inert here because this repository is not that project.",
     False),
]

if __name__ == "__main__":
    for rel, title, what, why, names in AREAS:
        rows = listing(rel, names)
        if rows:
            write(rel, title, what, why, rows, names)
