# Emergency authorization record — template

**Project:** BLACKHEART Security Framework · **Author:** Roshan
**Companion to:** [`../AUTHORIZATION-AGREEMENT.md`](../../AUTHORIZATION-AGREEMENT.md)
— this is the bounded variant, for use only when the ordinary approval process
cannot run fast enough and the activity is **already authorized**
**Read first:** [`EMERGENCY-GOVERNANCE.md`](EMERGENCY-GOVERNANCE.md)

---

## Before filling this in

This template does not grant authorization, and filling it in does not create any.
It **narrows and time-limits** an authorization that already exists, and records
why the normal review was accelerated.

**It is not for:** making a new activity authorized, speeding up an activity that
has no authorization, or covering a target that is not already in one. If the
target is not already authorized, the answer is no — and the correct action is in
[`EMERGENCY-GOVERNANCE.md`](EMERGENCY-GOVERNANCE.md) §1.

**It expires.** An emergency window with no end time is not this instrument.

---

## Section 1 — Incident

| Field | Value |
|---|---|
| Incident reference | *(required — a ticket or incident record id)* |
| Incident summary | *(one sentence)* |
| Date and time of first awareness | *(UTC)* |
| Why the normal review cannot run in time | *(required; if this cannot be written, there is no emergency)* |
| Harm that delaying would cause | |

## Section 2 — Existing authorization this relies on

| Field | Value |
|---|---|
| Underlying authorization reference | *(required — the record this shortens the review of)* |
| Target(s) named in it | |
| Does the underlying authorization cover this target? | Yes / **No — stop, this template does not apply** |
| Does it still cover this target's current environment? | Yes / No |

## Section 3 — Operator and authorizer

| Field | Value |
|---|---|
| Operator | |
| Organization (if applicable) | |
| Contact during the window | |
| Authorizer | *(a person entitled to speak for the target, or delegated by them)* |
| Authorizer's capacity | |
| Authorizer's contact | |
| **Operator and authorizer are the same person?** | Yes / No — if **yes**, see §7 |

## Section 4 — The narrow activity

| Field | Value |
|---|---|
| What is to be collected or observed | *(the specific thing)* |
| Why this is the minimum necessary | *(required)* |
| Methods permitted | *(default: `GET` and `HEAD`; anything else needs explicit justification)* |
| Hosts and paths | |
| Explicitly excluded | |
| Estimated requests | |
| Hard ceiling | *(cannot exceed the underlying authorization's budget)* |
| Interval between requests | |

> If the work is available through `emergency collect` — the target URL,
> `robots.txt` and `security.txt`, read-only, budget-capped at
> `min(scope.max_requests, 20)` — **use that**, and say so here. It is bounded by
> code, and the bounds are the point.

## Section 5 — The window

| Field | Value |
|---|---|
| Emergency window starts | *(date and time, UTC)* |
| **Emergency window expires** | *(required; default 24 hours; never later than the underlying authorization)* |
| Extension | A new decision, by the authorizer, recorded separately — not an edit to this field |

## Section 6 — Evidence

| Field | Value |
|---|---|
| Evidence to be preserved | |
| Where it will be stored | |
| Who may access it | |
| Hash and verification | `evidence manifest --verify`, this window's bundle |
| Retention, and deletion date | |

## Section 7 — Independent authorizer's declaration

Filled in by the authorizer. **If the operator is also the authorizer, this
instrument does not apply** — an emergency does not make one person two, and the
two-person rule exists precisely for the situation where one person is under
pressure.

> I confirm that the target is already covered by the authorization referenced in
> Section 2, that the activity in Section 4 is inside it, and that the window in
> Section 5 fits within it. I confirm the activity is limited to the minimum
> necessary. I understand this record expires at the time in Section 5 and that
> continuing afterwards requires a new decision.

| | |
|---|---|
| Name | |
| Title / capacity | |
| Signature or approval reference | |
| Date and time (UTC) | |
| Recorded in | *(system of record)* |

## Section 8 — Operator acknowledgement

> I will perform only the activity in Section 4, only within the window in
> Section 5, and only against the hosts named there. I will stop immediately if
> the authorization becomes unclear, if the target shows strain, if I encounter
> data the engagement did not contemplate, or if I am asked to stop. I will
> preserve evidence before anything else. I will record what I did, and I will not
> omit a refusal, a stop or an unexpected exposure from the record.

| | |
|---|---|
| Name | |
| Signature or acknowledgement reference | |
| Date and time (UTC) | |

---

## Section 9 — Closure

| Field | Value |
|---|---|
| Closed at | *(UTC)* |
| Activity actually performed | |
| Result summary | |
| Evidence identifier | |
| **Stop reason**, if it stopped early | |
| Any deviation, with approval or incident reference | |
| Temporary access removed | Yes / No — *and by whom* |
| Post-incident review scheduled for | |
| Reviewed by | *(someone other than the operator)* |

---

## What this template cannot do

| It cannot | Because |
|---|---|
| Authorize anything | Only the target's owner can, and only before the work |
| Apply to an unauthorized target | §1 of this document; the answer in that case is no |
| Cover an access control being defeated | Never, for any urgency |
| Cover another person's data | Never, for any urgency |
| Extend itself | A new window is a new decision, recorded separately |
| Enforce its own limits | There is no emergency enforcement in the software. The tool's bounds are in `emergency collect`; everything else here is discipline and review |
