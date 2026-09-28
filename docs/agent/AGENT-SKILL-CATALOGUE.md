# Agent Skill Catalogue

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`AGENT-OPERATING-PROTOCOL.md`](AGENT-OPERATING-PROTOCOL.md) · [`../AGENT.md`](../../AGENT.md) · [`../docs/SKILLS.md`](../SKILLS.md)

## What a skill is here

A skill is a **named, repeatable procedure with a defined trigger, a defined
output, and a defined stop condition**. It is the unit an operator invokes and
the unit an agent selects.

A skill is not a payload, a scanner invocation, or a fixed sequence of requests.
It is a method: what to establish, what to vary, what to observe, and — equally
important — **when to stop and what the result is allowed to claim**.

Every skill below is bounded by the engagement's written authorization. A skill
describes how to reason and what to measure; it never grants permission.

## Skill record format

```text
SKILL ID          : unique identifier
TRIGGER           : the observation that should invoke this skill
PROCEDURE         : the method
OUTPUT            : what the skill produces
MAX CLAIM         : the strongest status the output can support
STOP              : when to stop, even if no result yet
COMMON FAILURE    : the mistake this skill is designed to prevent
```

---

## Group A — Scope and boundary

### A1 · Scope gate
**Trigger:** Before any active interaction with any host.
**Procedure:** Confirm the host against `allowed_assets`. Classify it as
`AUTHORIZED THIRD-PARTY`, `DEPENDENCY / OBSERVATION ONLY`, or `OUT OF SCOPE`.
If unclassified, treat as out of scope.
**Output:** Classification recorded.
**Max claim:** N/A — a control step.
**Stop:** Any host not explicitly listed stops the engagement on that host.
**Common failure:** Treating a discovered subdomain or vendor endpoint as in
scope because the target talks to it.

### A2 · Third-party boundary
**Trigger:** A request would cross to a provider, CDN, payment processor, or
external identity service.
**Procedure:** Name the provider. Confirm whether the authorization document
names it. If not, record as dependency and do not test.
**Output:** Dependency register entry.
**Max claim:** N/A.
**Stop:** Immediate, on any unconfirmed third party.
**Common failure:** "It's the app's own payment provider, so it's in scope."
It is not, unless the authorization says so.

### A3 · Pre-flight authorization check
**Trigger:** Every action class, per
[`AGENT-OPERATING-PROTOCOL.md`](AGENT-OPERATING-PROTOCOL.md) §3.
**Procedure:** Run the eight-item checklist.
**Output:** Recorded pass/fail.
**Stop:** Any unticked box blocks the request.
**Common failure:** Skipping because the target "looks clearly in scope."

### A4 · Destructive-action gate
**Trigger:** A proposed action could delete, corrupt, lock out, disable, or
otherwise damage state.
**Procedure:** Determine whether destruction is authorized, for which assets,
and with what limit. If not authorized, find the strongest non-destructive
equivalent and use it.
**Output:** Authorization basis, or the substitute method used.
**Stop:** If no non-destructive equivalent exists and destruction is not
authorized, the boundary is `NOT TESTED`.
**Common failure:** Breaking a user's account to prove an authorization flaw.

### A5 · Data-minimisation gate
**Trigger:** Personal, financial, or production data is reachable.
**Procedure:** Determine the minimum record set that proves the boundary. Stop
broad collection. Prefer synthetic or canary data.
**Output:** Minimum-necessary record count, stated.
**Stop:** Stop enumeration as soon as the boundary is proven.
**Common failure:** Listing a table to demonstrate a point. That is data
collection, not security testing.

---

## Group B — Discovery

### B1 · Zero-credential surface mapping
**Trigger:** Start of any assessment, before authenticated testing.
**Procedure:** Enumerate what an unauthenticated actor can reach — public
endpoints, anonymous read paths, enumeration, signup flows, unauthenticated
API surface, robots/sitemap, and public artifacts.
**Output:** Anonymous-reachable asset inventory with status per entry.
**Max claim:** `NOT VULNERABLE` for anything tested clean; `UNVERIFIED` for
anything merely observed.
**Stop:** On rate limits or any stability signal.
**Common failure:** Moving to authenticated testing while the anonymous surface
is still unmapped.

