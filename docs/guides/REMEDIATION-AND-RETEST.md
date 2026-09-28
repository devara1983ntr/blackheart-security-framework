# Remediation and Retest

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`../AGENT.md`](../../AGENT.md) · [`REPORTING.md`](REPORTING.md) · [`DECISION-MATRIX.md`](DECISION-MATRIX.md) · [`../templates/FINDING.md`](../../templates/FINDING.md)

## Why this document exists

A finding without a remediation is an accusation. A finding without a *verifiable*
remediation is a complaint.

`AGENT.md` requires a `Remediation` and a `Regression Test` field on every
finding, and [`../templates/FINAL-REPORT.md`](../../templates/FINAL-REPORT.md)
carries dedicated remediation and regression-testing sections. This document
defines what belongs in them, so that guidance is specific enough to act on and
specific enough to close.

## The rule that prevents most bad fixes

**Fix the enforcement point, not the symptom.**

The framework's [Operating Rule 7](OPERATING-RULES.md) already states that
server-side enforcement is what matters. In practice this is where remediation
guidance most often goes wrong: the symptom is a request that was accepted, and
the proposed fix validates that specific request — while the enforcement gap
that allowed it stays open.

```text
Symptom  : POST /checkout accepted a client-supplied price
Bad fix  : "validate the price field format and range on submit"
Real fix : derive the price server-side from the product identifier; never
          accept a price, currency, or discount as authoritative from the client
```

The test of a good fix: **does it close the class of attack, or only the
instance?** Recommend the former and say so explicitly.

## Root cause before recommendation

Do not recommend a fix before identifying where the decision was actually made.
Trace the request to the point where the security-relevant value was trusted.

```text
Client sends price = 0
  → controller accepts the field
  → service passes it to the order model
  → persistence stores it
  → payment provider is called with that amount
  → entitlement is granted on successful payment
```

The root cause is the *first* point where an untrusted value was treated as
authoritative. Fixing downstream of that leaves the value forgeable.

State the enforcement point in the finding. It is the most useful single
sentence in the remediation section:

```text
Enforcement point: none — the price is accepted from the client and passed
through without server-side derivation.
```

## Fix patterns by enforcement layer

### UI / client layer

**Never the fix.** Removing a button, hiding a field, or adding a client-side
check does not change server behaviour. A client-side control is acceptable only
as usability guidance alongside a real server-side control, never instead of one.

If a client-only control was the finding, the remediation is the missing
server-side check — and the finding should have been `UNVERIFIED` until the
server response was observed. See [`DECISION-MATRIX.md`](DECISION-MATRIX.md).

### API / gateway layer

A gateway or API layer check is a reasonable control when the business logic
correctly depends on it, but gateway rules drift from application behaviour and
are bypassed by any other entry path (mobile app, internal service, admin tool).

If the fix is a gateway rule, ask what protects the service when it is called
directly. A gateway-only fix is defence in depth at best, and a single control
point only while every caller passes through it.

### Service / business logic layer

This is usually the correct layer. Authorization decisions, state transitions,
and entitlement logic belong in the service that owns the resource.

```text
Good  : the order service derives price from its own product record
Bad   : the controller sanitises price before passing it to the service
Good  : the download handler checks entitlement server-side at request time
Bad   : the client requests a short-lived URL only after a client-side check
```

### Data layer

A database-level constraint or row-level policy is a strong control and is
frequently the most durable, because it holds regardless of which service writes
the row. It is also easy to misconfigure into something that appears to work
while applying to the wrong operation.

When recommending a data-layer fix, state the policy that must hold — not just
the mechanism. "Enforce via RLS" is incomplete; "enforce via a policy such
that a user can select only rows where `user_id = auth.uid()`" is actionable.

## Fix patterns for the payment and entitlement chain

Because this is the framework's most specialised area, the chain-specific
failure modes are given explicitly.

| Failure at stage | Root cause | Recommended fix |
|---|---|---|
| Price accepted from client | Client is treated as authoritative for a commercial value | Derive price, currency and discount server-side from the product record; reject any client-supplied override |
| Order/payment mismatch | Payment is linked to an order by a client-supplied identifier | Bind payment to the order server-side; verify the binding before capture |
| Payment state forged | Status is set from a client or an unverified local flag | Derive state from the payment provider's verified result; never accept a client-declared status |
| Webhook replayed or forged | Callback is not authenticated, or is not idempotent | Verify the provider signature over the raw payload; reject stale timestamps; make state transitions idempotent |
| Entitlement created early | Entitlement is granted on order creation rather than verified payment | Create entitlement only on verified provider confirmation |
| Entitlement not bound to the payer | Entitlement is keyed to a client-supplied user id | Bind entitlement to the authenticated identity that completed the payment |
| Cross-product entitlement reuse | Entitlement is checked by existence rather than by product scope | Scope every entitlement check to the specific product and order |
| Download independent of entitlement | A signed or permanent URL is issued once and never revalidated | Authorise every download request against current entitlement; issue short-lived, single-purpose URLs |
| Signed URL long-lived or reusable | TTL and single-use are not enforced | Shorten expiry, bind the signature to the object and the identity, and invalidate on entitlement change |

**Two patterns that recur and are worth naming explicitly in a report:**

