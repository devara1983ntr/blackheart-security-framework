# Authorization Agreement — template

**Project:** BLACKHEART Security Framework · **Author:** Roshan
**Authorization schema version:** 1.0.0 · **Last updated:** 2026-09-30

---

## What this document is, and what it is not

This is a **template** for recording the authorization an operator has been
given. It is designed to be filled in by the person or organisation granting the
authorization, and kept as the engagement's record of scope.

It is not:

- proof of authorization in itself;
- a contract, unless the parties choose to make it one and their law permits;
- a substitute for a signed engagement agreement, a bug-bounty policy, a
  statement of work, or whatever instrument your situation requires.

**Completing this template does not create authority you do not already hold.**
It records authority you have been given. Whether the person filling it in is
entitled to grant that authority is a question this document cannot answer — and
one the operator must satisfy themselves about before testing anything.

The workbench's scope file is the machine-readable form of the fields below; it is
described in [`docs/workbench/COMMANDS.md`](docs/workbench/COMMANDS.md). One
assertion of scope, in two forms.

---

## Section 1 — Operator

| Field | Value |
|---|---|
| Operator name | |
| Organization (if applicable) | |
| Role in the engagement | |
| Contact address | |
| Emergency contact (reachable during the window) | |

## Section 2 — Authorizing party

| Field | Value |
|---|---|
| Name | |
| Organization (if applicable) | |
| Capacity in which they authorize testing | |
| Relationship to the target (owner, operator, controller, delegated) | |
| If delegated, from whom, and evidence of that delegation | |
| Contact address | |

> **Check before testing:** is this party entitled to authorize testing of this
> target? If the target is operated by a third party — a hosting provider, a
> managed service, a payment processor, a cloud tenant — their authorization may
> also be required. Record the answer rather than assuming it.

## Section 3 — Targets

| Field | Value |
|---|---|
| Target name / system | |
| Primary URL(s) | |
| Hostnames in scope | |
| IP ranges in scope (if applicable) | |
| Environment (production / staging / lab) | |
| Allowed paths or path prefixes (blank means "as recorded in the scope file") | |
| **Excluded** paths | |
| **Excluded** hosts or subdomains | |
| Third-party services reachable from the target — are they in scope? | |

## Section 4 — Techniques

| Field | Value |
|---|---|
| Allowed HTTP methods | |
| Prohibited HTTP methods | |
| State-changing requests permitted? (yes / no / with confirmation) | |
| Discovery crawling permitted? Page and depth limits | |
| Automated mutation or fuzzing permitted? Mutation and request limits | |
| Authentication testing permitted? With whose credentials? | |
| Load or rate testing permitted? At what ceiling? | |
| Social engineering permitted? | |
| Physical testing permitted? | |
| Anything else explicitly excluded | |

## Section 5 — Window and budget

| Field | Value |
|---|---|
| Authorization starts (date and time, with timezone) | |
| Authorization ends (date and time, with timezone) | |
| Days or hours when testing is not permitted | |
| Maximum requests over the whole engagement | |
| Maximum request rate (requests per second or per minute) | |
| Maximum concurrent connections | |
| Response-size ceiling the target operator expects | |

> The workbench enforces a request budget, a minimum interval between requests, a
> concurrency of one by default, and an authorization window. The values here are
> what the scope file should carry.

## Section 6 — Data handling

| Field | Value |
|---|---|
| Personal data expected to be encountered | |
| Handling requirement (minimise, redact, encrypt at rest, delete by date) | |
| Retention period for evidence | |
| Where evidence may be stored (jurisdiction, system) | |
| Who may see the evidence | |
| Disclosure rules (responsible disclosure window, agreed channels) | |
| Prohibited collection (for example: no user content beyond a proof of access) | |

## Section 7 — Stop conditions and escalation

| Field | Value |
|---|---|
| Contact to reach immediately if the target is affected | |
| Conditions that require an immediate stop | |
| Conditions that require prior notification | |
| Incident escalation path | |
| Emergency out-of-hours contact | |

## Section 8 — Declaration

Filled in by the authorizing party:

> I confirm that I am entitled to authorize security testing of the targets named
> in Section 3, within the techniques and window recorded above, by the operator
> named in Section 1. I understand that the operator will record every request
> made under this authorization, and that testing will stop if the scope of this
> agreement comes into question.

| | |
|---|---|
| Name | |
| Title | |
| Signature or approval reference | |
| Date | |
| Recorded in (system of record, ticket, contract reference) | |

## Section 9 — Operator acknowledgement

Filled in by the operator:

> I will test only the targets named in Section 3, only within the techniques and
> restrictions recorded above, and only inside the window in Section 5. I will
> stop if the authorization is unclear, if the target shows signs of strain, or if
> I am asked to stop. I will record what I did, redact credentials from my
> records, and handle the data I collect as Section 6 requires.

| | |
|---|---|
| Name | |
| Signature or acknowledgement reference | |
| Date | |

---

## Notes on using this template

- **Two records, one scope.** The values in Sections 3, 4 and 5 belong in the
  workbench scope file as well. If the two ever disagree, stop and reconcile them
  before continuing; the tool will enforce the file, not this document.
- **Written authorization, not verbal.** A verbal "go ahead" is hard to rely on
  and impossible to produce later. Ask for it in writing, and record where it is.
- **Scope narrows easily and widens slowly.** If testing reveals that something
  outside the recorded scope needs attention, that is a conversation to have
  before the request, not after it.
- **This is not legal advice.** Whether this template is adequate for your
  situation, and what additional agreements your law or your contract requires, is
  a question for your own advisers.
