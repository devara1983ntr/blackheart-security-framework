# BLACKHEART Adapter — `cloud-security`

**Vendored skill, unmodified.** This adapter is additive; it does not change the
upstream skill's behaviour. If the vendored files are ever changed, that must be
recorded here and flagged as a divergence from upstream.

## Provenance

| Field | Value |
|---|---|
| Upstream | `claude-skills @ 19392f7a08264ed00486a251f5b2098321771f94 (2026-08-26), Alireza Rezvani, MIT` |
| Upstream path | `engineering-team/skills/cloud-security` |
| License | MIT — Copyright (c) 2025 Alireza Rezvani (preserved in [`../../VENDOR.md`](../../../../../VENDOR.md)) |
| Local modifications to vendored files | **None** |
| Conformance | [`../conformance/SKILL.md`](../../../../../conformance/SKILL.md) — mandatory |

## What it does

Cloud posture assessment across AWS, Azure and GCP: IAM privilege-escalation paths, storage exposure, security-group rules, and IaC review, with ATT&CK mapping.

## Governing BLACKHEART document

[`CLOUD-IDENTITY.md`](../../../../../../docs/guides/CLOUD-IDENTITY.md)

## Interface

**Scripts**

`scripts/cloud_posture_check.py` — `--check {privilege-escalation,data-exfil,public-exposure,s3,sg,all}`, `--provider {aws,azure,gcp}`, `--severity-modifier`.

**Inputs**

Configuration or policy input. Confirm from the tool's own reference whether it reads live cloud APIs, exported policy JSON, or IaC files.

**Outputs**

JSON findings by check and provider.

**Exit codes**

Not documented upstream. Verify behaviour before relying on exit codes in automation.

## Authorization gate

**None.** If the tool can query a cloud control plane it needs real credentials. Supply them only via the engagement record, never by requesting them mid-task, and confirm the account tenancy is in scope before any call.

## Maximum claim

> A posture finding is `UNVERIFIED` until the effective behaviour is demonstrated. A policy that *looks* permissive is a hypothesis; the framework's default-deny test in [`CLOUD-IDENTITY.md`](../../../../../../docs/guides/CLOUD-IDENTITY.md) §3 is what establishes it.

## Skill-specific notes

- `--provider azure` is listed but Azure posture depth is narrower than AWS. Record the reduced coverage rather than implying parity.
- `--severity-modifier` adjusts the tool's own scale. BLACKHEART severity is set separately and is bounded by evidence status.
- **The provider platform is out of scope.** Only the customer tenancy is. Never use this tool to test a provider's own infrastructure.
- A discovered credential is a finding to report, **not a key to authenticate with and continue**. See [`CLOUD-IDENTITY.md`](../../../../../../docs/guides/CLOUD-IDENTITY.md) §6.
- Static policy review cannot establish the effective default. Run the default-deny test separately.

## Coverage contribution

Supplies parts of CLOUD-IDENTITY §3, §4 and §8. Does not cover tenant-boundary data minimisation, backup and snapshot exposure, or logging/alert effectiveness (§5, §7, §8).

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
| Auditor verdict | **PASS** |
| Raw findings | 0 critical · 0 high · 0 info |
| Contents re-verified | 3 markdown · 1 scripts, byte-identical to upstream |

No critical or high findings.

**No backdoor, covert channel, credential exfiltration, or safety-override behaviour was found in this skill.** Recorded findings are consistent with its stated purpose and are *accepted*, not suppressed.
