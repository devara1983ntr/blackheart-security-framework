# Architecture

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

## What "architecture" means here

BLACKHEART is a documentation framework, not a software system. It has no
runtime, no dependencies, and nothing to compile. Its architecture is the
structure of its own instruction set: which document governs what, how they
combine into an engagement, and which rule wins when two of them disagree.

This document describes that structure so that a reader can navigate the
framework deliberately rather than by trial and error.

## Design goal

A long instruction set has one dominant failure mode: documents accumulate until
it is unclear which one applies. Every structural decision here exists to
prevent that.

> **One governing rule, progressively specialised layers, and an explicit
> precedence order.**

## The four layers

```text
┌──────────────────────────────────────────────────────────────┐
│  LAYER 1 — CORE           AGENT.md                            │
│  Mission, scope intake, status taxonomy, methodology loop,   │
│  quality gate, non-fabrication rule. Governs everything.      │
└──────────────────────────────┬───────────────────────────────┘
                               │ extends, never relaxes
┌──────────────────────────────▼───────────────────────────────┐
│  LAYER 2 — MODES           docs/modes/                        │
│  Domain-specific operating procedures that expand Layer 1     │
│  for particular assessment shapes.                            │
└──────────────────────────────┬───────────────────────────────┘
                               │ selected per engagement
┌──────────────────────────────▼───────────────────────────────┐
│  LAYER 3 — GUIDES          docs/guides/                       │
│  Reference material: what to ask, how to classify, how to     │
│  report. Consulted rather than executed in sequence.          │
└──────────────────────────────┬───────────────────────────────┘
                               │ produces
┌──────────────────────────────▼───────────────────────────────┐
│  LAYER 4 — ARTEFACTS       templates/ · examples/             │
│  The concrete outputs of an engagement.                       │
└──────────────────────────────────────────────────────────────┘
```

### Layer 1 — Core

[`AGENT.md`](AGENT.md) is the master instruction. It is not a guide among
guides; it is the document every other document is subordinate to. It defines
the mission, the scope intake, the six-status evidence taxonomy, the
`SCOPE → … → FINAL REPORT` pipeline, the methodology loop, the final quality
gate, and the non-fabrication rule.

Its rules are unconditional. A mode may add specificity; it may never relax
anything here.

### Layer 2 — Modes

[`docs/modes/`](docs/modes/) contains four operating procedures:

| Mode | Scope of application |
|---|---|
| [`SECURITY-AUDIT.md`](docs/modes/SECURITY-AUDIT.md) | Default full-spectrum adversarial assessment across the whole authorized surface |
| [`SECURITY-RESEARCH-MODE.md`](docs/modes/SECURITY-RESEARCH-MODE.md) | Trust-boundary analysis and safe exploit validation for a defined research scope |
| [`DIGITAL-ASSET-DELIVERY-MODE.md`](docs/modes/DIGITAL-ASSET-DELIVERY-MODE.md) | Paid products, entitlements, and protected file delivery |
| [`ZERO-CREDENTIAL-ESCALATION-MODE.md`](docs/modes/ZERO-CREDENTIAL-ESCALATION-MODE.md) | Discovery from zero privilege, method escalation, proof strength, and coverage control |

A mode is selected by the shape of the engagement. A paid-product assessment
runs the audit mode for the general surface and the digital-asset mode for the
commerce path. The zero-credential layer applies across all of them, because
its concerns — method escalation and coverage — are not domain-specific.

### Layer 3 — Guides

[`docs/guides/`](docs/guides/) is reference material, consulted at the point of
need rather than executed in order.

| Guide | Answers |
|---|---|
| [`SCOPE.md`](docs/guides/SCOPE.md) | What may I test, and what does authorization actually cover? |
| [`WORKFLOW.md`](docs/guides/WORKFLOW.md) | What is the end-to-end phase sequence? |
| [`OPERATING-RULES.md`](docs/guides/OPERATING-RULES.md) | What are the twelve rules I must not break? |
| [`WEB-API-TESTING.md`](docs/guides/WEB-API-TESTING.md) | What do I test on web and API surfaces? |
| [`AUTH-AUTHZ.md`](docs/guides/AUTH-AUTHZ.md) | How do I test authentication and authorization lifecycles? |
| [`BUSINESS-LOGIC.md`](docs/guides/BUSINESS-LOGIC.md) | How do I model and attack a workflow? |
| [`PAYMENT-PREMIUM-TESTING.md`](docs/guides/PAYMENT-PREMIUM-TESTING.md) | How do I assess the paid-content chain? |
| [`ANDROID-TESTING.md`](docs/guides/ANDROID-TESTING.md) | How do I assess an APK/AAB? |
| [`DIGITAL-FILE-VALIDATION.md`](docs/guides/DIGITAL-FILE-VALIDATION.md) | How do I validate a real protected artifact? |
| [`EVIDENCE.md`](docs/guides/EVIDENCE.md) | What counts as evidence, and how is it stored? |
| [`DECISION-MATRIX.md`](docs/guides/DECISION-MATRIX.md) | What status does this situation map to? |
| [`SEVERITY-RATING.md`](docs/guides/SEVERITY-RATING.md) | How severe is this, and what is the evidence ceiling? |
| [`REFERENCE-MAPPINGS.md`](docs/guides/REFERENCE-MAPPINGS.md) | How does this map to OWASP, CWE, MASVS, ASVS, PCI, GDPR? |
| [`REMEDIATION-AND-RETEST.md`](docs/guides/REMEDIATION-AND-RETEST.md) | How do I fix it, and how is the fix verified? |
| [`REPORTING.md`](docs/guides/REPORTING.md) | What must the report contain? |
| [`TOOL-AND-ENVIRONMENT.md`](docs/guides/TOOL-AND-ENVIRONMENT.md) | What can I actually do with the tools I have? |

