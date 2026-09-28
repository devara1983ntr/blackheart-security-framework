# BLACKHEART Adapter — `threat-detection`

**Vendored skill, unmodified.** This adapter is additive; it does not change the
upstream skill's behaviour. If the vendored files are ever changed, that must be
recorded here and flagged as a divergence from upstream.

## Provenance

| Field | Value |
|---|---|
| Upstream | `claude-skills @ 19392f7a08264ed00486a251f5b2098321771f94 (2026-08-26), Alireza Rezvani, MIT` |
| Upstream path | `engineering-team/skills/threat-detection` |
| License | MIT — Copyright (c) 2025 Alireza Rezvani (preserved in [`../../VENDOR.md`](../../VENDOR.md)) |
| Local modifications to vendored files | **None** |
| Conformance | [`../conformance/SKILL.md`](../../conformance/SKILL.md) — mandatory |

## What it does

Hypothesis-driven threat hunting, IOC analysis, and anomaly prioritisation, with ATT&CK signal mapping.

## Governing BLACKHEART document

[`ADVERSARY-EMULATION.md`](../../../docs/guides/ADVERSARY-EMULATION.md) — the detection review

## Interface

**Scripts**

`scripts/threat_signal_analyzer.py` — `--mode {hunt,ioc,anomaly}`, `--hypothesis`, `--actor-relevance`, `--control-gap`

**Inputs**

A hunting hypothesis, or IOC/anomaly input.

**Outputs**

Prioritised signals and ATT&CK-mapped hunting direction.

**Exit codes**

Not documented upstream.

## Authorization gate

None. This skill analyses **telemetry you supply**. It does not touch a target, so the conformance gate applies only to the act of obtaining that telemetry.

## Maximum claim

> A prioritised signal is a **hunting lead**, which is `UNVERIFIED` by definition. It is not a finding about the assessed system, and it is not a vulnerability.

## Skill-specific notes

- The output is investigative direction, not a conclusion. A high-priority signal that survives hunting is still `UNVERIFIED` until corroborated.
- This skill does **not** test detection coverage. It reasons about signals. The framework's detection review in [`ADVERSARY-EMULATION.md`](../../../docs/guides/ADVERSARY-EMULATION.md) requires real activity and real evidence.
- Do not report hunting leads in the findings section. They belong in an appendix or as `UNVERIFIED` hypotheses with the corroborating test named.
- Telemetry may contain personal data. Apply the same minimisation rules as any other evidence.
- `--actor-relevance` and `--control-gap` are scoring inputs chosen by the operator, not measurements. State them as judgements.

## Coverage contribution

Supports the detection-review section of an emulation report. Contributes nothing to vulnerability coverage; do not let it mark boundaries tested.

---

*The vendored `SKILL.md` and scripts under this directory are byte-for-byte
upstream. Read them for the skill's own method. Read this adapter for how its
output may be used inside BLACKHEART.*
