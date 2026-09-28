# Glossary

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

Terminology used across the framework, defined once. Every entry below is a term
this repository actually uses; where a term has a common but looser usage in
general security work, that difference is noted, because the loose usage is
frequently where reporting errors originate.

---

## Assessment framing

**Attack surface** — Every reachable interface through which an untrusted actor
can influence system state or cause the system to return data. Includes HTTP
endpoints, deep links, exported mobile components, file parsers, message
consumers, and any vendor API the application will call.

**Attack chain** — A sequence of two or more individually-weaker findings whose
combination produces impact greater than the sum. Recorded as
`Finding A + Finding B → combined impact`, and only when every link is
evidence-supported. See `AGENT.md` §22.

**Attack hypothesis** — A testable proposition that a control may be
violated. Explicitly *not* a finding. A hypothesis is promoted to a finding
only through evidence.

**Trust boundary** — A point where data or control crosses from a lower-trust
context to a higher-trust one (anonymous user to authenticated user, client to
server, application to database, application to vendor). Testing is directed at
boundaries, not at endpoints in general. See `AGENT.md` §6.

**Enforcement point** — The specific location where a security decision is
actually made: UI, mobile client, gateway, API, service, database policy,
signed URL, or a payment/entitlement provider. Naming it is what makes a
finding actionable, because it identifies where the fix belongs. See
[`guides/REMEDIATION-AND-RETEST.md`](guides/REMEDIATION-AND-RETEST.md).

**Security property** — The statement of what *should* be enforced, written
before testing. Examples: "only the owner may modify this record"; "a premium
feature requires an active entitlement". A test either upholds or violates a
stated property; one that tests nothing specific is not a test.

**Security boundary failure** — The point at which the system's actual behaviour
diverges from its stated security property. Distinct from the weakness that
caused it and from the impact that follows it.

**Proof strength** — How much of the claim the evidence actually carries, from
a code indicator through a reproduced request to a validated artifact. A
stronger proof narrows what must be written as assumption. Used in
`modes/ZERO-CREDENTIAL-ESCALATION-MODE.md`.

**Differential testing** — Comparing behaviour between two states, actors, or
endpoints to isolate what a change actually altered: baseline versus
manipulated, role A versus role B, UI path versus direct API path. See
`modes/ZERO-CREDENTIAL-ESCALATION-MODE.md`.

**Method escalation** — The rule that a failed technique closes *that technique*
only, never the security objective. Having exhausted one approach, the
assessor changes method rather than declaring the area safe. Central to
`modes/ZERO-CREDENTIAL-ESCALATION-MODE.md` and `AGENT.md` §7.

**Coverage control** — Tracking what was actually tested, what was not, and why,
so that an untested area is never silently read as a safe one. See
`modes/ZERO-CREDENTIAL-ESCALATION-MODE.md` and
[`templates/COVERAGE-MATRIX.md`](../templates/COVERAGE-MATRIX.md).

**Negative result** — A hypothesis that was properly tested and did not
reproduce. Recorded as evidence that a control exists, not as an absence of
findings. See [`guides/OPERATING-RULES.md`](guides/OPERATING-RULES.md) Rule 12.

---

## Evidence and status

**Evidence status taxonomy** — The six-status system that every material claim
must use: `CONFIRMED`, `PARTIALLY CONFIRMED`, `UNVERIFIED`, `NOT TESTED`,
`NOT VULNERABLE`, `OUT OF SCOPE`. Defined in `AGENT.md` §5.

**CONFIRMED** — Direct evidence demonstrates the weakness and its stated impact.
Both halves are required; demonstrating the weakness without its impact does
not produce a confirmed impact claim.

**PARTIALLY CONFIRMED** — The weakness is demonstrated but a material part of
the impact chain is not. Rated at the demonstrated stage only.

**UNVERIFIED** — A credible hypothesis or indicator without sufficient proof.
Never severity-rated, never counted as a finding.

**NOT TESTED** — Testing could not or did not occur. A coverage fact, not a
risk judgement. Must name the exact blocking capability.

**NOT VULNERABLE** — The behaviour was tested with sufficient coverage and the
control held *under the tested conditions*. Never stated as a universal claim.

**OUT OF SCOPE** — Excluded by authorization or assessment boundary. The asset
is recorded; no active testing was performed.