### B2 · Endpoint inventory
**Trigger:** Application or API surface identified.
**Procedure:** Build a table: endpoint, method, authentication, authorization,
inputs, state change, sensitive output, tested, result. Include endpoints found
in client code that are not linked from the UI.
**Output:** Inventory table.
**Stop:** When the inventory stops producing new endpoints across a full pass.
**Common failure:** Only documenting endpoints reachable by clicking.

### B3 · Client–server divergence
**Trigger:** A mobile app, SPA, or thick client is in scope.
**Procedure:** Compare what the client believes about security against what the
server enforces. Extract embedded endpoints, hidden fields, and client-side
gates, then test each server-side directly.
**Output:** List of client assumptions with server-side test results.
**Max claim:** A client-side check found without server testing is `UNVERIFIED`.
**Stop:** When no further divergence is found.
**Common failure:** Reporting a hidden field as a vulnerability when the server
ignores it.

### B4 · Attack-surface graph
**Trigger:** Inventory substantially complete.
**Procedure:** Model assets and trust boundaries as nodes and edges. Identify
where attacker-influenced data crosses a boundary and where enforcement is
absent or duplicated.
**Output:** Graph with candidate entry points ranked.
**Stop:** When the graph stops yielding new entry points.
**Common failure:** Treating the graph as decoration. It exists to prioritise.

### B5 · Technology fingerprint
**Trigger:** Early phase.
**Procedure:** Identify frameworks, versions, protocols, auth schemes, and
third-party services. Record only what is directly observable.
**Output:** Fingerprint with evidence.
**Max claim:** Never a version-based vulnerability claim without confirmation
that the version is in use at the assessed component.
**Stop:** No fixed end — bounded by rate limits.
**Common failure:** Inferring a version from a header and asserting the
matching CVE.

---

## Group C — Authentication and authorization

### C1 · Horizontal boundary test (BOLA/IDOR)
**Trigger:** An object identifier exists in a request.
**Procedure:** Establish ownership. Substitute a second authorized identity's
identifier. Compare the response. Repeat across object types and endpoints.
**Output:** Per-boundary result with request/response evidence.
**Max claim:** `CONFIRMED` for the specific object type tested.
**Stop:** After establishing the pattern across the surface; do not enumerate.
**Common failure:** Claiming IDOR from a single successful substitution without
establishing that the second identity did not legitimately own the object.

### C2 · Vertical boundary test (BFLA)
**Trigger:** A role-restricted function exists.
**Procedure:** Invoke it directly as a lower-privileged authorized role. Test
both the endpoint and any alternate path to the same capability.
**Output:** Per-function result.
**Max claim:** `CONFIRMED` for the function tested.
**Stop:** After covering the role set in scope.
**Common failure:** Testing only the UI path, which the UI already blocks.

### C3 · Field-level authorization (mass assignment)
**Trigger:** A request binds client-supplied fields to a persistent object.
**Procedure:** Attempt to set fields that should be server-controlled —
`role`, `is_admin`, `price`, `user_id`, `status`, ownership fields. Observe
which are honoured.
**Output:** Field acceptance/rejection table.
**Max claim:** `CONFIRMED` for accepted fields with observed effect.
**Stop:** Once the field set is characterised.
**Common failure:** Reporting accepted-but-ignored fields as a finding.

### C4 · Session lifecycle test
**Trigger:** A session or token mechanism exists.
**Procedure:** Test registration, login, issuance, refresh, rotation,
revalidation, logout invalidation, expiry, and recovery — as a lifecycle, not
just login.
**Output:** Per-stage result.
**Stop:** On lockout; lockout is a working control, record it as a negative
result.
**Common failure:** Testing login only.

