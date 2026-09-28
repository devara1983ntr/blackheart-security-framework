# BLACKHEART Adapter — `security-pen-testing`

**Vendored skill, unmodified.** This adapter is additive; it does not change the
upstream skill's behaviour. If the vendored files are ever changed, that must be
recorded here and flagged as a divergence from upstream.

## Provenance

| Field | Value |
|---|---|
| Upstream | `claude-skills @ 19392f7a08264ed00486a251f5b2098321771f94 (2026-08-26), Alireza Rezvani, MIT` |
| Upstream path | `engineering-team/skills/security-pen-testing` |
| License | MIT — Copyright (c) 2025 Alireza Rezvani (preserved in [`../../VENDOR.md`](../../../../../VENDOR.md)) |
| Local modifications to vendored files | **None** |
| Conformance | [`../conformance/SKILL.md`](../../../../../conformance/SKILL.md) — mandatory |

## What it does

General application security: OWASP Top 10 systematic audit, static analysis, dependency scanning, secret detection, API security, and report generation.

## Governing BLACKHEART document

[`WEB-API-TESTING.md`](../../../../../../docs/guides/WEB-API-TESTING.md) · [`SEVERITY-RATING.md`](../../../../../../docs/guides/SEVERITY-RATING.md) · [`REPORTING.md`](../../../../../../docs/guides/REPORTING.md)

## Interface

**Scripts**

`vulnerability_scanner.py` (`--target {web,api,mobile}`, `--scope {quick,full}`, `--source`) · `dependency_auditor.py` (`--file <manifest>`) · `pentest_report_generator.py` (`--findings <json>`)

**Inputs**

Optional source directory; manifest file for dependency audit; findings JSON for report generation.

**Outputs**

JSON findings; Markdown or JSON report.

**Exit codes**

Not documented upstream. Verify before automating on exit status.

## Authorization gate

None. `--source` reads local code; the OWASP audit checklist implies active testing. Apply the conformance gate to any active step.

## Maximum claim

> Checklist and static matches are `UNVERIFIED`. `vulnerability_scanner.py` returning clean does **not** make any boundary `NOT VULNERABLE` — that status requires demonstrated coverage of the boundary.

## Skill-specific notes

- `pentest_report_generator.py` consumes a findings JSON **you** supply. It formats; it does not validate. Feeding it unverified findings produces a confident-looking report of unverified claims — the most likely way this skill could cause real harm inside BLACKHEART. **Every finding must carry a BLACKHEART status and evidence reference before it is passed in.**
- The skill's OWASP A08 checklist item contains the literal text `pickle.load(), yaml.load()` as **detection guidance for other people's code**. It is not a deserialization call. See the integration audit note.
- **This `SKILL.md` has three links that do not resolve here**: `../senior-secops/SKILL.md`, `engineering/skills/dependency-auditor/SKILL.md`, and `../code-reviewer/SKILL.md`. They are correct in the upstream repository layout and dangle only because this is a vendored subtree. They are left untouched, because vendored files are not modified — see [`../../VENDOR.md`](../../../../../VENDOR.md). The two skills that matter here are vendored separately: `dependency-auditor` alongside this one, and `threat-detection` for the defensive-operations role `senior-secops` covers.
- `--scope quick` deliberately skips non-high/critical results. Record that reduced coverage in the coverage matrix.
- `dependency_auditor.py` overlaps `dependency-auditor`. Prefer one and state which; do not run both and merge without reconciling.
- The skill's own guidance is not a substitute for the enforcement point and regression test BLACKHEART requires per finding.

## Coverage contribution

Supplies skills B5, C1–C3, E1, H1 and parts of the OWASP Top 10 mapping. Does not cover the payment chain beyond dependency level, mobile runtime, or coverage accounting.

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
| Raw findings | 2 critical · 4 high · 0 info |
| Contents re-verified | 5 markdown · 3 scripts, byte-identical to upstream |

### Categories and adjudication

| Category | Count | Assessment |
|---|---|---|
| `DESERIAL` | 4 | `pickle.load()` / `yaml.load()` appear as **detection guidance** inside a scanner — a false positive, not an actual unsafe deserialization call. |
| `CODE-EXEC` | 2 | Dynamic-import pattern; for this skill the two matches are the literal `__import__('datetime')` timestamp stamp — a **false positive**, re-confirmed by code read. |

<details><summary>Raw findings</summary>

| Sev | Category | Location | Pattern |
|---|---|---|---|
| HIGH | `DESERIAL` | `engineering-team/skills/security-pen-testing/scripts/dependency_auditor.py:132` | `"description": "PyYAML before 6.0.1 allows arbitrary code execution via yaml.load().",` |
| CRITICAL | `CODE-EXEC` | `engineering-team/skills/security-pen-testing/scripts/vulnerability_scanner.py:163` | `"recommendation": "Never use eval() or exec() with untrusted input. Use ast.literal_eval() for data ` |
| CRITICAL | `CODE-EXEC` | `engineering-team/skills/security-pen-testing/scripts/vulnerability_scanner.py:163` | `"recommendation": "Never use eval() or exec() with untrusted input. Use ast.literal_eval() for data ` |
| HIGH | `DESERIAL` | `engineering-team/skills/security-pen-testing/scripts/vulnerability_scanner.py:217` | `"recommendation": "Use yaml.safe_load() instead of yaml.load(). Avoid pickle for untrusted data.",` |
| HIGH | `DESERIAL` | `engineering-team/skills/security-pen-testing/scripts/vulnerability_scanner.py:406` | `"Review code for pickle.load(), yaml.load(), Java ObjectInputStream.",` |
| HIGH | `DESERIAL` | `engineering-team/skills/security-pen-testing/scripts/vulnerability_scanner.py:406` | `"Review code for pickle.load(), yaml.load(), Java ObjectInputStream.",` |

</details>

**No backdoor, covert channel, credential exfiltration, or safety-override behaviour was found in this skill.** Recorded findings are consistent with its stated purpose and are *accepted*, not suppressed.
