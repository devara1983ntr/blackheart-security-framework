# Documentation Guide

This directory contains the operating documentation for the BLACKHEART
authorized adversarial security research framework.
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

## Start here

| Document | Purpose |
|---|---|
| [`../AGENT.md`](../AGENT.md) | Master agent instruction, scope intake, evidence taxonomy, quality gate |
| [`modes/SECURITY-AUDIT.md`](modes/SECURITY-AUDIT.md) | Full-spectrum adversarial vulnerability assessment |
| [`modes/SECURITY-RESEARCH-MODE.md`](modes/SECURITY-RESEARCH-MODE.md) | Research methodology, trust boundaries, safe exploit validation |
| [`modes/DIGITAL-ASSET-DELIVERY-MODE.md`](modes/DIGITAL-ASSET-DELIVERY-MODE.md) | Payment, entitlement, premium access, digital-product delivery |
| [`modes/ZERO-CREDENTIAL-ESCALATION-MODE.md`](modes/ZERO-CREDENTIAL-ESCALATION-MODE.md) | Zero-credential discovery, method escalation, coverage control |

## Domain guides

| Guide | Purpose |
|---|---|
| [`guides/OPERATING-RULES.md`](guides/OPERATING-RULES.md) | Behavioural rules, safety constraints, non-fabrication |
| [`guides/SCOPE.md`](guides/SCOPE.md) | Target intake schema and authorization verification |
| [`guides/WORKFLOW.md`](guides/WORKFLOW.md) | End-to-end assessment lifecycle |
| [`guides/PAYMENT-PREMIUM-TESTING.md`](guides/PAYMENT-PREMIUM-TESTING.md) | Payment gateways, coupons, entitlement validation |
| [`guides/DIGITAL-FILE-VALIDATION.md`](guides/DIGITAL-FILE-VALIDATION.md) | Real artifact verification and evidence handling |
| [`guides/WEB-API-TESTING.md`](guides/WEB-API-TESTING.md) | Web/API assessment methodology |
| [`guides/ANDROID-TESTING.md`](guides/ANDROID-TESTING.md) | Android/APK/AAB, WebView, intent and IPC security |
| [`guides/AUTH-AUTHZ.md`](guides/AUTH-AUTHZ.md) | Authentication lifecycle, BOLA/IDOR, RBAC testing |
| [`guides/BUSINESS-LOGIC.md`](guides/BUSINESS-LOGIC.md) | Workflow skipping, race conditions, state machines |
| [`guides/EVIDENCE.md`](guides/EVIDENCE.md) | Raw traffic capture, redaction, evidence standard |
| [`guides/TOOL-AND-ENVIRONMENT.md`](guides/TOOL-AND-ENVIRONMENT.md) | Capability discovery, tool-honesty policy |
| [`guides/DECISION-MATRIX.md`](guides/DECISION-MATRIX.md) | Finding classification rules and status taxonomy |
| [`guides/REPORTING.md`](guides/REPORTING.md) | Report structure and executive-summary requirements |

## Templates and examples

| File | Purpose |
|---|---|
| [`../templates/FINDING.md`](../templates/FINDING.md) | Individual finding record template |
| [`../templates/TEST-LOG.md`](../templates/TEST-LOG.md) | Test log and execution journal template |
| [`../templates/FINAL-REPORT.md`](../templates/FINAL-REPORT.md) | Final report skeleton |
| [`../examples/NEW-PROJECT-BOOTSTRAP.md`](../examples/NEW-PROJECT-BOOTSTRAP.md) | Guide for bootstrapping a new assessment |

## Design goal

The documentation is intentionally detailed. The agent should investigate deeply
and continuously within scope, while never fabricating exploit evidence,
downloaded artifacts, payment results, or runtime capabilities.

Read [`../SECURITY.md`](../SECURITY.md) before applying any of this material to
a live system.