### C5 · Token substitution
**Trigger:** More than one authorized identity is available.
**Procedure:** Use identity A's token against identity B's objects and vice
versa. Test whether tokens are bound to identity, role, and session.
**Output:** Binding matrix.
**Stop:** After the binding model is clear.
**Common failure:** Assuming a valid token is a valid token for that object.

### C6 · Enforcement-point confirmation
**Trigger:** A control appears to be enforced somewhere.
**Procedure:** Determine whether enforcement is at UI, client, gateway, API,
service, database, or provider. Test the resource directly at each layer.
**Output:** Enforcement-point map.
**Max claim:** A control that exists only client-side is not a control.
**Stop:** When the enforcement layer is identified.
**Common failure:** Accepting a UI restriction as a server control.

---

## Group D — Business logic and state

### D1 · State machine extraction
**Trigger:** A multi-step workflow exists.
**Procedure:** Enumerate states and permitted transitions from observed
behaviour. Build the model. Mark every transition.
**Output:** State diagram.
**Stop:** When no new states or transitions appear.
**Common failure:** Modelling the intended workflow instead of the implemented
one. Test what the system actually permits.

### D2 · Transition skip test
**Trigger:** State model exists.
**Procedure:** For each transition, attempt to reach the next state without
completing the previous. Call the later-stage operation directly.
**Output:** Per-transition result.
**Max claim:** `CONFIRMED` for the specific transition bypassed.
**Stop:** After all transitions are attempted.
**Common failure:** Calling a skipped state change a compromise without showing
what the state now grants.

### D3 · Replay and reordering
**Trigger:** Requests carry a state token, nonce, or timestamp.
**Procedure:** Replay a prior valid request. Reorder a sequence. Reuse a token
after the state has changed.
**Output:** Replay results.
**Stop:** On rate limits.
**Common failure:** Replaying once and concluding "replay is possible" without
showing what the replayed action achieved.

### D4 · Concurrency test
**Trigger:** A security-relevant action depends on prior state.
**Procedure:** Where authorized and safe, issue concurrent or near-simultaneous
requests against the same object to test for a check-then-act gap.
**Output:** Observed outcome with both request sets preserved.
**Max claim:** `UNVERIFIED` unless an actual inconsistent outcome is observed.
**Stop:** Immediately on instability. Bounded concurrency only.
**Common failure:** Claiming a race condition from code reading alone. That is a
hypothesis, and it stays one until demonstrated.

### D5 · Cross-tenant substitution
**Trigger:** Multi-tenant or multi-customer data exists.
**Procedure:** As an authorized identity in tenant A, request tenant B's objects
by identifier, by reference, and by indirect reference.
**Output:** Cross-tenant results.
**Stop:** Prove the boundary failure with one object; do not enumerate.
**Common failure:** Downgrading a cross-tenant exposure to Medium because "only
one tenant was affected."

---

## Group E — Payment, entitlement and delivery

The framework's most specialised area, and the most frequently mis-reported.

### E1 · Chain decomposition
**Trigger:** Any payment or paid content in scope.
**Procedure:** Enumerate every stage: `price → order → payment → verification →
entitlement → premium access → download authorization → artifact`. Record the
actual implementation of each.
**Output:** Stage-by-stage implementation map.
**Stop:** Before any active payment testing begins.
**Common failure:** Testing the whole chain as one pass, so no stage can be
attributed.

### E2 · Price integrity
**Trigger:** A price is accepted from the client, or computed from
client-influenced values.
**Procedure:** Manipulate price, quantity, discount, and currency individually,
then in combination. Determine what the server does with each.
**Output:** Per-field manipulation results.
**Max claim:** `CONFIRMED` input-integrity weakness. **Never** "payment
bypass" from this skill alone.
**Stop:** After each field is characterised.
**Common failure:** Collapsing "price accepted" into "payment bypass," which
is a different and stronger claim requiring its own evidence.

