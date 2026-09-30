# Administrator threat model

**For:** whoever administers this project and whoever relies on that administration
**Scope:** the *governance* threats — compromise, misuse, confusion and drift.
The threats against the workbench's code are modelled separately in
[`../workbench/THREAT-MODEL.md`](../workbench/THREAT-MODEL.md)
**Format:** every threat states its impact, prevention, detection, response — and
its **limitation**, which is what that prevention cannot do

---

## Reading the limitations

Each threat below ends with a **limitation**. That is not a hedge. A threat model
without limitations tells a reader that the prevention is complete, and a reader
who believes that stops looking. The limitations here name what remains exposed
after everything in the prevention column has been done.

## T-1 — Compromised administrator account

| | |
|---|---|
| **Impact** | An attacker who controls the repository can change the software: add a bypass, weaken a gate, alter a policy document, or publish a misleading release |
| **Prevention** | Multi-factor authentication on the hosting account; least privilege; no shared administrator logins; signed commits; branch protection with required review; no credential in the repository to steal in the first place |
| **Detection** | Unfamiliar commits and releases; changes to workflows or policy documents; a diff that touches a control; the invariant checks in `SECURITY-CONTROLS.md` §2 failing |
| **Response** | Revoke access, revert the change, re-run the gates, audit what was published while the access lasted, notify anyone who consumed it |
| **Limitation** | A repository administrator is, by definition, permitted to change the repository. Prevention here is *detection and review*, not prevention. Somebody has to read the diff — and if the change is quietly reasonable-looking, review may pass it |

## T-2 — Malicious operator

| | |
|---|---|
| **Impact** | An operator uses a legitimate scope file as cover, or widens it, and tests or collects outside the authorization |
| **Prevention** | Authorizations that name targets specifically; budgets set from the authorization; a second person on high-risk work; evidence that is checked rather than accepted |
| **Detection** | Scope files that do not match their authorization record; request counts higher than the engagement expected; targets appearing in evidence that do not appear in the authorization; destination hosts the organisation does not recognise |
| **Response** | Stop the work, preserve the evidence as it stands, inform the authorizer, and treat the affected targets as potentially compromised |
| **Limitation** | **The tool cannot detect this.** A scope file is an assertion, and the workbench checks the assertion's arithmetic, not its truth. An operator who writes out-of-scope hosts into a scope file and runs a normal command produces a normal-looking result. The only real control is the authorization record and a person reviewing it |

## T-3 — Accidental misuse

| | |
|---|---|
| **Impact** | An honest operator sends a request they should not have — a wrong host, a production system mistaken for staging, a scope file copied from a previous engagement and not fully edited |
| **Prevention** | `scope validate` before every run, and actually reading its output; a distinctive scope file per engagement, never a reused template; the pre-request checklist |
| **Detection** | The scope decision printed with every response; an unexpected host in a redirect chain; a target that behaves like production |
| **Response** | Stop, report to the authorizer, disclose promptly. An accidental request disclosed immediately is a far better position than one discovered later |
| **Limitation** | The check exists and is printed, and a rushed operator still skips reading it. Prevention is a habit, and habits fail under time pressure — which is what T-4 is about |

## T-4 — Stolen credentials

| | |
|---|---|
| **Impact** | Depends entirely on what the credential could reach. A repository token is bounded; a credential to a target system is not |
| **Prevention** | No credential in the repository, ever; runtime injection; scoped and short-lived tokens; MFA; separate identities for separate systems |
| **Detection** | Unexpected authentication events; tokens used from an unfamiliar location; a credential appearing where it should not |
| **Response** | Rotate immediately — this is the one response with no analysis step first. Then audit what it reached |
| **Limitation** | Rotation is fast; assessing what the credential *already* reached is slow and often incomplete. Assume compromise and act |

## T-5 — Insider misuse

| | |
|---|---|
| **Impact** | Someone with legitimate access uses it for a purpose it was not given for — the engaged tester who keeps testing after the window, the administrator who reads evidence they are not a party to |
| **Prevention** | Scope and time windows that are enforced rather than remembered; least privilege on evidence access; a documented retention and deletion schedule |
| **Detection** | Activity outside the window; access to evidence by someone not named in the engagement |
| **Response** | Remove access, preserve the record, inform the authorizer |
| **Limitation** | Insider misuse is defined by *intent*, and the same action is legitimate or not depending on authorization that no log records. Detection sees the action, not the mandate |

## T-6 — Confused deputy

| | |
|---|---|
| **Impact** | The framework is asked to act with authority it holds for one purpose, in service of another. Example: an agent asked to "just download this PDF for me", using the operator's authenticated session, where the target is not in the engagement |
| **Prevention** | Every request checked against the scope, at the socket, regardless of who asked; the scope gate raising rather than returning a flag; the agent rules in [`AI-ADMIN-PROTOCOL.md`](AI-ADMIN-PROTOCOL.md) |
| **Detection** | A request to a host that is not in the engagement's authorization; a sudden widening of a scope file; an operator explaining why this one is different |
| **Response** | Refuse the request; record it; tell whoever asked why |
| **Limitation** | The gate refuses *out-of-scope* requests, not *inappropriate* ones. A request inside a valid scope, made for the wrong reason, passes every check the tool has |

## T-7 — Scope confusion

