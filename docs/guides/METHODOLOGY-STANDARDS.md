# Methodology Standards Mapping

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`WORKFLOW.md`](WORKFLOW.md) · [`ADVERSARY-EMULATION.md`](ADVERSARY-EMULATION.md) · [`REFERENCE-MAPPINGS.md`](REFERENCE-MAPPINGS.md) · [`SEVERITY-RATING.md`](SEVERITY-RATING.md)

## Purpose

Clients, procurement teams, and auditors frequently ask which recognised
methodology an engagement follows. This document states where BLACKHEART sits
relative to the standards most often named, and — equally important — where it
differs.

Claiming alignment with a standard the engagement does not actually meet is
both inaccurate and a poor commercial outcome. Where the mapping is partial,
it is stated as partial.

> **Verify before citing.** Standards are revised. Confirm current versions and
> requirements against the publishing body, and state the version used.

---

## 1. PTES — Penetration Testing Execution Standard

The most common framework named in engagement contracts. BLACKHEART's
[`WORKFLOW.md`](WORKFLOW.md) maps onto its seven phases.

| PTES phase | BLACKHEART equivalent | Depth note |
|---|---|---|
| **Pre-engagement interactions** | [`../templates/ENGAGEMENT-RECORD.md`](../../templates/ENGAGEMENT-RECORD.md) · [`SCOPE.md`](SCOPE.md) | Stronger than baseline: adds a capability inventory and a deviations log |
| **Intelligence gathering** | [`../modes/ZERO-CREDENTIAL-ESCALATION-MODE.md`](../modes/ZERO-CREDENTIAL-ESCALATION-MODE.md) · [`../AGENT.md`](../../AGENT.md) §4 | Anonymous-surface focused; passive OSINT collection is client-supplied or separately scoped |
| **Threat modelling** | [`BUSINESS-LOGIC.md`](BUSINESS-LOGIC.md) · [`ATTACK-PATHS.md`](ATTACK-PATHS.md) | BLACKHEART treats threat modelling as continuous rather than a discrete phase |
| **Vulnerability analysis** | [`WEB-API-TESTING.md`](WEB-API-TESTING.md) · [`AUTH-AUTHZ.md`](AUTH-AUTHZ.md) · [`ANDROID-TESTING.md`](ANDROID-TESTING.md) | Manual-first; no automated scanning phase in the methodology |
| **Exploitation** | [`../AGENT.md`](../../AGENT.md) §6, §21 | Explicit validation standard — a stricter requirement than baseline |
| **Post-exploitation** | [`ATTACK-PATHS.md`](ATTACK-PATHS.md) · [`../modes/RED-HEART-ADVERSARY-EMULATION.md`](../modes/RED-HEART-ADVERSARY-EMULATION.md) | Bounded by authorization; persistence assessed rather than established |
| **Reporting** | [`REPORTING.md`](REPORTING.md) · [`SEVERITY-RATING.md`](SEVERITY-RATING.md) · [`../templates/FINAL-REPORT.md`](../../templates/FINAL-REPORT.md) | Adds a required coverage statement and negative results, which baseline does not mandate |

**Claim:** "Follows the PTES seven-phase engagement lifecycle, with additional
scope-record, coverage-accounting, and evidence-discipline requirements."

---

## 2. NIST SP 800-115

A planning-and-execution standard widely used in regulated environments.

| SP 800-115 element | BLACKHEART equivalent |
|---|---|
| Planning | [`../templates/ENGAGEMENT-RECORD.md`](../../templates/ENGAGEMENT-RECORD.md) |
| Discovery | [`../modes/ZERO-CREDENTIAL-ESCALATION-MODE.md`](../modes/ZERO-CREDENTIAL-ESCALATION-MODE.md) |
| Attack | [`../modes/SECURITY-AUDIT.md`](../modes/SECURITY-AUDIT.md) |
| Reporting | [`REPORTING.md`](REPORTING.md) |

**Honest limitation.** SP 800-115 carries formal evidence-handling, personnel,
and quality-assurance requirements that a documentation framework does not
satisfy on its own. Those are delivery-provider obligations, not methodology
properties. State this plainly rather than implying full conformance.

**Claim:** "Methodology aligns to the SP 800-115 planning / discovery /
attack / reporting structure. Formal evidence-handling and QA requirements
remain with the delivery provider."

---

## 3. OSSTMM

An evidence-based measurement methodology organised across five channels:
human, physical, wireless, telecommunications, and data networks. It
introduces a Risk Assessment Value for relating exposure, controls, and
limitations in a single metric.

