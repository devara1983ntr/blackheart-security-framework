# Authorized use — the workbench's design position

**Project:** BLACKHEART Security Framework · **Author:** Roshan
**Last updated:** 2026-09-30

---

This is the document the workbench points at. It is named in the package
docstring (`workbench/__init__.py`) and in the User-Agent string the client sends
to a target (`workbench/http_client.py`), so an operator who receives a request
from this tool can read what sent it and what it is for.

## What the workbench is

A local, first-party toolkit for **authorized** HTTP, API and resource work. It
sends requests, records what came back, and refuses what it may not do.

## What it is for

Assessing systems the operator owns or holds written authorization to test, within
that authorization's scope, budget and window. Nothing else.

## What it will not do

This is the design position, not a policy aspiration: the capabilities below are
absent from the code rather than disabled by a setting.

| Not implemented, by design |
|---|
| Bypassing authentication, authorization, MFA or CAPTCHA |
| Evading a WAF, IDS, rate limit or any other security control |
| Circumventing a paywall, DRM, licensing control or signed-URL expiry |
| Reaching private storage, a private repository, or another person's data |
| Credential guessing, spraying, theft or reuse |
| Executing, importing or installing anything acquired |
| A flag that skips the scope check — it does not exist |

> This framework does not bypass authentication, authorization, paywalls, DRM,
> licensing controls, or other access restrictions.

## What it enforces, and where

Two gates, both at the socket, neither optional:

1. **Policy acceptance.** The first statement of `http_client.request()` refuses
   every active operation until the policy has been accepted on this machine and
   has not changed since. Local, read-only operations are exempt.
2. **Scope.** `scope.require()` is below the policy gate and runs on every
   request: host, path, method, exclusion, budget, interval, authorization window
   and resolved address. A refusal raises, and nothing is sent.

A refusal is a stop, not an obstacle: a blocked resource is recorded as `blocked`
with no file written, together with the route that **is** authorized.

## What it cannot do

The workbench cannot verify that the operator holds an authorization. The scope
file is the operator's assertion; the tool checks the assertion's arithmetic, not
its truth. Whether a use is lawful depends on the operator's jurisdiction and their
engagement, and no part of this software determines that.

## If you received a request from this tool

The User-Agent identifies the client and the version. Everything it did is written
locally by the operator, in their own history and evidence files, and nothing is
transmitted here.

If you believe a request was unauthorized, the operator's identity is not recorded
by the framework — by design, so that the tool collects no identity data — and the
person to ask is whoever sent it. To report a security issue **in this
repository**, see [`../SECURITY.md`](../SECURITY.md). If you believe the framework
is being used against you or against a system you are responsible for, that same
document describes how to raise it.

## The rules, in full

| Document | Covers |
|---|---|
| [`../ACCEPTABLE-USE.md`](../ACCEPTABLE-USE.md) | Permitted and prohibited use, operationally |
| [`../SECURITY-RESEARCH-DISCLAIMER.md`](../SECURITY-RESEARCH-DISCLAIMER.md) | What research under this framework does and does not establish |
| [`../AUTHORIZATION-AGREEMENT.md`](../AUTHORIZATION-AGREEMENT.md) | The template an authorization is recorded in |
| [`../DOWNLOAD-AND-ACQUISITION-POLICY.md`](../DOWNLOAD-AND-ACQUISITION-POLICY.md) | What may be acquired, and what is refused |
| [`../policy/BLACKHEART-POLICY.json`](../policy/BLACKHEART-POLICY.json) | The whole policy, machine-readable |
| [`../docs/workbench/README.md`](../docs/workbench/README.md) | The workbench, for a reviewer |
| [`../docs/workbench/LIMITATIONS.md`](../docs/workbench/LIMITATIONS.md) | What it cannot establish |
