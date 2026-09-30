# Administrator governance — start here

**For:** whoever administers this repository, and whoever operates the framework
under that administration
**Status:** governance documentation for **already-implemented** capabilities.
Phase 6 adds no tool, no command, no flag and no bypass.
**One rule above all others:** administrative authority is **not** target
authorization.

---

## The sentence this whole layer exists to state

> **Being an administrator of BLACKHEART does not authorize you to test anything.**

Controlling this repository gives you control over *this software*. It gives you
no permission over any external system, any other person's data, any account that
is not yours, or any resource behind an access control. No role in this project
confers target authorization, and none can.

## Read this first: this layer only ever adds

The Phase 5 agent layer told you what the framework does and refuses. This layer
tells you **who is permitted to direct it, under what review, and what must never
exist in it.**

The governance layer **grants nothing and relaxes nothing**. Every rule here either
adds a requirement on top of the Phase 5 rules or restates a Phase 5 prohibition in
administrative terms. Where this layer and a Phase 5 rule appear to differ, apply
the stricter one — which is always the Phase 5 rule, because this layer cannot
loosen it.

## The four roles, and they are not interchangeable

| Role | What they control | What they do **not** thereby acquire |
|---|---|---|
| **Repository administrator** | The BLACKHEART project: its code, its policy documents, its CI, its releases | Target authorization of any kind. Control of a *tool* is not permission over a *system* |
| **Framework operator** | A running instance of the workbench: the scope files, the budget, the evidence | Target authorization beyond the scope file they were given authority to write |
| **Authorized security tester** | Nothing by role. What they may do comes entirely from their authorization record | Any target not named in that authorization, and any action outside it |
| **Target / resource owner** | Access to their own systems and resources, and who may test them | — this is the only role whose permission creates target authorization |

**These identities are separate, and the separation is the point.** Confusing them
is the single most common way an authorized engagement becomes an unauthorized
one. §3 of [`ADMIN-GOVERNANCE.md`](ADMIN-GOVERNANCE.md) treats each in depth.

## Read in this order

```text
1  ADMIN-GOVERNANCE.md              the roles, authority vs authorization, and the
                                    invariant that this project must never contain
                                    a backdoor
2  HIGH-RISK-RESEARCH.md            what counts as high-risk, the elevated gate it
                                    requires, dual authorization, and where this
                                    work should actually happen
3  EMERGENCY-GOVERNANCE.md          emergency access, the deterministic decision
                                    tree, and fail-closed
4  SECURITY-CONTROLS.md             the backdoor prohibition in detail, how it is
                                    verified, and the credential policy
5  CONTENT-AND-DATA-RULES.md        paywalls, DRM, licensing, download restrictions,
                                    and private or sensitive data
6  AUDIT-AND-EVIDENCE.md            the administrative record, and evidence rules
7  ADMIN-THREAT-MODEL.md            twelve threats, and what to do about each
8  AI-ADMIN-PROTOCOL.md             the same rules, addressed to an AI agent
9  ADMIN-REVIEW-CHECKLIST.md        the checklist to run before, during and after
```

Templates and reference:

| | |
|---|---|
| [`EMERGENCY-AUTHORIZATION-TEMPLATE.md`](EMERGENCY-AUTHORIZATION-TEMPLATE.md) | The bounded, expiring authorization record |
| [`../../AUTHORIZATION-AGREEMENT.md`](../../AUTHORIZATION-AGREEMENT.md) | The ordinary authorization record |
| [`PHASE6-FINAL-REPORT.md`](PHASE6-FINAL-REPORT.md) | What this phase created, and every measurement |

## The policies this layer sits under

Administrator governance does not replace the project's policies. It operates
inside them, and they are stricter than anything here:

[`ACCEPTABLE-USE.md`](../../ACCEPTABLE-USE.md) ·
[`TERMS-OF-USE.md`](../../TERMS-OF-USE.md) ·
[`AUTHORIZATION-AGREEMENT.md`](../../AUTHORIZATION-AGREEMENT.md) ·
[`SECURITY-RESEARCH-DISCLAIMER.md`](../../SECURITY-RESEARCH-DISCLAIMER.md) ·
[`PRIVACY-POLICY.md`](../../PRIVACY-POLICY.md) ·
[`DOWNLOAD-AND-ACQUISITION-POLICY.md`](../../DOWNLOAD-AND-ACQUISITION-POLICY.md) ·
[`AI-AGENT-TERMS.md`](../../AI-AGENT-TERMS.md) ·
[`RESPONSIBLE-USE.md`](../../RESPONSIBLE-USE.md) ·
[`policy/BLACKHEART-POLICY.json`](../../policy/BLACKHEART-POLICY.json)

## Conflict resolution

Stricter wins. Always. If two documents appear to disagree:

1. apply the one that permits **less**;
2. check the implementation — `workbench/` is the source of truth for what the
   tool actually does;
3. report the contradiction rather than choosing quietly.

## What is **not** claimed here

Stated up front, because a governance document that overstates its own
enforcement is worse than none:

| Not claimed | Why |
|---|---|
| That any role in this document exists in the software | **It does not.** There is no administrator account, no login, no role, no privileged mode and no admin credential anywhere in this framework. Verified, and restated in `ADMIN-GOVERNANCE.md` §4 |
| That dual authorization is technically enforced | It is not. It is a procedural control, and §5 of `HIGH-RISK-RESEARCH.md` says so |
| That emergency access is technically enforced | It is not. The `emergency collect` command is bounded by code; the emergency *review process* is not |
| That this layer can verify anyone's authorization | Nothing can. A scope file is an assertion, and the tool checks its arithmetic, not its truth |
