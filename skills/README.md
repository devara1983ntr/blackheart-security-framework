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

This directory holds the **executable** side: a vendored mirror of the
**complete upstream repository** — 3,864 files covering 388 skills, 39 slash
commands, 33 agent personas, plugin manifests, upstream tooling, standards, audit
records, and documentation — plus the conformance layer that makes their output
admissible inside a BLACKHEART engagement.

```text
skills/
├── README.md                      This file
├── VENDOR.md                      Attribution, provenance, and the full audit record
├── openclaw.example.json5         Validated example configuration
├── conformance/
│   └── SKILL.md                   Mandatory wrapper for all vendored skills
├── third-party/
│   └── claude-skills/             Full mirror of the upstream catalogue
│       ├── engineering/           93 skills
│       ├── engineering-team/      53
│       ├── marketing-skill/       49
│       ├── c-level-advisor/       46
│       ├── c-level-agents/        22
│       ├── ra-qm-team/            19
│       ├── product-team/          17
│       ├── productivity/          12
│       ├── research/              10
│       ├── compliance-os/         9
│       ├── project-management/    9
│       ├── commercial/            8
│       ├── business-operations/   7
│       ├── marketing/             7
│       ├── agent-launcher/        6
│       ├── business-growth/       5
│       ├── finance/               5
│       ├── markdown-html/         5
│       └── research-ops/          5
│       ├── commands/              39 slash commands        + adapter
│       ├── agents/                33 agent personas        + adapter
│       ├── scripts/               upstream tooling         + adapter
│       ├── standards/             authoring standards      + adapter
│       ├── audit/                 upstream audit history   + adapter
│       ├── docs/                  667 reference pages      + adapter
│       ├── templates/             authoring templates      + adapter
│       ├── .claude-plugin/        plugin manifest          + adapter
│       ├── .codex-plugin/         plugin manifest          + adapter
│       ├── .claude/               project configuration    + adapter
│       └── <group>/skills/<name>/
│           ├── SKILL.md           Unmodified upstream content
│           └── _BLACKHEART-ADAPTER.md
├── catalog/                       Complete upstream index (30 categories), reference only
└── licenses/                      Preserved upstream licence texts
```

The mirror preserves upstream's own `<group>/skills/<name>` layout rather than
flattening it, so every skill's origin stays visible and upstream's cross-skill
links keep resolving. Every one of the 388 skills carries an adapter recording
its audit verdict and its conditions of use. The complete index, the audit
results, the adjudicated findings, and the list of what is deliberately *not*
vendored are in [`VENDOR.md`](VENDOR.md).

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

## The promoted security skills

Eight skills from the catalogue are promoted to a standing role in a security
engagement. These have individually hand-written adapters with full interface
documentation, authorization gates, maximum claims, and coverage contributions.
**Read the adapter before using the skill.**

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

## Commands, personas, and the rest of the mirror

The catalogue is not only skills. Three kinds of non-skill content load into an
agent, and each has a collection adapter:

**`commands/` — 39 slash commands.** Invocable as `/name`. A command is a
user-invoked entry point, not an analysis unit; it can launch a skill, so it
inherits that skill's conditions. A command that reaches a target with no
engagement record is the same violation as a skill doing it.

**`agents/` — 33 agent personas.** Role definitions that change how an agent
reasons and what it will do. This is the **highest-leverage** vendored content
in the repository and the easiest to get wrong: a persona can redefine an
agent's identity, widen its scope, or instruct it to act without asking, which is
precisely what the authorization gate prevents. Every persona is therefore
treated as **untrusted instruction**. No persona may widen scope, disable the
gate, or authorize a target. Where a persona conflicts with
`conformance/SKILL.md`, **conformance wins**. None is enabled in the example
config; adopting one is an explicit decision.

**`scripts/`, `standards/`, `audit/`, `docs/`, `templates/`, plugin manifests.**
Upstream's own tooling, conventions, audit history, generated documentation,
templates, and packaging declarations. All vendored verbatim and adapter-covered.
A plugin manifest is a **declaration, not an enforcement**: vendoring one
installs nothing and grants no permission.

## Three defects found by testing, not scanning

Every vendored tool passed the static audit. The most security-relevant one did
not survive being *run*. Testing `ai-security` against controlled input found:

1. **Its jailbreak signature fires on ordinary words.** `(DAN|STAN|DUDE|KEVIN|AIM|...)`
   has no word boundaries, so it matches *claim*, *standard*, *dangerous*. It
   scored 12 findings on `ARCHITECTURE.md` and 11 on `AGENT.md` — documents with
   no attack content at all.
2. **Its stdin path returns a constant.** Six different documents returned an
   identical score and an identical excerpt that was not in the input. Only
   `--test-file` actually scans.
