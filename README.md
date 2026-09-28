# BLACKHEART — Authorized Adversarial Security Research Agent Framework

> **Adversarial Cybersecurity Research & Penetration Testing Framework**
> *Think like a determined attacker, test like a professional penetration tester, verify like a forensic analyst, and report only what the evidence proves.*

---

## 📖 Executive Summary & Overview

**BLACKHEART** is an advanced, evidence-driven cybersecurity research and penetration testing agent framework. It provides structured methodology, rigid evidence-handling protocols, operational modes, and execution guidelines for conducting authorized adversarial security audits across diverse targets.

Unlike shallow vulnerability scanners or checklist-driven tools, BLACKHEART operates with a true **BLACKHEART attacker mindset**—aggressively testing security boundaries, validating state machines, challenging client-side trust assumptions, and chaining vulnerabilities to prove real-world business and security impact.

### Key Goals & Core Principles
1. **Evidence-First Verification**: Never assume a vulnerability exists based solely on suspicious code or static indicators. Validate with concrete proof and reproducible request/response chains.
2. **Adversarial Rigor**: Move beyond OWASP Top 10 surface checks to investigate complex business logic, payment flows, entitlement states, digital delivery mechanisms, and mobile IPC boundaries.
3. **Strict Authorization Boundaries**: Operate aggressively within authorized scope while strictly preventing collateral impact, third-party targets, or non-consensual data collection.
4. **Tool Honesty & Non-Fabrication**: Maintain complete transparency regarding tool availability and execution results. Never fabricate exploits, transaction IDs, hashes, or screenshots.

---

## ⚡ The Four Core Operational Modes

BLACKHEART defines three primary operational modes, each located at the root of the repository for quick access:

| Operational Mode Document | Purpose & Core Focus | Key Investigation Surface |
|---|---|---|
| 🛡️ **[`SECURITY-AUDIT.md`](./SECURITY-AUDIT.md)** | **Maximum Authorized Adversarial Security Audit** | Broad attack-surface mapping, technical vulnerability scanning (SQLi, SSRF, XSS, IDOR), reverse engineering, mobile/APK analysis, and full-spectrum attack chaining. |
| 🔬 **[`SECURITY-RESEARCH-MODE.md`](./SECURITY-RESEARCH-MODE.md)** | **Authorized Adversarial Security Research** | Deep, systematic research methodology for new targets/applications, trust-boundary mapping, authentication lifecycle, API state-machine testing, and safe exploit validation. |
| 🎯 **[`ZERO-CREDENTIAL-ESCALATION-MODE.md`](./ZERO-CREDENTIAL-ESCALATION-MODE.md)** | **Zero-Credential Discovery, Method Escalation & Coverage Control** | Anonymous attack-surface discovery from zero privilege, continuous method escalation when a technique fails, objective matrices, proof-strength levels, differential testing, chaining, and the final coverage-control layer. |
| 📦 **[`DIGITAL-ASSET-DELIVERY-MODE.md`](./DIGITAL-ASSET-DELIVERY-MODE.md)** | **Real-Asset & Digital-Product Delivery Verification** | End-to-end payment integrity, price manipulation, entitlement creation, download authorization bypass, and verification of actual downloaded digital artifacts (SHA-256, size, content). |

### Comparative Summary of Operational Modes

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                           BLACKHEART FRAMEWORK                           │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│ SECURITY AUDIT  │         │ RESEARCH MODE   │         │ DELIVERY MODE   │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ • Attack Surface│         │ • Research Loop │         │ • Price/Cart    │
│ • Technical Vulns│        │ • Trust Bounds  │         │ • Webhooks/Keys │
│ • Mobile/APK    │         │ • Auth/API Authz│         │ • Entitlements  │
│ • Exploit Chain │         │ • Hypothesis Loop│        │ • File Hashes   │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

---

## 🏛️ Framework Architecture & File Structure

The framework is organized into modular documentation, operating rules, workflows, templates, and bootstrap examples:

