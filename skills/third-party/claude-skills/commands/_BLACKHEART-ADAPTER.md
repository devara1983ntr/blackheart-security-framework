# Blackhearts Adapter — `commands/` (slash commands)

| Field | Value |
|---|---|
| Upstream | `https://github.com/alirezarezvani/claude-skills` |
| Upstream commit | `19392f7a08264ed00486a251f5b2098321771f94` |
| Upstream path | `commands/` |
| Upstream licence | MIT (c) 2025 Alireza Rezvani |
| Integrity | byte-identical to upstream, verified 2026-09-29 |
| Modified by Blackhearts | No — this `_BLACKHEART-ADAPTER.md` is the only added file |
| Contents | 40 files |
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

Upstream's **slash commands** — invocable as `/name`, each a markdown file whose frontmatter declares its name, description, and argument hint. They wrap or invoke skills; they are not skills themselves.

## Why it matters here

A command is a **user-invoked entry point**, not an analysis unit. It can launch a skill, so it inherits that skill's adapter and its conditions. A command that reaches a target with no engagement record is the same violation as a skill doing it.

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

| File | Frontmatter `name` |
|---|---|
| `.gitkeep` | — |
| `a11y-audit.md` | `a11y-audit` |
| `changelog.md` | `changelog` |
| `chaos-experiment.md` | — |
| `code-to-prd.md` | `code-to-prd` |
| `competitive-matrix.md` | `competitive-matrix` |
| `cs-aeo.md` | `cs-aeo` |
| `cs-backend-review.md` | — |
| `cs-engineer-grill.md` | — |
| `cs-frontend-review.md` | — |
| `cs-fullstack-review.md` | — |
| `cs-webinar.md` | `cs-webinar` |
| `financial-health.md` | `financial-health` |
| `flag-cleanup.md` | — |
| `focused-fix.md` | `focused-fix` |
| `google-workspace.md` | `google-workspace` |
| `karpathy-check.md` | `karpathy-check` |
| `okr.md` | `okr` |
| `operator-audit.md` | — |
| `persona.md` | `persona` |
| `pipeline.md` | `pipeline` |
| `plugin-audit.md` | `plugin-audit` |
| `prd.md` | `prd` |
| `project-health.md` | `project-health` |
| `retro.md` | `retro` |
| `rice.md` | `rice` |
| `saas-health.md` | `saas-health` |
| `seo-auditor.md` | `seo-auditor` |
| `slo-design.md` | — |
| `sprint-health.md` | `sprint-health` |
| `sprint-plan.md` | `sprint-plan` |
| `tc.md` | `tc` |
| `tdd.md` | `tdd` |
| `tech-debt.md` | `tech-debt` |
| `user-story.md` | `user-story` |
| `wiki-ingest.md` | `wiki-ingest` |
| `wiki-init.md` | `wiki-init` |
| `wiki-lint.md` | `wiki-lint` |
| `wiki-log.md` | `wiki-log` |
| `wiki-query.md` | `wiki-query` |
