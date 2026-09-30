# Emergency governance and fail-closed

**For:** whoever is deciding under time pressure
**Two things this document separates, because conflating them is dangerous:**
`emergency collect` is a **command with code behind it**; emergency access is a
**review process with no code behind it at all**
**Principle:** when the answer is not clearly yes, the operation stops

---

## 1. Emergency access is not a bypass, and must never become one

An incident is already happening. The pressure to act first and get authorization
later is strongest exactly when it should be resisted — because a request made
without authorization during an incident makes the incident worse, and it damages
the operator's position at the moment they may need it most.

**Emergency access means:** an *accelerated review* of an activity that is
**already authorized**, where the delay of the normal review would itself cause
harm. It does not mean:

| Never | |
|---|---|
| Permission to test something that is not authorized | An emergency does not create authority. Only the owner can |
| Permission to skip authorization "temporarily" | There is no temporary authorization |
| A generic escalation for any urgent request | Urgency is not authorization |
| Permission to bypass an access control | Never, under any framing, for any reason |
| Permission to reach another person's data | Same |
| A standing mode | It expires. See §3 |

## 2. Emergency access requires all eight

| Required | Detail |
|---|---|
| **A documented incident** | A reference to an incident ticket or record. "It felt urgent" is not one |
| **An authorized target** | The system must already be inside an authorization. Emergency access accelerates review; it cannot supply permission |
| **Emergency justification** | Why waiting for the normal review would make things worse. If you cannot write this sentence, there is no emergency |
| **Minimum necessary access** | The narrowest action that answers the question. Not the full check list, not a sweep |
| **A time limit** | Expiry is mandatory. See §3 |
| **An audit record** | The administrative-record fields in [`AUDIT-AND-EVIDENCE.md`](AUDIT-AND-EVIDENCE.md) §2 |
| **Evidence preservation** | Collected before anything else is done. There is no second chance at an incident's evidence |
| **Post-incident review** | By someone who was not the operator |

## 3. It expires, automatically, and expiry is not negotiable

```text
Emergency access window:  set at approval, never extended in place
On expiry:                the access ends. A new incident reference and a new
                          approval are required to continue
Extending:                is a new decision, made by the authorizer, recorded
                          separately. It is never a field edit
```

The workbench enforces expiry for *authorization* — `authorized_until` is checked
on every request, and a run that outlives its window is refused from that moment.
Emergency access must follow the same shape. The administrative process does not
enforce it; the discipline does.

## 4. `emergency collect` is a command, and it is already bounded

Do not confuse the governance process above with the capability that exists in
code. What the command actually does, verified against `workbench/emergency.py`:

| Property | Value |
|---|---|
| Methods | `GET` and `HEAD` only — a **module constant**, not a parameter, proven by a test over the module's own AST |
| Collects | The target URL, `/robots.txt` and `/.well-known/security.txt` |
| Budget | `min(scope.max_requests, 20)` |
| Sends anything before you agree? | No. It prints the plan and sends nothing until `--yes` |
| Records | Timestamps, hashes, provenance and the responses themselves |
| Scope | The same scope gate as every other command. It is not exempt |

**It is read-only collection for preserving evidence.** It does not investigate,
probe, escalate or confirm anything, and it cannot be turned into a
general-purpose mode — the method list is in the code, and the test fails if it
changes.

## 5. Mandatory stop conditions

Trigger any of these and the action stops. Not slows, not narrows — stops.

| # | Condition |
|---|---|
| 1 | Authorization revoked, expired, or withdrawn mid-run |
| 2 | Scope ambiguity — anything you cannot resolve from the written scope |
| 3 | An unexpected target appears (a redirect, a linked host, a shared service) |
| 4 | Unexpected data exposure — you are seeing data the engagement did not contemplate |
| 5 | Unexpected production impact — errors, latency, degraded responses |
| 6 | Resource exhaustion on the target |
| 7 | A rate-limit warning or throttling response |
| 8 | Service instability of any kind |
| 9 | Credential exposure — a secret appears in output, logs or a response |
| 10 | Evidence-integrity failure — a record fails its hash check |
| 11 | The authorization window closes |
| 12 | The emergency window closes |
| 13 | Unexpected third-party involvement — a hosting provider, payment processor or API you did not know was in the path |
| 14 | You do not understand what you are seeing |

