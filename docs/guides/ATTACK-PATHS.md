# Attack Path Construction

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`RED-HEART-ADVERSARY-EMULATION.md`](../modes/RED-HEART-ADVERSARY-EMULATION.md) · [`../AGENT.md`](../../AGENT.md) §22 · [`SEVERITY-RATING.md`](SEVERITY-RATING.md) · [`../templates/ATTACK-PATH.md`](../../templates/ATTACK-PATH.md)

## Why this matters more than it looks

Most assessments test controls one at a time and find that each individually
holds. Most real breaches are not a control that fails; they are several
controls that each hold *and are insufficient in combination*.

The classic pattern: rate limiting works, and the account lockout works, and
the reset token is cryptographically strong — and all three are still defeated
because the reset flow has no rate limit, so the token strength is irrelevant.

Constructing paths is the method that finds these. It is also the method most
often skipped, because a path takes longer than a check and produces no single
impressive-looking finding.

## The two kinds

```text
INTRUSION PATH      entry → foothold → privilege → objective
                    the adversary's route in and what it yields

ATTACK CHAIN        finding A + finding B + … → combined impact
                    weaknesses composing after discovery
```

The framework reports the second as an attack chain. The first is what you
build to discover the second.

## Building a graph

Model assets, identities, and controls as nodes.

```text
NODE TYPES
  ASSET      invoice, order, user profile, entitlement, file
  IDENTITY   anonymous, registered user, role, service account
  CONTROL    a check that stands between two nodes
  STATE      workflow position, entitlement, session

EDGE TYPES
  CAN REACH      identity A can obtain asset B under conditions C
  IS ENFORCED BY which control actually makes that true
  IS TRUSTED BY  which other component assumes it holds
```

For every edge, answer: **what is the evidence?** An edge with no evidence is
a hypothesis, and it is drawn dashed.

## The tracing procedure

```text
1. Fix the objective      what is the adversary actually after?
2. Fix the starting point who is the adversary, with what access
3. Enumerate reachable    from that position, what can they touch directly?
4. For each reachable item, ask what that position now permits
5. For each permission gained, ask what it unlocks
6. Repeat until the objective is reached or no new position is reachable
7. Mark every edge with its evidence or mark it unproven
```

Step 6 terminating is a real outcome. Not every objective is reachable, and
proving unreachability from a defined position is a legitimate, valuable
result.

## Evidence states for an edge

| State | Meaning | How it is shown |
|---|---|---|
| **Demonstrated** | Walked during the engagement | Request/response pair, state change, artefact |
| **Inferred** | Strongly implied by demonstrated edges, not directly walked | Stated as inference with the reasoning |
| **Hypothesised** | Plausible, untested | Stated with the test that would confirm it |
| **Blocked** | Tested and prevented | The control, and the evidence it held |

A path is only as strong as its weakest edge. State which kind of path you are
reporting:

```text
FULLY DEMONSTRATED   every edge walked
PARTIALLY DEMONSTRATED  some edges walked, others inferred
THEORETICAL          plausible route, nothing walked
```

Only the first may be described as a demonstrated attack chain. The others are
`UNVERIFIED` and are reported with the missing steps named individually. This
is the framework's core rule applied to paths, and it is where emulation
reporting most often overreaches.

## Chaining findings

Once individual findings exist, test the combinations.

```text
FOR EACH PAIR AND TRIPLE:
  Does A's capability expand what B allows?
  Does A remove a precondition B depended on?
  Does A change the reach of B?
  Do A and B require the same preconditions?  ← if so the chain is weaker
```

**Prerequisites are the thing most often lost.** A chain requiring a
pre-existing compromised administrator account is a different finding from one
requiring only a registered user, often several severities apart. Every chain
states its entry position explicitly.

## Severity of a chain

Rate the destination, not the components.

```text
Three Low findings chaining to cross-tenant data access  →  High or Critical
One High finding standalone                                  →  High
Three High findings with no demonstrated combination       →  three High findings
```

The last case is the one testers get wrong in the client's favour. Findings
that do not demonstrably combine are three findings, not one escalated
finding. Claiming the combination without walking it inflates the report and
is precisely the behaviour this framework exists to prevent.

## Lateral and identity reasoning

Where the engagement permits it, treat identities as the primary attack
surface rather than the network.

```text
Given identity I with access to system S:
  What does S trust about I beyond the check it performs?
  Does any token or session issued to I work at T?
  Does a service account or integration credential reach further than its
     owning application?
  Can a role be assumed, inherited, or delegated?
  Where does I's trust terminate, and where does it resume without a re-check?
```

**Trust does not propagate implicitly.** A finding that a token works on a
second system is a finding *about that token*; it is not authorization to test
the second system. It is recorded as a dependency and reported. See
[`SCOPE.md`](SCOPE.md).

## Where paths break

Most of the time a path terminates at a real control. That is a useful result
and is recorded as one.

```text
Broken by            how to record it
──────────────────────────────────────────────────
AuthN/AuthZ check    NOT VULNERABLE for that boundary, with conditions
Out-of-scope system  OUT OF SCOPE, dependency named
Unavailable tooling  NOT TESTED, capability named
Non-destructive only NOT TESTED, method named
Business rule        Documented constraint, not a technical finding
```

The last row matters. "The support team must manually verify identity" is not a
vulnerability and not a non-vulnerability — it is a documented business
control, and reporting it as a finding wastes remediation effort. It becomes a
finding only if a test shows the control can be bypassed.

## Reporting a path

```text
PATH ID:
Objective:
Entry position and prerequisites:
Sequence, edge by edge, each with status and evidence:
Where it terminated, and why:
Objective reached: yes / no / not attempted
Status and severity of the destination:
Every unproven edge, named
What would close the remaining links
```

See [`../templates/ATTACK-PATH.md`](../../templates/ATTACK-PATH.md).

## The common failures

| Failure | Why it is common | Correction |
|---|---|---|
| Drawing a path from the architecture diagram | It shows intent, not implementation | Trace from observed behaviour |
| Marking every edge solid once one is demonstrated | Confirmation bias | Each edge needs its own evidence |
| Calling a plausible route a "critical path" | It reads as a finding | It is `UNVERIFIED` until walked |
| Omitting prerequisites | Makes a weak chain look strong | State entry position first |
| Stopping at the first reachable objective | The objective was not the interesting one | Continue to the real objective |
| Never attempting the path | Safest and least informative | Test the chain or record it as untested |

## The rule that keeps this honest

A path is a **claim about a sequence**, and sequences are only worth what their
evidence is worth. The discipline is identical to every other part of the
framework:

> Demonstrate what you can. Name what you cannot. Never let the diagram imply
> more than the testing established.

A partially demonstrated path with every edge honestly labelled is more useful
to a client than a fully "demonstrated" one that was reconstructed after the
fact.
