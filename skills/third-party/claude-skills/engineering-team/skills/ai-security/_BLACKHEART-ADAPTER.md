# BLACKHEART Adapter — `ai-security`

**Vendored skill, unmodified.** This adapter is additive; it does not change the
upstream skill's behaviour. If the vendored files are ever changed, that must be
recorded here and flagged as a divergence from upstream.

## Provenance

| Field | Value |
|---|---|
| Upstream | `claude-skills @ 19392f7a08264ed00486a251f5b2098321771f94 (2026-08-26), Alireza Rezvani, MIT` |
| Upstream path | `engineering-team/skills/ai-security` |
| License | MIT — Copyright (c) 2025 Alireza Rezvani (preserved in [`../../VENDOR.md`](../../../../../VENDOR.md)) |
| Local modifications to vendored files | **None** |
| Conformance | [`../conformance/SKILL.md`](../../../../../conformance/SKILL.md) — mandatory |

## What it does

Static signature detection for prompt injection, jailbreak, model inversion, data poisoning, and agent tool abuse in AI/LLM systems, with MITRE ATLAS technique mapping.

## Governing BLACKHEART document

[`AGENTIC-AI-SECURITY.md`](../../../../../../docs/guides/AGENTIC-AI-SECURITY.md) §5, §12 and [`AGENT-THREAT-MODEL.md`](../../../../../../templates/AGENT-THREAT-MODEL.md)

## Interface

**Scripts**

`scripts/ai_threat_scanner.py` — offline signature matcher. Does **not** require live model access; it scores inputs before they reach the model.

**Inputs**

A JSON array of prompt strings or `{prompt: ...}` objects. Built-in seed prompts are used when `--test-file` is omitted.

**Outputs**

JSON: `target_type`, `access_level`, `prompts_tested`, `injection_score` (0–1), and per-finding `signature_name`, `atlas_id`, `atlas_name`, `severity`, `matched_pattern`.

**Exit codes**

`0` low risk · `1` medium/high findings · `2` **critical findings or missing authorization for invasive access levels**

## Authorization gate

**Built in and verified.** `--access-level gray-box` and `white-box` require `--authorized`; without it the scanner emits an `authorization_required` finding at `critical` and exits `2`. Verified during integration: gray-box without the flag exits 2; with the flag it proceeds.

## Maximum claim

> A signature match is `UNVERIFIED`. It establishes that a pattern is present in the supplied input, not that a model's safety control was bypassed. `CONFIRMED` requires the agent to be observed acting on the injected instruction.

## Skill-specific notes

- The scanner's `severity` field is **its own scale, not BLACKHEART severity**. Do not carry it across.
- `injection_score` is a ratio of matched signatures, not a probability of exploitability.
- Signature matching finds *known* patterns. Absence of matches is **not** evidence of safety, and does not make a boundary `NOT VULNERABLE` — that requires testing the control.
- Only the techniques the reference table marks as covered are addressed; the skill's own `atlas-coverage.md` lists several as **Not covered** or **Partial**. Carry those into the coverage matrix.
- Semantic and multi-turn attacks, and obfuscated variants, are outside signature matching. Record them as `NOT TESTED` unless separately exercised.

## Coverage contribution

Supplies skills G2, G3, G4 and part of G7. Does not cover tool-layer authorization tested directly (§6), retrieval authorization (§7), or inter-agent boundaries (§12).

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