**When triggered:**

```text
1  STOP active actions
2  PRESERVE evidence — hashes first, before anything is moved or edited
3  RECORD the reason, in the terms the tool used, not paraphrased
4  ESCALATE to the authorized contact
```

Condition 14 is a full stop condition and is not decoration. An operator or agent
who does not understand a response is one request away from making it worse.

## 6. Fail-closed

The default answer to any unanswered question about authorization is **no**.

| Situation | Fail-open (wrong) | Fail-closed (required) |
|---|---|---|
| The scope file will not load | Edit it until it does | Stop. Report the loader's reason |
| The authorizer cannot be reached | Assume the earlier approval covers it | Stop. Approval does not renew itself |
| The target responds oddly | Try another method to understand it | Stop. Record it, escalate |
| The window may have closed | Estimate that it is probably fine | Stop. The window is a timestamp, not a judgement |
| The engagement record is missing | Reconstruct it from memory | Stop. Reconstructed authorization is not authorization |
| A control blocks the path | Find the route around it | Stop. That is not the assessment, it is the bypass |

**Every fail-closed row costs a delay. Every fail-open row costs an
authorization.** That trade is always worth taking, and it is the reason this
section exists.

## 7. The decision tree

Deterministic. Two people in the same state reach the same answer.

```text
Is the operation local and read-only (parse, hash, report from existing evidence)?
├─ YES ──────────────────────────────► continue, per repository policy.
│                                       No scope or acceptance needed
└─ NO   (it would open a socket)
   │
   Is there a valid, current policy acceptance on this machine?
   ├─ NO ────────────────────────────► STOP. Report the `policy status` reason
   └─ YES
      │
      Is there a target authorization, recorded and written into a scope file?
      ├─ NO ─────────────────────────► STOP. Authority is not established
      └─ YES
         │
         Does `scope validate` accept the file, and does it cover this target
         and this method?
         ├─ NO ──────────────────────► STOP. Record the scope decision verbatim
         └─ YES
            │
            Is the requested action inside the WRITTEN scope — not merely inside
            what the tool would allow?
            ├─ NO ───────────────────► STOP
            └─ YES
               │
               Is it high-risk? (any trigger in HIGH-RISK-RESEARCH.md §2)
               ├─ YES ───────────────► Is there an independent authorizer's
               │                       approval, recorded, unexpired?
               │                       ├─ NO ──► STOP
               │                       └─ YES ─► continue to the checks below
               └─ NO ────────────────► continue to the checks below
                  │
                  Does it involve another person's private data or account?
                  ├─ YES ─────────────► Is that explicitly authorized, with
                  │                     minimum necessary access?
                  │                     ├─ NO ──► STOP
                  │                     └─ YES ─► continue, with data minimisation
                  └─ NO ──────────────► continue
                     │
                     Would completing it require defeating an access control?
                     ├─ YES ───────────► STOP. That is a bypass. It is not a test
                     └─ NO
                        │
                        Is authorization ambiguous, expired, or revoked?
                        ├─ YES ───────► STOP
                        └─ NO
                           │
                           Is the emergency window, if one is in use, still open?
                           ├─ NO ─────► STOP
                           └─ YES
                              │
                              Is evidence preservation in place (hashes, history,
                              bundle, before anything else)?
                              ├─ NO ──► STOP, preserve evidence first, then resume
                              └─ YES ► execute within the limits, and keep the
                                       stop conditions armed
```

Three branches carry the most weight, and they are the ones people improvise at:

- **"Would completing it require defeating an access control?"** — the answer is
  never yes. A check that needs the control defeated is a finding about the
  control, reportable as it stands.
- **"Is authorization ambiguous?"** — a stop, not a smaller run. A reduced scan
  against a target whose authorization is unclear is still a scan of that target.
- **"Is evidence preservation in place?"** — before, not after. An incident's
  evidence is at its most fragile in the first minutes.

## 8. What this document does not claim

None of the process in §1–§3 is enforced by software. The workbench has no
emergency mode, no elevated role and no approval check. What it *does* enforce is
bounded, and those bounds are in §4 — read-only methods, a small budget, and the
same scope gate as everything else.

Emergency governance is a discipline an organisation operates. Its evidence is the
audit record, and its integrity depends on people. Claiming otherwise would remove
the human check that is doing the actual work.
