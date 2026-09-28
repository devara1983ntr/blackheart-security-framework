# ATTACK-PATH-XXX — [Path Objective]

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`../docs/guides/ATTACK-PATHS.md`](../docs/guides/ATTACK-PATHS.md) · [`../docs/modes/RED-HEART-ADVERSARY-EMULATION.md`](../docs/modes/RED-HEART-ADVERSARY-EMULATION.md)

> **Fill every edge.** An edge with no status is an unexamined link. Do not
> leave the diagram implying a step that was never tested.

## Identity

```text
Path ID:
Operational objective:
Entry position and attacker prerequisites:
Starting identity and privileges:
Overall status: FULLY DEMONSTRATED / PARTIALLY DEMONSTRATED / THEORETICAL
Objective reached: yes / no / not attempted
```

## Prerequisites

Every condition that must hold before the path can start. State this before
the path — a chain requiring a compromised administrator is a materially
different finding from one requiring only a registered account.

```text
[ ]
```

## Path

```text
STEP   EDGE / ACTION                    EVIDENCE STATUS    FINDING
────   ─────────────────────────────    ──────────────    ───────
  1    Entry: how the foothold is       Demonstrated      F-00x
       obtained                                   / Inferred
                                              / Hypothesised
                                              / Blocked
  2    Capability gained:                  ...
  3    Control bypassed:                    ...
  4    Next position obtained:              ...
  n    Objective reached:                    ...
```

**Evidence status values:** `Demonstrated` (walked during the engagement) ·
`Inferred` (implied by demonstrated edges, not walked) · `Hypothesised`
(untested) · `Blocked` (tested and prevented).

## Objective outcome

```text
Objective:
Reached:            yes / no
Demonstration:      what exactly was obtained or affected
Evidence:           request/response pairs, state changes, artefacts
Severity:           per SEVERITY-RATING.md, from the demonstrated destination
```

## Blocked steps

Record every edge that a control stopped. These are results, not omissions.

| Step | Control that stopped it | Conditions tested | Finding |
|---|---|---|---|
| | | | |

## Unproven edges

Every edge not walked. Each must name the test that would close it.

| Step | Why unproven | Test that would establish it |
|---|---|---|
| | | |

## Detection review

For each step taken, what would a defender have seen?

| Step | Logged? | Retained? | Would alert? | Response plausible? |
|---|---|---|---|---|
| | | | | |

*Section 5 of an emulation report. Frequently the most actionable part of the
engagement.*

## Remediation

```text
For each unproven edge worth closing:
  Prevention — what would stop this step occurring
  Detection  — what would reveal it if it occurs
  Hardening  — what reduces the consequence if it succeeds

Weakest currently-demonstrated link:
Recommended fix location (the enforcement point, not the symptom):
Regression test for the primary fix:
```

## Limitations

```text
Areas of the path not tested, and why:
Tooling or access constraints:
Third-party boundaries not crossed:
```

## Reporting rules

- `PARTIALLY DEMONSTRATED` and `THEORETICAL` paths are `UNVERIFIED` findings.
  Do not describe them as demonstrated attack chains.
- Severity follows the **demonstrated destination**, never the theoretical one.
- Prerequisite conditions appear in the finding text, not only here.
- A blocked step is reported as a negative result, not omitted.
