# Phase 5 agent overview

**For:** an AI agent, or a human operating one
**Read first:** [`README.md`](README.md) for the reading order, then this
**Sources:** every statement here is derived from the implementation in
`workbench/`, which is the source of truth

---

## 1. What BLACKHEART is

BLACKHEART Security Framework is a governed security-supply-chain framework for AI
agents: an instruction set, a mirror of third-party skills under audit, and — since
Phase 5 — a first-party workbench for authorised assessment work.

| Layer | What it is | Where |
|---|---|---|
| Instruction set | How an agent is expected to behave, and the rules that win conflicts | `AGENT.md`, `skills/conformance/SKILL.md` |
| Vendored mirror | Third-party skills, pinned and byte-identical, never modified | `skills/` |
| **Workbench** | First-party tooling that sends requests, records what it observed, and refuses what it may not do | `workbench/` |
| Policy | The rules, in prose and in machine-readable form | root `*.md`, `policy/` |

**It does not grant authorization, and no part of it can.** Possession of the
source, reachability of a URL, and public accessibility are not permission. See
[`../../SECURITY-RESEARCH-DISCLAIMER.md`](../../SECURITY-RESEARCH-DISCLAIMER.md).

## 2. What Phase 5 adds

The workbench: standard-library Python, no subprocess anywhere, no third-party
dependency, one command per capability. It records observations, refuses what it
may not do, and never turns an observation into a finding.

| Capability | Commands | Refuses |
|---|---|---|
| HTTP inspection, replay, comparison | `http inspect`, `http replay`, `http diff` | Off-scope hosts and methods, excluded paths, exhausted budgets, write methods without confirmation |
| Mutation and bounded fuzzing | `http mutate`, `http fuzz` | Mutations past the budget or rate limit; it never generates write verbs |
| API description reading | `api inspect`, `api discover` | Out-of-scope fetches; it calls nothing it finds |
| Web discovery | `web crawl`, `web scan` | Off-host links, off-scope paths, page and depth caps |
| Resource acquisition | `resource download` | `401`/`402`/`403`/`407`/`451`, paywalls, DRM and licence markers, challenges, expired signed URLs |
| Document and archive reading | `resource inspect`, `resource extract` | Traversal members, absolute paths, symlinks, device nodes, size/count/ratio/depth bombs, files that fail their own hash check |
| Emergency collection | `emergency collect` | Anything but `GET`/`HEAD`; budget `min(scope.max_requests, 20)` |
| Evidence and reporting | `evidence hash`, `evidence manifest`, `report generate` | Records that fail their own hash check are not counted |
| Policy | `policy validate`, `policy status`, `policy accept`, `policy show` | Active work until the policy is accepted and current |

Twenty-one commands. The count is asserted against the command parser rather than
typed. The full surface is in [`PHASE5-WORKBENCH-OPERATIONS.md`](PHASE5-WORKBENCH-OPERATIONS.md).

## 3. Read-only, or active

The dividing line is **a socket**. It decides which requirements apply, and it is
not a matter of judgement.

| | Read-only / local | Active / network |
|---|---|---|
| What it does | Parses, hashes, reads files already on disk, writes a report from records already collected | Opens a connection to a target |
| Examples | `policy *`, `scope validate`, `http diff`, `http mutate`, `resource inspect`, `resource extract`, `evidence hash`, `evidence manifest`, `report generate` | `http inspect`, `http replay`, `http fuzz`, `api discover`, `web crawl`, `web scan`, `resource download`, `emergency collect` |
| Policy acceptance required | **No** — the exemption exists so that analysing evidence someone else collected needs no authorization | **Yes** |
| Scope file required | **No** | **Yes** |
| Enforced at | Not at all: nothing is sent | The first statement of `http_client.request()`, which is the socket boundary |

The exempt list is published in `policy/BLACKHEART-POLICY.json` under
`exempt_operations`, and a test holds it against the command parser so that a
command requiring `--scope` cannot be described as exempt.

**What "read-only" does not mean:** that the output is harmless. `resource extract`
writes files to a directory you name. `report generate` writes target data into a
report. Neither sends a request; both can still expose what was collected.

## 4. The five statuses, and what they mean

Every evidence record carries exactly one, from `workbench/evidence.py`:

| Status | Means | What it does **not** mean |
|---|---|---|
| `OBSERVED` | Recorded from a real response, once | Not reproduced, not validated, not a finding |
| `POTENTIAL` | Looks like it might matter | Nothing is established. This is where the overwhelming majority of interesting observations stay |
| `INFERRED` | Derived from other observations rather than seen directly | The derivation is stated, and it is not evidence of the thing derived |
| `REPRODUCED` | A second matching observation was made | Still not a validated defect unless a person validated it, and still not a statement about impact |
| `UNVERIFIED` | Recorded, with no basis to say more | The honest default |

The permitted transitions are defined in the implementation, and reproduction is
the only path upward:

```text
POTENTIAL    -> REPRODUCED, UNVERIFIED, INFERRED
OBSERVED     -> REPRODUCED, INFERRED, UNVERIFIED
INFERRED     -> REPRODUCED, UNVERIFIED
REPRODUCED   -> UNVERIFIED
UNVERIFIED   -> REPRODUCED, INFERRED
```

