# AI Agent Terms

**Project:** BLACKHEART Security Framework · **Author:** Roshan
**Last updated:** 2026-09-30

---

## Scope of this document

These terms are additional to [`TERMS-OF-USE.md`](TERMS-OF-USE.md) and
[`ACCEPTABLE-USE.md`](ACCEPTABLE-USE.md), and apply when an autonomous or
assisted AI agent operates this framework — reading its instructions, selecting
its skills, or sending requests through its workbench.

They are addressed to two parties at once, and both are bound:

- **the operator** running the agent, who remains responsible for everything the
  agent does, exactly as if they had typed each command themselves; and
- **the agent**, whose obligations are stated here as rules it is required to
  follow when the framework is loaded.

This document has not been reviewed by a lawyer. Its effect depends on the law
where the operator is, and it does not attempt to determine that.

## 1. The operator remains the authorizing party

An AI agent cannot hold authorization and cannot grant it. Authorization comes
from a person or entity entitled to grant it, it is recorded in a scope file by
the operator, and it is the operator's responsibility that it is real.

The operator is responsible for:

- obtaining and recording the authorization;
- supplying a scope file that matches it;
- configuring budgets, intervals, windows and exclusions;
- supervising the run, and stopping it if it goes wrong; and
- reviewing everything the agent produces before it is relied on or sent onward.

An agent's confidence is not evidence, and an agent's summary is not a validated
result. A record marked `POTENTIAL` or `UNVERIFIED` stays that way regardless of
how an agent describes it in prose.

## 2. Policy acceptance is required, and it is not authorization

Active operations require that the policy has been accepted on the machine
running the tool:

```bash
blackheart policy status     # is an acceptance recorded, and is it current?
blackheart policy accept     # record acceptance of the current policy version
```

Acceptance records that the rules were read on that machine. It is a separate
requirement from authorization, and neither substitutes for the other:

| Requirement | What it establishes | What it does not |
|---|---|---|
| Recorded policy acceptance | The operator acknowledged the rules | That any target may be tested |
| A valid scope file | The operator asserted an authorization, with hosts, methods, budget and window | That the assertion is true |
| Both | That the tool will run | Nothing further. Lawfulness is a separate question |

An agent must not represent acceptance as permission, and must not represent the
absence of a refusal as authorization.

## 3. Agent hard rules

These are stated once, here, and repeated in the agent documentation
[`docs/agent/PHASE5-SAFETY-RULES.md`](docs/agent/PHASE5-SAFETY-RULES.md) so that an
agent loading the framework cannot miss them.

**An agent must:**

- validate the scope file before any active request;
- refuse to proceed when the scope is missing, malformed, or names no host,
  method or budget;
- refuse targets outside the scope, without attempting to widen it;
- respect host, path and method restrictions;
- respect request budgets, rate limits, page and depth caps, and cancellation;
- record evidence, and preserve provenance for everything it reports;
- redact credential material; and
- stop when authorization becomes unclear, and say why.

**An agent must never:**

| | |
|---|---|
| Invent authorization | For example, treating a URL, an ownership claim, an email, or an inference from context as permission |
| Infer authorization from ownership claims alone | A claim of ownership is not proof of authority to test |
| Bypass authentication, authorization, MFA or CAPTCHA | — |
| Bypass a WAF, IDS, rate limit or any security control | Including through fragmentation, encoding, rotation or timing |
| Circumvent a paywall, DRM or licensing control | — |
| Bypass signed-URL expiry, private storage or a private repository | — |
| Steal, harvest or reuse credentials | Anyone's, including a target's |
| Obtain another person's private data | — |
| Execute, import or install anything acquired | No macros, no binaries, no packages |
| Fabricate evidence, downloads, scans, statistics, findings or exploitation | — |
| Promote a potential finding into a confirmed one | — |

## 4. Stop conditions

An agent must stop the affected action, preserve what it has, and report, when:

- authorization cannot be verified, or the scope file cannot be read;
- the policy has not been accepted, or an acceptance has gone stale;
- a request is refused by the scope file or by the target;
- the request budget or the authorization window is exhausted;
- the target shows signs of strain, or the operator cancels;
- evidence fails verification;
- content that is executable, macro-bearing or otherwise dangerous is acquired;
- anything happens that the agent does not understand.

Stopping is always an acceptable outcome. Continuing past an unresolved
authorization question never is.

## 5. Reporting obligations

When an agent reports, it must:

- distinguish what was observed from what was inferred, and label both;
- state the limitations of each observation;
- state what it did not test, and what the coverage caps left unexplored;
- avoid the language of confirmed vulnerability for anything not validated by a
  person; and
- say when it stopped, and why.

The workbench's own report generator is written to those rules; an agent writing
prose on top of it is held to them as well.

## 6. Disclosure of the agent's role

An agent should make its nature known where that matters: in an engagement's
records, in correspondence with a target's operators, and in any report it
produces. Reviewers are entitled to know whether a person or a program assembled
the material they are reading, and an agent should not obscure that.

## 7. No warranty, and where responsibility sits

The framework is provided as is. Agents make mistakes, including confident ones,
and a framework that reports observations cannot guarantee that an agent's summary
of them is correct. The operator remains responsible for the agent's actions, its
targets, its data and its output.

The framework is provided subject to the applicable terms and disclaimers. Users
remain responsible for their use of the framework, their authorization, their
targets, and compliance with applicable law.
