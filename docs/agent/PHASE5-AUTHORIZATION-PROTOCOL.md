# Phase 5 authorization protocol

**For:** an AI agent, or a human operating one, before anything active
**Companion:** [`../../AUTHORIZATION-AGREEMENT.md`](../../AUTHORIZATION-AGREEMENT.md)
— the template an authorization is recorded in
**Sources:** the requirements are the framework's; the mechanism is
`workbench/scope.py` and `workbench/policy.py`

---

## 1. The three things that are not authorization

An agent's most consequential mistake is treating an incidental fact as
permission. These are stated first because they are the ones that get mistaken:

| Not authorization | Why not |
|---|---|
| **A written template** | Filling in `AUTHORIZATION-AGREEMENT.md` records an authorization somebody granted. It does not grant one. The document is a form, not a power |
| **A URL, a domain, or reachability** | Being able to address a system says nothing about who may test it. Every system on the internet has an address |
| **Public accessibility** | A public endpoint is public *to the extent its operator intends*. That intent is not permission for security testing, and "nobody stopped me" is not permission either |

Two more, because agents meet them constantly:

- **A person's claim of ownership** is a claim. It is not proof that they are
  entitled to authorize testing of that system.
- **Being employed to work on a system** does not put it in scope. The
  authorization determines scope, not the employment.

**The operator is responsible for obtaining valid authorization.** No tool in this
repository checks whether they did, and none can.

## 2. What must exist before an active operation

Four conditions. All of them, in this order, before the first request:

```text
1. A grant      A person or entity entitled to grant it has granted it, in writing
2. A target     The system is named in that grant
3. An action    What is about to be sent is inside what the grant permits
4. A record     The operator has written it into a scope file the workbench accepts
```

If any one is missing, the correct action is **stop** — not a smaller scan, not a
read-only probe of the same target to "check it is up".

### The framework's two gates, which are separate

| Requirement | Command | Establishes | Enforced at |
|---|---|---|---|
| Policy acceptance | `blackheart policy accept` | The rules were read on that machine | The first statement of `http_client.request()` |
| Target authorization | a scope file passed as `--scope` | The operator asserts an authorization, with hosts, methods, budget and window | `scope.require()`, below the policy gate, on every request |

```bash
python3 -m workbench.cli policy status                     # accepted, and current?
python3 -m workbench.cli policy accept                     # record that you read the version in front of you
python3 -m workbench.cli scope validate --scope scope.json # what will actually be enforced
```

**Acceptance does not authorize any target, and a scope file does not prove one.**
They are two different questions, and an agent must report them separately: "the
policy is accepted on this machine, and the operator's scope file asserts these
hosts" is honest. "Policy accepted, proceeding" is not.

## 3. The authorization record, field by field

The template at each point below is
[`../../AUTHORIZATION-AGREEMENT.md`](../../AUTHORIZATION-AGREEMENT.md). These are
the fields an agent should confirm exist and are filled, before it operates.

| Field | Why an agent needs it | What to check |
|---|---|---|
| Operator, organization, contact | Attribution, and who to call when something goes wrong | Named, and reachable during the window |
| Authorizing party, and their capacity | Whether the grant comes from someone entitled to give it | If a third party operates part of the target — hosting, payments, an API — their authorization may also be needed |
| Target name, URLs, hostnames, IP ranges | The perimeter the scope file will mirror | Every host the tool could reach is either listed or deliberately excluded |
| Environment (production / staging / lab) | Whether a mistake touches real users | Production testing needs a different conversation |
| Allowed paths, excluded paths | The boundary inside a host | Empty allowed-paths is not "everything"; read the scope model |
| Allowed and prohibited methods | Whether a request can change state | Write methods need explicit confirmation at the call site *and* a scope that permits them |
| Testing window, start and end | Authorization expires | A run that outlives the window is unauthorized from the moment it lapses |
| Request budget, rate limit, concurrency cap | Whether the target is at risk from volume | The tool enforces these; the values must come from the authorization, not from the tool's defaults |
| Data-handling requirements | What may be collected, kept, and where | Minimisation, retention, disclosure |
| Emergency contact and stop conditions | What to do when it goes wrong | Reachable during the window, not the day after |
| Approval, signature, reference | The evidence that authorization exists | Written, not verbal; the reference says where it is recorded |

**Two records, one scope.** The template and the scope file must agree. If they
disagree, stop and reconcile them; the tool enforces the file, not the document.

## 4. Before every request, not once per session

The checks below are cheap. Skipping one is how a run becomes unauthorized partway
through.

```text
[ ] policy status says accepted, and current
[ ] the scope file loads, and `scope validate` prints what I expect
[ ] this exact host is in the allowlist and not excluded
[ ] this exact path is inside the allowed paths and not excluded
[ ] this exact method is allowed by the scope
[ ] the request budget is not exhausted
[ ] the authorization window has not closed
[ ] the interval since the last request respects the rate limit
[ ] the target is not showing signs of strain
[ ] the operator has not cancelled
```

The realistic failure is not deciding to skip these. It is never noticing there
were any.

## 5. Stop conditions

Stop the affected action, preserve what exists, and report, when **any** of the
following is true:

- authorization cannot be verified, or the scope file cannot be read;
- the policy has not been accepted, or the acceptance has gone stale;
- the target is not in scope, or a redirect leaves scope;
- a request is refused by the scope file or by the target;
- the budget or the authorization window is exhausted;
- the target shows signs of strain, or the operator cancels;
- evidence fails verification;
- acquired content is executable or macro-bearing;
- anything happens that the agent does not understand.

**Stopping is always an acceptable outcome.** An agent reporting "I stopped because
X was unclear" has done its job. An agent that manufactures a finding to avoid
stopping empty-handed has failed it, and §"Prohibited behaviour" in
[`PHASE5-SAFETY-RULES.md`](PHASE5-SAFETY-RULES.md) says so.

## 6. What to do when authorization is unclear

Deterministic, so that two agents facing the same state reach the same answer:

```text
Authorization is unclear, or the four conditions are not all met
  ├─ Is the operation local and read-only?
  │    ├─ yes ──► proceed; the exemption is documented and tested
  │    └─ no
  │         ├─ the affected action stops, now
  │         ├─ everything already collected is preserved and hashed
  │         ├─ the reason is recorded verbatim, not paraphrased
  │         └─ the operator is told what would need to be true to continue
  └─ Do not: run a reduced version, run a "read-only" version of the same
     active check, retry with a different identity, or ask the target's own
     software whether it minds
```

Reducing scope on your own authority is still deciding about a target whose
authorization was unclear. That decision belongs to the person who granted it.

## 7. What the tool will and will not do for you

| | |
|---|---|
| **Will** | Refuse a request outside the recorded scope, and say which rule refused it |
| **Will** | Refuse every active operation while the policy has not been accepted or has gone stale |
| **Will** | Refuse a scope file containing a key that looks like a bypass, and refuse one with no request budget |
| **Will** | Record the refusal, its status and the authorized route, so the report shows what was declined |
| **Will not** | Verify that an authorization exists, or that the person who signed it was entitled to |
| **Will not** | Decide whether your use is lawful; that depends on your jurisdiction and your engagement |
| **Will not** | Widen scope on request. There is no flag, and a test asserts that no option string is named after a control it disables |

The last row is the point. An agent that needs a bypass to finish a task has been
given a task it must not finish.
