# Skills

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`../AGENT.md`](../AGENT.md) · [`../ARCHITECTURE.md`](../ARCHITECTURE.md) · [`VENDOR.md`](VENDOR.md) · [`conformance/SKILL.md`](conformance/SKILL.md) · [`../docs/agent/AGENT-OPERATING-PROTOCOL.md`](../docs/agent/AGENT-OPERATING-PROTOCOL.md)

> This directory grants **no authorization to test any system.** It provides
> tools and methods for engagements that have written authorization recorded in
> an engagement record. See [`../SECURITY.md`](../SECURITY.md).

## What is here

BLACKHEART's own skills are documented in
[`../docs/agent/AGENT-SKILL-CATALOGUE.md`](../docs/agent/AGENT-SKILL-CATALOGUE.md)
— 48 named skills, each with a trigger, procedure, output, maximum claim, and
stop condition. That catalogue is the methodology.

This directory holds the **executable** side: eight vendored third-party skills
that perform real analysis, plus the conformance layer that makes their output
admissible inside a BLACKHEART engagement.

```text
skills/
├── README.md                      This file
├── VENDOR.md                      Attribution, licensing, provenance
├── conformance/
│   └── SKILL.md                   Mandatory wrapper for all vendored skills
├── third-party/
│   ├── ai-security/               + _BLACKHEART-ADAPTER.md
│   ├── cloud-security/            + _BLACKHEART-ADAPTER.md
│   ├── dependency-auditor/        + _BLACKHEART-ADAPTER.md
│   ├── incident-response/         + _BLACKHEART-ADAPTER.md
│   ├── red-team/                  + _BLACKHEART-ADAPTER.md
│   ├── security-pen-testing/      + _BLACKHEART-ADAPTER.md
│   ├── senior-security/           + _BLACKHEART-ADAPTER.md
│   └── threat-detection/          + _BLACKHEART-ADAPTER.md
├── catalog/                       Reference index only — no code
└── licenses/                      Preserved upstream licence texts
```

## The conformance layer is not optional

Vendored skills were written by other authors, for their own purposes. Most are
competent. **None were written knowing BLACKHEART's evidence rules.** They do
not know about the status taxonomy, the severity ceiling, the authorization
gate, or the coverage discipline.

[`conformance/SKILL.md`](conformance/SKILL.md) closes that gap. It requires:

```text
1. The authorization gate, before any invocation
2. Status conversion of every tool result — a match is UNVERIFIED, not CONFIRMED
3. Severity computed separately, bounded by the evidence status
4. An enforcement point on every finding carried forward
5. Coverage recorded, including what the tool could not do
6. Raw tool output preserved unmodified, as evidence
```

**Load `blackheart-conformance` before any vendored skill.** It is marked
`always: true` in frontmatter so it is eligible in every session.

The vendored skills are **not modified**. What BLACKHEART adds lives in
separate adapter files. See [`VENDOR.md`](VENDOR.md).

## The vendored skills

| Skill | Does | Governed by | Max claim |
|---|---|---|---|
| `ai-security` | Prompt injection, jailbreak, poisoning, tool-abuse signatures; MITRE ATLAS | `AGENTIC-AI-SECURITY.md` | Signature match → `UNVERIFIED` |
| `red-team` | Kill-chain planning, choke points, OPSEC risk | `RED-HEART-ADVERSARY-EMULATION.md` | A plan is `UNVERIFIED` by construction |
| `cloud-security` | IAM, storage exposure, security groups, IaC | `CLOUD-IDENTITY.md` | Posture finding → `UNVERIFIED` until demonstrated |
| `security-pen-testing` | OWASP audit, static analysis, API testing, report generation | `WEB-API-TESTING.md` | Checklist/static match → `UNVERIFIED` |
| `dependency-auditor` | Vulnerabilities, licence conflicts, upgrade paths | `SUPPLY-CHAIN.md` | CVE match → `UNVERIFIED` until reachability |
| `threat-detection` | Threat hunting, IOC analysis, anomaly prioritisation | `ADVERSARY-EMULATION.md` | A hunting lead is `UNVERIFIED` by definition |
| `senior-security` | STRIDE, DREAD, secret scanning, skill routing | `ATTACK-PATHS.md`, `SUPPLY-CHAIN.md` | A risk model is not evidence |
| `incident-response` | Triage, classification, false-positive filtering | `ADVERSARY-EMULATION.md` | Classification → `UNVERIFIED` until corroborated |

