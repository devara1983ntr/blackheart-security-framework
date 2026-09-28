# RED HEART — Adversary Emulation Mode

**Document type:** Core operational mode — offensive thinking and adversary emulation
**Purpose:** Structure how an assessor emulates a real adversary: build attack paths, chain weaknesses, reason about persistence and lateral movement, and test human and process controls — inside a defined Rules of Engagement.
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`../../AGENT.md`](../../AGENT.md) · [`SECURITY-AUDIT.md`](SECURITY-AUDIT.md) · [`ZERO-CREDENTIAL-ESCALATION-MODE.md`](ZERO-CREDENTIAL-ESCALATION-MODE.md) · [`../guides/ATTACK-PATHS.md`](../guides/ATTACK-PATHS.md) · [`../guides/ADVERSARY-EMULATION.md`](../guides/ADVERSARY-EMULATION.md)

> **Authorized use only.** This mode grants no authorization to test any system.
> It describes *how to think like an adversary*, not permission to act. Every
> activity it describes requires explicit written authorization recorded in
> [`../../templates/ENGAGEMENT-RECORD.md`](../../templates/ENGAGEMENT-RECORD.md).
> See [`../../SECURITY.md`](../../SECURITY.md).

---

## 1. Why this mode exists

BLACKHEART governs **proof and honesty**: what may be claimed, on what
evidence, at what severity.

It is deliberately conservative in expression. That is correct for reporting —
but it is not the whole job. An assessment that only reasons defensively will
never discover the path an actual attacker would take, because real attackers
do not evaluate controls one at a time. They move.

RED HEART is the offensive thinking layer. It supplies the missing half:

```text
BLACKHEART  →  what is true, and how do I prove it
RED HEART   →  what would an adversary actually try, and in what order
```

The two are not in tension. RED HEART finds the path; BLACKHEART decides how
much of it may be claimed. An emulation that produces an unprovable theory is
still useful — it goes into the report as an `UNVERIFIED` hypothesis with a
defined next test, not as a finding.

**The failure mode RED HEART exists to prevent:** an assessment that tests
controls individually, finds nothing conclusive, and concludes "no critical
issues" — while a trivial chain of three Low findings walks straight past the
boundary. Most real breaches are chains. Single-issue testing finds few of them.

---

## 2. The adversary model

Never emulate "an attacker" in the abstract. Build a specific one.

```text
ADVERSARY PROFILE
  Identity        : who is this actor class? (opportunistic, credential
                    thief, malicious insider, competing tenant, supply-chain
                    operator, automated botnet)
  Objective       : what do they want? (specific data, access, money, disruption,
                    reputation, staging ground)
  Capability      : what can they bring? (skill, time, tooling, money, insiders)
  Access          : how do they start? (anonymous, registered user, low-priv
                    employee, compromised third party)
  Constraints     : what stops them? (monitoring, rate limits, MFA, legal
                    exposure, operational security)
  Persistence     : can they return after eviction?
```

Two consequences follow, and both are frequently skipped in ordinary
assessments:

1. **Test what this adversary can reach**, not everything reachable. A
   zero-skill opportunistic botnet operator and a funded intrusion team
   produce completely different test plans.
2. **An objective defines a terminal condition.** An adversary pursuing money
   stops at the transfer. An adversary pursuing persistence does not. Knowing
   which one you are emulating tells you when to stop testing and what counts
   as the critical path.

---

## 3. Operational objective

The engagement has one operational objective: the specific end-state you are
testing for. Everything in the plan should trace back to it.

```text
OPERATIONAL OBJECTIVE
  Primary    :
  Secondary  :
  Explicitly out of objective :
  Success condition (what "reached" looks like, concretely) :
  Abort condition (what stops the engagement immediately) :
```

An objective stated as "find vulnerabilities" is not an objective. An objective
stated as *"demonstrate whether a low-privilege registered user can reach
another tenant's data without crossing into a third-party provider"* is.

Without an objective, adversarial testing degenerates into unstructured
clicking — active, busy, and unfalsifiable.

---

## 4. Engagement goals

An adversary engagement usually pursues one or more of three goals. They imply
different tests and different evidence.

| Goal | Question | Typical evidence |
|---|---|---|
| **Expose** | Can the adversary be detected when active? | Detection fired with the adversary's actual technique and timing |
| **Affect** | Can the adversary's ability to operate be disrupted? | The technique was neutralised or the path closed |
| **Elicit** | What can be learned about the adversary? | Observed tooling, timing, and behaviour |