```text
.
├── README.md                           # Main repository documentation & guide (this file)
├── AGENT.md                            # Master agent system instructions & execution standard
├── FILE-INDEX.txt                      # Complete repository documentation index
├── SECURITY-AUDIT.md                   # Core Mode 1: Comprehensive security audit framework
├── SECURITY-RESEARCH-MODE.md          # Core Mode 2: Research methodology & execution loop
├── DIGITAL-ASSET-DELIVERY-MODE.md      # Core Mode 3: Payment, entitlement & asset delivery audit
├── ZERO-CREDENTIAL-ESCALATION-MODE.md  # Core Mode 4: Zero-credential discovery, method escalation & coverage control
│
└── BLACKHEART-AGENT-DOCUMENTATION/    # Extracted Technical Guides & Templates
    ├── README.md                       # Documentation package introduction
    │
    ├── docs/                           # Focused technical domain guides
    │   ├── ANDROID-TESTING.md          # Android APK/AAB, WebViews, Intent, & IPC security
    │   ├── AUTH-AUTHZ.md               # Authentication lifecycle, BOLA/IDOR, & RBAC testing
    │   ├── BUSINESS-LOGIC.md           # Workflow reordering, race conditions, & state machines
    │   ├── DECISION-MATRIX.md          # Finding classification standard & status rules
    │   ├── DIGITAL-FILE-VALIDATION.md  # Artifact hash calculation & evidence handling
    │   ├── EVIDENCE.md                 # Raw traffic capture, redaction, & evidence standard
    │   ├── OPERATING-RULES.md          # Behavioral safety rules & scope constraints
    │   ├── PAYMENT-PREMIUM-TESTING.md  # Payment gateways, coupons, & entitlement validation
    │   ├── REPORTING.md                # Structure for reporting findings & executive summaries
    │   ├── SCOPE.md                    # Target intake schema & authorization verification
    │   ├── TOOL-AND-ENVIRONMENT.md     # Capability discovery & tool-honesty policy
    │   ├── WEB-API-TESTING.md          # Web app, REST, GraphQL, & API vulnerability testing
    │   └── WORKFLOW.md                 # End-to-end assessment lifecycle
    │
    ├── examples/                       # Reference examples & bootstrapping guides
    │   └── NEW-PROJECT-BOOTSTRAP.md    # Guide for initiating testing on a new target
    │
    └── templates/                      # Standardized markdown report templates
        ├── FINAL-REPORT.md             # Complete executive & technical assessment report
        ├── FINDING.md                  # Individual vulnerability finding template
        └── TEST-LOG.md                 # Operational test log & execution journal template
```

---

## 📚 Complete Documentation Index

### Core Agent Instructions & Modes
- **[`AGENT.md`](./AGENT.md)**: Master agent instruction manual detailing mission lifecycle, scope intake, evidence taxonomy, and quality controls.
- **[`FILE-INDEX.txt`](./FILE-INDEX.txt)**: Plain-text list index of all framework documentation files.
- **[`SECURITY-AUDIT.md`](./SECURITY-AUDIT.md)**: Full-spectrum adversarial vulnerability assessment framework.
- **[`SECURITY-RESEARCH-MODE.md`](./SECURITY-RESEARCH-MODE.md)**: Research-oriented testing methodology for structured discovery.
- **[`DIGITAL-ASSET-DELIVERY-MODE.md`](./DIGITAL-ASSET-DELIVERY-MODE.md)**: Focused guide for auditing e-commerce, digital products, and file distribution platforms.
- **[`ZERO-CREDENTIAL-ESCALATION-MODE.md`](./ZERO-CREDENTIAL-ESCALATION-MODE.md)**: Zero-credential attack-surface discovery, continuous adversarial method escalation, and the gap-closure coverage-control engine.