Two rules follow, and an agent must not work around either:

- **A status is never promoted by argument.** `POTENTIAL` becomes `REPRODUCED` by
  a second observation, and by nothing else.
- **The language of confirmed defect is reserved.** A record that is not
  `REPRODUCED` may not contain "vulnerable", "vulnerability", "confirmed",
  "exploitable", "exploit works", "attack succeeded" or "proof of concept works" in
  its title, impact or observation. The record fails validation if it does.

An "observable response difference" is exactly that. It is not a vulnerability, and
reporting it as one is the failure this framework exists to prevent. See
[`PHASE5-EVIDENCE-PROTOCOL.md`](PHASE5-EVIDENCE-PROTOCOL.md).

## 5. Authorization and scope, in one paragraph each

**Authorization** is a permission held from a person or entity entitled to grant
it, recorded before anything active happens. The framework does not check it, and
cannot: the scope file is the operator's *assertion*, and the tool checks the
assertion's arithmetic, not its truth. The template is
[`../../AUTHORIZATION-AGREEMENT.md`](../../AUTHORIZATION-AGREEMENT.md); the
agent-side rules are
[`PHASE5-AUTHORIZATION-PROTOCOL.md`](PHASE5-AUTHORIZATION-PROTOCOL.md).

**Scope** is the machine-checked form of that authorization: allowed hosts, paths,
methods, budget, interval, window, exclusions. `require()` raises rather than
returning a flag, there is no bypass parameter, and a scope file containing a key
that looks like a bypass is refused outright. The model is documented field by
field in [`PHASE5-SCOPE-PROTOCOL.md`](PHASE5-SCOPE-PROTOCOL.md).

**Acceptance is not authorization.** `policy status` returning `accepted` means the
rules were read on that machine. It names no target and permits none. An agent that
reports "policy accepted, proceeding" as though it had established permission has
confused an acknowledgement with authority.

## 6. Acquisition and extraction, in one paragraph each

**Acquisition** obtains public resources, resources the operator is authorized to
access, and resources whose licence or terms permit it. An access control is a
stop: the status is recorded as `blocked`, **no file is written**, and the
authorised route is named — ask the owner, use the publisher's own access route,
cite the public metadata, or stop. Nothing substitutes a mirror, cache or proxy.
Full policy: [`../../DOWNLOAD-AND-ACQUISITION-POLICY.md`](../../DOWNLOAD-AND-ACQUISITION-POLICY.md).

**Extraction** reads what was obtained, and treats it as hostile input. Nothing is
executed, imported, installed or invoked — no macros, no binaries, no subprocess.
Traversal members, absolute paths, symlinks, hardlinks and device nodes are
refused; size, count, ratio, depth and file limits apply; and a file whose hash no
longer matches its manifest is refused **before** it is parsed. See
[`PHASE5-WORKBENCH-OPERATIONS.md`](PHASE5-WORKBENCH-OPERATIONS.md).

## 7. Emergency mode

Bounded, read-only collection for an incident already in progress: the target URL,
`/robots.txt` and `/.well-known/security.txt`. `GET` and `HEAD` are a module
constant rather than a parameter, and a test proves it over the module's own AST.
The budget is `min(scope.max_requests, 20)`. It is for **preserving evidence**, not
for exploiting anything, and uncertainty about authorization stops the operation
rather than escalating it.

## 8. Reporting

An agent reports what happened, in the terms the records use:

- observations separately from inferences, both labelled;
- the limitation of every observation, in the record's own words — do not trim
  them for the audience;
- what was **not** tested, and what the coverage caps left unexplored;
- every refusal, as a result rather than an absence of results;
- never the language of confirmed vulnerability for anything a person has not
  validated.

## 9. Limitations, stated plainly

- **The tool cannot verify authorization.** It checks the scope file's arithmetic.
  Whether the operator is telling the truth is beyond it, and beyond any tool.
- **Redaction covers what it was told about.** A credential in a body that was
  never named with `--secret` is stored as received.
- **Unknown parameters stay unknown.** A request body the framework cannot parse is
  reported as unparsed, not enumerated.
- **The TLS check is standard**, not pinned to a certificate.
- **Loops and single samples are single samples.** One response at one moment is
  one response at one moment.
- **The independent review is outstanding.** `docs/workbench/INDEPENDENT-SECURITY-REVIEW.md`
  records an adversarial self-review and states plainly that no separate reviewer
  has performed one.

The full list is `docs/workbench/LIMITATIONS.md`. Read it before relying on output.

## 10. Prohibited behaviour

The never-do list is stated in full in [`PHASE5-SAFETY-RULES.md`](PHASE5-SAFETY-RULES.md).
In summary, an agent must never: invent authorization, infer it from a URL or
ownership claim, bypass authentication, authorization, MFA, CAPTCHA, a WAF, an IDS,
a rate limit, a paywall, DRM, a licensing control or signed-URL expiry, obtain
another person's private data, steal credentials, execute or install anything
acquired, fabricate any result, or promote a potential finding. There is no
authorized version of any of them.

> This framework does not bypass authentication, authorization, paywalls, DRM,
> licensing controls, or other access restrictions.
