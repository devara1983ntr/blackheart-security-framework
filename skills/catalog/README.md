# Third-Party Skill Catalogue — Reference Only

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Source:** <https://github.com/VoltAgent/awesome-openclaw-skills> @ `f274daa9d24c0803c8f94a4630aa4922ca4b950e`
**Licence:** MIT — Copyright (c) 2026 VoltAgent · [`../licenses/awesome-openclaw-skills-LICENSE`](../licenses/awesome-openclaw-skills-LICENSE)

> **No skill from this source is vendored as executable content, and none
> should be installed from it automatically.** This directory is a **complete
> reference record** of the catalogue, preserved verbatim so nothing is lost and
> every entry stays searchable.

## What this source actually is

`awesome-openclaw-skills` contains **zero skills**. It is a discovery index.

## What is vendored here

The **entire** catalogue, byte-for-byte, so that "use everything" is honoured
for the index even though none of it may be executed:

```text
upstream-README.md          Master index              (862 URLs)
upstream-CONTRIBUTING.md    Upstream contribution rules
categories/*.md             All 30 category files     (5,210 unique URLs)
README.md                   This policy document (Blackhearts-authored)
```

```text
Upstream layout            Count
README.md                  1,265 lines
categories/*.md            30 category files
SKILL.md files             0
Unique URLs                5,267
Distinct registries        clawskills.sh, clawhub.ai
```

Every entry is a link to a skill hosted elsewhere by an independent publisher.
All 32 files here are verified byte-identical to upstream at
`f274daa9d24c0803c8f94a4630aa4922ca4b950e`. Vendoring an index of links is
risk-free — nothing here executes.

Two upstream files are deliberately not vendored, and the omission is recorded
rather than implied. `.github/workflows/pr-check.yml` is upstream's own
pull-request gate: it fails any pull request whose description lacks a ClawHub
link, which has no meaning here. `.claude/settings.local.json` is a
machine-local permission list naming one contributor's absolute home path —
the one file in either source that names a private filesystem path, and not
something to mirror into another repository. Neither carries catalogue
content, and neither is executable here. **Resolving** those links is what carries
risk, and that is what the vetting process below governs.

## Why nothing is executed from it

Resolving those links means installing executable content from thousands of
unrelated publishers, and it would contradict this framework's own supply-chain
rules. The gaps:

```text
No version pinning      the index records no ref, tag, or digest
No provenance           publisher identity is unverified
No pre-execution audit  content cannot be reviewed before it runs
No trust envelope       no equivalent of the registry verification record
No transitive control   each entry is an independent trust decision
```

[`../../docs/guides/SUPPLY-CHAIN.md`](../../docs/guides/SUPPLY-CHAIN.md) holds
that reachability and provenance decide whether something is a finding or a
non-issue. Here, neither is established for any entry. Under the framework's
own rules, every one of the 5,267 is **`UNVERIFIED` at best, and `NOT TESTED`
in practice** — an index is not an assessment.

### The category that decides it

The catalogue's own `security-and-passwords` category lists skills whose stated
purpose is handling credentials:

```text
credential-manager    "MANDATORY security foundation for OpenClaw"
1password / 1claw     vault and secret management
bitwarden / bitwarden-vault / dashlane / cifer-sdk
authensor-gateway     "Fail-safe policy gate for OpenClaw marketplace skills"
```

Installing a credential-handling skill from an unpinned, unreviewed registry is
the single highest-consequence integration mistake available here. It is not
worth the convenience of a list.

This is also precisely what the OpenClaw documentation warns about when it
says to treat third-party skills as untrusted code, read them before enabling,
and prefer sandboxed runs.

## Shortlist — for individual vetting only

From the security category, entries whose *subject* matches the framework. This
is a **review starting point, not a recommendation**, and nothing here has been
downloaded, audited, or verified.

| Entry | Subject | Overlap with BLACKHEART |
|---|---|---|
| `api-security` | Secure API design, authz, validation, rate limiting | `WEB-API-TESTING.md`, `AUTH-AUTHZ.md` |
| `clawdstrike` | Security audit and threat model for gateway hosts | `AGENT-OPERATING-PROTOCOL.md` |
| `authensor-gateway` | Policy gate for marketplace skills | `conformance/SKILL.md` |
| `credential-manager` | Agent secret management | `SECURITY.md` secrets policy |

**Overlap is a reason for caution, not comfort.** The first duplicates guidance
this framework already provides and would need a long adapter to avoid
conflicting with it. Note that `clawaudit` in the index is described as
"coming soon" — an entry advertising a tool that does not yet exist is itself
a signal about the catalogue's curation.

## Adopting any entry — required process

```text
1. RESOLVE the real source repository
   The registry link is a pointer, not the source. Find where the code lives.

2. PIN
   Record an exact commit. Never install from a moving branch or a bare tag.

3. AUDIT — before any code runs
     python3 engineering/skills/skill-security-auditor/scripts/skill_security_auditor.py <path>
   Then read every script in full. The auditor produces false positives —
   verify each finding before acting on it (see the notes in
   skills/VENDOR.md § Integration audit summary).

4. CHECK the authorization surface
   What does this skill cause an agent to do? Does it request credentials?
   Does it contact an external service? Is it in scope for the engagement?

5. WRITE AN ADAPTER
   _BLACKHEART-ADAPTER.md with provenance, governing document, interface,
   authorization gate, maximum claim, stop conditions, coverage contribution.

6. VENDOR from the pinned commit
   Never from the registry, never from a branch.

7. REGISTER
   skills/README.md, skills/VENDOR.md, and FILE-INDEX.txt.

8. CONFIRM conformance
   blackheart-conformance applies to it unchanged.
```

A skill that fails the audit, or cannot state a maximum claim, is not integrated
regardless of how useful it appears.

## Why the framework vendors instead

The eight vendored skills come from a repository that is:

```text
Version-controlled   yes, pinned to an exact commit
Auditable            yes, a tree you can read and diff
Attributable          yes, a single named author and a preserved licence
Reviewable           yes, statically scanned and the findings verified
Repeatable           yes, re-vendor by commit hash
```

A catalogue of 5,267 unpinned external links has none of these. That is the
difference between integrating a dependency and accumulating links, and it is
the reason this directory is a reference rather than a source.

## Related

| Document | Purpose |
|---|---|
| [`../VENDOR.md`](../VENDOR.md) | Full attribution and the vendor decision |
| [`../../docs/guides/SUPPLY-CHAIN.md`](../../docs/guides/SUPPLY-CHAIN.md) | The rules this decision follows |
| [`../README.md`](../README.md) | Loading and using the vendored skills |
