# Agent documentation — start here

**For:** an AI agent, or a human operating one, working inside BLACKHEART
**Status:** the entry point. Read the documents in the order below.
**Scope note:** everything here documents the **already-implemented** framework.
Nothing in this directory adds a capability.

---

## The reading order

```text
START HERE  (this file)
   │
   ├─ 1  PHASE5-AGENT-OVERVIEW.md          what BLACKHEART is, what Phase 5 provides,
   │                                       read-only vs active, the five statuses
   │
   ├─ 2  ../AGENT-OPERATING-PROTOCOL.md    the operating discipline, the eleven-step
   │    PHASE5-FAILURE-HANDLING.md         order, and the deterministic failure matrix
   │
   ├─ 3  PHASE5-AUTHORIZATION-PROTOCOL.md  what must exist before anything active
   │    PHASE5-SCOPE-PROTOCOL.md           the scope model, exactly as implemented
   │
   ├─ 4  PHASE5-SAFETY-RULES.md            the never-do list, in full
   │
   ├─ 5  PHASE5-WORKBENCH-OPERATIONS.md    what each command does and refuses
   │
   ├─ 6  PHASE5-EVIDENCE-PROTOCOL.md       the record, the status ladder, integrity
   │
   └─ 7  ../workbench/                     the implementation-derived reference
        README · COMMANDS · LIMITATIONS · THREAT-MODEL · END-TO-END
        INDEPENDENT-SECURITY-REVIEW.md     the review, and its status: outstanding
```

A diagram is not a rule. The binding order is §31's hierarchy below, and where two
documents disagree, **the stricter one wins**.

## Policy documents, in the order they bind

| Document | Read it for |
|---|---|
| [`../../LEGAL.md`](../../LEGAL.md) | Who this project is, and what it does not claim |
| [`../../AUTHORIZATION-AGREEMENT.md`](../../AUTHORIZATION-AGREEMENT.md) | The template an authorization is recorded in |
| [`../../TERMS-OF-USE.md`](../../TERMS-OF-USE.md) | The terms, liability, and the limits of enforceability |
| [`../../ACCEPTABLE-USE.md`](../../ACCEPTABLE-USE.md) | Permitted and prohibited use, in operational detail |
| [`PHASE5-SAFETY-RULES.md`](PHASE5-SAFETY-RULES.md) | Agent-specific binding rules (mirrors AI Agent Terms) |
| [`../../AI-AGENT-TERMS.md`](../../AI-AGENT-TERMS.md) | The same obligations, as terms |
| [`../../SECURITY-RESEARCH-DISCLAIMER.md`](../../SECURITY-RESEARCH-DISCLAIMER.md) | What research under this framework establishes |
| [`../../PRIVACY-POLICY.md`](../../PRIVACY-POLICY.md) | What the software and site actually do with data |
| [`../../DOWNLOAD-AND-ACQUISITION-POLICY.md`](../../DOWNLOAD-AND-ACQUISITION-POLICY.md) | What may be acquired, and what is refused |
| [`../../RESPONSIBLE-USE.md`](../../RESPONSIBLE-USE.md) | How to work without causing harm |
| [`../../THIRD-PARTY-CONTENT.md`](../../THIRD-PARTY-CONTENT.md) | Licences, attribution, what is not claimed |
| [`../../policy/BLACKHEART-POLICY.json`](../../policy/BLACKHEART-POLICY.json) | The whole policy, machine-readable, v1.0.0 |

## Hierarchy

Six levels. A rule at a lower level never overrides a higher one; a specific
instruction never overrides a prohibition.

| Level | What it is | Where |
|---|---|---|
| **1** | Core BLACKHEART rules — identity, evidence discipline, the conformance layer | `AGENT.md`, `skills/conformance/SKILL.md` |
| **2** | Phase 5 agent operating rules — authorization first, the never-do list, stop conditions | `PHASE5-SAFETY-RULES.md`, `PHASE5-FAILURE-HANDLING.md` |
| **3** | Authorization and scope — what must exist before anything active, and what the scope file enforces | `PHASE5-AUTHORIZATION-PROTOCOL.md`, `PHASE5-SCOPE-PROTOCOL.md` |
| **4** | Technical workbench documentation — per capability, implementation-derived | `PHASE5-WORKBENCH-OPERATIONS.md`, `docs/workbench/` |
| **5** | Evidence and reporting — the record, the status ladder, the report's own rules | `PHASE5-EVIDENCE-PROTOCOL.md`, `docs/workbench/LIMITATIONS.md` |
| **6** | Legal, usage and privacy policies | the root policy documents above |

**Conflict resolution.** Stricter wins. If two documents appear to contradict each
other, do the following, in order:

1. follow the one that permits **less**;
2. check the implementation, which is the source of truth for what the tool
   actually does;
3. report the contradiction rather than choosing quietly.

## Where the rest of the material lives

| Topic the directive names | Where it actually is |
|---|---|
| Decision tree (blocked / ambiguous) | `../AGENT-OPERATING-PROTOCOL.md` §3.2 and `PHASE5-WORKBENCH-OPERATIONS.md` §"The decision tree" |
| HTTP workbench, replay, comparison | `../workbench/README.md`, `../workbench/COMMANDS.md`, and §"Per-capability notes" in `PHASE5-WORKBENCH-OPERATIONS.md` |
| API testing | same, plus `AGENT.md` §"API" guidance |
| Web discovery | same; the external-domain rule is stated in `PHASE5-WORKBENCH-OPERATIONS.md` |
| Fuzzing | same; the budget and destructiveness rules are in `PHASE5-SAFETY-RULES.md` |
| Resource acquisition | `PHASE5-WORKBENCH-OPERATIONS.md` + `../../DOWNLOAD-AND-ACQUISITION-POLICY.md` |
| Document and archive extraction | `PHASE5-WORKBENCH-OPERATIONS.md` + `../workbench/LIMITATIONS.md` |
| Emergency mode | `PHASE5-WORKBENCH-OPERATIONS.md` §"Per-capability notes" |
| Reporting | `PHASE5-EVIDENCE-PROTOCOL.md` + `../workbench/COMMANDS.md` |

Codes are not maintained as a separate copy here. They are recorded in
[`../../SECURITY.md`](../../SECURITY.md) and in
[`../workbench/INDEPENDENT-SECURITY-REVIEW.md`](../workbench/INDEPENDENT-SECURITY-REVIEW.md).
