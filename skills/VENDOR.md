# Third-Party Attribution and Licensing

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

This directory contains skills authored by third parties. They are used under
their original licences, with attribution preserved. The BLACKHEART framework
itself is MIT-licensed by Roshan; vendored content is **not** relicensed by
inclusion.

## Principle

Vendored code stays recognisably someone else's work. Three rules follow, and
they are not discretionary:

1. **No vendored file is modified.** Every `SKILL.md` and script under
   [`third-party/`](third-party/) is byte-for-byte upstream. Anything BLACKHEART
   needs to add lives in a separate adapter file, never inside the vendored
   content.
2. **Attribution travels with the code.** Each vendored skill has a
   `_BLACKHEART-ADAPTER.md` recording its upstream repository, exact commit,
   path, licence, and local modification status.
3. **Nothing here is claimed as BLACKHEART work.** The conformance layer,
   adapters, and this file are BLACKHEART's. The skills are not.

---

## Source 1 — claude-skills

| Field | Value |
|---|---|
| Upstream | <https://github.com/alirezarezvani/claude-skills> |
| Commit vendored | `19392f7a08264ed00486a251f5b2098321771f94` |
| Commit date | 2026-08-26 |
| Upstream author | Alireza Rezvani <5697919+alirezarezvani@users.noreply.github.com> |
| Licence | MIT — Copyright (c) 2025 Alireza Rezvani |
| Licence text | [`licenses/claude-skills-LICENSE`](licenses/claude-skills-LICENSE) |
| Skills vendored | 8 of 388 canonical |
| Licence compatibility | MIT is permissive; redistribution with attribution is permitted |

### What was vendored

Only skills assessed as relevant to the BLACKHEART methodology, and only from
**canonical** skill directories:

| Skill | Upstream path | Governs |
|---|---|---|
| `ai-security` | `engineering-team/skills/ai-security` | `docs/guides/AGENTIC-AI-SECURITY.md` |
| `red-team` | `engineering-team/skills/red-team` | `docs/modes/RED-HEART-ADVERSARY-EMULATION.md` |
| `cloud-security` | `engineering-team/skills/cloud-security` | `docs/guides/CLOUD-IDENTITY.md` |
| `security-pen-testing` | `engineering-team/skills/security-pen-testing` | `docs/guides/WEB-API-TESTING.md` |
| `dependency-auditor` | `engineering/skills/dependency-auditor` | `docs/guides/SUPPLY-CHAIN.md` |
| `threat-detection` | `engineering-team/skills/threat-detection` | `docs/guides/ADVERSARY-EMULATION.md` |
| `senior-security` | `engineering-team/skills/senior-security` | `docs/guides/ATTACK-PATHS.md`, `SUPPLY-CHAIN.md` |
| `incident-response` | `engineering-team/skills/incident-response` | `docs/guides/ADVERSARY-EMULATION.md` |

### Upstream mirror trees — not vendored

Upstream contains cross-platform mirror trees at `.gemini/`, `.codex/`,
`.vibe/`, and `.hermes/`, built as **relative symlinks** into the canonical
skill directories.

These were **not** copied. Upstream's own `INSTALLATION.md` documents that on
Windows, or wherever `core.symlinks=false`, these check out as one-line text
files containing only a target path — so copying from a mirror yields dead
pointer files rather than skills. Vendoring from the canonical paths avoids the
hazard entirely, and avoids vendoring 458 duplicate copies of the same content.

### Skills reviewed and not vendored

Approximately 380 further canonical skills were reviewed by name and subject
area. The remainder cover marketing, finance, C-suite personas, compliance
certification (SOC 2, ISO, FDA, HIPAA), product management, and similar domains
outside the framework's scope. They remain available upstream and can be
vendored later using the same process: audit, adapt, register.

---

## Source 2 — awesome-openclaw-skills

