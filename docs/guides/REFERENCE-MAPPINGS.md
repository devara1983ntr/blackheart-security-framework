# Reference Mappings

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`SEVERITY-RATING.md`](SEVERITY-RATING.md) · [`DECISION-MATRIX.md`](DECISION-MATRIX.md) · [`REPORTING.md`](REPORTING.md)

## Purpose

The framework assesses real systems. Real systems are assessed against
recognised standards, because a finding that cannot be expressed in the
language of the recipient's compliance programme cannot be prioritised, tick
off, or closed.

This document maps BLACKHEART's own vocabulary — the weakness classes it tests
for in [`../AGENT.md`](../../AGENT.md) and the domain guides — onto the standards
most often required by clients, bug-bounty programmes, and internal audit.

**No mapping is mandatory.** The framework is standard-independent; these are
provided so that an assessor does not have to reconstruct them under deadline.
Use the set your engagement actually requires.

> **Verify before you cite.** CWE entries are revised, and OWASP and MASVS
> versions change. Confirm the identifier and its current definition against the
> publishing body before it appears in a client-facing report, and state the
> version you mapped against.

---

## 1. Weakness class to CWE

| BLACKHEART weakness class | CWE | Note |
|---|---|---|
| BOLA / IDOR — identifier substitution on a protected object | **CWE-639** | Authorization Bypass Through User-Controlled Key |
| Missing authorization check entirely | **CWE-862** | Distinct from an incorrect check |
| Authorization check present but wrong | **CWE-863** | Incorrect Authorization |
| BFLA — administrative function reachable by a normal user | **CWE-862** / **CWE-863** | Depends on whether a check is absent or wrong |
| General access-control failure | **CWE-284** | Improper Access Control |
| Privilege assignment / role confusion | **CWE-269** / **CWE-266** | Improper Privilege Management / Incorrect Privilege Assignment |
| Client-only enforcement of a server-side control | **CWE-602** | Client-Side Enforcement of Server-Side Security |
| Hidden or "immutable" parameter trusted by the server | **CWE-472** | External Control of Assumed-Immutable Web Parameter — the price-tampering class |
| Workflow / state transition skipped | **CWE-841** | Improper Enforcement of Behavioral Workflow |
| Race condition on a security-relevant action | **CWE-362** | Concurrent Execution using Shared Resource with Improper Synchronization |
| Time-of-check to time-of-use | **CWE-367** | TOCTOU Race Condition |
| Data authenticity not verified (payment callback, signature) | **CWE-345** | Insufficient Verification of Data Authenticity |
| Cryptographic signature not verified | **CWE-347** | Improper Verification of Cryptographic Signature |
| Replayable authentication or payment token | **CWE-294** | Authentication Bypass by Capture-replay |
| Session not invalidated on logout/expiry | **CWE-613** | Insufficient Session Expiration |
| Session fixation | **CWE-384** | Session Fixation |
| Account enumeration via recovery or login | **CWE-204** | Observable Response Discrepancy |
| Object reachable from the wrong execution sphere | **CWE-668** | Exposure of Resource to Wrong Sphere |
| Incorrect permission on a critical resource | **CWE-732** | Incorrect Permission Assignment for Critical Resource |
| SQL injection | **CWE-89** | |
| OS command injection | **CWE-78** | |
| Cross-site scripting | **CWE-79** | |
| Cross-site request forgery | **CWE-352** | |
| Server-side request forgery | **CWE-918** | |
| Path traversal | **CWE-22** | |
| Unsafe deserialization | **CWE-502** | |
| Hardcoded credential in source or binary | **CWE-798** | |
| Credential stored/transmitted without protection | **CWE-522** | Insufficiently Protected Credentials |
| Sensitive data in cleartext | **CWE-319** | Cleartext Transmission |
| Sensitive data stored unencrypted | **CWE-311** | Missing Encryption of Sensitive Data |
| Weak or broken cryptographic primitive | **CWE-327** | |
| Predictable identifier or token | **CWE-330** | Use of Insufficiently Random Values |
| Verbose error exposing internals | **CWE-209** | Information Exposure Through an Error Message |
| Sensitive information exposure generally | **CWE-200** | |
| Debug code or debug endpoint left in production | **CWE-489** | Active Debug Code |
| CORS allowing untrusted origin | **CWE-942** | Permissive Cross-domain Policy with Untrusted Domains |
| Open redirect | **CWE-601** | URL Redirection to Untrusted Site |
| Exported Android component | **CWE-926** | Improper Export of Android Application Components |
| Deep link / custom URL scheme handler without authorization | **CWE-939** | Improper Authorization in Handler for Custom URL Scheme |
| WebView exposing a JavaScript bridge to untrusted content | **CWE-749** | Exposed Dangerous Method or Function |

