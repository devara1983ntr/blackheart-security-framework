# BLACKHEART Adapter — `senior-security`

**Vendored skill, unmodified.** This adapter is additive; it does not change the
upstream skill's behaviour. If the vendored files are ever changed, that must be
recorded here and flagged as a divergence from upstream.

## Provenance

| Field | Value |
|---|---|
| Upstream | `claude-skills @ 19392f7a08264ed00486a251f5b2098321771f94 (2026-08-26), Alireza Rezvani, MIT` |
| Upstream path | `engineering-team/skills/senior-security` |
| License | MIT — Copyright (c) 2025 Alireza Rezvani (preserved in [`../../VENDOR.md`](../../../../../VENDOR.md)) |
| Local modifications to vendored files | **None** |
| Conformance | [`../conformance/SKILL.md`](../../../../../conformance/SKILL.md) — mandatory |

## What it does

Owns STRIDE threat modelling and DREAD risk scoring, provides secret scanning, and routes other security requests to the correct sibling skill.

## Governing BLACKHEART document

[`BUSINESS-LOGIC.md`](../../../../../../docs/guides/BUSINESS-LOGIC.md) · [`ATTACK-PATHS.md`](../../../../../../docs/guides/ATTACK-PATHS.md) · [`SUPPLY-CHAIN.md`](../../../../../../docs/guides/SUPPLY-CHAIN.md) §5

## Interface

**Scripts**

`secret_scanner.py` (`--format`, `--output`, `--list-patterns`, `--severity`) · `threat_modeler.py` (`--component`, `--assets`, `--interactive`)

**Inputs**

Components and assets for threat modelling; a target path or files for secret scanning.

**Outputs**

STRIDE threat model; DREAD scores; secret findings.

**Exit codes**

Not documented upstream. `secret_scanner.py` emits its own `severity` scale — not BLACKHEART severity.

## Authorization gate

None in the tool. Local, offline analysis only. The conformance gate still applies to how the output may be claimed.

## Maximum claim

> STRIDE/DREAD output is a **risk model**, not evidence of a weakness. A STRIDE category identified on a component is `UNVERIFIED` until a weakness is demonstrated at that boundary. DREAD is a prioritisation aid, not a severity rating.

## Skill-specific notes

- **Read the routing table first.** This skill is designed as an entry point that dispatches to siblings. Use it to route, not to replace the specialist skills.
- Secret findings: report the **location and type, never the value**. See [`SECURITY.md`](../../../../../../SECURITY.md) and [`SUPPLY-CHAIN.md`](../../../../../../docs/guides/SUPPLY-CHAIN.md) §5.
- A committed secret is a finding regardless of whether it is still active. Do not downgrade on the basis that it has been rotated.
- DREAD scores must not be presented as BLACKHEART severity. They answer a different question.
- The skill's scripts use `__import__('datetime')` with a **string literal**. The integration audit flagged this as dynamic-import (critical); it is a **false positive** — the argument is a literal module name, not a variable. Recorded here so it is not re-raised on every audit.
- `secret_scanner.py --list-patterns` is a good way to see exactly what the tool matches before trusting a clean result.

## Coverage contribution

Supplies the threat-modelling step of [`ATTACK-PATHS.md`](../../../../../../docs/guides/ATTACK-PATHS.md) and SUPPLY-CHAIN §5. Tests nothing: every boundary it names remains `NOT TESTED` until executed.

---

*The vendored `SKILL.md` and scripts under this directory are byte-for-byte
upstream. Read them for the skill's own method. Read this adapter for how its
output may be used inside BLACKHEART.*

---

## Full-mirror audit (Round 5, complete catalogue re-scan)

This skill was re-audited as part of the vendoring of **all 388 canonical skills** from `claude-skills`, on 2026-09-28. The result below is additive to the analysis above.

| Field | Value |
|---|---|
| Scope | Full canonical catalogue (388 skills, 20 groups) |
| Auditor verdict | **FAIL** |
| Raw findings | 2 critical · 0 high · 0 info |
| Contents re-verified | 5 markdown · 2 scripts, byte-identical to upstream |

### Categories and adjudication

| Category | Count | Assessment |
|---|---|---|
| `CODE-EXEC` | 2 | Dynamic-import pattern; for this skill the two matches are the literal `__import__('datetime')` timestamp stamp — a **false positive**, re-confirmed by code read. |

<details><summary>Raw findings</summary>

| Sev | Category | Location | Pattern |
|---|---|---|---|
| CRITICAL | `CODE-EXEC` | `engineering-team/skills/senior-security/scripts/secret_scanner.py:384` | `"scan_date": __import__('datetime').datetime.now().isoformat(),` |
| CRITICAL | `CODE-EXEC` | `engineering-team/skills/senior-security/scripts/threat_modeler.py:468` | `"analysis_date": __import__('datetime').datetime.now().isoformat(),` |

</details>

**No backdoor, covert channel, credential exfiltration, or safety-override behaviour was found in this skill.** Recorded findings are consistent with its stated purpose and are *accepted*, not suppressed.