### E3 · Order and payment binding
**Trigger:** A payment references an order.
**Procedure:** Attempt to bind a payment to a different order, a different
user's order, or a second instance of the same order.
**Output:** Binding test results.
**Max claim:** `CONFIRMED` for the binding stage tested.
**Stop:** When the binding model is established.
**Common failure:** Reporting an order mismatch as a full payment bypass.

### E4 · Payment state verification
**Trigger:** A payment state is set or trusted.
**Procedure:** Determine the source of truth for payment status. Test whether a
client-declared status is honoured, whether a callback is signature-verified,
whether timestamps are checked, and whether transitions are idempotent.
**Output:** State-source map and test results.
**Stop:** Once the trust chain is proven or broken.
**Common failure:** Accepting an unsigned or replayable callback as valid
payment.

### E5 · Entitlement binding and scope
**Trigger:** Entitlements are created.
**Procedure:** Test whether entitlement is bound to the paying identity, scoped
to the specific product, revoked on refund or cancellation, and re-checked at
use time.
**Output:** Entitlement lifecycle results.
**Max claim:** `CONFIRMED` at the highest stage demonstrated only.
**Stop:** After the lifecycle is characterised.
**Common failure:** Reporting entitlement creation as equivalent to obtaining
the protected content.

### E6 · Download authorization
**Trigger:** Protected content is served.
**Procedure:** Test authorization at request time, not at URL issuance. Test
alternate download paths, URL replay, TTL enforcement, and behaviour after
entitlement removal.
**Output:** Per-path download authorization results.
**Max claim:** `CONFIRMED` download bypass.
**Stop:** Once a valid bypass is demonstrated; do not download repeatedly.
**Common failure:** Treating a successfully issued URL as a download bypass
without removing the entitlement and re-requesting.

### E7 · Artifact validation
**Trigger:** A protected artifact is actually obtained.
**Procedure:** Record real filename, content type, byte size, computed SHA-256,
acquisition timestamp and path, and entitlement state at acquisition. Confirm
content corresponds to the protected product.
**Output:** Artifact evidence block.
**Max claim:** `CONFIRMED` actual acquisition.
**Stop:** One artifact. Do not collect more.
**Common failure:** Substituting a placeholder file for a missing artifact.
Never, under any circumstance.

---

## Group F — Mobile

### F1 · Manifest and component analysis
**Trigger:** APK, AAB, or mobile source in scope.
**Procedure:** Extract the manifest. Enumerate exported components, intent
filters, permissions, and deep-link handlers.
**Output:** Component inventory with export status.
**Max claim:** An exported component is attack surface, not a vulnerability.
**Stop:** When the component set is enumerated.
**Common failure:** Reporting every exported component as a finding.

### F2 · Deep-link authorization
**Trigger:** A deep link or custom scheme exists.
**Procedure:** Trace each link to the component it launches. Determine whether
authorization is checked before the privileged action, not after.
**Output:** Per-link authorization result.
**Stop:** When all links are traced.
**Common failure:** Confirming the link works without confirming it
authorizes.

### F3 · WebView bridge analysis
**Trigger:** A WebView loads content.
**Procedure:** Enumerate JavaScript interfaces, file-access settings, origin
restrictions, and cookie availability. Determine whether the loaded content can
be influenced by an attacker.
**Output:** WebView risk assessment per instance.
**Max claim:** A dangerous configuration is `UNVERIFIED` until an
attacker-influenced content path is demonstrated.
**Stop:** When the configuration and its reachability are established.
**Common failure:** Reporting "JavaScript enabled in a WebView" as a finding.

### F4 · Local data exposure
**Trigger:** An app stores data locally.
**Procedure:** Examine databases, shared preferences, cache, external storage,
logs, and backup configuration for sensitive material.
**Output:** Storage inventory with findings.
**Max claim:** `CONFIRMED` only for data actually observed at rest.
**Stop:** When storage paths are exhausted.
**Common failure:** Assuming a value is stored in a particular location without
confirming it.