`DECISION-MATRIX`, `SEVERITY-RATING`, and `REFERENCE-MAPPINGS` form a natural
decision sequence during report writing: classify the situation, rate it, then
map it.

### Layer 4 — Artefacts

The outputs an engagement produces.

| Artefact | Produced at |
|---|---|
| [`templates/ENGAGEMENT-RECORD.md`](templates/ENGAGEMENT-RECORD.md) | Engagement start — scope, authorization, capabilities, substitutions |
| [`templates/COVERAGE-MATRIX.md`](templates/COVERAGE-MATRIX.md) | Throughout — what was tested, what was not, and why |
| [`templates/TEST-LOG.md`](templates/TEST-LOG.md) | Per test — hypothesis, baseline, manipulation, result, status |
| [`templates/FINDING.md`](templates/FINDING.md) | Per confirmed or partially-confirmed finding |
| [`templates/FINAL-REPORT.md`](templates/FINAL-REPORT.md) | Engagement end |
| [`examples/NEW-PROJECT-BOOTSTRAP.md`](examples/NEW-PROJECT-BOOTSTRAP.md) | Engagement start — the bootstrap prompt |

## Precedence

Documents in this framework are not peers. When two appear to conflict, this
order resolves it:

```text
1. Authorization boundaries        — never overridden by any document
2. Non-fabrication rule            — never overridden
3. AGENT.md (Layer 1)              — governs all
4. The active mode (Layer 2)       — governs within its scope
5. Guides (Layer 3)                — reference; cannot override 1–4
6. Templates (Layer 4)             — shape only; no rules
```

The zero-credential layer declares a specific refinement of this, stating that
where the other documents are silent on **coverage control, state management,
differential testing, proof strength, or environmental boundaries**, it governs.

**Authorization always wins.** If any document, mode, or example appears to
permit an action that the authorization does not cover, the authorization is
correct and the document has been misread. This is not a close call, and it is
the single most important rule in the framework.

## How an engagement flows

```text
ENGAGEMENT-RECORD          scope, authorization, capabilities, substitutions
        │
        ▼
   AGENT.md §3             scope intake confirmed before anything active
        │
        ▼
   Mode selected           audit │ research │ digital-asset │ zero-credential
        │
        ▼
   WORKFLOW.md             phases 0-12
        │
        ├─ throughout ──▶ COVERAGE-MATRIX      what was and was not tested
        ├─ per test ────▶ TEST-LOG            hypothesis → result → status
        └─ per finding ─▶ FINDING             status, severity, remediation
        │
        ▼
   DECISION-MATRIX         observed situation → correct status
        │
        ▼
   SEVERITY-RATING         demonstrated impact → severity, within status ceiling
        │
        ▼
   REFERENCE-MAPPINGS      weakness → OWASP / CWE / MASVS / ASVS
        │
        ▼
   REMEDIATION-AND-RETEST  root cause → fix → regression test
        │
        ▼
   FINAL-REPORT            + coverage statement + limitations
        │
        ▼
   AGENT.md §26            final quality gate before delivery
```

## Invariants

Properties that hold across the whole framework. A change that breaks one is a
defect, not a simplification.

1. **Evidence before conclusions.** A hypothesis is not a finding.
2. **Severity is bounded by status.** An unproven weakness is not rated.
3. **No fabrication, ever.** Missing data is reported as missing.
4. **Authorization is absolute.** Discovery never creates permission.
5. **Minimum necessary data.** Prove the boundary, collect nothing extra.
6. **Untested is not safe.** Coverage is reported alongside findings, always.
7. **Tool honesty.** An unavailable tool is documented, never assumed.
8. **The client is the attacker.** A client-side control is not a control.
9. **Stopped technique, not stopped objective.** See
   [`modes/ZERO-CREDENTIAL-ESCALATION-MODE.md`](docs/modes/ZERO-CREDENTIAL-ESCALATION-MODE.md).
10. **Authoritative only at the enforcement point.** A fix anywhere else is
    incomplete.

## Extending the framework

If you add a document, preserve the layering:

- **New mode** — Layer 2. Must extend Layer 1, never relax it, and must declare
  its scope and its relationship to the existing modes.
- **New guide** — Layer 3. Reference material. Cannot introduce rules that
  override Layers 1–2.
- **New template** — Layer 4. Defines structure only. Carries no rules.
- **Change to Layer 1** — Changes the framework's meaning. Update
  [`CHANGELOG.md`](CHANGELOG.md) under `Unreleased` and state the invariant
  affected.

Every new document is registered in [`FILE-INDEX.txt`](FILE-INDEX.txt) and
linked from [`README.md`](README.md) and [`docs/README.md`](docs/README.md).
An unlinked document is not part of the framework.