---

## 2. Web and API — OWASP Top 10 and API Security Top 10

### OWASP Top 10 (2021)

| ID | Category | Where it shows up in BLACKHEART |
|---|---|---|
| A01 | Broken Access Control | BOLA, IDOR, BFLA, entitlement bypass, download bypass — the framework's largest class |
| A02 | Cryptographic Failures | Cleartext transport, weak crypto, unsigned tokens |
| A03 | Injection | SQL, command, template, and deserialization classes |
| A04 | Insecure Design | Missing state machine, absent server-side entitlement check — the "designed this way" class |
| A05 | Security Misconfiguration | Verbose errors, debug endpoints, permissive CORS, exposed components |
| A06 | Vulnerable and Outdated Components | Supply chain; a dependency finding, not an application-logic one |
| A07 | Identification and Authentication Failures | Account enumeration, session invalidation, recovery weaknesses |
| A08 | Software and Data Integrity Failures | Unsigned updates, unverified webhook/callback payloads |
| A09 | Security Logging and Monitoring Failures | Security-relevant actions performed without an audit trail |
| A10 | Server-Side Request Forgery | Server fetching attacker-supplied URLs |

### OWASP API Security Top 10 (2023)

| ID | Category | BLACKHEART guide |
|---|---|---|
| API1 | Broken Object Level Authorization | [`AUTH-AUTHZ.md`](AUTH-AUTHZ.md), [`WEB-API-TESTING.md`](WEB-API-TESTING.md) |
| API2 | Broken Authentication | [`AUTH-AUTHZ.md`](AUTH-AUTHZ.md) |
| API3 | Broken Object Property Level Authorization | [`WEB-API-TESTING.md`](WEB-API-TESTING.md) — mass assignment |
| API4 | Unrestricted Resource Consumption | Rate-limit testing, deliberately bounded — see `AGENT.md` §19 |
| API5 | Broken Function Level Authorization | [`AUTH-AUTHZ.md`](AUTH-AUTHZ.md) — vertical testing |
| API6 | Unrestricted Access to Sensitive Business Flows | [`BUSINESS-LOGIC.md`](BUSINESS-LOGIC.md) |
| API7 | Server-Side Request Forgery | [`WEB-API-TESTING.md`](WEB-API-TESTING.md) |
| API8 | Security Misconfiguration | [`TOOL-AND-ENVIRONMENT.md`](TOOL-AND-ENVIRONMENT.md) |
| API9 | Improper Inventory Management | [`WEB-API-TESTING.md`](WEB-API-TESTING.md) — untracked/legacy endpoints |
| API10 | Unsafe Consumption of APIs | Third-party dependency handling; never expanded into testing without authorization |

---

## 3. Mobile — OWASP Mobile Top 10 and MASVS

### OWASP Mobile Top 10 (2024)

| ID | Category | Where it applies |
|---|---|---|
| M1 | Improper Credential Usage | Hardcoded keys, credentials in logs or storage |
| M2 | Inadequate Supply Chain Security | Untrusted build or update chain |
| M3 | Insecure Authentication/Authorization | Client-side premium or role checks, token handling |
| M4 | Insufficient Input/Output Validation | Untrusted input reaching IPC, intents, WebView bridges |
| M5 | Insecure Communication | Cleartext traffic, weak TLS pinning posture |
| M6 | Inadequate Privacy Controls | Excessive collection, logs containing personal data |
| M7 | Insufficient Binary Protections | Tamperability, reversibility, debuggability |
| M8 | Security Misconfiguration | Exported components, permissive WebView settings, enabled backup |
| M9 | Insecure Data Storage | Local databases, shared preferences, cache, external storage |
| M10 | Insufficient Cryptography | Weak primitives or key handling in local storage |

### MASVS v2 domains