### F5 · Runtime-availability substitution
**Trigger:** No emulator, device, or runtime is available.
**Procedure:** Fall back to static analysis. Record explicitly that runtime
behaviour is unproven, and list the conclusions the fallback cannot support.
**Output:** Static findings with a stated limitation.
**Max claim:** Static findings cannot establish runtime exploitability.
**Stop:** No substitution claim about runtime is permitted.
**Common failure:** Quietly implying a runtime result from static evidence.

---

## Group G — AI and agentic systems

Full procedure in [`../guides/AGENTIC-AI-SECURITY.md`](../guides/AGENTIC-AI-SECURITY.md).

### G1 · Agent capability inventory
**Trigger:** Any system invoking an LLM, or any agent with tool access.
**Procedure:** Enumerate every tool, function, API, datastore, and external
service the agent can reach, with the permission scope of each. Record the
model version, the system prompt location, and any memory or retrieval store.
**Output:** Capability and permission map.
**Stop:** This skill precedes all others in the group.
**Common failure:** Testing the chat interface and missing that the real surface
is the tool set.

### G2 · Prompt injection — direct
**Trigger:** Untrusted input reaches the model.
**Procedure:** Test whether user-controlled text can override system
instructions. Vary framing, role assertion, and instruction priority.
**Output:** Injection results.
**Max claim:** `CONFIRMED` only where a policy boundary demonstrably fails.
**Stop:** On unbounded generation or cost; bound immediately.
**Common failure:** Reporting a model producing an odd response as an
injection. A jailbreak is only a finding if it defeats a control.

### G3 · Prompt injection — indirect
**Trigger:** The agent processes untrusted external content — documents, web
pages, email, tool output, retrieved records.
**Procedure:** Place controlled payloads in each such channel and observe
whether the agent treats retrieved text as instruction.
**Output:** Per-channel injection results.
**Max claim:** `CONFIRMED` where the agent acts on injected instruction.
**Stop:** Per channel, after establishing behaviour.
**Common failure:** Testing only the user input and missing every retrieval
channel, which is where the serious cases live.

### G4 · Tool-call boundary test
**Trigger:** The agent can invoke tools.
**Procedure:** Attempt to induce calls outside intended sequence, with
manipulated parameters, to unintended targets, and in combinations the design
did not anticipate. Test whether authorization is enforced at the tool layer
or merely described in the prompt.
**Output:** Tool invocation abuse results.
**Max claim:** `CONFIRMED` where an unauthorized action demonstrably occurred.
**Stop:** Immediately on any real-world effect — no transactions, no sends, no
deletions without explicit authorization.
**Common failure:** Treating a control that exists only in the system prompt as
an enforced control.

### G5 · Excessive agency assessment
**Trigger:** Tool access is confirmed.
**Procedure:** Assess functionality, permissions, and autonomy separately.
Identify capabilities the agent holds but does not need.
**Output:** Least-privilege gap analysis.
**Max claim:** A design weakness, not a vulnerability, until an abuse path is
demonstrated.
**Stop:** When the capability set is characterised.
**Common failure:** Reporting broad permissions as a vulnerability without
showing the abuse path.

### G6 · Retrieval authorization test
**Trigger:** The system retrieves documents or records.
**Procedure:** As a low-privilege identity, attempt to retrieve content scoped
to a higher-privilege identity or another tenant, by direct query and by
induced disclosure.
**Output:** Cross-tenant retrieval results.
**Max claim:** `CONFIRMED` for content actually returned across a boundary.
**Stop:** On the first cross-boundary retrieval. Do not enumerate the corpus.
**Common failure:** Assuming retrieval inherits the requesting user's
permissions.

### G7 · Memory persistence test
**Trigger:** The agent retains state across sessions.
**Procedure:** Plant content in one session, then verify in a later session
whether it changed behaviour. Determine whether attacker-influenced content
persists and re-fires.
**Output:** Persistence result.
**Max claim:** `CONFIRMED` only if the planted content demonstrably altered
later behaviour.
**Stop:** After establishing whether persistence occurs.
**Common failure:** Claiming persistence from a single session.