For a pure assessment — as opposed to a live detection exercise — the relevant
question becomes: **if this adversary ran, which of their steps would we
actually see, and which would we miss?** That question exposes blind spots in
logging and monitoring that no amount of vulnerability testing will find.

---

## 5. Building the attack path

A single control test answers "is this boundary sound?" An attack path answers
"can an adversary reach the objective anyway?"

Construct it as a graph, not a list.

```text
ENTRY
  └─→ foothold (how)
        └─→ capability acquired (what it now permits)
              └─→ constraint bypassed (which control it defeated)
                    └─→ next position
                          └─→ ... → OBJECTIVE
```

Each edge is a **weakness with evidence**. If an edge is unproven, mark it. An
unproven edge is a hypothesis in the path, and a path is only as strong as its
weakest link.

**The critical discipline:** never describe a complete path when only part of
it was walked. A path with three unproven links is not a demonstrated attack
chain; it is a plausible route requiring validation, and it is reported as
`UNVERIFIED` with each missing step named.

See [`../guides/ATTACK-PATHS.md`](../guides/ATTACK-PATHS.md) for the
construction method.

---

## 6. Chaining discipline

Individually unremarkable weaknesses compose. This is where the highest-value
findings live, and where sloppy reporting does the most damage.

**The chaining test.** For each finding, ask: *if an attacker already had this,
what else becomes possible?* Apply it symmetrically.

```text
FINDING-002  Weak rate limiting on login
  + FINDING-005  Predictable reset tokens
  + FINDING-009  No lockout notification
  = credential compromise at scale
```

Rules:

- Every link needs its own finding with its own evidence.
- The combined impact is a *separate claim* from any individual finding and
  needs its own reproduction.
- If the chain was not actually walked, the combined impact is `UNVERIFIED`.
  Do not present an arithmetic result as a demonstrated breach.
- State the **prerequisites** explicitly. A chain that assumes an
  already-compromised account is a different, usually weaker, finding.

**Chains are rateable.** A chain that reaches a High objective through three
Low findings is a High finding. Rate the demonstrated destination, not the
size of the individual pieces. See
[`../guides/SEVERITY-RATING.md`](../guides/SEVERITY-RATING.md).

---

## 7. Evasion and misdirection

A real adversary assumes their presence is watched and actively misleads. An
assessment that never considers this will miss whole classes of weakness.

```text
WHAT WOULD AN ADVERSARY DO IF THEY KNEW THEY WERE WATCHED?

  Blend legitimate-looking traffic into normal patterns?
  Use the sanctioned interface rather than an obviously wrong one?
  Operate slowly enough to stay under alert thresholds?
  Work from a plausible identity and device?
  Phrase requests as ordinary business operations?
  Wait for a maintenance window, a weekend, a low-traffic period?
  Use one compromised third party to appear legitimate?
  Exploit a control *because* it is assumed to be the only check?
```

The last line is the one testers most often miss. A control that everyone
assumes is the only defence will receive attention, and attention finds
failures.

**Framing matters for a finding.** "The attacker can reach the admin function"
is a test result. "The attacker can reach the admin function through a path
that generates no distinguishing log entry" is a *business-relevant* result,
because detection is a real control.

---

## 8. Post-exploitation reasoning

Where authorization permits it, the question after a foothold is not "what can
I break" but "what does this position now permit, and how would it be used?"

```text
POSITION          : what identity / access / context do we now hold?
CAPABILITIES      : what does that identity legitimately permit?
LATERAL PATHS     : which other systems trust this identity or its tokens?
PERSISTENCE       : can the position be re-established after remediation?
BLAST RADIUS      : what is the largest credible impact from here?
DATA REACH        : what data is reachable, and how much is needed to prove it?
```

Three constraints apply, and they are not negotiable:

- **Re-establishment is assessed, never established.** Do not create a durable
  persistence mechanism on a production system to prove one exists. Analyse
  the re-establishment path; demonstrate it only in a sandbox, or on a system
  the engagement explicitly authorises.
- **Lateral movement testing stays inside scope.** A token that authenticates
  to another system does not make that other system in scope. See
  [`../guides/SCOPE.md`](../guides/SCOPE.md).
- **Data access is proven minimally.** One record that demonstrates the
  boundary failed is sufficient. Enumerating a table to demonstrate a point is
  data collection, not security testing.

---

## 9. Human and process targets

Software is not the only attack surface, and the most reliable adversary paths
frequently run through people and process rather than through code.

Where explicitly authorized — and social engineering, phishing, and physical
testing require authorization far more explicitly than technical testing — the
assessor examines:

