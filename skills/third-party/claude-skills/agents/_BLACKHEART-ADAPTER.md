# Blackhearts Adapter — `agents/` (agent personas)

| Field | Value |
|---|---|
| Upstream | `https://github.com/alirezarezvani/claude-skills` |
| Upstream commit | `19392f7a08264ed00486a251f5b2098321771f94` |
| Upstream path | `agents/` |
| Upstream licence | MIT (c) 2025 Alireza Rezvani |
| Integrity | byte-identical to upstream, verified 2026-09-29 |
| Modified by Blackhearts | No — this `_BLACKHEART-ADAPTER.md` is the only added file |
| Contents | 35 files |
| Governing policy | [SKILL.md](../../../../conformance/SKILL.md) |

## What this adapter is for

Blackhearts-local metadata. The directory is **unmodified upstream content**. This file records provenance and the conditions under which it may be used inside a BLACKHEART engagement.

## Why this is a collection adapter

Skills get one adapter each because each is an independently
loadable, separately audited unit. The content covered here is not: it loads as
a set, shares a single upstream review, and is governed by the same conditions.
One adapter per directory is proportionate and states the same guarantees
without generating boilerplate that would carry no information.

## What this is

Upstream's **agent personas** — specialist role definitions (`cs-*` plus a handful of personas) that set role, scope, and escalation behaviour for an agent. They contain no executable logic; they change how an agent reasons and what it is willing to do.

## Why it matters here

A persona is the **highest-leverage** vendored content here and the easiest to get wrong. A persona can redefine an agent's identity, widen its scope, or instruct it to act without asking — which is exactly what the authorization gate prevents, and a persona is a natural place for that instruction to be smuggled in.

Every persona is therefore treated as **untrusted instruction**, not trusted policy. `skills/conformance/SKILL.md` governs. No persona may widen scope, disable the gate, or authorize a target. Where a persona conflicts with the conformance layer, **conformance wins**.

## Evidence status

Any result this content produces is `UNVERIFIED` until independently demonstrated. Loading it does not authorize it to act on any target. A tool's own severity rating is **not** a BLACKHEART severity.

## Conditions of use

1. Read [`skills/conformance/SKILL.md`](../../../../conformance/SKILL.md)
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

- Licence text: [claude-skills-LICENSE](../../../../licenses/claude-skills-LICENSE)
- Integration record: [VENDOR.md](../../../../VENDOR.md)

## Inventory

| File | Frontmatter `name` |
|---|---|
| `CLAUDE.md` | — |
| `business-growth/cs-growth-strategist.md` | `cs-growth-strategist` |
| `c-level/cs-ceo-advisor.md` | `cs-ceo-advisor` |
| `c-level/cs-cto-advisor.md` | `cs-cto-advisor` |
| `engineering-team/cs-engineering-lead.md` | `cs-engineering-lead` |
| `engineering-team/cs-workspace-admin.md` | `cs-workspace-admin` |
| `engineering/cs-backend-engineer.md` | `cs-backend-engineer` |
| `engineering/cs-frontend-engineer.md` | `cs-frontend-engineer` |
| `engineering/cs-fullstack-engineer.md` | `cs-fullstack-engineer` |
| `engineering/cs-karpathy-reviewer.md` | `cs-karpathy-reviewer` |
| `engineering/cs-senior-engineer.md` | `cs-senior-engineer` |
| `engineering/cs-wiki-ingestor.md` | `cs-wiki-ingestor` |
| `engineering/cs-wiki-librarian.md` | `cs-wiki-librarian` |
| `engineering/cs-wiki-linter.md` | `cs-wiki-linter` |
| `finance/cs-financial-analyst.md` | `cs-financial-analyst` |
| `marketing/cs-aeo.md` | `cs-aeo` |
| `marketing/cs-content-creator.md` | `cs-content-creator` |
| `marketing/cs-demand-gen-specialist.md` | `cs-demand-gen-specialist` |
| `marketing/cs-webinar-marketer.md` | `cs-webinar-marketer` |
> **Count: 38 files — 33 agent personas** (32 deployable plus `personas/TEMPLATE.md`, a blank starting point), plus `CLAUDE.md` and `personas/README.md` as collection documentation, and 3 empty `.gitkeep` files marking category directories. The `.gitkeep` files and the two documentation files are vendored byte-identical and carry no persona definition; they are listed here so the collection is fully accounted for. Earlier drafts of this repository claimed 34 personas — that figure counted `CLAUDE.md` as a persona and is corrected here.

| `personas/README.md` | — |
| `c-level/.gitkeep` | — |
| `marketing/.gitkeep` | — |
| `product/.gitkeep` | — |
| `personas/TEMPLATE.md` | `Agent Name` |
| `personas/content-strategist.md` | `Content Strategist` |
| `personas/devops-engineer.md` | `DevOps Engineer` |
| `personas/finance-lead.md` | `Finance Lead` |
| `personas/growth-marketer.md` | `Growth Marketer` |
| `personas/product-manager.md` | `Product Manager` |
| `personas/solo-founder.md` | `Solo Founder` |
| `personas/startup-cto.md` | `Startup CTO` |
| `product/cs-agile-product-owner.md` | `cs-agile-product-owner` |
| `product/cs-product-analyst.md` | `cs-product-analyst` |
| `product/cs-product-manager.md` | `cs-product-manager` |
| `product/cs-product-strategist.md` | `cs-product-strategist` |
| `product/cs-ux-researcher.md` | `cs-ux-researcher` |
| `project-management/cs-project-manager.md` | `cs-project-manager` |
| `ra-qm-team/cs-quality-regulatory.md` | `cs-quality-regulatory` |
