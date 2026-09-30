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
| [`modes/RED-HEART-ADVERSARY-EMULATION.md`](modes/RED-HEART-ADVERSARY-EMULATION.md) | Adversary emulation, attack-path reasoning, post-exploitation, RoE |

## Framework references

| Document | Purpose |
|---|---|
| [`CAPABILITY-AUDIT.md`](CAPABILITY-AUDIT.md) | What this framework can and cannot do, checked against the tree, with the decisions taken on every gap |

## The workbench

`workbench/` is the framework's own code: an authorized-use HTTP, API and resource
toolkit with a command surface, an evidence format and a report generator.

| Document | Purpose |
|---|---|
| [`workbench/README.md`](workbench/README.md) | What it is, the rules it is built around, and how to run it |
| [`workbench/COMMANDS.md`](workbench/COMMANDS.md) | Every command, its flags, and what each exit code means |
| [`workbench/THREAT-MODEL.md`](workbench/THREAT-MODEL.md) | What the code must never do, and the threats it is built against |
| [`workbench/LIMITATIONS.md`](workbench/LIMITATIONS.md) | What it cannot establish, stated plainly |
| [`workbench/END-TO-END.md`](workbench/END-TO-END.md) | A real transcript of one run, failures included |

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
| [`guides/SEVERITY-RATING.md`](guides/SEVERITY-RATING.md) | Impact × reach severity rubric, bounded by evidence status |
| [`guides/REFERENCE-MAPPINGS.md`](guides/REFERENCE-MAPPINGS.md) | CWE, OWASP Web/API/Mobile, MASVS, ASVS, PCI DSS, GDPR, LLM mappings |
| [`guides/REMEDIATION-AND-RETEST.md`](guides/REMEDIATION-AND-RETEST.md) | Root cause, fix patterns, regression tests, retest protocol |
| [`guides/ATTACK-PATHS.md`](guides/ATTACK-PATHS.md) | Path construction, evidence states for edges, chain severity |
| [`guides/ADVERSARY-EMULATION.md`](guides/ADVERSARY-EMULATION.md) | Engagement structure, goals, safety planning, detection review |
| [`guides/AGENTIC-AI-SECURITY.md`](guides/AGENTIC-AI-SECURITY.md) | LLM and agent assessment: injection, tool abuse, retrieval, agency |
| [`guides/CLOUD-IDENTITY.md`](guides/CLOUD-IDENTITY.md) | IAM, policy, tenant boundary, confused deputy, cloud secrets |
| [`guides/SUPPLY-CHAIN.md`](guides/SUPPLY-CHAIN.md) | Dependencies, reachability, build integrity, supply-chain secrets |
| [`guides/METHODOLOGY-STANDARDS.md`](guides/METHODOLOGY-STANDARDS.md) | PTES, NIST SP 800-115, OSSTMM, MITRE Engage, OWASP alignment |

## AI agent layer

How an autonomous agent operates this framework, and the skills it selects.

| Document | Purpose |
|---|---|
| [`agent/AGENT-BOOTSTRAP.md`](agent/AGENT-BOOTSTRAP.md) | **Activation protocol** — the verbatim prompt used to load this framework into an agent, with its response contract and design rationale |
| [`agent/AGENT-OPERATING-PROTOCOL.md`](agent/AGENT-OPERATING-PROTOCOL.md) | Agent non-negotiables, tool protocol, evidence discipline, stop conditions |
| [`agent/AGENT-SKILL-CATALOGUE.md`](agent/AGENT-SKILL-CATALOGUE.md) | Named skills with trigger, procedure, output, max claim, and stop |

## Reference

| Document | Purpose |
|---|---|
| [`GLOSSARY.md`](GLOSSARY.md) | Every term the framework uses, defined once |
| [`SKILLS.md`](SKILLS.md) | Competency-to-document map for learning and self-direction |
| [`../ARCHITECTURE.md`](../ARCHITECTURE.md) | Framework layering, precedence order, and invariants |
| [`../ROADMAP.md`](../ROADMAP.md) | Recognised gaps and out-of-scope items |

## Templates and examples

| File | Purpose |
|---|---|
| [`../templates/ENGAGEMENT-RECORD.md`](../templates/ENGAGEMENT-RECORD.md) | Scope, authorization, capability inventory, tool substitutions |
| [`../templates/COVERAGE-MATRIX.md`](../templates/COVERAGE-MATRIX.md) | Per-boundary test coverage and explicit blockers |
| [`../templates/AGENT-THREAT-MODEL.md`](../templates/AGENT-THREAT-MODEL.md) | AI/agentic system action surface, tools, input channels |
| [`../templates/ATTACK-PATH.md`](../templates/ATTACK-PATH.md) | Path edges with evidence states, detection review, blind spots |
| [`../templates/FINDING.md`](../templates/FINDING.md) | Individual finding record template |
| [`../templates/TEST-LOG.md`](../templates/TEST-LOG.md) | Test log and execution journal template |
| [`../templates/FINAL-REPORT.md`](../templates/FINAL-REPORT.md) | Final report skeleton |
| [`../examples/NEW-PROJECT-BOOTSTRAP.md`](../examples/NEW-PROJECT-BOOTSTRAP.md) | Guide for bootstrapping a new assessment |

## Suggested reading order

For a first engagement:

1. [`../AGENT.md`](../AGENT.md) — the governing document
2. [`../templates/ENGAGEMENT-RECORD.md`](../templates/ENGAGEMENT-RECORD.md) — establish scope and capabilities
3. [`guides/SCOPE.md`](guides/SCOPE.md) and [`guides/OPERATING-RULES.md`](guides/OPERATING-RULES.md) — the boundaries
4. [`../templates/COVERAGE-MATRIX.md`](../templates/COVERAGE-MATRIX.md) — open it before testing starts
5. The mode matching the engagement, then the relevant domain guides
6. [`guides/REPORTING.md`](guides/REPORTING.md), then
   [`guides/DECISION-MATRIX.md`](guides/DECISION-MATRIX.md) →
   [`guides/SEVERITY-RATING.md`](guides/SEVERITY-RATING.md) →
   [`guides/REFERENCE-MAPPINGS.md`](guides/REFERENCE-MAPPINGS.md) →
   [`guides/REMEDIATION-AND-RETEST.md`](guides/REMEDIATION-AND-RETEST.md)

Unknown terminology: [`GLOSSARY.md`](GLOSSARY.md).
Structure and precedence: [`../ARCHITECTURE.md`](../ARCHITECTURE.md).

## Design goal

The documentation is intentionally detailed. The agent should investigate deeply
and continuously within scope, while never fabricating exploit evidence,
downloaded artifacts, payment results, or runtime capabilities.

Read [`../SECURITY.md`](../SECURITY.md) before applying any of this material to
a live system.