```text
PROCESS TARGETS
  Support and reset flows       : can a user be socially escalated by support?
  Identity verification         : what does verification actually check?
  Multi-approval controls       : can the approver be manipulated?
  Incident response             : would this activity be detected in time?
  Onboarding / offboarding     : are terminated users actually removed?
  Shared credentials            : where do they exist and who knows them?
  Documentation drift            : does the runbook describe what the system does?

HUMAN TARGETS (authorized only)
  Role authority                : what can a senior employee actually authorise?
  Trust assumptions             : does any process assume a request is genuine?
  Fatigue and urgency           : which approvals degrade under pressure?
```

**Rules that do not bend.** Social engineering requires its own explicit
written authorization, separate from technical testing authorization. Never
target a person who is not part of the authorized engagement. Never send
realistic lures to real recipients outside the exercise scope. Record what was
tested and what was not.

If human testing is not authorized, the correct output is `NOT TESTED` with the
authorization named as the blocker — not a speculative guess about how social
engineering would succeed.

---

## 10. Rules of engagement

RED HEART is the most operationally intrusive mode, so its limits are the
tightest. These are recorded in the engagement record before execution.

```text
RULES OF ENGREGEMENT

  Time window            : testing permitted only between these times
  Rate limits             : maximum request rate and concurrency
  Prohibited             : explicit list — DoS, social engineering,
                            physical access, data destruction, etc.
  Data access limit       : maximum records that may be read to prove a finding
  Maximum impact         : the worst effect that may be caused, by design
  Escalation contact     : who decides to continue or stop, and how fast
  Abort conditions        : production instability, unintended data exposure,
                            discovery of an active incident, any of the above
  Third-party boundary    : hard stop at any vendor or provider
  Evidence handling       : what may be retained, and how it must be secured
```

**The abort conditions are not advisory.** When an abort condition is met, the
engagement stops and the client decides whether to resume. An assessor who
continues past an abort condition has not been aggressive — they have been
uncontrolled, and they have put the client at risk.

---

## 11. Stopping

RED HEART has a much lower stopping threshold than a vulnerability
assessment, because adversary emulation is open-ended by nature.

Stop a path when:

- the objective is reached and evidenced;
- an abort condition is met;
- the next action would exceed the stated maximum impact;
- the next action requires an unauthorized system;
- the next action would expose real personal data beyond the minimum;
- continuing would produce no new information.

Two failures to guard against:

- **Underexploitation.** Stopping at the first successful step because it was
  already interesting. The interesting finding is rarely the first one, and it
  is frequently not a vulnerability at all — it is the foothold from which the
  real one is reachable.
- **Unexploited depth without evidence.** Walking an entire path and then
  claiming less than was demonstrated. Equally wrong, and rarer. If you have
  the artifact, the artifact is the finding.

---

## 12. Emulation reporting

An emulation report differs from an assessment report in one important way: it
must convey **what the defender would have seen**.

```text
1. Adversary model and operational objective
2. Attack paths attempted, with each edge evidenced or marked unproven
3. Paths reached, and the demonstrated objective
4. Technique-by-technique review:
     - what the adversary did
     - whether it would have been detected
     - detection latency, if measurable
     - what the evidence of it would look like in a log
5. Paths that were blocked, and by what control
6. Blind spots — the path an adversary would take that nobody would see
7. Detection and hardening recommendations
8. Coverage statement, including paths not attempted
```

Section 4 is the part ordinary assessments omit and defenders need most. A
path that succeeded is a finding. A path that succeeded *silently* is a
finding about the monitoring programme, and it is frequently the more expensive
one.

## 13. Relationship to BLACKHEART

| Concern | Owning document |
|---|---|
| Authorization, scope, status taxonomy | [`AGENT.md`](../../AGENT.md) |
| Evidence standard, severity, honesty | BLACKHEART core, this repo's guides |
| Method escalation, coverage control | [`ZERO-CREDENTIAL-ESCALATION-MODE.md`](ZERO-CREDENTIAL-ESCALATION-MODE.md) |
| Attack path construction | [`../guides/ATTACK-PATHS.md`](../guides/ATTACK-PATHS.md) |
| Engagement structure, goals, matrices | [`../guides/ADVERSARY-EMULATION.md`](../guides/ADVERSARY-EMULATION.md) |
| Adversary emulation, chained objectives | **This document** |

Where RED HEART produces a result, BLACKHEART decides how that result may be
stated. Where the two appear to conflict, BLACKHEART wins — because a
demonstrated breach reported honestly is worth more than a spectacular
unverified one.
