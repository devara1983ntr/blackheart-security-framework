# Acceptable Use

**Project:** BLACKHEART Security Framework · **Author:** Roshan
**Acceptable-use version:** 1.0.0 · **Last updated:** 2026-09-30

This document is part of the [`TERMS-OF-USE.md`](TERMS-OF-USE.md). It states what
this framework may be used for, and what it may not. It has not been reviewed by a
lawyer.

---

## Permitted

| Permitted | Notes |
|---|---|
| Testing infrastructure you own or operate | You are still bound by any contract that covers it |
| Testing a target you are authorized to test | Authorization must come from someone entitled to grant it, and should be recorded — see [`AUTHORIZATION-AGREEMENT.md`](AUTHORIZATION-AGREEMENT.md) |
| Local test environments | Containers, VMs, lab networks, deliberately vulnerable applications |
| The loopback fixtures shipped with this repository | `workbench/tests/fixtures.py`; no test in this repository contacts anything else |
| Authorized security research within an agreed scope | Scoped, budgeted, time-boxed, with a contact and a stop condition |
| Authorized acquisition of public resources | Within the rules in [`DOWNLOAD-AND-ACQUISITION-POLICY.md`](DOWNLOAD-AND-ACQUISITION-POLICY.md) |
| Authorized acquisition of resources you are authorized to access | Using your own credentials, supplied through a supported mechanism |
| Authorized incident evidence collection | Read-only, within scope, under the emergency protocol |
| Reading, hashing and reporting on evidence you already hold | Local operations; no network, no scope file required |
| Reading this repository's documentation | — |

## Prohibited

Using this framework for any of the following is prohibited, and is not a use
this project permits or supports. The list is not exhaustive; it names the
categories the code and documentation are built to refuse.

### Access and control

| Prohibited | |
|---|---|
| Unauthorized access to any system, service, account or data | Including "just looking" |
| Bypassing authentication or authorization | Login, session, token, permission or role checks |
| Bypassing MFA or CAPTCHA | Any form, including solving services and solver farms |
| Bypassing, evading or defeating a WAF, IDS, IPS or rate limit | Including through fragmentation, encoding tricks, header games, IP rotation or timing games |
| Circumventing a paywall or subscription check | — |
| Circumventing DRM or a licensing control | Including watermark or notice removal |
| Circumventing signed-URL expiry, private storage or a private repository | Including guessing URLs, reusing expired links, or trying another host that serves the same object |
| Accessing another person's data | Regardless of how the identifier was obtained |

### Identity and credentials

| Prohibited | |
|---|---|
| Obtaining, using or transferring credentials that are not your own authorized access material | Passwords, tokens, API keys, session cookies, private keys |
| Session hijacking, fixation, replay of another person's session | — |
| Phishing, credential harvesting, social engineering against a target's people | — |
| Extracting credentials from a target and reusing them beyond the authorized purpose | — |

### Data and privacy

| Prohibited | |
|---|---|
| Collecting personal data beyond what the authorized engagement requires | — |
| Unauthorized surveillance or monitoring of any person | — |
| Retaining, publishing or transferring data obtained without authorization | — |
| Using assessment data for any purpose other than the engagement it came from | — |

### Harm

| Prohibited | |
|---|---|
| Destructive testing, data alteration or deletion without explicit written authorization | — |
| Denial of service, load testing or resource exhaustion against a target that has not authorized it | — |
| Deploying malware, ransomware, backdoors or persistence | — |
| Establishing persistence, exfiltrating data, or lateral movement beyond authorized scope | — |
| Exploiting a system without authorization | Including exploiting anything the workbench observes |
| Fraud, extortion, harassment or abuse of any person or infrastructure | — |
| Attacking third-party infrastructure reached through a target | A redirect, an embedded script, a linked domain or an upstream API is not in scope because the target referred to it |

### Integrity of the work

| Prohibited | |
|---|---|
| Fabricating results | Findings, scans, downloads, screenshots, statistics, evidence, API responses, exploitation outcomes |
| Representing simulated traffic as real traffic from a target | — |
| Promoting a potential or unverified observation into a confirmed finding | — |
| Presenting the framework's output, or possession of the framework, as authorization | — |
| Editing evidence to change what it shows | — |
| Executing, importing or installing anything acquired by the framework | No macros, no binaries, no packages |

## How the code enforces part of this

The prohibitions above are not only prose. Some are enforced mechanically, and a
reader should know exactly which:

| Prohibition | Enforcement | Where |
|---|---|---|
| Unauthorized access | Every request checked against the scope file; refusal raises, and there is no flag that skips it | `workbench/scope.py`, `workbench/cli.py` |
| Bypassing access controls | No evasion capability exists; blocked statuses end the path | `workbench/fetch.py` |
| Circumventing a paywall, DRM or licence | Recorded as blocked, with the authorized route named instead | `workbench/fetch.py` |
| Unauthorized load | Request budget, a one-second default interval, concurrency of one, page and depth caps | `workbench/scope.py`, `workbench/fuzz.py`, `workbench/discover.py` |
| Probing third-party infrastructure | Every hop and every discovered reference is checked against scope before it is requested | `workbench/http_client.py`, `workbench/discover.py` |
| Executing downloaded content | Nothing is executed, imported or installed; AST tests assert the absence of such calls | `workbench/extract.py`, `workbench/tests/test_extract.py` |
| Promoting a potential finding | Status transitions are a defined ladder; `REPRODUCED` requires a second observation | `workbench/evidence.py` |
| Acting without acknowledging the rules | Active operations require a recorded policy acceptance | `workbench/policy.py` |

What is *not* enforced, and cannot be: whether you actually hold the authorization
a scope file asserts. The scope file is your assertion. The tool checks its
arithmetic, not your authority.

### Acceptance is not authorization

Active operations require two things, and neither is a substitute for the other:

| Requirement | Established by | Establishes |
|---|---|---|
| Policy acceptance | `blackheart policy accept`, recorded locally | That the rules were read on that machine |
| Authorization | a scope file for the target | That the operator asserts an authorization, with hosts, methods, budget and window |

```bash
python3 -m workbench.cli policy status   # accepted, and current?
python3 -m workbench.cli policy accept   # record that you read the version in front of you
python3 -m workbench.cli scope validate --scope scope.json
```

**Accepting the policy does not authorize any target.** It cannot: the policy is
the same for everyone, and it names no system. An agent or operator that treats
`policy status` returning `accepted` as permission to test something has confused
an acknowledgement with authority — which is why the two are separate commands and
separate records.

Local, read-only operations — parsing a document, hashing a file, writing a report
from evidence already collected — are exempt from both, so that analysing evidence
someone else collected needs no authorization. That exemption ends the moment a
socket would be opened, and the list of exempt commands is published in
[`policy/BLACKHEART-POLICY.json`](policy/BLACKHEART-POLICY.json).

## Reporting misuse

If you believe this framework is being used against you or against a system you
are responsible for, [`SECURITY.md`](SECURITY.md) describes how to report a
security issue privately. Reports about *this repository's* security are welcome;
the project cannot investigate third-party misuse beyond what its own code does.
