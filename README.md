<div align="center">

# BLACKHEART

### Adversarial Security Research Framework

**An evidence-first methodology and agent instruction set for authorized
application, API, mobile, payment, and digital-product security assessments.**

[Documentation](#documentation) · [Repository Structure](#repository-structure) ·
[Quick Start](#quick-start) · [Responsible Use](#responsible-use) · [License](#license)

</div>

---

## Overview

**BLACKHEART** is a structured framework for conducting **authorized** adversarial
security assessments. It provides operating modes, domain guides, report templates,
and a decision taxonomy that together define *how* to test, *what evidence* is
required, and *what may honestly be concluded*.

It is a methodology and instruction set — **not a scanner, not a toolkit, and not
a collection of exploits.** It is written for security engineers, penetration
testers, security researchers, and practitioners who need an assessment to be
reproducible, evidence-linked, and defensible.

### The problem this solves

Most security assessments fail in one of two directions:

- **False confidence** — a 200 response is treated as "the endpoint is exposed,"
  or a client-side filter is mistaken for an authorization control, so a
  non-vulnerability is reported as a breach.
- **Unfalsifiable reporting** — a finding is asserted without evidence, without
  a stated attacker privilege, and without separating an intermediate
  behaviour from actual security impact.

BLACKHEART is built to prevent both. Its governing rule:

> **Report only what the evidence proves.**

## Core Principles

| Principle | What it means in practice |
|---|---|
| **Evidence before conclusions** | A suspicious pattern is a hypothesis, not a finding. Status is earned by proof, not suspicion. |
| **No artificial stopping** | A failed technique closes *that technique*, never the security objective. Method escalation is mandatory. |
| **Zero fabrication** | No invented hashes, transactions, responses, screenshots, artifacts, or exploitation results. Ever. |
| **Confirmed by impact, not possibility** | "A price parameter is editable" is not "payment bypass." Each escalation needs its own proof. |
| **Tool honesty** | If a tool was unavailable, the report says so and names the alternative actually used. |
| **Third-party boundaries** | A vendor endpoint in client code is documented, not attacked. Authorization never inherits. |
| **Minimum necessary data** | Prove the authorization failure with the smallest sufficient proof. Do not harvest real user data. |
| **Negative results are evidence** | A correctly-rejected attack is documented, because it proves a control exists. |

---

## Documentation

### Core operational modes

The four modes define how an assessment is conducted. Each is a complete,
self-contained operating document.

| Mode | Focus | Read it when |
|---|---|---|
| [`AGENT.md`](AGENT.md) | Master agent instruction, scope intake, evidence taxonomy, quality gate | Always — this is the entry point |
| [`docs/modes/SECURITY-AUDIT.md`](docs/modes/SECURITY-AUDIT.md) | Full-spectrum adversarial vulnerability assessment | Running a broad technical assessment |
| [`docs/modes/SECURITY-RESEARCH-MODE.md`](docs/modes/SECURITY-RESEARCH-MODE.md) | Structured research loop, trust boundaries, safe exploit validation | Investigating an unfamiliar target |
| [`docs/modes/DIGITAL-ASSET-DELIVERY-MODE.md`](docs/modes/DIGITAL-ASSET-DELIVERY-MODE.md) | Payment integrity, entitlement, download authorization, real-artifact validation | The target sells digital goods or premium access |
| [`docs/modes/ZERO-CREDENTIAL-ESCALATION-MODE.md`](docs/modes/ZERO-CREDENTIAL-ESCALATION-MODE.md) | Zero-credential discovery, method escalation, coverage control | Exhausting the anonymous surface and preventing premature closure |

### Domain guides

Focused references for specific assessment concerns.

| Guide | Covers |
|---|---|
| [`OPERATING-RULES.md`](docs/guides/OPERATING-RULES.md) | Behavioural rules, non-fabrication, safety constraints |
| [`SCOPE.md`](docs/guides/SCOPE.md) | Target intake schema, authorization verification, scope hierarchy |
| [`WORKFLOW.md`](docs/guides/WORKFLOW.md) | The 13-phase assessment lifecycle |
| [`EVIDENCE.md`](docs/guides/EVIDENCE.md) | Evidence hierarchy, chain of custody, redaction |
| [`DECISION-MATRIX.md`](docs/guides/DECISION-MATRIX.md) | **Finding classification rules** — read this before writing a report |
| [`AUTH-AUTHZ.md`](docs/guides/AUTH-AUTHZ.md) | Authentication lifecycle, BOLA/IDOR, RBAC testing |
| [`BUSINESS-LOGIC.md`](docs/guides/BUSINESS-LOGIC.md) | Workflow skipping, races, state-machine violations |
| [`WEB-API-TESTING.md`](docs/guides/WEB-API-TESTING.md) | Endpoint discovery, parameter tampering, API testing |
| [`ANDROID-TESTING.md`](docs/guides/ANDROID-TESTING.md) | APK/AAB, WebView, intent and IPC security |
| [`PAYMENT-PREMIUM-TESTING.md`](docs/guides/PAYMENT-PREMIUM-TESTING.md) | Payment gateways, coupons, entitlement validation |
| [`DIGITAL-FILE-VALIDATION.md`](docs/guides/DIGITAL-FILE-VALIDATION.md) | Real artifact verification, SHA-256, evidence handling |
| [`TOOL-AND-ENVIRONMENT.md`](docs/guides/TOOL-AND-ENVIRONMENT.md) | Capability discovery and tool-honesty policy |
| [`REPORTING.md`](docs/guides/REPORTING.md) | Report structure and writing standards |

### Templates and examples

| File | Purpose |
|---|---|
| [`templates/FINDING.md`](templates/FINDING.md) | Individual finding record |
| [`templates/TEST-LOG.md`](templates/TEST-LOG.md) | Hypothesis/execution journal |
| [`templates/FINAL-REPORT.md`](templates/FINAL-REPORT.md) | Full assessment report skeleton |
| [`examples/NEW-PROJECT-BOOTSTRAP.md`](examples/NEW-PROJECT-BOOTSTRAP.md) | Engagement bootstrap prompt |
| [`FILE-INDEX.txt`](FILE-INDEX.txt) | Authoritative flat index of every document |

---

## Repository Structure

```text
.
├── README.md                          # This file — project overview and navigation
├── AGENT.md                           # Master agent instruction and execution standard
├── FILE-INDEX.txt                     # Authoritative flat index of all documents
├── LICENSE                            # MIT License
├── AUTHOR                             # Authorship and third-party attribution
├── CHANGELOG.md                       # Version history
├── CONTRIBUTING.md                    # Contribution guidelines
├── CODE_OF_CONDUCT.md                 # Contributor Covenant 2.1
├── SECURITY.md                        # Security policy and responsible-use policy
│
├── docs/
│   ├── README.md                      # Documentation package guide
│   ├── modes/                         # Core operational modes
│   │   ├── SECURITY-AUDIT.md
│   │   ├── SECURITY-RESEARCH-MODE.md
│   │   ├── DIGITAL-ASSET-DELIVERY-MODE.md
│   │   └── ZERO-CREDENTIAL-ESCALATION-MODE.md
│   └── guides/                        # Domain guides
│       ├── ANDROID-TESTING.md
│       ├── AUTH-AUTHZ.md
│       ├── BUSINESS-LOGIC.md
│       ├── DECISION-MATRIX.md
│       ├── DIGITAL-FILE-VALIDATION.md
│       ├── EVIDENCE.md
│       ├── OPERATING-RULES.md
│       ├── PAYMENT-PREMIUM-TESTING.md
│       ├── REPORTING.md
│       ├── SCOPE.md
│       ├── TOOL-AND-ENVIRONMENT.md
│       ├── WEB-API-TESTING.md
│       └── WORKFLOW.md
│
├── examples/
│   └── NEW-PROJECT-BOOTSTRAP.md       # Engagement bootstrap prompt
│
└── templates/
    ├── FINAL-REPORT.md                # Assessment report skeleton
    ├── FINDING.md                     # Finding record template
    └── TEST-LOG.md                    # Test journal template
```

---

## Quick Start

### For a new engagement

1. **Establish authorization first.** A public URL, a shared link, a hosting
   tenancy, or a similar name is *not* authorization. Record the scope, the
   authorized party, the environment, and the prohibited actions.

2. **Read [`AGENT.md`](AGENT.md)** end to end. It is the master instruction.

3. **Choose your mode.** Technical breadth → `SECURITY-AUDIT.md`. Unfamiliar
   target → `SECURITY-RESEARCH-MODE.md`. Paid/digital products →
   `DIGITAL-ASSET-DELIVERY-MODE.md`. Always pair with
   `ZERO-CREDENTIAL-ESCALATION-MODE.md` for the anonymous surface and for
   coverage control.

4. **Bootstrap the engagement** using
   [`examples/NEW-PROJECT-BOOTSTRAP.md`](examples/NEW-PROJECT-BOOTSTRAP.md).

5. **Record as you go.** Use [`templates/TEST-LOG.md`](templates/TEST-LOG.md)
   per hypothesis. A test with no record cannot later be distinguished from a
   test that was never run.

6. **Classify honestly** using
   [`docs/guides/DECISION-MATRIX.md`](docs/guides/DECISION-MATRIX.md).

7. **Report** against [`templates/FINAL-REPORT.md`](templates/FINAL-REPORT.md)
   and [`docs/guides/REPORTING.md`](docs/guides/REPORTING.md).

### Writing a finding

Every finding uses the same 17-field structure:

```text
Finding ID · Title · Status · Severity · Affected Asset
Security Property · Preconditions · Normal Workflow · Attack Hypothesis
Reproduction · Observed Evidence · State Before/After
Security Boundary Failure · Root Cause · Actual Impact
Attack Chain · Artifact Evidence · Remediation · Regression Test · Limitations
```

### The status taxonomy

Use these terms precisely. They are not interchangeable.

| Status | Meaning |
|---|---|
| `CONFIRMED` | Direct evidence demonstrates the weakness **and** its stated impact |
| `PARTIALLY CONFIRMED` | The weakness is demonstrated; a material link in the impact chain is not |
| `UNVERIFIED` | Credible hypothesis; evidence is insufficient |
| `NOT TESTED` | Testing could not or did not occur — **state the blocking capability** |
| `NOT VULNERABLE` | Tested with sufficient coverage; the control held **under the tested conditions** |
| `OUT OF SCOPE` | Excluded by authorization or assessment boundary |
| `BLOCKED BY ENVIRONMENT` | The required tool, runtime, or account was unavailable |
| `INCONCLUSIVE` | Testing was performed but the result is ambiguous |

> Never write `SAFE`, `SECURE`, or `NO VULNERABILITIES` without scoping the
> statement to the exact condition tested. "Not demonstrated under tested
> conditions" is a defensible claim. "Secure" is not.

---

## Technologies & Methodologies

This repository documents methodology, not an implementation stack. The
following are the domains and techniques the framework actually addresses.

**Assessment domains**

- Web application security · REST/JSON API security · GraphQL · WebSocket & SSE
- Authentication lifecycle (registration, login, OAuth, OTP/MFA, recovery,
  session invalidation, token lifecycle)
- Authorization: BOLA/IDOR, BFLA, horizontal and vertical privilege escalation,
  field-level authorization, role/privilege escalation matrices
- Business logic and state-machine analysis
- Payment, entitlement, and premium-feature integrity
- Digital-product delivery, signed URLs, and real-artifact validation
- Android/APK/AAB: manifest, exported components, deep links, WebView, JavaScript
  bridges, IPC, network security configuration
- OSINT and attack-surface reconnaissance
- Client-side trust, storage, cache, and stale-state analysis
- Secret discovery and classification
- Rate limiting, replay, race conditions, and time/expiration logic

**Techniques**

- Differential testing across identities and roles
- Identity-confusion and object-substitution testing
- Mass assignment / property pollution
- Parser, content-type, and method-override differentials
- Proof-strength classification and attack-chaining
- Evidence chain-of-custody and forensic artifact validation

**Practitioner tooling referenced as methodology** (availability is always
verified and reported, never assumed): `curl`, `git`, `openssl`, `jq`,
`python3`, proxy/interceptor tooling, `adb`, `apktool`, `JADX`, `Frida`.

---

## Responsible Use

> **This repository grants no authorization to test any system.**

The framework is intended exclusively for systems you **own**, systems you have
**written permission** to test, and explicitly authorized lab, staging, or
sandbox environments.

**Prohibited in all engagements:**

- Testing systems you do not own or have written permission to test
- Attacking third-party SaaS, CDN, payment-provider, or cloud infrastructure
  discovered in client code
- Credential theft, brute force, phishing, or session hijacking
- Denial-of-service, stress testing, or deliberate service degradation
- Real payments, deliberate financial loss, or bulk extraction of personal data
- Destructive modification of production data
- Fabricated evidence of any kind

Unauthorized access to computer systems is unlawful in most jurisdictions.
The techniques in this repository are published for **defensive** and
**authorized** use.

Full policy: **[`SECURITY.md`](SECURITY.md)**

---

## Contributing

Contributions are welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md) for scope,
rules, and the required `FILE-INDEX.txt` update when adding or moving a document.

Please read the hard rules before submitting: no fabrication, no secrets, no
removal of original content without justification, and precise use of the
status taxonomy.

Participation is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Security Reports

Defects in the methodology — anything that could lead a practitioner to an
incorrect or unsafe conclusion — are prioritised. Report privately; do **not**
open a public issue containing live secrets or real target data.
See [`SECURITY.md`](SECURITY.md).

---

## Author

**Roshan** — <https://github.com/devara1983ntr>

See [`AUTHOR`](AUTHOR) for authorship and third-party attribution.
This repository contains no third-party source code, vendored libraries, or
external datasets.

---

## License

Released under the [MIT License](LICENSE).

The license covers the documentation in this repository only and **confers no
authorization to test any system**. See [`SECURITY.md`](SECURITY.md).

## Disclaimer

Provided "as is", without warranty of any kind. The author is not liable for
any use of, or damage arising from, the use of this material. Users are
responsible for ensuring they operate within the law and within a valid
authorization scope.
