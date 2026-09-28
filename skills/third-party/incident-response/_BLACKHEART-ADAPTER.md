# BLACKHEART Adapter — `incident-response`

**Vendored skill, unmodified.** This adapter is additive; it does not change the
upstream skill's behaviour. If the vendored files are ever changed, that must be
recorded here and flagged as a divergence from upstream.

## Provenance

| Field | Value |
|---|---|
| Upstream | `claude-skills @ 19392f7a08264ed00486a251f5b2098321771f94 (2026-08-26), Alireza Rezvani, MIT` |
| Upstream path | `engineering-team/skills/incident-response` |
| License | MIT — Copyright (c) 2025 Alireza Rezvani (preserved in [`../../VENDOR.md`](../../VENDOR.md)) |
| Local modifications to vendored files | **None** |
| Conformance | [`../conformance/SKILL.md`](../../conformance/SKILL.md) — mandatory |

## What it does

Incident triage and classification, a severity framework, false-positive filtering, and forensic evidence collection.

## Governing BLACKHEART document

[`ADVERSARY-EMULATION.md`](../../../docs/guides/ADVERSARY-EMULATION.md) and the framework's evidence rules in [`EVIDENCE.md`](../../../docs/guides/EVIDENCE.md)

## Interface

**Scripts**

`scripts/incident_triage.py` — `--input <json>`, `--classify`, `--false-positive-check`

**Inputs**

A JSON security event describing the incident.

**Outputs**

Classification, severity assessment, false-positive determination.

**Exit codes**

Not documented upstream.

## Authorization gate

**Critical, and unlike the rest of this set.** Triage operates on evidence from a live incident. Handling a real incident's evidence is not an assessment activity and is not covered by a testing authorization. Use only on synthetic events, or on an incident the client has explicitly brought into scope. If in doubt, do not run it.

## Maximum claim

> A classification is `UNVERIFIED` until corroborated with host and telemetry evidence. Triage output is a starting hypothesis about what happened, not a determination.

## Skill-specific notes

- **This skill sits closest to the framework's authorization boundary.** Incident response touches live systems, live data, and frequently personal data. Default to synthetic input.
- `--false-positive-check` is genuinely valuable and is a good model for the framework's own negative-result discipline — a rejected hypothesis is evidence, not an absence of one.
- Do not run forensic collection against any system without explicit, incident-scoped authorization. A penetration-testing authorization does not extend to incident response.
- Incident data is frequently sensitive. Apply minimisation, and do not move evidence outside the engagement's stated handling requirements.
- The skill's severity framework is its own and is separate from BLACKHEART severity, which applies to assessment findings.

## Coverage contribution

Out of the normal assessment path. Included for its triage methodology and its false-positive discipline, **not** for engagements against live systems.

---

*The vendored `SKILL.md` and scripts under this directory are byte-for-byte
upstream. Read them for the skill's own method. Read this adapter for how its
output may be used inside BLACKHEART.*
