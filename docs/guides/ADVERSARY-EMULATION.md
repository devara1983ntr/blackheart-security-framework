# Adversary Emulation

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`../modes/RED-HEART-ADVERSARY-EMULATION.md`](../modes/RED-HEART-ADVERSARY-EMULATION.md) · [`ATTACK-PATHS.md`](ATTACK-PATHS.md) · [`TOOL-AND-ENVIRONMENT.md`](TOOL-AND-ENVIRONMENT.md) · [`METHODOLOGY-STANDARDS.md`](METHODOLOGY-STANDARDS.md)

## What this is

A structured way to run an engagement against a *defined adversary* rather
than against a checklist. It gives the engagement a purpose beyond "find
things", and it produces two outputs ordinary assessments do not: whether the
adversary's route actually works, and **whether anyone would have noticed**.

The second is frequently the more valuable one, and it is invisible to
vulnerability testing.

Structured after the MITRE Engage model, which organises adversary engagement
around an operational objective, engagement goals, and a matrix of
goal → approach → activity. This document adapts that structure to assessment
engagements; it does not require the full matrix or any MITRE tooling.

## The engagement process

```text
PREPARE  →  define the objective, the adversary, and the rules
OPERATE  →  run the engagement activities against that objective
UNDERSTAND → analyse what happened, including what was not detected
          ↓
        loops back: new information changes the next operation
```

The loop matters. An engagement that runs once, top to bottom, without feeding
its results back into planning is a checklist. The loop is what makes it
adversarial.

## Prepare

```text
1. Assess what is known
   Assets of value, current controls, known weaknesses, threat landscape

2. Define the operational objective
   The specific end-state the engagement tests for
   "Demonstrate whether a low-privilege user can reach another tenant's data"

3. Determine the desired adversary reaction
   If the adversary is exposed, what do we want them to do?
   Withdraw? Persist? Escalate? Reveal more technique?

4. Determine what the adversary should perceive
   The environment must be plausible enough that the adversary behaves
   naturally rather than abandoning it on sight

5. Select engagement channels
   The surfaces through which the adversary can reach the objective

6. Establish rules of engagement
   Time windows, rate limits, prohibited actions, data limits, abort
   conditions, escalation contact, third-party boundary
```

Steps 4 and 5 are where most engagements under-invest, and they are why
emulation produces better results than scanning: a test conducted against an
implausible environment produces implausible adversary behaviour, and
implausible behaviour teaches you nothing.

## Engagement goals

| Goal | The question | Evidence produced |
|---|---|---|
| **Expose** | Would this activity have been detected? | A detection with the actual technique and realistic timing |
| **Affect** | Could the adversary's capability have been disrupted? | The technique neutralised or the path closed |
| **Elicit** | What can be learned about the adversary? | Observed behaviour, tooling, and timing |

For a black-box assessment, the Expose goal becomes a coverage question in
reverse: **for each step the adversary took, would a defender have seen it?**

```text
For each adversary step:
  Would it generate a log entry?           yes / no
  Would that entry be retained long enough? yes / no
  Would it trigger a detection rule?       yes / no
  Would a human plausibly respond in time?  yes / no / unmeasurable
```

Steps that answer "no" repeatedly are the finding. A path that succeeded
without leaving a trace is materially more dangerous than one that succeeded
loudly, and it is the one ordinary vulnerability testing will never surface.

## Approaches

Engagement activity is organised under five approaches. Selecting deliberately
prevents a common drift toward only the technical.

```text
PLAN       align the operation with a desired end-state
COLLECT    gather adversary tools, observe tactics, capture raw intelligence
DETECT     establish or maintain awareness of adversary activity
PREVENT    stop the adversary's operation from achieving its objective
DIRECT     encourage or discourage specific adversary behaviour
```

An assessment that only does PREVENT produces a list of weaknesses. Adding
DETECT and COLLECT produces an assessment the defender can actually act on.

## Blended objective testing

Rather than testing against one hypothetical adversary, run several bounded
blends that force different approaches and expose different weaknesses.

