# Coverage Matrix

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`../modes/ZERO-CREDENTIAL-ESCALATION-MODE.md`](../docs/modes/ZERO-CREDENTIAL-ESCALATION-MODE.md) · [`../guides/WORKFLOW.md`](../docs/guides/WORKFLOW.md) · [`../guides/OPERATING-RULES.md`](../docs/guides/OPERATING-RULES.md)

## What this is for

A findings list shows what was found. It does not show what was looked for.

This matrix records the second thing, and it is the one clients actually need
when deciding whether to trust the engagement: every boundary that was in scope,
whether it was tested, and if not, exactly why not.

Its purpose is to make the following sentence impossible to write by omission:

> "The assessment found two issues."

Without this artifact, that sentence is indistinguishable from "the tester
looked at two things and stopped."

## How to use it

1. Create one row per **security boundary**, not per endpoint. A boundary is a
   question like "can a normal user read another user's invoice?".
2. Fill it in as you go. A matrix reconstructed at the end of an engagement
   reconstructs the conclusions too.
3. Leave nothing blank. Every cell is either a status or a reason.
4. Carry it into the report as the coverage statement.

## Status values

Use only these. Each implies an obligation described below.

| Value | Meaning | Obligation |
|---|---|---|
| `TESTED — CLEAN` | Tested with sufficient coverage; control held | State the conditions tested |
| `TESTED — FINDING` | Tested; weakness found | Link the finding ID |
| `PARTIAL` | Some paths or roles tested, others not | Name exactly what was not covered |
| `NOT TESTED` | Not attempted or not possible | Name the blocking capability |
| `OUT OF SCOPE` | Excluded by authorization | Name the authorizing document or constraint |
| `BLOCKED — DEPENDENCY` | Requires third-party system not authorized | Name the dependency |

`NOT TESTED` without a stated reason is not an acceptable entry. If the reason
is not yet known, that is itself the finding to resolve before reporting.

## Matrix — authentication and session

| # | Boundary | Status | Finding | Evidence | Notes / blocker |
|---|---|---|---|---|---|
| A1 | Registration rejects malformed input | | | | |
| A2 | Account enumeration — login response | | | | |
| A3 | Account enumeration — password reset | | | | |
| A4 | OTP/MFA issuance and validation | | | | |
| A5 | Session token is unpredictable | | | | |
| A6 | Session fixation on login | | | | |
| A7 | Token refresh rejects an invalid/expired token | | | | |
| A8 | Logout invalidates the session server-side | | | | |
| A9 | Password reset cannot target another account | | | | |
| A10 | Alternate login endpoint enforces the same control | | | | |

## Matrix — authorization

| # | Boundary | Role A | Role B | Role C | Status | Finding | Notes / blocker |
|---|---|---|---|---|---|---|---|
| Z1 | Read own record | | | | | | |
| Z2 | Read another user's record | | | | | | |
| Z3 | Modify own record | | | | | | |
| Z4 | Modify another user's record | | | | | | |
| Z5 | Administrative function | | | | | | |
| Z6 | Delete own object | | | | | | |
| Z7 | Delete another user's object | | | | | | |
| Z8 | Export/bulk operation | | | | | | |
| Z9 | Field-level restriction (mass assignment) | | | | | | |
| Z10 | UI restriction is also enforced by API | | | | | | |

**Complete every role column.** A cell left empty is an untested role, not an
irrelevant role.

## Matrix — API and input integrity

| # | Boundary | Status | Finding | Evidence | Notes / blocker |
|---|---|---|---|---|---|
| P1 | Object identifier substitution | | | | |
| P2 | Direct API access bypassing UI flow | | | | |
| P3 | Hidden/assumed-immutable parameters | | | | |
| P4 | Type and format validation | | | | |
| P5 | Injection classes in scope | | | | |
| P6 | File upload validation | | | | |
| P7 | SSRF-relevant outbound fetches | | | | |
| P8 | Path traversal | | | | |
| P9 | CORS policy | | | | |
| P10 | Error verbosity / stack traces | | | | |
| P11 | Rate limiting (bounded) | | | | |
| P12 | Undocumented or legacy endpoints | | | | |