Each has a `_BLACKHEART-ADAPTER.md` with its full interface, authorization gate,
maximum claim, skill-specific cautions, and coverage contribution. **Read the
adapter before using the skill.**

## Two cautions worth stating up front

**`security-pen-testing` includes a report generator that formats findings you
supply.** It does not validate them. Feeding it unverified findings produces a
confident-looking report of unverified claims — the most likely way any of
these skills could cause real harm inside this framework. Every finding must
carry a BLACKHEART status and an evidence reference before it is passed in.

**`incident-response` operates on live incident evidence**, which a
penetration-testing authorization does not cover. Default to synthetic input.

## Loading

These are standard [`SKILL.md`](https://agentskills.io) skills, so they load
under OpenClaw and other AgentSkills-compatible runtimes.

```text
Workspace skills root : <workspace>/skills          ← this directory
Project agent skills  : <workspace>/.agents/skills
Extra directories     : skills.load.extraDirs
```

Discovery finds a `SKILL.md` anywhere under a configured root, up to six levels
deep. The folder path is for organisation only — the **name and slash command
come from the `name` field in frontmatter**, so `third-party/ai-security`
loads as `ai-security`, not as a path.

A working configuration, including agent allowlists and per-skill gating, is in
[`openclaw.example.json5`](openclaw.example.json5).

### Agent allowlists

Restrict which skills an agent may see independently of where they load from:

```json5
{
  agents: {
    defaults: { skills: ["blackheart-conformance"] },
    entries: {
      "assessor": {
        skills: [
          "blackheart-conformance", "ai-security", "cloud-security",
          "dependency-auditor", "security-pen-testing", "senior-security",
          "threat-detection", "red-team",
        ],
      },
      "read-only": { skills: ["blackheart-conformance", "dependency-auditor"] },
    },
  },
}
```

A non-empty per-agent list is the **final** set — it does not merge with
defaults. An empty list exposes no skills.

The allowlist is a visibility control, not a security boundary. An agent that
can execute a shell can reach anything on the host regardless of which skills
it can see. Constrain execution separately with sandboxing, OS-level isolation,
and per-resource credentials.

## Using a skill

```text
1. Engagement record exists and authorization is CONFIRMED
2. Target is inside allowed_assets
3. blackheart-conformance is loaded
4. The skill's _BLACKHEART-ADAPTER.md has been read
5. The adapter's authorization gate is satisfied
6. Run the tool; capture raw output unmodified
7. Convert every result to a BLACKHEART status
8. Compute severity separately, within the status ceiling
9. Record the coverage contribution
```

## Requirements

```text
Python 3.8+ for all vendored scripts
No network access required by the analysis paths
No credentials required — and none should ever be requested
```

All eight skills run as local, offline analysis. `ai-security` is the only one
with a built-in authorization gate (`--authorized` for gray-box and white-box,
exiting `2` without it). That gate is a **floor, not a substitute** for the
engagement record.

## Maintenance

```text
Update a vendored skill : see VENDOR.md § Updating a vendored skill
Add a skill             : audit → adapter → conformance check → register
Change the methodology  : update docs/ first, then adapters, then this file
```

A vendored skill without an adapter, or an adapter without a maximum claim, is
not integrated — it is a liability.

## Related

| Document | Purpose |
|---|---|
| [`../docs/agent/AGENT-SKILL-CATALOGUE.md`](../docs/agent/AGENT-SKILL-CATALOGUE.md) | BLACKHEART's own 48 skills |
| [`../docs/agent/AGENT-OPERATING-PROTOCOL.md`](../docs/agent/AGENT-OPERATING-PROTOCOL.md) | How an agent must operate |
| [`../docs/guides/SUPPLY-CHAIN.md`](../docs/guides/SUPPLY-CHAIN.md) | Why provenance decides what is a finding |
| [`VENDOR.md`](VENDOR.md) | Attribution, licences, and the catalogue decision |