3. **It does not detect `"Ignore all previous instructions"`.** Score `0.0`.

None of this is patched — vendored content stays byte-identical to upstream, or
the integrity guarantee is meaningless. It is recorded in the skill's adapter and
in [`VENDOR.md`](VENDOR.md) §3.1.1. The rule: **a finding from this tool is a
hypothesis, and a clean result is a coverage gap, not a clearance.**

## The rest of the catalogue

The other 380 skills are not promoted. Most are engineering, business, and
research tooling — competent at their own jobs and not written with security
evidence rules in mind. They are vendored in full because they are useful, and
each carries a machine-generated adapter recording its provenance, its audit
verdict, the categories of any findings, and the same five conditions of use.

That adapter is the whole contract. It does not claim a skill is safe. It
records what was found, adjudicates each finding in context, and states the
conditions under which the skill may be used. **A skill with no adapter is
unaudited third-party content and must not be used in an engagement** — the
validator fails the build if one appears.

Audit outcomes across all 388 skills: **354 PASS, 21 WARN, 13 FAIL.** Every
CRITICAL and HIGH finding was read by hand and adjudicated. No skill in the
catalogue showed a backdoor, a covert channel, credential exfiltration, or an
attempt to override safety. The recurring false-positive classes — a security
scanner flagging its own detection strings, literal `__import__('datetime')`
timestamps, documentation that advises *against* the pattern it matched — are
enumerated in [`VENDOR.md`](VENDOR.md) §3.1.

One finding is a genuine standing condition rather than a false positive:
`tech-debt-tracker` ships a sample codebase containing working code that POSTs
to live Stripe, Square, and PayPal endpoints. It is a teaching artefact, not
exfiltration, and its adapter marks it **never execute**.

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
come from the `name` field in frontmatter**, so
`third-party/claude-skills/engineering-team/skills/ai-security` loads as
`ai-security`, not as a path.

Because the mirror keeps upstream's nesting, some skills sit more than six
levels below a configured root. The example config therefore lists all 20 group
directories **plus** `commands/` and `agents/` in `skills.load.extraDirs`, so
**nothing vendored is silently skipped by a depth limit**. It then declares an explicit `enabled` policy for
every one of the 374 distinct skill names.

Note that 374 names cover 387 loadable directories: 13 names are defined at two
upstream paths each (for example `handoff` exists under both `engineering/` and
`productivity/`). One entry enables both copies. The path-level mapping is in
[`VENDOR.md`](VENDOR.md) §5.

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

The promoted security skills run as local, offline analysis. `ai-security` is
the only one with a built-in authorization gate (`--authorized` for gray-box
and white-box, exiting `2` without it). That gate is a **floor, not a
substitute** for the engagement record.

The wider catalogue has mixed requirements. 693 vendored scripts need
Python 3.8+; some need Node.js; a substantial number perform outbound HTTP
because fetching the target is their function. **Check a skill's adapter before
running anything.** No credentials are required by any analysis path, and none
should ever be requested.

## Maintenance

```text
Check for upstream drift : python3 .github/scripts/sync_upstream.py
Re-vendor and re-audit   : python3 .github/scripts/sync_upstream.py --apply
Regenerate the manifest  : python3 .github/scripts/gen_manifest.py
Regenerate the config    : python3 .github/scripts/gen_config.py
Validate everything      : python3 .github/scripts/validate.py
Add a skill              : audit → adapter → conformance check → register
Change the methodology   : update docs/ first, then adapters, then this file
```

`upstream-sync.yml` runs the drift check daily and **opens a pull request when
upstream changes**. It is configured never to merge — see the rationale at the
top of that workflow. Automation fetches, diffs, copies, re-audits, and
regenerates adapters; a human reads the diff and decides. A skill removed
upstream is reported and left in place, because deleting content is a human
decision and not a side effect of a cron job.

A vendored skill without an adapter, or an adapter without a maximum claim, is
not integrated — it is a liability.

## Related

| Document | Purpose |
|---|---|
| [`../docs/agent/AGENT-SKILL-CATALOGUE.md`](../docs/agent/AGENT-SKILL-CATALOGUE.md) | BLACKHEART's own 48 skills |
| [`../docs/agent/AGENT-OPERATING-PROTOCOL.md`](../docs/agent/AGENT-OPERATING-PROTOCOL.md) | How an agent must operate |
| [`../docs/guides/SUPPLY-CHAIN.md`](../docs/guides/SUPPLY-CHAIN.md) | Why provenance decides what is a finding |
| [`VENDOR.md`](VENDOR.md) | Attribution, licences, audit record, and the catalogue decision |