## Matrix — payment, entitlement and delivery

**Only where payment testing is authorized.** Leave the whole section out
rather than filling it with `OUT OF SCOPE` if the target has no payment.

| # | Stage / boundary | Status | Finding | Artifact | Notes / blocker |
|---|---|---|---|---|---|
| E1 | Price derived server-side, not client-supplied | | | | |
| E2 | Discount/quantity arithmetic | | | | |
| E3 | Currency handling | | | | |
| E4 | Order bound to authenticated user | | | | |
| E5 | Payment bound to correct order | | | | |
| E6 | Payment state set only from verified provider result | | | | |
| E7 | Callback signature verified | | | | |
| E8 | Callback replay / stale timestamp rejected | | | | |
| E9 | State transition idempotent | | | | |
| E10 | Entitlement created only on verified payment | | | | |
| E11 | Entitlement bound to payer identity | | | | |
| E12 | Entitlement scoped to specific product | | | | |
| E13 | Entitlement revoked on refund/cancellation | | | | |
| E14 | Premium access requires active entitlement | | | | |
| E15 | Download authorized at request time | | | | |
| E16 | Signed URL short-lived and single-purpose | | | | |
| E17 | Entitlement checked for alternate download paths | | | | |
| E18 | Protected artifact acquired and validated | | | | |

E18 is the only row that can be satisfied by an actual hashed file. Leave it
`NOT TESTED` if no artifact was obtained — do not mark it clean on the basis
that the download UI looked correct.

## Matrix — mobile

**Only for APK/AAB/mobile targets.**

| # | Boundary | Status | Finding | Notes / blocker |
|---|---|---|---|---|
| M1 | Exported components reviewed | | | |
| M2 | Exported component with harmful path | | | |
| M3 | Deep link authorization at entry | | | |
| M4 | Custom URL scheme handler authorization | | | |
| M5 | WebView JavaScript enablement | | | |
| M6 | WebView JavaScript bridge exposure | | | |
| M7 | WebView file access configuration | | | |
| M8 | WebView origin restrictions | | | |
| M9 | Local storage of tokens/secrets | | | |
| M10 | Local database protection | | | |
| M11 | External/shared storage usage | | | |
| M12 | Cleartext traffic permitted | | | |
| M13 | Certificate validation posture | | | |
| M14 | Backup extraction exposure | | | |
| M15 | Hardcoded secrets in code/resources | | | |
| M16 | Client-side premium/role check (hypothesis only) | | | |
| M17 | Runtime environment available for testing | | | |

M17 exists to record whether runtime testing happened at all. Without it, a
static-only engagement can be mistaken for a full assessment.

## Matrix — evidence and data handling

| # | Item | Status | Notes |
|---|---|---|---|
| V1 | Synthetic/canary records used for validation | | |
| V2 | Production personal data encountered | | |
| V3 | Broad enumeration performed | | |
| V4 | Real artifacts obtained | | |
| V5 | Artifacts hashed (SHA-256) | | |
| V6 | Secrets redacted before reporting | | |
| V7 | Raw evidence preserved and linked | | |
| V8 | Secrets committed to any repository | | |

## Coverage statement

Summarise honestly at the end of the engagement. This paragraph is required by
[`../AGENT.md`](../AGENT.md)'s final quality gate.

```text
Boundaries in scope           : N
TESTED — CLEAN                : N
TESTED — FINDING              : N
PARTIAL                       : N
NOT TESTED                    : N
OUT OF SCOPE                  : N
BLOCKED — DEPENDENCY          : N

Principal untested areas and why:

Not tested, blocked by unavailable runtime/emulator:

Not tested, blocked by absent authorization for third-party dependency:

Conclusions that are therefore conditional on the above:
```

## Using this matrix honestly

The most common failure is a coverage matrix quietly shrunk to look complete.
Every row removed is a boundary no longer accounted for.

If a boundary was not assessed, it stays in the matrix as `NOT TESTED` with a
reason. A large honest coverage table is a stronger deliverable than a small
flattering one, and `AGENT.md` is explicit that an untested area must never be
allowed to read as a secure one.
