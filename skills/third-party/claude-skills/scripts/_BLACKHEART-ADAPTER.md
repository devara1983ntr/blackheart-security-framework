# Blackhearts Adapter — `scripts/` (upstream tooling)

| Field | Value |
|---|---|
| Upstream | `https://github.com/alirezarezvani/claude-skills` |
| Upstream commit | `19392f7a08264ed00486a251f5b2098321771f94` |
| Upstream path | `scripts/` |
| Upstream licence | MIT (c) 2025 Alireza Rezvani |
| Integrity | byte-identical to upstream, verified 2026-09-29 |
| Modified by Blackhearts | No — this `_BLACKHEART-ADAPTER.md` is the only added file |
| Contents | 29 files |
| Governing policy | [SKILL.md](../../../conformance/SKILL.md) |

## What this adapter is for

Blackhearts-local metadata. The directory is **unmodified upstream content**. This file records provenance and the conditions under which it may be used inside a BLACKHEART engagement.

## Why this is a collection adapter

Skills get one adapter each because each is an independently
loadable, separately audited unit. The content covered here is not: it loads as
a set, shares a single upstream review, and is governed by the same conditions.
One adapter per directory is proportionate and states the same guarantees
without generating boilerplate that would carry no information.

## What this is

Upstream's own **build, audit, and sync tooling** — the scripts that lint skills, check frontmatter, verify plugin manifests, publish mirrors, and install the catalogue into other agents.

## Why it matters here

These operate on **this mirror as a checkout**, not on an engagement target. They are vendored so an operator can see exactly how upstream validates and publishes, and so the process is reproducible. Do not run them against a client system: they are repository tooling and expect upstream's own layout.

## Evidence status

Any result this content produces is `UNVERIFIED` until independently demonstrated. Loading it does not authorize it to act on any target. A tool's own severity rating is **not** a BLACKHEART severity.

## Conditions of use

1. Read [`skills/conformance/SKILL.md`](../../../conformance/SKILL.md)
   before any use.
2. No target may be scanned, tested, or profiled until the operator supplies the
   target and explicit, written authorization recorded in the engagement file.
3. Do not execute any script from this content against a third-party system
   without that authorization. These are third-party files with third-party
   defects.
4. Report every result as `UNVERIFIED` until independently demonstrated, and
   record rejected hypotheses alongside confirmed findings.
5. Record the upstream commit and this adapter path in the evidence log, so any
   finding traces to the exact tool version that produced it.

## Provenance

- Licence text: [claude-skills-LICENSE](../../../licenses/claude-skills-LICENSE)
- Integration record: [VENDOR.md](../../../VENDOR.md)

## Inventory

| File | |
|---|---|
| `audit_skills.py` | — |
| `check_dual_publish.py` | — |
| `check_frontmatter.py` | — |
| `check_model_freshness.py` | — |
| `check_model_freshness_allowlist.txt` | — |
| `check_paths.py` | — |
| `check_paths_allowlist.txt` | — |
| `check_plugin_json.py` | — |
| `check_skill_names.py` | — |
| `codex-install.bat` | — |
| `codex-install.sh` | — |
| `convert.sh` | — |
| `derive_counters.py` | — |
| `extract_release_notes.py` | — |
| `gemini-install.sh` | — |
| `generate-docs.py` | — |
| `install.sh` | — |
| `openclaw-install.sh` | — |
| `review-new-skills.sh` | — |
| `smoke_exceptions.txt` | — |
| `smoke_json_output.py` | — |
| `smoke_scripts.py` | — |
| `sync-codebuff-skills.py` | — |
| `sync-codex-skills.py` | — |
| `sync-gemini-skills.py` | — |
| `sync-hermes-skills.py` | — |
| `sync-vibe-skills.py` | — |
| `sync_skill_bundles.py` | — |
| `vibe-install.sh` | — |