**Severity** — Rated from demonstrated impact and reach, on a five-level scale,
and bounded by evidence status. Defined in
[`guides/SEVERITY-RATING.md`](guides/SEVERITY-RATING.md). Note that severity
and status are different axes: status is what the evidence proves, severity is
how much it matters.

**Evidence hierarchy** — The framework's preference order for proof: direct
server responses, then actual state changes, then actual protected-resource
access, then actual downloaded artifacts, then reproducible sequences, then
source/configuration evidence, then screenshots. Defined in
[`guides/EVIDENCE.md`](guides/EVIDENCE.md).

**Minimum necessary evidence** — Collect only what proves the security
property, and no more. Reduces exposure of real users and real data while
remaining sufficient. See [`guides/OPERATING-RULES.md`](guides/OPERATING-RULES.md)
Rule 9.

**Redaction** — Removing credentials, tokens, secrets, and unnecessary personal
data from an artifact while retaining enough context to prove the issue.

**Canary / synthetic record** — A deliberately identifiable test record or
identity used to establish that observed data is real, in preference to
enumerating genuine production records. Preferred first choice under
`AGENT.md` §14.

**Redundant coverage** — Testing a boundary that has already been proven at a
different entry point, without adding a distinct hypothesis. Discouraged: it
consumes effort without evidence gain.

---

## Authorization and scope

**Scope hierarchy** — The order of authority governing what may be tested:
explicit user-provided scope, then written authorization, then identified
systems, then discovered technical relationships. A discovered relationship does
not create authorization. See [`guides/SCOPE.md`](guides/SCOPE.md).

**Third-party classification** — Every external dependency is labelled
`AUTHORIZED THIRD-PARTY`, `DEPENDENCY / OBSERVATION ONLY`, or `OUT OF SCOPE`.
A vendor API seen in application traffic is never automatically testable.

**Synthetic identity** — An account created for testing rather than borrowed
from a real user, used wherever the engagement permits it.

**Authorization** — The decision that a specific actor may perform a specific
action on a specific object. Distinct from authentication, which establishes
*who* the actor is. See [`guides/AUTH-AUTHZ.md`](guides/AUTH-AUTHZ.md).

**Horizontal authorization** — Access boundaries *between* peers: user A acting
on user B's objects.

**Vertical authorization** — Access boundaries *between roles*: a normal user
acting on an administrative function.

---

## Weakness classes

**BOLA / IDOR** — Broken Object Level Authorization, also known as Insecure
Direct Object Reference. The application does not verify that the caller may
access the *specific object* requested, so changing an identifier returns
another user's object. Mapped to CWE-639 and OWASP API1.

**BFLA** — Broken Function Level Authorization. A normal user reaches a
function that should be restricted by role, typically administrative. Mapped to
OWASP API5.

**Mass assignment** — The API accepts and binds client-supplied fields that
should never be client-controlled, such as `role`, `is_admin`, `price`, or
`user_id`. Mapped to CWE-915 and OWASP API3.

**Parameter tampering** — Modifying a value the client was not meant to control,
including hidden form fields and identifiers the UI presents as fixed. Mapped
to CWE-472.

**Type confusion** — Supplying a value of an unexpected type or shape that the
server processes differently from the intended one.

**Replay** — Re-submitting a previously valid request, token, callback, or
signed URL after its state should have invalidated it. Mapped to CWE-294 for
authentication tokens.

**Race condition** — A security-relevant outcome that depends on the ordering of
concurrent operations. Mapped to CWE-362.

**TOCTOU** — Time-of-check to time-of-use: a state validated at one moment and
relied upon later, after it has changed. Mapped to CWE-367.

**Server-side enforcement** — A control applied by the server, API, service, or
database rather than by the client. Client-side enforcement is advisory only,
because the client is attacker-controlled. See
[`guides/OPERATING-RULES.md`](guides/OPERATING-RULES.md) Rule 7.

**State machine** — A model of a workflow as explicit states and the permitted
transitions between them — for example `DRAFT → CREATED → PAID → VERIFIED →
ENTITLED → DELIVERED`. Business-logic testing asks whether a transition can be
skipped, reordered, replayed, or re-bound. See
[`guides/BUSINESS-LOGIC.md`](guides/BUSINESS-LOGIC.md).