| Domain | BLACKHEART coverage |
|---|---|
| MASVS-STORAGE | Local data at rest; maps to M9 |
| MASVS-CRYPTO | Cryptographic use; maps to M10 |
| MASVS-AUTH | Authentication and session binding; maps to M3 |
| MASVS-NETWORK | Transport security; maps to M5 |
| MASVS-PLATFORM | WebView, IPC, deep links, exported components; maps to M4, M8 |
| MASVS-CODE | Build and release integrity; maps to M2, M7 |
| MASVS-RESILIENCE | Tamper and reverse-engineering resistance; maps to M7 |
| MASVS-PRIVACY | Personal-data handling in the app; maps to M6 |

See [`ANDROID-TESTING.md`](ANDROID-TESTING.md) for the corresponding assessment
procedure.

---

## 4. Application security verification — ASVS v4

| Chapter | Area |
|---|---|
| V1 | Architecture and design |
| V2 | Authentication |
| V3 | Session management |
| V4 | Access control |
| V5 | Validation, sanitisation and encoding |
| V6 | Stored cryptography |
| V7 | Error handling and logging |
| V8 | Data protection |
| V9 | Communication security |
| V10 | Malicious code |
| V11 | Business logic |
| V12 | Files and resources |
| V13 | API and web services |
| V14 | Configuration |

ASVS is requirement-based: it asks whether a specific control exists, whereas
BLACKHEART asks whether a specific control *holds under attack*. A finding that
maps to an ASVS requirement should still be reported as a demonstrated boundary
failure, with the reproduction attached.

---

## 5. Payment contexts — PCI DSS v4.0

Relevant when the assessment touches cardholder data, payment flows, or the
systems that process them.

| Requirement | Area | Relevance |
|---|---|---|
| 3.x | Protect stored account data | Storage of PAN, expiry, CVV |
| 4.x | Protect account data in transit | Transport security of payment paths |
| 6.x | Develop and maintain secure systems and software | The application logic behind payment |
| 7.x | Restrict access by business need to know | Authorization on administrative and payment operations |
| 8.x | Identify users and authenticate access | Authentication of operator and customer identities |
| 10.x | Log and monitor all access | Audit trail for payment state changes |
| 11.x | Test security of systems and networks | The engagement itself |

**Scope note.** A finding in an application that processes cardholder data may
carry PCI DSS obligations for the merchant. That is a business determination,
not a tester's judgement. State the technical finding and the data touched; let
the compliance owner draw the obligation. Never claim or imply a compliance
status from a black-box test — you are not conducting a QSA assessment.

---

## 6. Data protection contexts — GDPR

The framework's [minimum necessary data principle](OPERATING-RULES.md) aligns
directly with data minimisation, which is a useful alignment to state explicitly
in European engagements.

| Article | Principle | Relationship to BLACKHEART practice |
|---|---|---|
| Art. 5(1)(c) | Data minimisation | Collect only what proves the security property; stop broad collection on encountering personal data |
| Art. 5(1)(b) | Purpose limitation | Assessment evidence has a defined purpose; do not repurpose collected data |
| Art. 5(1)(f) | Integrity and confidentiality | The security property under test |
| Art. 25 | Data protection by design and by default | Root-cause and remediation guidance |
| Art. 32 | Security of processing | The security boundary being assessed |
| Art. 33 / 34 | Breach notification duties | **Determined by the controller, not the assessor** |
| Art. 35 | Data protection impact assessment | Engagement-level, owner responsibility |

**Do not advise on notification duties.** State what data was observed and
whether it appeared to be personal data. The controller decides what follows.
This framework does not provide legal advice and cannot determine regulatory
obligations.

---

## 7. Using mappings in a report

1. **Map to the recipient's framework, not every framework.** Five mappings on
   one finding is noise, not thoroughness.
2. **State the version.** "OWASP Top 10 (2021)" is useful; "OWASP Top 10" is not.
3. **Mapping never sets severity.** [`SEVERITY-RATING.md`](SEVERITY-RATING.md)
   sets severity from demonstrated impact. A CWE identifier describes the
   weakness class, not how bad it is.
4. **A mapping is not a verdict.** Mapping a finding to A01 does not assert that
   the system fails A01 broadly. The finding stands on its own evidence.
5. **Unmapped findings are still real.** A weakness with no clean CWE or OWASP
   home is often the interesting one. Report it on its evidence.
