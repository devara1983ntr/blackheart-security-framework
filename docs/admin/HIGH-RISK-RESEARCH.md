# High-risk authorized research

**For:** administrators deciding what needs elevated review, and operators
carrying it out
**Governing principle:** the higher the potential to affect people, data or
availability, the more review before the first request — and the more stopping
rules during it
**Enforcement claim:** §5's dual authorization is a **procedural** control. The
implementation does not enforce it, and this document does not claim it does.

---

## 1. Why classify at all

Most authorized assessment work is low-consequence: a response header, a TLS
configuration, a published document. Some of it is not. A single misjudged request
against an authentication boundary, a payment flow or a production database can
affect real users during the window between "sent" and "undone" — and no evidence
record reverses it.

Classification exists so that the small set of genuinely consequential activities
gets a second person's attention **before** it starts, rather than a review
afterwards.

## 2. What makes an activity high-risk

An activity is high-risk if it touches **any** of these. The list is
deliberately broad: overlapping triggers all apply, and the strictest gate wins.

| # | Trigger | Why it is high-risk |
|---|---|---|
| 1 | **Authentication boundary** | Testing login paths risks lockouts, account state changes, and MFA fatigue for real users |
| 2 | **Authorization boundary** | The error is invisible: an unauthorized success looks like a normal response |
| 3 | **Sensitive data** | Data once read cannot be unread, and it is now in your evidence files |
| 4 | **Destructive methods** | The change may not be reversible, or may replicate |
| 5 | **State-changing requests** | `POST`, `PUT`, `PATCH`, `DELETE` alter the target's world |
| 6 | **Account operations** | Registration, password reset, email change, deletion — these act on people |
| 7 | **Payment-related functionality** | Financial consequences, regulatory exposure, and a high chance of a third party's involvement |
| 8 | **Privileged APIs** | Administrative endpoints multiply impact per request |
| 9 | **Administrative interfaces** | Same, and they often log nothing useful if they fail |
| 10 | **Private resources** | Access controls exist because someone decided who may read the thing |
| 11 | **Regulated or sensitive information** | Health, financial, biometric, children's data — additional law applies, fast |
| 12 | **Production systems** | Real users, real availability, real consequences |

**One exception worth stating plainly:** running the same check against your own
local lab is not high-risk, even if the check itself targets an authentication
boundary. §6 covers where the work should happen.

## 3. What high-risk work requires

Every high-risk activity carries all ten. A missing item is a stop, not a caveat.

| Required | What it means in practice |
|---|---|
| **Explicit authorization** | Written, naming this activity class — not implied by a general engagement |
| **Defined scope** | Hosts, paths, methods, exclusions, in a scope file the workbench accepts |
| **Defined time window** | Start and expiry, both in the record. The tool enforces expiry; honour it |
| **Defined targets** | Named systems, not "the application" |
| **Defined methods** | The specific requests permitted, not "whatever is needed" |
| **Request and resource limits** | A budget from the authorization, not from the tool's defaults |
| **Emergency contact** | Reachable **during** the window, able to stop you |
| **Evidence requirements** | What must be recorded, and what must never be collected |
| **Stop conditions** | The list in [`EMERGENCY-GOVERNANCE.md`](EMERGENCY-GOVERNANCE.md) §5, plus any specific to this engagement |
| **Post-test review** | A named reviewer, and the checklist in [`ADMIN-REVIEW-CHECKLIST.md`](ADMIN-REVIEW-CHECKLIST.md) |

## 4. The reference environment

For any high-risk activity where a laboratory reproduction is possible, **do that
first**. A finding that was reproduced in a lab can be reported to the owner
without a single request against production, which is better for everyone
involved — including the reporter, whose evidence is now reproducible by the
owner.

```text
Prefer, in order:
  1  A local lab you own
  2  A dedicated test environment provided for this engagement
  3  An intentionally vulnerable fixture built for the purpose
  4  An authorized staging system
  5  An authorized test account against the real system
  ─  Production, with authorization naming this specific activity
```

The workbench's own tests follow this principle: they run against a **loopback
fixture server** and nothing else, and the CI gate restricts the socket layer to
loopback for the whole suite. That is the pattern to copy.

## 5. Dual authorization (two-person rule)

For high-risk work, one person deciding is not enough — not because operators are
untrustworthy, but because a single person under time pressure on a consequential
task is exactly the situation where a scope error goes unnoticed.

### The model

```text
PRIMARY OPERATOR            performs the work
      +
INDEPENDENT AUTHORIZER      agrees it should happen, and is not the operator
```

