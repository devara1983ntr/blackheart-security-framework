# Blackhearts Adapter — `browser-automation`

| Field | Value |
|---|---|
| Upstream | `https://github.com/alirezarezvani/claude-skills` |
| Upstream commit | `19392f7a08264ed00486a251f5b2098321771f94` |
| Upstream path | `engineering/skills/browser-automation` |
| Upstream licence | MIT (c) 2025 Alireza Rezvani |
| Integrity | byte-identical to upstream, verified 2026-09-28 |
| Modified by Blackhearts | No — this `_BLACKHEART-ADAPTER.md` is the only added file |
| Security audit | **WARN** — 0 critical, 2 high, 0 info |
| Classification | engineering-and-delivery |
| Priority | P3 - engineering and delivery |
| Contents | 4 markdown files, 3 scripts |
| Governing policy | [SKILL.md](../../../../../conformance/SKILL.md) |

## What this adapter is for

This file is Blackhearts-local metadata. The skill directory itself is **unmodified upstream content**. It records provenance, the audit result, and the conditions under which the skill may be used inside a Blackhearts engagement.

## Evidence status

Per the governing conformance policy, **any match this skill reports is `UNVERIFIED` until it is independently demonstrated.** Loading this skill does not authorize it to scan, test, or touch any target. A skill's own severity rating is **not** a Blackhearts severity.

## Audit adjudication

The upstream auditor returned **WARN** with 2 raw finding(s). Categories: `DEPS-RUNTIME` (2).

| Category | Assessment |
|---|---|
| `DEPS-RUNTIME` (2) | Third-party imports in example/tooling code. See Skills/VENDOR.md for the dependency policy. |

<details><summary>Raw findings as reported by the auditor</summary>

| Sev | Category | Location | Pattern |
|---|---|---|---|
| HIGH | `DEPS-RUNTIME` | `engineering/skills/browser-automation/scripts/form_automation_builder.py:183` | `pip install playwright` |
| HIGH | `DEPS-RUNTIME` | `engineering/skills/browser-automation/scripts/scraping_toolkit.py:107` | `pip install playwright` |

</details>

**Manual adjudication.** No finding in this skill indicates a backdoor, covert channel, credential exfiltration, or safety override. Findings are consistent with the skill's stated purpose and are recorded as accepted, not suppressed.

## Known defects

None found. All local links in this skill resolve.

## Conditions of use

1. Read [`skills/conformance/SKILL.md`](../../../../../conformance/SKILL.md) before any use. It governs authorization, evidence status, severity, and secrets handling.
2. No target may be scanned, tested, or profiled until the operator supplies the target and explicit authorization, in writing, in the engagement record.
3. Do not execute any script from this skill against a third-party system without that authorization. Scripts are third-party code with third-party defects.
4. Report every result as `UNVERIFIED` until independently demonstrated, and record rejected hypotheses alongside confirmed findings.
5. Record the skill name, upstream commit, and this adapter path in the evidence log so any finding can be traced back to the exact tool version that produced it.

## Provenance

- Licence text: [claude-skills-LICENSE](../../../../../licenses/claude-skills-LICENSE)
- Full provenance and integration record: [VENDOR.md](../../../../../VENDOR.md)
- Regenerate with the mirror audit workflow; see `.github/workflows/upstream-sync.yml`.