### G8 · Output handling test
**Trigger:** Model output reaches a renderer, an interpreter, or a downstream
system.
**Procedure:** Determine whether output is treated as data or as code. Where
output is executed or rendered, test injection through it.
**Output:** Output handling findings.
**Max claim:** `CONFIRMED` where injected output executed or rendered.
**Stop:** Before executing anything with side effects.
**Common failure:** Assessing the model and never assessing what happens to its
output.

### G9 · Resource and cost bounds
**Trigger:** Any LLM-backed endpoint reachable.
**Procedure:** Confirm request limits, iteration limits, and cost controls
exist. Test bounded — never unbounded.
**Output:** Limit verification.
**Max claim:** Absence of limits is a design weakness unless demonstrated to
cause material impact.
**Stop:** **Hard stop.** This is never stress-tested. Bound every request.
**Common failure:** Any form of load or cost testing against a third-party
model endpoint.

---

## Group H — Evidence and reporting

### H1 · Evidence capture
**Trigger:** Every significant test.
**Procedure:** Capture raw request, raw response, state before, state after,
timestamps, and artefacts — before interpretation.
**Output:** Numbered evidence files linked to the test ID.
**Stop:** Minimum necessary; stop when the property is proven.
**Common failure:** Interpreting first and recording the expectation afterwards.

### H2 · Status assignment
**Trigger:** A test completes.
**Procedure:** Map the observed situation through
[`../guides/DECISION-MATRIX.md`](../guides/DECISION-MATRIX.md). When unsure,
take the lower status and state the missing proof.
**Output:** Status with rationale.
**Max claim:** The status assigned, no higher.
**Stop:** N/A.
**Common failure:** Upgrading to `CONFIRMED` because the finding feels
significant.

### H3 · Severity rating
**Trigger:** A `CONFIRMED` or `PARTIALLY CONFIRMED` finding.
**Procedure:** Apply the impact × reach rubric and complete the worksheet.
Check the evidence ceiling.
**Output:** Severity with written rationale.
**Max claim:** The level the evidence permits.
**Stop:** N/A.
**Common failure:** Rating the theoretical ceiling rather than the demonstrated
effect.

### H4 · Coverage accounting
**Trigger:** Continuously, and at engagement end.
**Procedure:** Keep the coverage matrix current. Every boundary is tested,
partial, untested with a blocker, out of scope, or dependency-blocked.
**Output:** Coverage statement.
**Stop:** N/A.
**Common failure:** Deleting a row because it looks bad. It stays, with the
reason.

### H5 · Remediation specification
**Trigger:** A confirmed finding.
**Procedure:** Identify the enforcement point, state the root cause, specify
the class-level fix, and write a runnable binary regression test.
**Output:** Remediation and regression test.
**Stop:** N/A.
**Common failure:** Recommending input validation for a business-logic defect.

### H6 · Chain documentation
**Trigger:** Two or more findings may combine.
**Procedure:** Map each link with its own evidence and prerequisites. State
which links were walked and which were not.
**Output:** Chain diagram.
**Max claim:** The strongest link actually walked.
**Stop:** N/A.
**Common failure:** Presenting an arithmetic combination as a demonstrated
breach.

---

## Selecting and composing skills

```text
Engagement starts
  → A1, A2, A3, A4, A5   scope and boundaries, before anything active
  → B1                 anonymous surface
  → B2, B4, B5         inventory and graph
  → C*, D*, E*, F*, G* by target shape
  → B3                 client divergence, if a client exists
  → RED HEART          path construction across everything found
  → H1..H6             evidence through to report
```

**Skills compose by evidence, not by convenience.** A finding from C1 feeds
H6 for chain analysis. A result from E5 constrains what E6 may claim. Never
compose a claim from skills that have not both run.

## Extending the catalogue

A new skill must specify all six fields. A procedure without a stop condition
or a max claim is not a skill — it is a suggestion, and it will eventually be
executed without either bound.

See [`../CONTRIBUTING.md`](../../CONTRIBUTING.md) for contribution rules.