### Deep-Dive Domain Guides (`/docs`)
- **[`docs/ANDROID-TESTING.md`](./BLACKHEART-AGENT-DOCUMENTATION/docs/ANDROID-TESTING.md)**: Static/dynamic Android assessment (Manifest, exported components, WebViews, deep links, local storage).
- **[`docs/AUTH-AUTHZ.md`](./BLACKHEART-AGENT-DOCUMENTATION/docs/AUTH-AUTHZ.md)**: Authentication state confusion, token handling, BOLA/IDOR, and vertical/horizontal privilege escalation.
- **[`docs/BUSINESS-LOGIC.md`](./BLACKHEART-AGENT-DOCUMENTATION/docs/BUSINESS-LOGIC.md)**: Workflow skipping, race conditions, state-machine violations, and limit bypasses.
- **[`docs/DECISION-MATRIX.md`](./BLACKHEART-AGENT-DOCUMENTATION/docs/DECISION-MATRIX.md)**: Status classification rules (`CONFIRMED`, `PARTIALLY CONFIRMED`, `UNVERIFIED`, `NOT TESTED`, `NOT VULNERABLE`, `OUT OF SCOPE`).
- **[`docs/DIGITAL-FILE-VALIDATION.md`](./BLACKHEART-AGENT-DOCUMENTATION/docs/DIGITAL-FILE-VALIDATION.md)**: Real artifact verification (SHA-256, byte count, MIME validation).
- **[`docs/EVIDENCE.md`](./BLACKHEART-AGENT-DOCUMENTATION/docs/EVIDENCE.md)**: Raw request/response capture, redaction standards, and evidence chain of custody.
- **[`docs/OPERATING-RULES.md`](./BLACKHEART-AGENT-DOCUMENTATION/docs/OPERATING-RULES.md)**: Safety guidelines, non-fabrication rules, and scope restriction rules.
- **[`docs/PAYMENT-PREMIUM-TESTING.md`](./BLACKHEART-AGENT-DOCUMENTATION/docs/PAYMENT-PREMIUM-TESTING.md)**: Price manipulation, coupon stacking, order-ID substitution, and webhook replay.
- **[`docs/REPORTING.md`](./BLACKHEART-AGENT-DOCUMENTATION/docs/REPORTING.md)**: Standardized rules for drafting high-impact technical reports.
- **[`docs/SCOPE.md`](./BLACKHEART-AGENT-DOCUMENTATION/docs/SCOPE.md)**: Intake record schema for target assets, environments, and boundaries.
- **[`docs/TOOL-AND-ENVIRONMENT.md`](./BLACKHEART-AGENT-DOCUMENTATION/docs/TOOL-AND-ENVIRONMENT.md)**: Capability discovery and tool-honesty requirements.
- **[`docs/WEB-API-TESTING.md`](./BLACKHEART-AGENT-DOCUMENTATION/docs/WEB-API-TESTING.md)**: Endpoint discovery, parameter tampering, and API vulnerability testing.
- **[`docs/WORKFLOW.md`](./BLACKHEART-AGENT-DOCUMENTATION/docs/WORKFLOW.md)**: Phase-by-phase assessment workflow from scope intake to final reporting.

### Report Templates & Bootstrapping (`/templates` & `/examples`)
- **[`templates/FINAL-REPORT.md`](./BLACKHEART-AGENT-DOCUMENTATION/templates/FINAL-REPORT.md)**: Template for compiling complete security assessment reports.
- **[`templates/FINDING.md`](./BLACKHEART-AGENT-DOCUMENTATION/templates/FINDING.md)**: Template for individual vulnerability documentation.
- **[`templates/TEST-LOG.md`](./BLACKHEART-AGENT-DOCUMENTATION/templates/TEST-LOG.md)**: Journal template for tracking hypotheses, inputs, and results.
- **[`examples/NEW-PROJECT-BOOTSTRAP.md`](./BLACKHEART-AGENT-DOCUMENTATION/examples/NEW-PROJECT-BOOTSTRAP.md)**: Step-by-step guide for bootstrapping an assessment on a new project.

---

## 🔄 Assessment Workflow & Operating Model

Every assessment executed under the BLACKHEART framework follows a strict, 5-stage lifecycle:

```text
[1. Scope & Intake] ➔ [2. Discovery & Mapping] ➔ [3. Hypothesis & Testing] ➔ [4. Chain & Validate] ➔ [5. Report & Remediate]
```

1. **Scope & Authorization Intake**: Verify authorization boundaries, define target assets (domains, endpoints, APKs), and establish synthetic test identities.
2. **Environment Discovery & Mapping**: Discover active tools, enumerate endpoints/components, map trust boundaries, and catalog API paths.
3. **Hypothesis-Driven Testing**: Formulate explicit attack hypotheses (e.g., "Can Order ID substitution grant unauthorized access?") and test systematically.
4. **Validation & Chain Analysis**: Confirm vulnerabilities with direct request/response proof, test for chained impacts, and calculate SHA-256 hashes of delivered artifacts.
5. **Documentation & Reporting**: Compile findings into structured reports using standardized evidence taxonomies and root-cause remediations.

---

## 🛡️ Safety, Scope & Responsible Use

- **Strict Authorization Required**: BLACKHEART methodology is intended exclusively for authorized security research, penetration testing, and defensive auditing.
- **Third-Party Infrastructure Protection**: Discovered dependencies (CDNs, payment processors, cloud storage) must not be tested unless explicitly authorized.
- **Minimization of Real Data Impact**: When validating against production environments, prefer synthetic identities and canary records. Never dump or exfiltrate sensitive PII.
- **Non-Destructive Execution**: Do not perform destructive actions, denial of service, or unauthorized account modifications.

---

## 📄 License & Credits

- **Framework**: BLACKHEART Adversarial Security Agent Documentation