| Channel | BLACKHEART coverage |
|---|---|
| Data networks | Strong — the primary domain |
| Human | Partial — process and authorized social-engineering assessment in [`../modes/RED-HEART-ADVERSARY-EMULATION.md`](../modes/RED-HEART-ADVERSARY-EMULATION.md) §9 |
| Physical | Not covered |
| Wireless | Not covered |
| Telecommunications | Not covered |

**Claim:** "Partial coverage. Data-network channel is in scope; human channel
partially; physical, wireless, and telecommunications are outside this
framework's scope and require a separate engagement."

The RAV metric is **not** implemented and should not be claimed.

---

## 4. MITRE Engage and ATT&CK

| Engage element | BLACKHEART equivalent |
|---|---|
| Operational objective | [`../modes/RED-HEART-ADVERSARY-EMULATION.md`](../modes/RED-HEART-ADVERSARY-EMULATION.md) §3 |
| Prepare / Operate / Understand | [`ADVERSARY-EMULATION.md`](ADVERSARY-EMULATION.md) |
| Engagement goals (Expose / Affect / Elicit) | [`ADVERSARY-EMULATION.md`](ADVERSARY-EMULATION.md) |
| Approaches (Plan / Collect / Detect / Prevent / Direct) | [`ADVERSARY-EMULATION.md`](ADVERSARY-EMULATION.md) |
| ATT&CK technique mapping | Available in most engagement reporting as a behavioural reference |

**Claim:** "The adversary-emulation mode is structured after the MITRE Engage
model. The Engage matrix and ATT&CK Navigator are not required and are not
mandated; technique mapping is a reporting convenience, not a methodology
requirement."

---

## 5. OWASP WSTG and ASVS

| Standard | Relationship |
|---|---|
| **OWASP Web Security Testing Guide** | Complementary. WSTG is a content catalogue; BLACKHEART is a process discipline. Domain guides align to WSTG categories |
| **OWASP ASVS** | Verification requirements; see [`REFERENCE-MAPPINGS.md`](REFERENCE-MAPPINGS.md) §4 |
| **OWASP API Security Top 10** | Risk classification; see [`REFERENCE-MAPPINGS.md`](REFERENCE-MAPPINGS.md) §2 |
| **OWASP Top 10 for LLM Applications** | Risk classification for AI systems; see [`AGENTIC-AI-SECURITY.md`](AGENTIC-AI-SECURITY.md) §13 |
| **MASVS** | Mobile verification; see [`REFERENCE-MAPPINGS.md`](REFERENCE-MAPPINGS.md) §3 |

**Claim:** "Uses OWASP WSTG categories as a content reference and OWASP risk
taxonomies for classification. Does not claim WSTG or ASVS certification."

---

## 6. Severity standards

| Standard | Role in BLACKHEART |
|---|---|
| **CVSS v3.1 / v4.0** | Optional technical supplement; see [`SEVERITY-RATING.md`](SEVERITY-RATING.md) |
| **BLACKHEART rubric** | Primary rating, bounded by evidence status |

The two measure different things. The rubric is primary because it is bound to
what was actually demonstrated; CVSS is reported alongside where the recipient
requires it, and never for an unverified hypothesis.

---

## 7. Compliance frameworks

| Framework | Relationship |
|---|---|
| **PCI DSS v4.0** | Requirement references, not a compliance assessment; see [`REFERENCE-MAPPINGS.md`](REFERENCE-MAPPINGS.md) §5 |
| **GDPR** | Data-minimisation alignment; see [`REFERENCE-MAPPINGS.md`](REFERENCE-MAPPINGS.md) §6 |
| **ISO 27001** | Control-domain alignment only |

**Hard limitation.** A black-box technical assessment does not determine
compliance status. Nothing in this framework constitutes a QSA assessment, a
certification, or legal advice. State findings and observed data; the
compliance owner determines obligations.

---

## 8. Summary claim sheet

For use in engagement documentation, these statements are accurate:

```text
✓ Follows the PTES seven-phase engagement lifecycle
✓ Adds a mandatory scope and capability record
✓ Adds a mandatory coverage statement and negative-results reporting
✓ Adds an evidence-status taxonomy bounding every claim
✓ Adds a severity rubric bounded by evidence status
✓ Structures adversary emulation on the MITRE Engage model
✓ Uses OWASP taxonomies for classification
✓ Supports optional CVSS reporting alongside its own rubric

✗ Does not claim NIST SP 800-115 formal conformance
✗ Does not claim OWASP WSTG or ASVS certification
✗ Does not implement OSSTMM RAV
✗ Does not cover physical, wireless, or telecommunications security
✗ Does not perform compliance or certification assessment
✗ Does not provide legal advice
```

Use the ones that apply. **Delete the rest.** A methodology that claims
everything is trusted for nothing.
