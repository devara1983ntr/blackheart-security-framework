<div align="center">

# ⬢ BLACKHEART

### A governed security-supply-chain framework for AI agents

**388 security skills · 39 commands · 33 agent personas · 3,864 verified files · 399 audited adapters**

*Skills are not the problem. Unvetted skills are.*

[![validate](https://github.com/devara1983ntr/blackheart-security-framework/actions/workflows/validate.yml/badge.svg)](https://github.com/devara1983ntr/blackheart-security-framework/actions/workflows/validate.yml)
[![upstream-sync](https://github.com/devara1983ntr/blackheart-security-framework/actions/workflows/upstream-sync.yml/badge.svg)](https://github.com/devara1983ntr/blackheart-security-framework/actions/workflows/upstream-sync.yml)
[![license](https://img.shields.io/badge/license-MIT-00d4a5.svg)](LICENSE)
[![upstream](https://img.shields.io/badge/mirror-alirezarezvani%2Fclaude--skills-6f42c1.svg)](https://github.com/alirezarezvani/claude-skills)

</div>

---

## The problem

A security agent is only as trustworthy as the skills it loads. Install an
unvetted skill and you have handed an autonomous system a third-party
instruction — one that can read files, run shell commands, and exfiltrate. There
is no lockfile, no signature, no audit trail, and no way to tell a helpful
prompt from a hostile one.

The industry currently answers this with a README. That is not a control.

## The answer

Blackhearts treats every third-party skill as **untrusted code**, and makes the
governance mechanical rather than aspirational.

| Problem | Blackhearts answer |
|---|---|
| Unvetted instructions reach the agent | Every skill ships a reviewed `_BLACKHEART-ADAPTER.md` declaring exactly what it does and what it must never do |
| Upstream changes silently | 3,864 files pinned to a commit SHA, compared byte-for-byte by CI on every push |
| Agent personas quietly widen scope | 33 personas treated as **hostile input** — none enabled by default, none may authorize a target or disable the gate |
| A scanner's clean bill of health is trusted | Findings are hypotheses; clean results are recorded as **coverage gaps** |
| Nobody can prove coverage | A 7-check CI gate and a 15-group audit that fail loudly |

> **The premise:** you cannot make untrusted instructions safe. You can only
> make them *legible, bounded, and accountable* before they run.

---

## Coverage

Everything upstream ships, verified and accounted for — not just the skills.

<div align="center">

| Collection | Files | | Collection | Files |
|---|---:|---|---|---:|
| 🔐 Skills | **388** skills | | 📋 Standards | **11** |
| ⌘ Slash commands | **39** | | 🗂️ Audit records | **32** |
| 🤖 Agent personas | **33** (+1 template) | | 📚 Doc pages | **667** |
| 🧩 Plugin manifests | **2** | | 🧪 Test fixtures | **1** |
| 🛠️ Upstream scripts | **29** | | 🔗 Catalogue files | **32** |
| 🧱 `.claude/` config | **13** | | 📦 Templates | **3** |
| 🔀 Orchestration | **1** | | 🤖 Custom GPT | **1** |
| | | | **Total vendored** | **3,864** |
| | | | **Blackhearts adapters** | **399** |

</div>

**53 of 58 upstream top-level areas vendored. 5 excluded — every one with a
recorded reason.** See [`skills/VENDOR.md`](skills/VENDOR.md) §2.0.1.

---

## Architecture

```
                    untrusted upstream
                            │
                            ▼
                 ┌──────────────────────┐
                 │   PIN + VERIFY       │   3,864 files vs commit SHA
                 │   no drift allowed   │   byte-for-byte, in CI
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │   ADAPTER LAYER      │   399 reviewed contracts
                 │   one per skill      │   declared capability
                 │   and collection     │   declared prohibitions
                 └──────────┬───────────┘
                            ▼
        ┌────────────────────────────────────────────┐
        │              CONFORMANCE                   │  wins every conflict
        │   evidence vocabulary · status ladder      │
        │   no-scope no-test · no claim without proof │
        └──────────┬─────────────────────────────────┘
                   ▼
        ┌────────────────────────────────────────────┐
        │             SECURITY GATE                  │  declarative
        │  requireAuthorizedTarget · requireRecord   │  not advisory
        │  requireAdapter · denyTargetsWithoutScope  │
        └──────────┬─────────────────────────────────┘
                   ▼
                   agent
```

### The conformance layer wins

Where a vendored persona, command, or skill conflicts with
[`skills/conformance/SKILL.md`](skills/conformance/SKILL.md), **conformance
wins.** No vendored content can widen scope, disable the gate, or authorize a
target. This is the single most important design decision in the framework.

---

## The evidence rules

Most security tooling overstates what it knows. Blackhearts does not.

- **A finding is a hypothesis, never a conclusion.** It becomes a finding only
  after independent demonstration.
- **A clean result is a coverage gap, not a clearance.** An untested category is
  reported as untested.
- **Negative results and rejected hypotheses are preserved.** They are evidence.
- **Every claim traces to a log ID, or it is not a claim.**

The payoff: the most security-relevant vendored tool — a jailbreak detector —
still has three real defects after passing a full static audit. A framework that
only runs scanners would have shipped those silently. See
[`VENDOR.md`](skills/VENDOR.md) §3.1.1.

---

## Quick start

```bash
git clone https://github.com/devara1983ntr/blackheart-security-framework.git
cd blackheart-security-framework

# prove the mirror is intact — 7/7 checks
python3 -m pip install json5
python3 .github/scripts/validate.py

# check for upstream drift — report-only, never mutates
python3 .github/scripts/sync_upstream.py
```

<details>
<summary><b>Start an authorised engagement</b></summary>

```yaml
engagement:
  id: ENG-2026-001
  target: https://example.com
  authorizedBy: <named owner>
  window: 2026-09-29T00:00Z/2026-10-06T00:00Z
```

Without a target, a window, and a named authoriser, **the gate refuses to run.**
That refusal is the feature.

</details>

---

## The gate

`skills/openclaw.example.json5` — 374 entries, generated and CI-verified.

```json5
security: {
  requireAuthorizedTarget: true,
  requireEngagementRecord: true,
  requireAdapter: true,
  denyTargetsWithoutScope: true,
  defaultEvidenceStatus: 'UNVERIFIED',
}
```

Declarative flags, not executable policy — a config that can run code is not a
control, it is a vulnerability.

---

## CI: 7 checks, 2 workflows

| Check | What it proves |
|---|---|
| `adapters` | every skill and collection has a reviewed adapter |
| `integrity` | 3,864 files byte-identical to the pinned SHA + 399 adapters |
| `catalog` | 32 catalogue files unmodified |
| `links` | 5,287 local links; **0 broken in authored docs** |
| `index` | 4,364 entries; 0 unindexed, 0 dangling |
| `secrets` | no credential material outside a 15-entry allowlist |
| `config` | JSON5 parses; 374/374 skills declared |

`validate.yml` runs on push and PR. `upstream-sync.yml` runs daily at 03:17 UTC
and **opens a PR — it never auto-merges.** Invariant 14: *detection is
automated; judgement is not.*

---

## Documentation

| | |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | layers, data flow, invariants, trade-offs |
| [`AGENT.md`](AGENT.md) | how an agent is expected to behave |
| [`SECURITY.md`](SECURITY.md) | threat model, disclosure, secret handling |
| [`CHANGELOG.md`](CHANGELOG.md) | full version history |
| [`ROADMAP.md`](ROADMAP.md) | what is next |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | how to contribute safely |
| [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) | conduct |
| [`FILE-INDEX.txt`](FILE-INDEX.txt) | all 4,364 files, one per line |
| [`skills/VENDOR.md`](skills/VENDOR.md) | provenance, exclusions, defects |
| [`skills/README.md`](skills/README.md) | the catalogue and its rules |
| [`skills/conformance/SKILL.md`](skills/conformance/SKILL.md) | the rules that win |
| [`docs/`](docs) · [`examples/`](examples) · [`templates/`](templates) | reference material |

---

## Responsible use

Blackhearts is for **authorised** security work. It is not for attacking
systems you do not own or have written permission to test.

- No target is engaged without an explicit, recorded authorisation.
- No credential is ever requested, stored, or handled by this framework.
- No production data is modified. Write capability is answered by static
  analysis, not by writing.
- Findings default to `UNVERIFIED`. Claims require evidence.

Violating these constraints is both a security failure and a legal one.

---

## Provenance

Vendored content is **never modified.** Not one byte. If an upstream tool has a
defect, we record the defect and leave the code alone — a mirror that patches its
source stops being a mirror, and stops being evidence.

| Source | Pin | Licence |
|---|---|---|
| [`alirezarezvani/claude-skills`](https://github.com/alirezarezvani/claude-skills) | `19392f7a` | MIT — [`claude-skills-LICENSE`](skills/licenses/claude-skills-LICENSE) |
| [`VoltAgent/awesome-openclaw-skills`](https://github.com/VoltAgent/awesome-openclaw-skills) | `f274daa` | MIT — [`awesome-openclaw-skills-LICENSE`](skills/licenses/awesome-openclaw-skills-LICENSE) |

Blackhearts-authored content is MIT, © 2026 Devara.

---

<div align="center">

**Blackhearts** — *verify before you enable.*

[![MIT](https://img.shields.io/badge/license-MIT-00d4a5.svg)](LICENSE)
[![maintained](https://img.shields.io/badge/maintained-yes-00d4a5.svg)](CHANGELOG.md)

</div>
