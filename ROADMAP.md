# Roadmap

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

## How to read this

This is a statement of **direction**, not a schedule. There are no dates here
and none should be inferred.

Nothing on this list is a promise of delivery, and nothing is marked "in
progress" or "complete" unless it already exists in the repository. An item
appears on this list because it is a recognised gap in the current framework —
not because it has been planned, funded, or assigned.

Check a document against [`FILE-INDEX.txt`](FILE-INDEX.txt) before assuming it
is planned. If it is not indexed, it does not exist yet.

## Current state

The framework is a complete, coherent instruction set covering scope and
authorization, the evidence status taxonomy, adversarial methodology, web/API
and mobile assessment, business logic, the payment and entitlement chain,
artifact validation, evidence handling, severity rating, reference mappings,
remediation and retest, and reporting.

It is documentation only: no code, no scanners, no automation, and deliberately
none. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for why that is the correct
shape for a methodology framework.

## Recently closed

Gaps that were on this list and are now filled. Recorded so they are not
re-proposed.

| Gap | Closed by |
|---|---|
| Cloud and infrastructure assessment | [`docs/guides/CLOUD-IDENTITY.md`](docs/guides/CLOUD-IDENTITY.md) — IAM, policy, tenant boundary, confused deputy, cloud secrets |
| Agent instruction accessibility for agents | [`docs/agent/AGENT-OPERATING-PROTOCOL.md`](docs/agent/AGENT-OPERATING-PROTOCOL.md) — Layer 0 of the architecture |
| Depth on adversary emulation and attack paths | [`docs/modes/RED-HEART-ADVERSARY-EMULATION.md`](docs/modes/RED-HEART-ADVERSARY-EMULATION.md) · [`docs/guides/ATTACK-PATHS.md`](docs/guides/ATTACK-PATHS.md) |
| Alignment to recognised methodology standards | [`docs/guides/METHODOLOGY-STANDARDS.md`](docs/guides/METHODOLOGY-STANDARDS.md) |
| AI/agentic application assessment | [`docs/guides/AGENTIC-AI-SECURITY.md`](docs/guides/AGENTIC-AI-SECURITY.md) |

## Recognised gaps

Ordered by how much they weaken the framework when left unaddressed.

### 1. Worked end-to-end example

**Gap.** The templates show structure, but no complete worked engagement
demonstrates how a single finding travels from scope intake to a closed
remediation item.

**Why it matters.** A worked example is the fastest way to expose whether a
methodology is actually followable. Without one, structural correctness is
unproven — readers must supply their own operational intuition.

**Would consist of.** One synthetic, clearly-fictional engagement traced
through [`templates/ENGAGEMENT-RECORD.md`](templates/ENGAGEMENT-RECORD.md),
[`templates/TEST-LOG.md`](templates/TEST-LOG.md), [`templates/FINDING.md`](templates/FINDING.md),
and [`templates/FINAL-REPORT.md`](templates/FINAL-REPORT.md), including a
deliberately rejected hypothesis to demonstrate negative-result reporting.

**Constraint.** Must be entirely synthetic. No real target, no real
vulnerability, no invented statistics. A fabricated example teaching accurate
behaviour would violate the framework's own non-fabrication rule.

### 2. GraphQL and modern API surface shapes

**Gap.** [`docs/guides/WEB-API-TESTING.md`](docs/guides/WEB-API-TESTING.md)
assumes REST-shaped surfaces. GraphQL introspection, batching abuse, field-level
authorization, and WebSocket subscription authorization are not covered.

**Would consist of.** A guide covering introspection exposure, query-depth and
cost controls, field-level authorization, and subscription authorization.

### 3. Source-code review as a distinct mode

**Gap.** [`AGENT.md`](AGENT.md) §17 covers static and source analysis, but only
as a technique within other modes. There is no mode for a source-led engagement
where the codebase is the primary target.

**Would consist of.** A mode for taint-driven review, authorization-check
inventory across services, and secret scanning with the framework's evidence
discipline applied to source findings.

### 4. Accessibility of the instruction set for agent use

**Gap.** The framework is written for a human reader and for an AI agent
alike, but nothing states which parts are addressed to which.

**Would consist of.** Explicit markers distinguishing operator instruction from
agent instruction, reducing the chance that a human-facing instruction is
executed as an action.

### 5. Deeper coverage-control tooling

**Gap.**
[`templates/COVERAGE-MATRIX.md`](templates/COVERAGE-MATRIX.md) is a manual
artefact.

**Would consist of.** A generator that turns an endpoint inventory into a
starter matrix.

**Constraint.** A coverage aid only. It must not become a scanner — a tool that
probes targets would sit outside the framework's authorization model, which is
built on explicit human scoping.

### 6. Translation

**Gap.** English only.

**Would consist of.** Non-English editions, starting with the language most
used by the intended readership.

**Constraint.** Terminology is load-bearing here — `CONFIRMED` versus
`PARTIALLY CONFIRMED` versus `UNVERIFIED` is a distinction the whole framework
turns on. Translations must preserve the status vocabulary exactly or state
explicitly where it diverges.

## Explicitly out of scope

Recorded so these are not repeatedly proposed.

| Not planned | Why |
|---|---|
| Automated scanning or exploitation tooling | The framework's integrity model depends on explicit, human-established authorization. A tool that acts on targets cannot guarantee that. |
| Exploit or payload collections | Contradicts the framework's purpose. A methodology is not an arsenal. |
| A hosted assessment service | Would introduce authorization ambiguity the framework exists to remove. |
| Real-world case studies | Requires authorization that cannot be granted for retrospective disclosure. Synthetic examples only. |
| Bug-bounty scope automation | Scope interpretation is a human judgement, and automating it risks testing what is not permitted. |
| Severity as an automated score | [`docs/guides/SEVERITY-RATING.md`](docs/guides/SEVERITY-RATING.md) is deliberately a human rubric; automated severity is exactly the inflation this framework exists to prevent. |
| Broadening the status taxonomy | Six statuses already cover the observed situations. More statuses would add vocabulary without adding precision. |

## Contributing to this roadmap

Open an issue describing the gap and what a document covering it would need to
contain. The bar for anything on this list is that it closes a real gap and
does not introduce content the framework cannot honestly support.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the scope and hard rules that apply
to any proposed addition.
