# BLACKHEART Adapter — `dependency-auditor`

**Vendored skill, unmodified.** This adapter is additive; it does not change the
upstream skill's behaviour. If the vendored files are ever changed, that must be
recorded here and flagged as a divergence from upstream.

## Provenance

| Field | Value |
|---|---|
| Upstream | `claude-skills @ 19392f7a08264ed00486a251f5b2098321771f94 (2026-08-26), Alireza Rezvani, MIT` |
| Upstream path | `engineering/skills/dependency-auditor` |
| License | MIT — Copyright (c) 2025 Alireza Rezvani (preserved in [`../../VENDOR.md`](../../VENDOR.md)) |
| Local modifications to vendored files | **None** |
| Conformance | [`../conformance/SKILL.md`](../../conformance/SKILL.md) — mandatory |

## What it does

Multi-language dependency audit: vulnerability identification, license-conflict detection, transitive-risk analysis, and safe upgrade planning.

## Governing BLACKHEART document

[`SUPPLY-CHAIN.md`](../../../docs/guides/SUPPLY-CHAIN.md) — in particular §2 reachability

## Interface

**Scripts**

`dep_scanner.py` (`--format`, `--fail-on-high`, `--quick-scan`) · `license_checker.py` (`--inventory`, `--policy {permissive,strict}`) · `upgrade_planner.py` (`--timeline`, `--risk-threshold`)

**Inputs**

Project manifests; an inventory for the license checker.

**Outputs**

Vulnerability, license, and upgrade-path reports.

**Exit codes**

`--fail-on-high` exists specifically for CI gating. Documented upstream.

## Authorization gate

None required — this is local, offline analysis of files you already have. No network target is contacted by the analysis path.

## Maximum claim

> A CVE match is `UNVERIFIED` until reachability is established. Per [`SUPPLY-CHAIN.md`](../../../docs/guides/SUPPLY-CHAIN.md) §2, reachability decides whether it is a finding at all.

## Skill-specific notes

- **This is the most misused skill in the set if its output is taken at face value.** A CVE list with no reachability analysis is a scan report, not an assessment.
- Verify the version against the artefact that is actually deployed, not a manifest that may be stale. See [`SUPPLY-CHAIN.md`](../../../docs/guides/SUPPLY-CHAIN.md) §3.
- `--quick-scan` skips transitive dependencies. Record the reduced coverage.
- Advisory data changes. Record the date checked, and never assert a CVE identifier from memory.
- `license_checker.py` findings are compliance observations, not vulnerabilities. Do not route them into the severity scale.
- `upgrade_planner.py` produces a plan; it does not perform upgrades and must never be run in a way that mutates a target.

## Coverage contribution

Supplies SUPPLY-CHAIN §1 and §2 and the base of §4. Does not cover build pipeline integrity, publish/update channels, secrets in build artefacts, or agent plugin supply chains.

---

*The vendored `SKILL.md` and scripts under this directory are byte-for-byte
upstream. Read them for the skill's own method. Read this adapter for how its
output may be used inside BLACKHEART.*