| Field | Value |
|---|---|
| Upstream | <https://github.com/VoltAgent/awesome-openclaw-skills> |
| Commit inspected | `f274daa9d24c0803c8f94a4630aa4922ca4b950e` |
| Commit date | 2026-09-28 |
| Licence | MIT — Copyright (c) 2026 VoltAgent |
| Licence text | [`licenses/awesome-openclaw-skills-LICENSE`](licenses/awesome-openclaw-skills-LICENSE) |
| Skills vendored | **0** |

### No skills were taken from this source, deliberately

This repository contains **no skills**. It is a discovery index: a 1,265-line
README and 30 category files comprising approximately **5,265 unique links** to
skills hosted on `clawskills.sh` and `clawhub.ai`.

### Why it is a reference and not an integration source

Resolving those links to pull in code would mean installing executable content
from thousands of independent publishers, with:

```text
No version pinning        — no ref, digest, or commit is recorded
No provenance             — publisher identity is unverified
No pre-execution audit    — content cannot be reviewed before it runs
No provenance verification — no equivalent of the ClawHub trust envelope
Thousands of publishers  — each an independent supply-chain trust decision
```

That is not an integration. It is an unreviewed bulk execution of third-party
code, and it would directly contradict this framework's own
[`SUPPLY-CHAIN.md`](../docs/guides/SUPPLY-CHAIN.md), which holds that
**reachability and provenance decide whether something is a finding or a
non-issue** — and its rule that a tool cannot verify its own authorization.

The risk is not hypothetical in this category. `security-and-passwords` lists
skills named `credential-manager` ("MANDATORY security foundation"),
`1password`, `bitwarden`, `bitwarden-vault`, `dashlane`, `authensor-gateway`,
`cifer-sdk`, and `1claw` (HSM-backed secret vault). These exist to handle
credentials. Auto-installing credential-handling skills from an unpinned
registry is not a risk worth accepting for the convenience of a catalogue.

### How to use it safely

The catalogue is preserved as a **reference index only**:
[`catalog/security-and-passwords.index.md`](catalog/security-and-passwords.index.md).

To adopt any individual entry from it:

```text
1. Resolve the exact source repository — the registry link is not the source
2. Pin to a specific commit; record it
3. Audit with engineering/skills/skill-security-auditor (vendored here)
4. Read every script in full
5. Add a _BLACKHEART-ADAPTER.md with a maximum claim and stop conditions
6. Vendor from a pinned commit, never from a moving branch or tag
7. Register in skills/README.md and FILE-INDEX.txt
```

Steps 2 and 3 are not optional. A skill that fails the audit is not integrated
regardless of how useful it looks.

---

## Local additions

Everything below is original BLACKHEART work, MIT-licensed by Roshan.

| Path | Purpose |
|---|---|
| [`conformance/SKILL.md`](conformance/SKILL.md) | Mandatory wrapper applying framework non-negotiables to any vendored skill |
| `third-party/*/_BLACKHEART-ADAPTER.md` | Per-skill binding to a governing document, maximum claim, and stop conditions |
| [`README.md`](README.md) | Integration guide, loading, and layout |
| [`catalog/`](catalog/) | Preserved catalogue index, reference only |
| [`licenses/`](licenses/) | Preserved upstream licence texts |

## Integration audit summary

Both sources were audited before vendoring. Findings are recorded in
[`../docs/guides/SUPPLY-CHAIN.md`](../docs/guides/SUPPLY-CHAIN.md) process and
summarised in the main documentation. In short: no live credentials, no
malicious code, no exfiltration paths, and two security-scanner flags that were
independently verified as **false positives**.

## Updating a vendored skill

```text
1. Note the current pinned commit
2. Fetch upstream, diff the specific skill directory only
3. Re-run the security audit
4. Re-verify the false-positive notes still hold
5. Update the adapter's provenance table
6. Note the change in CHANGELOG.md
```

Never update a vendored skill by copying a newer tree wholesale: the rest of
upstream is not under audit in this repository.
