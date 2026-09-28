# BLACKHEART Adapter — `red-team`

**Vendored skill, unmodified.** This adapter is additive; it does not change the
upstream skill's behaviour. If the vendored files are ever changed, that must be
recorded here and flagged as a divergence from upstream.

## Provenance

| Field | Value |
|---|---|
| Upstream | `claude-skills @ 19392f7a08264ed00486a251f5b2098321771f94 (2026-08-26), Alireza Rezvani, MIT` |
| Upstream path | `engineering-team/skills/red-team` |
| License | MIT — Copyright (c) 2025 Alireza Rezvani (preserved in [`../../VENDOR.md`](../../VENDOR.md)) |
| Local modifications to vendored files | **None** |
| Conformance | [`../conformance/SKILL.md`](../../conformance/SKILL.md) — mandatory |

## What it does

Planning support for authorized adversary emulation: kill-chain phase sequencing, technique scoring, choke-point identification, OPSEC risk assessment, and crown-jewel targeting.

## Governing BLACKHEART document

[`RED-HEART-ADVERSARY-EMULATION.md`](../../../docs/modes/RED-HEART-ADVERSARY-EMULATION.md) and [`ADVERSARY-EMULATION.md`](../../../docs/guides/ADVERSARY-EMULATION.md)

## Interface

**Scripts**

`scripts/engagement_planner.py` — plans an engagement from techniques, access level, crown jewels, and target count. Planning only; it does not execute techniques.

**Inputs**

Technique list, `--access-level {external,internal,credentialed}`, crown jewels, target count.

**Outputs**

A planned engagement: phase sequencing, prioritised techniques, choke points, OPSEC risk.

**Exit codes**

Not documented upstream. Treat any non-zero exit as a planning failure, not a target result.

## Authorization gate

None in the tool. **The conformance gate applies in full.** Planning an engagement is not authorization to run one; `engagement_planner.py` output never establishes scope.

## Maximum claim

> A plan is `UNVERIFIED` by construction — it is a hypothesis about a route. Nothing in this skill's output is evidence of any boundary failing. Evidence comes only from executed, recorded tests.

## Skill-specific notes

- The planner produces **intent**. It is a planning artefact, not a finding and not evidence.
- Do not let planned techniques appear in a report as attempted techniques. Track execution separately, per [`COVERAGE-MATRIX.md`](../../../templates/COVERAGE-MATRIX.md).
- `--access-level credentialed` implies credentialed testing. That requires credentials supplied by the client through the engagement record — **never requested by the agent**. See [`AGENT-OPERATING-PROTOCOL.md`](../../../docs/agent/AGENT-OPERATING-PROTOCOL.md) §8.
- Any technique this skill proposes must still be checked against the engagement's Rules of Engagement before execution.
- Kill-chain phase language is ATT&CK-oriented. BLACKHEART's own pipeline is authoritative for reporting; ATT&CK phase names are useful for describing adversary behaviour, not for structuring the report.

## Coverage contribution

Supplements RED HEART. Contributes no evidence on its own. The detection review in [`ADVERSARY-EMULATION.md`](../../../docs/guides/ADVERSARY-EMULATION.md) remains unexecuted without real activity.

---

*The vendored `SKILL.md` and scripts under this directory are byte-for-byte
upstream. Read them for the skill's own method. Read this adapter for how its
output may be used inside BLACKHEART.*