---

## Payment, entitlement and delivery

**Entitlement** — The server-side record that a specific identity is entitled to
a specific paid product or feature. Distinct from the client's belief about
access, and the value at which a payment weakness becomes an access weakness.

**Premium access** — Functionality gated behind an entitlement. Verified
separately from entitlement creation, because a granted entitlement does not
prove the gated functionality was actually reached.

**Entitlement bypass** — Premium access obtained without the entitlement
condition being satisfied. A stronger claim than a payment-verification
weakness, and requiring its own evidence.

**Signed URL** — A time-limited URL carrying a cryptographic signature that
grants access without per-request authorization. Secure only while the TTL is
short, the signature is bound to the intended object and identity, and the URL
becomes invalid when the underlying authorization changes.

**Payment verification** — Establishing, from a trusted source, that payment
actually succeeded for the expected amount. Never a client-declared status and
never an unauthenticated callback.

**Webhook / callback** — A server-to-server notification from a payment
provider. Must have its signature verified over the raw payload, its timestamp
checked for freshness, and its state transition made idempotent.

**Chain stages** — The framework's standard assessment order for paid products:
`price → order → payment → verification → entitlement → premium access →
download authorization → artifact delivery`. A finding is rated at the highest
stage *actually demonstrated*. See
[`guides/PAYMENT-PREMIUM-TESTING.md`](guides/PAYMENT-PREMIUM-TESTING.md) and
`AGENT.md` §12.

**Artifact** — A real, actually-obtained protected file. Validated by real
filename, real content type, real byte size, and a real computed SHA-256. The
framework forbids substituting a dummy file for a missing one.

---

## Mobile

**Exported component** — An Android activity, service, receiver, or provider
reachable by other applications. An exported component is *attack surface*, not
a vulnerability, until a harmful path is demonstrated.

**Deep link** — An external URL that launches the application into a specific
screen or action. A deep link that reaches a privileged action without an
authorization check is a real finding. Mapped to CWE-939.

**WebView** — An embedded browser component. Security-relevant configuration
includes JavaScript enablement, JavaScript bridge exposure, file access, origin
restrictions, and cookie availability.

**JavaScript bridge** — A native method exposed to web content inside a WebView.
A bridge reachable from attacker-influenced content is a control-flow path into
native code, not merely a configuration weakness.

**Static analysis** — Assessment of an application without executing it. It
establishes what code *exists*, not what it *does at runtime*. Static indicators
alone do not prove runtime exploitability; see
[`guides/TOOL-AND-ENVIRONMENT.md`](guides/TOOL-AND-ENVIRONMENT.md).

**Runtime analysis** — Assessment of behaviour during execution. Where a runtime
environment is unavailable, the limitation must be stated rather than papered
over by a static claim.

---

## Process and integrity

**Non-fabrication rule** — Never invent evidence of any kind: files, hashes,
responses, transaction IDs, screenshots, or exploitation results. A complete
report with unverified areas is preferred over a false one. See `AGENT.md` §27.

**Tool honesty** — Never claim to have used a tool that was unavailable or was
not actually run. Where a substitute method was used, state the substitution
and its limitation. See
[`guides/TOOL-AND-ENVIRONMENT.md`](guides/TOOL-AND-ENVIRONMENT.md).

**Controlled aggressiveness** — Testing as an attacker would, within the
authorized boundary, while minimising real-world effect on users, systems, and
third parties. Aggression toward the target is not licence to be careless
toward the data.

**Rate limit / throttling** — Server-side limits on request frequency. Tested
deliberately and within bounds: `AGENT.md` §19 forbids turning an assessment
into an uncontrolled denial-of-service event.

**Lockout** — The server's response to repeated failed authentication attempts.
An observed lockout is a control that worked and belongs in negative results.

**Regression test** — A binary, runnable test confirming a fix holds at the
enforcement point. Built from the original reproduction so it can be executed
by someone who was not present. See
[`guides/REMEDIATION-AND-RETEST.md`](guides/REMEDIATION-AND-RETEST.md).

**Cannot verify** — A retest outcome meaning the environment prevented testing.
The finding stays open. It is not a pass, and not a downgrade.
