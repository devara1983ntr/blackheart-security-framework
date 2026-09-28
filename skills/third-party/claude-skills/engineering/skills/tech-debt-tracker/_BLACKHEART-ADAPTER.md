# Blackhearts Adapter — `tech-debt-tracker`

| Field | Value |
|---|---|
| Upstream | `https://github.com/alirezarezvani/claude-skills` |
| Upstream commit | `19392f7a08264ed00486a251f5b2098321771f94` |
| Upstream path | `engineering/skills/tech-debt-tracker` |
| Upstream licence | MIT (c) 2025 Alireza Rezvani |
| Integrity | byte-identical to upstream, verified 2026-09-28 |
| Modified by Blackhearts | No — this `_BLACKHEART-ADAPTER.md` is the only added file |
| Security audit | **FAIL** — 3 critical, 0 high, 0 info |
| Classification | engineering-and-delivery |
| Priority | P3 - engineering and delivery |
| Contents | 6 markdown files, 6 scripts |
| Governing policy | [SKILL.md](../../../../../conformance/SKILL.md) |

## What this adapter is for

This file is Blackhearts-local metadata. The skill directory itself is **unmodified upstream content**. It records provenance, the audit result, and the conditions under which the skill may be used inside a Blackhearts engagement.

## Evidence status

Per the governing conformance policy, **any match this skill reports is `UNVERIFIED` until it is independently demonstrated.** Loading this skill does not authorize it to scan, test, or touch any target. A skill's own severity rating is **not** a Blackhearts severity.

## Audit adjudication

The upstream auditor returned **FAIL** with 3 raw finding(s). Categories: `NET-EXFIL` (3).

| Category | Assessment |
|---|---|
| `NET-EXFIL` (3) | Outbound HTTP request — expected for skills whose stated function is to fetch a URL (SEO/AEO audit, search, screenshot). No destination exfiltrating local data was found. |

<details><summary>Raw findings as reported by the auditor</summary>

| Sev | Category | Location | Pattern |
|---|---|---|---|
| CRITICAL | `NET-EXFIL` | `engineering/skills/tech-debt-tracker/assets/sample_codebase/src/payment_processor.py:100` | `response = requests.post(` |
| CRITICAL | `NET-EXFIL` | `engineering/skills/tech-debt-tracker/assets/sample_codebase/src/payment_processor.py:142` | `response = requests.post(` |
| CRITICAL | `NET-EXFIL` | `engineering/skills/tech-debt-tracker/assets/sample_codebase/src/payment_processor.py:182` | `response = requests.post(` |

</details>

**Manual adjudication.** 3 NET-EXFIL findings are in `assets/sample_codebase/src/payment_processor.py` — a deliberately bad **teaching artefact** whose code posts to the real Stripe / Square / PayPal endpoints. Not exfiltration, but see Known defects: this sample is executable and must never be run.

## Known defects

None found. All local links in this skill resolve.

## Conditions of use

1. Read [`skills/conformance/SKILL.md`](../../../../../conformance/SKILL.md) before any use. It governs authorization, evidence status, severity, and secrets handling.
2. No target may be scanned, tested, or profiled until the operator supplies the target and explicit authorization, in writing, in the engagement record.
3. Do not execute any script from this skill against a third-party system without that authorization. Scripts are third-party code with third-party defects.
4. Report every result as `UNVERIFIED` until independently demonstrated, and record rejected hypotheses alongside confirmed findings.
5. Record the skill name, upstream commit, and this adapter path in the evidence log so any finding can be traced back to the exact tool version that produced it.

> **Extra condition — do not execute the sample codebase.** `assets/sample_codebase/src/payment_processor.py` contains working code that POSTs to live Stripe, Square, and PayPal endpoints. It exists to be *analysed*, not run. Never execute it.

## Provenance

- Licence text: [claude-skills-LICENSE](../../../../../licenses/claude-skills-LICENSE)
- Full provenance and integration record: [VENDOR.md](../../../../../VENDOR.md)
- Regenerate with the mirror audit workflow; see `.github/workflows/upstream-sync.yml`.