*Fixing the link but not the check.* The order is now bound correctly, but the
download handler still trusts possession of a URL. The next finding is the same
class one layer down.

*Fixing the check but not the lifecycle.* Entitlement is now verified at
download, but never revoked when a subscription is cancelled or a refund is
issued. The stale-state variant is a distinct finding and needs its own fix.

## Anti-patterns in remediation advice

Do not recommend these. They consume engineering time and leave the boundary
open.

| Anti-pattern | Why it fails |
|---|---|
| "Implement input validation" with no rule stated | Cannot be tested, so it cannot be closed |
| "Use a library" | Says nothing about the actual defect |
| "Add rate limiting" as a fix for an authorization failure | Does not restore the boundary |
| "Sanitize the input" for a business-logic defect | The input is well-formed; the logic is wrong |
| "Ensure the server validates requests" | Restates the finding instead of fixing it |
| "We are planning to fix this next quarter" | Not a remediation; a schedule note |
| "Add client-side validation" | Changes no server behaviour |
| "This is by design" | Design may be intentional and still insecure; record the business decision and the residual risk separately |

## Writing a regression test

A regression test is the proof the fix holds. It must be executable by someone
who was not present during the assessment.

```text
Regression test ID:
Finding it closes:
Security property being enforced:
Preconditions (accounts, roles, state, data):
Steps (numbered, exact):
Expected result after the fix:
Observed result if the test fails:
Pass criteria (binary, unambiguous):
```

Rules:

1. **Binary.** It passes or it fails. "Should not be vulnerable" is not a
   criterion.
2. **Reuses the original reproduction.** The retest runs the attack that
   succeeded. If it cannot be written from the reproduction steps in the
   finding, the reproduction was not precise enough — fix the finding first.
3. **Targets the enforcement point.** A fix at the service layer is not
   verified by a UI test.
4. **Covers the boundary, not the payload.** One representative case per
   boundary is normally sufficient. Twenty variations of the same request prove
   nothing additional and are discouraged by
   [`AGENT.md`](../../AGENT.md#7-no-artificial-stopping).

**Example — client-supplied price**

```text
Preconditions : authenticated buyer, any product with a known server price
Steps         :
  1. Add the product to the cart through the normal flow.
  2. Capture the checkout request.
  3. Set the price field to 1 in the captured request.
  4. Resubmit.
Expected      : the request is rejected, or the order is created at the
                server-side price and the response shows that price
Pass criteria : the order total never equals the client-supplied value
```

Note the second acceptable outcome. A fix that ignores the field and derives
the price from the product record passes this test even though the request is
not "rejected". Requiring rejection would reject a correct fix.

## Retest protocol

```text
1. Confirm the fix deployed
   Identify the build, version, or commit under test. Do not retest an
   environment you cannot identify.

2. Confirm the scope matches
   Re-read the original finding. Note anything that has legitimately changed
   since the original assessment.

3. Re-run the regression test
   The original reproduction, unchanged, against the fixed build.

4. Re-run the adjacent boundary tests
   A fix at one enforcement point can shift behaviour at another. Test the
   same boundary through at least one alternative path — the mobile client, a
   second endpoint, a different identifier form.

5. Verify the control holds, do not merely observe the request fail
   Confirm the rejection happens server-side. A request that fails because the
   endpoint changed is not a fix.

6. Check for regression
   Confirm the fix did not break legitimate use. An authorization check that
   blocks all access has not fixed the boundary, it has closed the feature.
```

Step 4 is the one that is most often skipped and most often finds the next
finding.

## Retest outcomes

Use one of these. There is no third option, and an unresolved retest is not a
pass.

| Outcome | Meaning | What the report says |
|---|---|---|
| **Verified fixed** | Regression test passes and the control holds at the enforcement point | Closed, with the retest date and build referenced |
| **Partially fixed** | The original reproduction fails but an adjacent path still succeeds | Remains open. Record the surviving path as a new observation with its own evidence. |
| **Not fixed** | Regression test fails | Remains open at original severity. Re-running the retest does not lower severity. |
| **Cannot verify** | Environment, access, or tools prevent testing | Remains open, explicitly unverified. State the blocking capability. |
| **Regressed** | New behaviour introduced by the fix affects a different boundary | New finding. Do not fold it into the original. |

Two rules that matter:

- **A fix does not lower severity.** Severity is a property of the weakness. A
  patched finding is closed, not downgraded to Low. Downgrading on the basis of
  remediation is a reporting error.
- **An unverified fix is not a closed finding.** If the retest could not be
  performed, the honest status is `Cannot verify`, and the finding stays on the
  open list.

## Reporting the remediation section

Structure it so a team can work through it without re-reading the findings.

```text
| Finding | Severity | Enforcement point | Fix summary | Regression test | Owner | Status |
```

Follow with, per finding:

- **Root cause** — the point where an untrusted value was trusted.
- **Recommended fix** — at the enforcement point, closing the class.
- **Alternative if the primary fix is rejected** — so a team that cannot
  implement the preferred fix still knows what a real fix requires.
- **Regression test** — the runnable test above.
- **Verification expectation** — what the retest must show to close it.

State clearly when a fix is **partially** in place, when business constraints
make full remediation conditional, or when the residual risk is accepted. A
documented accepted risk is a legitimate outcome; an undocumented one is a
finding that will return.
