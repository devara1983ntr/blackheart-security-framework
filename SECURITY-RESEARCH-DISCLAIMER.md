# Security Research Disclaimer

**Project:** BLACKHEART Security Framework · **Author:** Roshan
**Last updated:** 2026-09-30

---

## The short version

BLACKHEART is a security research and assessment framework. **It does not grant
you authorization to test anything.**

Possession of this framework does not grant authorization.
A target URL does not establish authorization.
A public endpoint does not authorize security testing beyond ordinary access.

Obtain appropriate permission before active testing. You are responsible for your
actions, your targets, your credentials, your data, your downloads, and your
compliance with applicable law.

## The slightly longer version

### What this framework is

- An instruction set for authorized security assessment: scope intake, evidence
  standards, methodology, reporting.
- A governed mirror of third-party agent skills, pinned and integrity-checked.
- A workbench: first-party tooling that can make HTTP requests, read documents and
  archives, record evidence, and write reports — within limits an operator sets,
  and only against targets the operator has authorized.

### What it is not

- **Not authorization.** No document, file, flag or configuration in this
  repository can grant permission to test a system. Only the party entitled to
  grant that permission can.
- **Not a scanner that decides for you.** The workbench records observations and
  refuses to promote them. It does not tell you a system is vulnerable.
- **Not a bypass tool.** It has no capability to defeat authentication,
  authorization, MFA, CAPTCHA, a paywall, DRM, a licensing control, a rate limit,
  a WAF, an IDS, or signed-URL expiry — and where a resource is protected, it
  records the refusal and stops.
- **Not legal advice.** Nothing here has been reviewed by a lawyer. Nothing here
  tells you whether your activity is lawful.
- **Not certified.** No certification, accreditation or approval of any kind is
  claimed by this project.

### Authorization, in practice

Before active testing, confirm:

| Question | If the answer is not clear |
|---|---|
| Who owns or operates the target? | Stop. Establish it |
| Are they, or is someone in the chain, entitled to authorize testing? | Stop. Establish it |
| Is the authorization written, and does it name the hosts, paths and methods? | Stop. Get it in writing |
| Does it cover the window you will test in? | Stop. Confirm the window |
| Does it cover the techniques you intend to use? | Stop. Confirm, in writing, for anything destructive or high-load |
| Is there a contact who can stop you, and a way to reach them? | Stop. Establish it |
| Are third parties in the path — a host, a payment processor, an API? | Stop. Establish whether their authorization is also needed |

The [`AUTHORIZATION-AGREEMENT.md`](AUTHORIZATION-AGREEMENT.md) template exists to
help record these answers. Filling it in does not create authority you do not
already hold; it records what you were given.

### What the workbench will refuse to do

Some of this is enforced in code, and a reader should be able to check which:

- It will not send a request that is outside the scope file (enforced in
  `workbench/scope.py`, below every request).
- It will not send a request at all until the policy has been accepted on the
  machine (enforced in `workbench/policy.py`, at the socket boundary).
- It will not replay a state-changing request without an explicit confirmation at
  the call site (enforced in `workbench/scope.py` and `workbench/scope.py`'s
  callers).
- It will not follow a redirect, a link, a sitemap entry or a form action to a
  host outside the scope (enforced in `workbench/http_client.py` and
  `workbench/discover.py`).
- It will not execute, import or install anything it acquires (enforced by
  construction; asserted by AST tests in `workbench/tests/`).
- It will not record a file it did not obtain, or a download that was refused
  (enforced in `workbench/fetch.py`).
- It will not present an observation as a finding (enforced in
  `workbench/evidence.py`).

### No warranty, and where responsibility sits

The framework is provided as is, without warranty of any kind. It may be wrong,
incomplete, or may fail in ways not yet discovered. A clean result is not a
clearance: absence of an observation is not evidence of absence.

The framework is provided subject to the applicable terms and disclaimers. Users
remain responsible for their use of the framework, their authorization, their
targets, and compliance with applicable law. The author and contributors accept
no responsibility for how the framework is used; that statement is a description
of the project's position, not a claim that liability is excluded in every
jurisdiction or circumstance.

### If you are being tested by this framework

If you are responsible for a system and you believe this framework has been used
against it without authorization, [`SECURITY.md`](SECURITY.md) explains how to
report a security issue to this project. The project cannot investigate
third-party activity, but it can act on reports about what this repository
contains or how it behaves, and it will.