| | |
|---|---|
| **Impact** | The most likely route to an accidental unauthorized test. Two environments with similar names, a staging host that shares a domain with production, a shared service behind both |
| **Prevention** | Scope files that name hosts explicitly; exclusions listed rather than implied; an environment field recorded and checked |
| **Detection** | `scope validate` output read before the run; an unexpected host in a redirect chain or a discovered link |
| **Response** | Stop, record the scope decision verbatim, escalate |
| **Limitation** | Nothing in the tool knows that `api.example.com` is production and `api-staging.example.com` is not. That distinction lives entirely in the authorization, and only a person holds it |

## T-8 — Authorization expiration

| | |
|---|---|
| **Impact** | Work continues past the moment it stopped being authorized. Every request after that point is unauthorized, however ordinary it looks |
| **Prevention** | `authorized_until` set from the authorization, and checked on every request; a window that matches the engagement rather than being rounded up |
| **Detection** | The tool refuses once the window closes; a run that stops unexpectedly at a timestamp is this working |
| **Response** | Stop. A new authorization is required, not an extension by the operator |
| **Limitation** | The tool enforces the window it was *given*. An operator who sets a later date than the authorization grants is not detected — the check is on the assertion, not the mandate |

## T-9 — Emergency-mode abuse

| | |
|---|---|
| **Impact** | "Emergency" becomes the standing reason to skip review. This is how a governance control decays: not by being broken once, but by being invoked routinely |
| **Prevention** | Emergency access requires a documented incident, an already-authorized target, and an expiry; extensions are new decisions, not edits |
| **Detection** | Frequency of emergency use; emergencies declared by the operator who benefits from them; incidents that turn out to have no incident record |
| **Response** | Review the pattern, not just the instance. Repeated emergency use is an approval-process problem, not a discipline problem |
| **Limitation** | The framework has no emergency mode to abuse — so there is nothing to log, alert on, or detect technically. This threat is visible only in the administrative record |

## T-10 — Evidence tampering

| | |
|---|---|
| **Impact** | The report no longer describes what happened. Every conclusion drawn from the altered record is suspect, including the ones that were correct |
| **Prevention** | SHA-256 per record and per bundle; verification on read; a report that excludes records failing verification rather than counting them |
| **Detection** | `evidence manifest --verify` reports the mismatch; the report names the excluded record |
| **Response** | Report the integrity failure as a finding in its own right; do not repair the record; say which conclusions depended on it |
| **Limitation** | Someone who can rewrite both the record and the manifest recomputes both hashes, and the bundle verifies. Verification detects accident and casual tampering, not a determined forger. The remaining control is the administrative record and the operator's disclosure |

## T-11 — Secret leakage

| | |
|---|---|
| **Impact** | Wide, and worse the longer it is unnoticed: a leaked credential reaches forks, caches, CI logs and artifacts, and a public commit can never be fully unpublished |
| **Prevention** | Secrets never enter the repository; redaction by header name and by `--secret` value; the secrets gate on every push; placeholders in documentation |
| **Detection** | The secrets check in `validate.py`; a scanner; a reader noticing |
| **Response** | Rotate first, investigate second, record the incident without reproducing the value |
| **Limitation** | Redaction covers what the tool was told about. A credential in a response body that was never named with `--secret` is stored as received. Inspect anything before sharing it — the tool will not catch what it was not told |

## T-12 — Unauthorized target selection

| | |
|---|---|
| **Impact** | The worst outcome in this list, because the harm lands on someone who never agreed to anything. A scan of a system nobody authorized is not a mistake in a report; it is the event the report was supposed to prevent |
| **Prevention** | A scope file derived from the authorization rather than from memory; exclusions; validation before the run; the stop conditions |
| **Detection** | The scope decision on every response; a host that does not appear in the authorization record |
| **Response** | Stop immediately, notify the authorizer, and treat it as a disclosure matter rather than a testing matter |
| **Limitation** | **The tool cannot tell an authorized target from an unauthorized one.** It checks the scope file it was given. Every prevention in this row is a human process, and this threat is the reason the governance layer exists at all |

## What the threats have in common

Read the limitations column straight down, and a pattern appears: **almost every
limitation is the same limitation.** The framework checks an assertion; it cannot
check the mandate behind it. Scope, window, targets, exclusions, approval
references — all of them are recorded from what a person said, and the tool
verifies their arithmetic and their internal consistency, never their truth.

That is not a defect to be fixed. A tool cannot verify that someone is entitled to
authorize a system, because entitlement is not visible from inside a request. What
a tool *can* do is refuse to make the situation worse: gate every request, record
what it did, refuse what it must not do, and stop rather than improvise.

That is what this framework does, and the governance layer above it is what makes
the human checks real.

## Residual risk, stated plainly

After every prevention in this document is in place, the following remain:

1. **An operator who asserts an authorization they do not hold will not be caught
   by the tool.**
2. **An administrator who changes the code can remove a control**, and the only
   check is review of the diff.
3. **A forger who rewrites a bundle and its manifest defeats hash verification.**
4. **Emergency procedures decay into routine** unless someone reviews the pattern.
5. **Redaction is only as complete as what the tool was told.**
6. **The independent security review of the workbench remains outstanding** — see
   [`../workbench/INDEPENDENT-SECURITY-REVIEW.md`](../workbench/INDEPENDENT-SECURITY-REVIEW.md).

None of these is closed by documentation. Naming them is what makes the rest of
this document usable.