```text
BLEND              favours                    tends to expose
──────────────────────────────────────────────────────────────
Technical          speed, tooling, automation  missing controls,
                                              weak configuration
Human              social influence, trust     process gaps, weak
                                              verification, approval
                                              fatigue
Hybrid             technical + social          control layering failures —
                                              paths where the social
                                              step reaches a technical
                                              boundary
```

Blends are a planning device, not a licence. Each still runs under the same
Rules of Engagement, and human or social testing requires its own explicit
authorization. See §6 of
[`../modes/RED-HEART-ADVERSARY-EMULATION.md`](../modes/RED-HEART-ADVERSARY-EMULATION.md).

## Safety planning

Emulation is the most operationally intrusive work in this framework, so the
safety planning is the most explicit.

```text
DEFINE
  [ ] Operational objective agreed and written
  [ ] Risk appetite agreed with stakeholders
  [ ] Third-party boundaries identified
  [ ] Prohibited actions enumerated
  [ ] Data-access ceiling set
  [ ] Maximum permitted impact stated

PREPARE
  [ ] Test environment prepared and verified
  [ ] Monitoring capable of detecting adverse effects
  [ ] Communication channel and escalation contact confirmed
  [ ] Abort conditions written and shared
  [ ] Rollback plan exists for state changes made during testing

EXECUTE
  [ ] Rules of Engagement re-read before start
  [ ] Activity logged with timestamps for audit
  [ ] Abort conditions monitored continuously

UNDERSTAND
  [ ] Actions taken recorded completely
  [ ] Deviations from plan recorded
  [ ] Lessons captured for the next operation
```

A monitoring capability is a prerequisite, not a nicety. Running intrusive
adversary activity with no way to detect your own adverse effect is not
aggressive engagement — it is unmanaged risk, and the Rules of Engagement
exist precisely to prevent it.

## Stopping

```text
Stop the operation when:
  the objective is reached and evidenced
  an abort condition is met
  the next action exceeds the maximum permitted impact
  the next action requires an unauthorized system
  real personal data would be exposed beyond the minimum
  the adversary path is exhausted and no new information would result
  the window closes
```

Two asymmetric errors to avoid:

- **Stopping at the first success.** The first foothold is rarely the finding;
  it is usually the position from which the finding is reachable.
- **Continuing past a limit.** Aggression without a defined ceiling converts
  an authorised engagement into an incident.

## Reporting

```text
1.  Operational objective and rules of engagement
2.  Adversary model used
3.  Path attempted, with each edge evidenced or marked unproven
4.  Objective reached: demonstrated / not reached / not attempted
5.  Technique-by-technique detection review
        technique → logged? → retained? → alert? → response?
6.  Paths blocked, and by what control
7.  Blind spots: routes an adversary could take unseen
8.  Prevention and detection recommendations
9.  Deviations from plan
10. Coverage statement, including what was not attempted
```

Sections 5 and 7 are the ones that change defender behaviour, and they are the
ones most often omitted. Section 5 turns a breach report into a detection
programme. Section 7 is frequently the most actionable part of the whole
engagement, because it describes the attack that did not happen and would not
have been seen.

## Relationship to the rest of the framework

| Concern | Document |
|---|---|
| Authorization, evidence, honesty | [`../AGENT.md`](../../AGENT.md) |
| Path construction and evidence states | [`ATTACK-PATHS.md`](ATTACK-PATHS.md) |
| Emulation as a mode, and its stop conditions | [`../modes/RED-HEART-ADVERSARY-EMULATION.md`](../modes/RED-HEART-ADVERSARY-EMULATION.md) |
| Where this sits in the wider standards landscape | [`METHODOLOGY-STANDARDS.md`](METHODOLOGY-STANDARDS.md) |

## Tooling note

This framework requires no specific tooling, and deliberately specifies none. A
tool that automates adversary activity cannot verify its own authorization, and
the framework's entire value rests on authorization being explicit and
human-established.

Tool usage is governed by
[`TOOL-AND-ENVIRONMENT.md`](TOOL-AND-ENVIRONMENT.md): use what is available,
substitute honestly, and never claim a tool was used when it was not.
