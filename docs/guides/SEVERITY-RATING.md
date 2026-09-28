# Severity Rating

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`DECISION-MATRIX.md`](DECISION-MATRIX.md) · [`../AGENT.md`](../../AGENT.md) · [`REPORTING.md`](REPORTING.md)

## Why this document exists

The framework defines a precise [evidence status taxonomy](../../AGENT.md#5-evidence-status-taxonomy)
but status answers only *what the evidence proves*. It does not answer *how much
that matters*.

Without a rating rubric, severity collapses into whichever adjective felt
accurate at the moment of writing, and two testers rate the same behaviour
differently. This document supplies one rubric, applied identically by everyone
using the framework.

The rubric is deliberately conservative. It is built to resist inflation, because
inflation is the failure mode that destroys trust in a report faster than any
missing finding.

## The two rules that matter most

**Rule 1 — Severity is bounded by evidence.**
A finding is never rated above what has been demonstrated. An `UNVERIFIED`
item is not "potentially critical"; it is unverified and is excluded from the
severity scale entirely.

**Rule 2 — Rate the demonstrated effect, not the theoretical ceiling.**
If a manipulated request lets an attacker change a price field on their own
order, the demonstrated effect is *order-price integrity failure on
self-owned orders*. It is not *free access to all products* unless that was
actually shown.

Both rules exist for the same reason: the strongest defensible statement is
always better than the most alarming one.

## The model

Severity is derived from two independent axes. Rate each, then combine.

### Axis 1 — Impact

What does the attacker actually gain, as demonstrated?

| Level | Demonstrated effect |
|---|---|
| **I5 — Systemic** | Compromise of the security boundary across the whole system or tenant: unauthenticated administrative capability, ability to read or modify arbitrary users' protected data at scale, or control of the authorization layer itself. |
| **I4 — Cross-user** | Access to or modification of **another** user's protected records, entitlements, orders, or files. The attacker is a legitimate user crossing a boundary they do not own. |
| **I3 — Protected asset** | Acquisition of a paid, premium, or otherwise protected digital asset without satisfying the required condition. The artifact is real and was actually obtained. |
| **I2 — Integrity** | A security-relevant state, input, or value is manipulated and accepted by the server where it should have been rejected — but no protected asset or other user's data is reached. |
| **I1 — Information** | Sensitive information is exposed that the attacker should not see, without crossing into another user's data or a protected asset. |
| **I0 — Hygiene** | A weakness with no demonstrated security consequence: missing hardening, verbose errors, weak configuration, absent defense-in-depth. |

### Axis 2 — Reach

How much effort does the attacker need, and how repeatable is it?

| Level | Description |
|---|---|
| **R3 — Remote, unauthenticated** | Reachable by an anonymous internet user with no account, no prior state, and no special position. |
| **R2 — Remote, authenticated** | Reachable by any registered user using only in-application capability. No privilege required. |
| **R1 — Elevated** | Requires a specific role, a specific state, or a chained step. |
| **R0 — Constrained** | Requires conditions the attacker does not control, or is demonstrably not reachable in the assessed environment. |

### Combining the axes

|  | R3 Remote/Unauth | R2 Remote/Auth | R1 Elevated | R0 Constrained |
|---|---|---|---|---|
| **I5 Systemic** | Critical | Critical | High | Medium |
| **I4 Cross-user** | Critical | High | High | Medium |
| **I3 Protected asset** | High | High | Medium | Medium |
| **I2 Integrity** | Medium | Medium | Medium | Low |
| **I1 Information** | Medium | Low | Low | Low |
| **I0 Hygiene** | Low | Low | Informational | Informational |

### Level definitions

**Critical** — A security boundary is broken in a way that is remotely reachable
by an unauthenticated attacker and yields systemic or cross-user capability.
The remediation is urgent and the exposure should be disclosed immediately.

**High** — A security boundary is broken with real, demonstrated impact:
cross-user access, acquisition of a protected asset, or systemic control
failure requiring some prerequisite. Remediate on a short timeline.

**Medium** — A genuine security weakness with contained, demonstrated impact,
or a serious weakness whose reach is constrained. Remediate in normal course.

**Low** — Limited demonstrated impact. Remediate when convenient.

**Informational** — No demonstrated security consequence. Record it; do not
present it as a vulnerability and do not let it displace real findings in the
summary.

## Interaction with the status taxonomy

| Status | May carry a severity? | Rule |
|---|---|---|
| `CONFIRMED` | Yes | Rate normally. |
| `PARTIALLY CONFIRMED` | Yes, at reduced impact | Rate the impact that was **demonstrated**. State plainly which part of the chain remains unproven. Do not rate the unproven remainder. |
| `UNVERIFIED` | **No** | Excluded from the severity scale. List it with the exact missing proof and the test that would produce it. |
| `NOT TESTED` | **No** | Excluded. Not-tested is a coverage fact, not a risk rating. |
| `NOT VULNERABLE` | No | Not a finding. |
| `OUT OF SCOPE` | No | Not a finding. |

A partially-confirmed chain is rated at the **lowest unproven link's predecessor**.
Concretely: if payment verification is confirmed broken but entitlement creation
was never observed, the rating reflects the payment-verification weakness. The
entitlement-bypass severity is unearned until entitlement creation is observed.

## Payment, premium and entitlement findings

These are the framework's most commonly mis-rated class. Apply these rules.

**Rate the stage you proved.** The chain is
`price → order → payment → verification → entitlement → premium access → delivery → artifact`.
Rate the highest stage actually demonstrated, and no higher.

| Demonstrated | Rate as | Not |
|---|---|---|
| Client-supplied price accepted | I2 Integrity | Payment bypass |
| Order/payment mismatch accepted | I2 Integrity | Payment bypass |
| Payment state forged or replayed, entitlement not observed | I2 Integrity | Entitlement bypass |
| Entitlement created without successful payment | I3 Protected asset | "Free premium for all products" |
| Premium feature usable without entitlement | I3 Protected asset | — |
| Protected file actually downloaded and hashed | I3 Protected asset, evidenced by the artifact | — |

**Artifact acquisition raises confidence, not severity.**
A downloaded artifact does not become more severe because it was hashed. It
becomes *uncontestable*. Severity still follows demonstrated impact; the hash
is what makes the rating defensible in review.

**Cross-user payment impact outranks self-order manipulation.**
Changing the price on your own cart is I2. Using another user's order,
payment, or entitlement to obtain a paid asset is I4.

## Relationship to CVSS

CVSS is a legitimate and widely recognised scoring system, and the framework
does not replace it. Two notes on using it correctly:

1. **CVSS requires a demonstrated vulnerability.** Scoring an unverified
   hypothesis with CVSS is a category error and this framework does not permit it.
2. **CVSS Base scores describe technical severity, not business impact.** A
   technically severe issue on a low-value asset may be Medium for the
   organisation. Where a business-impact rating is also required, report the
   rubric rating as the primary figure and CVSS as a technical supplement.

State which one you are reporting. Never present a rubric rating and a CVSS
score as if they were the same measurement.

## Anti-inflation rules

These are the specific habits this rubric exists to prevent.

- Do not use *critical* without a demonstrated systemic or cross-user effect.
- Do not use *complete account takeover* or *full compromise* unless literally
  demonstrated.
- Do not rate a finding by the value of what *would* be reachable if the rest
  of the chain held. Rate what was reached.
- Do not rate an informational hygiene item as a vulnerability to make a report
  look thorough.
- Do not let a long list of Low findings imply a higher overall risk than a
  short list of High findings. Count the Highs.
- Do not inflate to compensate for a small number of findings. An honest short
  report is the goal, not a long one.

## Rating worksheet

Complete this before assigning a level. It is deliberately short.

```text
FINDING ID:
Status (from taxonomy):                     
Impact axis demonstrated (I0–I5):            
  Evidence for that level:                   
Reach axis demonstrated (R0–R3):             
  Evidence for that reach:                   
Combined level:                              
Highest stage actually demonstrated in the
  payment/entitlement chain (if applicable): 
Any unproven remainder of the impact chain:  
Ceiling check — does the level exceed what the
  status allows? (must be NO):               
Rationale in one sentence:                     
```

## Worked examples

**A. Unauthenticated user reads any user's invoice by ID**

```text
Status   : CONFIRMED
Impact   : I4 Cross-user  — another user's protected record returned
Reach    : R3 Remote, unauthenticated — no session required
Combined : CRITICAL
Note     : "IDOR" is a weakness class, not a severity. State the data crossed.
```

**B. Any logged-in user edits another user's profile**

```text
Status   : CONFIRMED
Impact   : I4 Cross-user — modification of another user's protected object
Reach    : R2 Remote, authenticated — any registered account
Combined : HIGH
```

**C. Debug stack trace discloses internal class names and file paths**

```text
Status   : CONFIRMED
Impact   : I0 Hygiene — no protected data or asset reached
Reach    : R3 Remote, unauthenticated
Combined : LOW
Note     : report as Low. Do not promote to Medium because it "reveals
           structure" — nothing security-relevant was obtained.
```

**D. Price field accepted client-side, payment completed at the manipulated amount**

```text
Status   : CONFIRMED
Impact   : I2 Integrity — server accepted a client-controlled value and a real
           payment proceeded at the wrong amount
Reach    : R2 Remote, authenticated
Combined : MEDIUM
Not      : "Payment bypass" — no payment requirement was skipped; the payment
           occurred at an attacker-chosen amount. That distinction matters and
           is the strongest defensible statement.
```

**E. Premium entitlement created without payment, but the protected file was never downloaded**

```text
Status   : PARTIALLY CONFIRMED
Impact   : I3 Protected asset — entitlement itself is the protected asset
Reach    : R2 Remote, authenticated
Combined : MEDIUM  (not High — delivery was never demonstrated)
Unproven : artifact delivery
Note     : if delivery is later demonstrated, the impact is evidenced by the
           artifact and the rating is revisited on evidence, not on assumption.
```

**F. Payment verification logic looks bypassable in source; not executed**

```text
Status   : UNVERIFIED
Severity : not rated
Output   : listed under Unverified Hypotheses with the exact runtime test that
           would confirm or refute it
```

## Reporting the distribution

Summarise with counts by level and status, and state them plainly:

```text
Critical: 0   High: 2   Medium: 3   Low: 5   Informational: 4
Confirmed: 9   Partially confirmed: 2   Unverified: 3   Not tested: 11
```

Always show `Not tested` alongside the findings. A report that lists only
confirmed issues without coverage figures is not a complete picture, and
`AGENT.md`'s [final quality gate](../../AGENT.md#26-final-quality-gate) requires
the coverage side to be stated explicitly.