**Administrative status alone is not sufficient**, on either side. Being the
repository administrator does not make someone an authorizer for a target they do
not own or represent. The independent authorizer must be a person entitled to
speak for the target, or a person the target's owner has delegated that to.

### The record

| Field | Notes |
|---|---|
| Operator | Who will perform the work |
| Authorizer | Who approved it, and in what capacity |
| Target | Named systems, hostnames, paths |
| Scope | The perimeter, mirrored into the scope file |
| Purpose | What question this answers. "Assessment" is not a purpose |
| Permitted action | The specific activity, not a category |
| Start time | Including timezone |
| Expiry | Mandatory. An authorization with no expiry is not an authorization |
| Limits | Request budget, rate, resource ceiling |
| Approval reference | Where the approval is recorded, so a third party can find it |

### What this does not do

**It is not enforced by the software.** The workbench has no concept of an
authorizer, no two-person mode, and no way to check that an approval exists. It
will send the request of a single operator who wrote a scope file. Dual
authorization is a control the organisation operates and an administrator audits —
and it is only as real as the record kept.

> Claiming that the tool enforces this would be false, and a false claim about a
> control is worse than an acknowledged gap, because it removes the human check
> that was doing the work.

## 6. Access-control research

Research involving authentication, authorization, sessions, object-level
authorization, role boundaries or administrative boundaries is legitimate and
important work. It is also where this framework's rules are most load-bearing.

### Permitted, within an authorization that names it

| Activity | Requires |
|---|---|
| Observing authentication behaviour | The target's own login, with your own credentials supplied through a supported mechanism |
| Observing authorization decisions | An explicitly authorized test account |
| Comparing what two identities may do | **Two authorized test accounts**, both provided for this purpose |
| Recording an access-control response | Recording the status, headers and body — the response, not the data behind it |
| Session handling observations | Your own session. Cookie attributes are evidence; values are redacted |

### Absolutely prohibited

| Prohibited | Why |
|---|---|
| Obtaining another person's private information | This is the harm the rules exist to prevent, at any authorization level |
| Using real user accounts or real user data | Not authorized by having been technically reachable |
| Testing access control by attempting to reach a real user's records | The test and the harm are the same act |
| Creating accounts to reach other people's data | The account is authorized; the access is not |
| Reusing a session, token or cookie that is not yours | Credential theft, whatever the intent |
| Treating a `403` as a puzzle | A refusal is a result to report |

**If a test requires more than one identity, use explicitly authorized test
accounts created for that purpose.** If the engagement provides one account and
the test needs two, the answer is to ask for the second — not to find one.

### Recording what you observed

An access-control observation is written up as: the request, the identity it was
made with (by reference, never its credential), the response, the expected
decision and the observed one, and the limitation. An **observable response
difference** between two authorized identities is a finding to investigate with
the owner. It is not, by itself, a vulnerability.

## 7. Payment and premium functionality

Testing payment or subscription systems is high-risk under triggers 3, 6, 7 and
often 11 simultaneously.

| Permitted | Requires |
|---|---|
| Observing a payment flow's request and response shape | Explicit written authorization naming payment functionality |
| Testing with the provider's own sandbox or test cards | Use the sandbox the provider publishes for exactly this |
| Comparing entitlements between two authorized test accounts | Both accounts authorized; bonus or test entitlements |
| Recording a paywall or entitlement *decision* | Recorded as an observation, never as a target to defeat |

| Prohibited, absolutely |
|---|
| Circumventing a paywall, subscription or entitlement check |
| Obtaining premium content without authorization, on any system, by any route |
| Using real payment instruments you are not authorized to use |
| Attempting to obtain another person's entitlement |

The framework's own code refuses the acquisition side of this: `402` and
entitlement markers are **blocking** statuses, recorded with the authorized route
and **no file written**. See
[`CONTENT-AND-DATA-RULES.md`](CONTENT-AND-DATA-RULES.md) §1.

> If an authorized assessment genuinely covers such a system, the authorization
> must name it and the work must use a defined test environment or test resource.
> Generic circumvention recipes do not appear in this documentation, and none will
> be added.

## 8. When to decline the work

An administrator or operator should decline — and an agent must stop — when:

- the requester cannot say who owns the target;
- the authorization is verbal, unclear, or does not name this activity;
- the scope would have to be widened to complete the test;
- the work would touch another person's data or account;
- the only way to get the result is to defeat a control;
- the requester asks for the result rather than the finding;
- the requester asks for it to be kept off the record.

None of those are judgement calls. Each one is a stop.
