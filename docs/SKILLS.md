# Skills Map

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

## What this document is

A map from real assessment competencies to the documents in this repository
that develop them.

It is **not** a claim about anyone's experience, certifications, or professional
history, and it contains no self-assessment. It answers a narrower and more
useful question: *if I want to get better at this specific thing, which file do
I read?*

## How to use it

Work a row top to bottom for a domain. Each row is a competency, and the
documents listed are the framework's actual treatment of it.

A competency is only held once you can perform it unaided against a target you
are authorized to test. Reading is not the same as capability, and this
framework never treats it as such.

---

## 1. Engagement and authorization

| Competency | Document |
|---|---|
| Establishing that authorization exists before testing | [`../AGENT.md`](../AGENT.md) §3 · [`guides/SCOPE.md`](guides/SCOPE.md) |
| Resolving scope ambiguity without guessing | [`guides/SCOPE.md`](guides/SCOPE.md) |
| Classifying third-party dependencies and holding the boundary | [`guides/SCOPE.md`](guides/SCOPE.md) §3 |
| Recording capability and tool substitution honestly | [`templates/ENGAGEMENT-RECORD.md`](../templates/ENGAGEMENT-RECORD.md) · [`guides/TOOL-AND-ENVIRONMENT.md`](guides/TOOL-AND-ENVIRONMENT.md) |
| Managing production validation with data minimisation | [`../AGENT.md`](../AGENT.md) §14 · [`guides/SCOPE.md`](guides/SCOPE.md) §4 |

## 2. Method

| Competency | Document |
|---|---|
| Stating a security property before testing it | [`../AGENT.md`](../AGENT.md) §6 |
| Locating the actual enforcement point | [`../AGENT.md`](../AGENT.md) §6 Step 2 |
| Forming testable attack hypotheses | [`../AGENT.md`](../AGENT.md) §6 Step 3 |
| Escalating method instead of stopping early | [`modes/ZERO-CREDENTIAL-ESCALATION-MODE.md`](modes/ZERO-CREDENTIAL-ESCALATION-MODE.md) · [`../AGENT.md`](../AGENT.md) §7 |
| Running differential tests between two states or actors | [`modes/ZERO-CREDENTIAL-ESCALATION-MODE.md`](modes/ZERO-CREDENTIAL-ESCALATION-MODE.md) |
| Judging proof strength for a claim | [`modes/ZERO-CREDENTIAL-ESCALATION-MODE.md`](modes/ZERO-CREDENTIAL-ESCALATION-MODE.md) |
| Maintaining coverage control across an engagement | [`templates/COVERAGE-MATRIX.md`](../templates/COVERAGE-MATRIX.md) |
| Zero-credential attack-surface discovery | [`modes/ZERO-CREDENTIAL-ESCALATION-MODE.md`](modes/ZERO-CREDENTIAL-ESCALATION-MODE.md) |

## 3. Web and API

| Competency | Document |
|---|---|
| Building an endpoint and attack-surface inventory | [`../AGENT.md`](../AGENT.md) §8 · [`guides/WEB-API-TESTING.md`](guides/WEB-API-TESTING.md) |
| Finding BOLA/IDOR by object-identifier substitution | [`guides/WEB-API-TESTING.md`](guides/WEB-API-TESTING.md) · [`guides/AUTH-AUTHZ.md`](guides/AUTH-AUTHZ.md) |
| Finding BFLA through role testing | [`guides/AUTH-AUTHZ.md`](guides/AUTH-AUTHZ.md) |
| Testing horizontal and vertical boundaries | [`guides/AUTH-AUTHZ.md`](guides/AUTH-AUTHZ.md) |
| Detecting mass assignment and property-level over-posting | [`guides/WEB-API-TESTING.md`](guides/WEB-API-TESTING.md) |
| Detecting client/server validation mismatch | [`../AGENT.md`](../AGENT.md) §8 · [`guides/WEB-API-TESTING.md`](guides/WEB-API-TESTING.md) |
| Full authentication lifecycle analysis | [`../AGENT.md`](../AGENT.md) §9 · [`guides/AUTH-AUTHZ.md`](guides/AUTH-AUTHZ.md) |
| Mapping findings to OWASP and CWE | [`guides/REFERENCE-MAPPINGS.md`](guides/REFERENCE-MAPPINGS.md) |

## 4. Business logic and state

| Competency | Document |
|---|---|
| Modelling a workflow as a state machine | [`guides/BUSINESS-LOGIC.md`](guides/BUSINESS-LOGIC.md) · [`../AGENT.md`](../AGENT.md) §11 |
| Detecting skipped, reordered, and replayed transitions | [`guides/BUSINESS-LOGIC.md`](guides/BUSINESS-LOGIC.md) |
| Race conditions and TOCTOU on state transitions | [`guides/BUSINESS-LOGIC.md`](guides/BUSINESS-LOGIC.md) |
| Distinguishing possibility from actual impact | [`../AGENT.md`](../AGENT.md) §6 Step 5 · [`guides/DECISION-MATRIX.md`](guides/DECISION-MATRIX.md) |
| Building attack chains from weak findings | [`../AGENT.md`](../AGENT.md) §22 |

## 5. Payment and digital products

The framework's most specialised area, and the one most often reported wrongly.

| Competency | Document |
|---|---|
| Decomposing the payment chain into stages | [`../AGENT.md`](../AGENT.md) §12 · [`guides/PAYMENT-PREMIUM-TESTING.md`](guides/PAYMENT-PREMIUM-TESTING.md) |
| Testing price and discount integrity | [`guides/PAYMENT-PREMIUM-TESTING.md`](guides/PAYMENT-PREMIUM-TESTING.md) |
| Testing order/payment/user binding | [`guides/PAYMENT-PREMIUM-TESTING.md`](guides/PAYMENT-PREMIUM-TESTING.md) |
| Verifying payment state from a trusted source | [`guides/PAYMENT-PREMIUM-TESTING.md`](guides/PAYMENT-PREMIUM-TESTING.md) |
| Testing webhook signature, freshness, and idempotency | [`guides/PAYMENT-PREMIUM-TESTING.md`](guides/PAYMENT-PREMIUM-TESTING.md) |
| Separating payment weakness from entitlement bypass | [`guides/DECISION-MATRIX.md`](guides/DECISION-MATRIX.md) · [`guides/SEVERITY-RATING.md`](guides/SEVERITY-RATING.md) |
| Testing entitlement scoping, binding, and revocation | [`guides/PAYMENT-PREMIUM-TESTING.md`](guides/PAYMENT-PREMIUM-TESTING.md) |
| Testing signed-URL and download authorization | [`guides/PAYMENT-PREMIUM-TESTING.md`](guides/PAYMENT-PREMIUM-TESTING.md) |
| Validating a real protected artifact and hashing it | [`guides/DIGITAL-FILE-VALIDATION.md`](guides/DIGITAL-FILE-VALIDATION.md) · [`modes/DIGITAL-ASSET-DELIVERY-MODE.md`](modes/DIGITAL-ASSET-DELIVERY-MODE.md) |
| Handling payment data and PCI context responsibly | [`guides/REFERENCE-MAPPINGS.md`](guides/REFERENCE-MAPPINGS.md) §5 |

## 6. Mobile

| Competency | Document |
|---|---|
| Static APK/AAB assessment without a runtime | [`../AGENT.md`](../AGENT.md) §15, §17 · [`guides/ANDROID-TESTING.md`](guides/ANDROID-TESTING.md) |
| Manifest and component analysis | [`guides/ANDROID-TESTING.md`](guides/ANDROID-TESTING.md) |
| Exported-component impact analysis | [`guides/ANDROID-TESTING.md`](guides/ANDROID-TESTING.md) |
| WebView and JavaScript bridge analysis | [`../AGENT.md`](../AGENT.md) §16 |
| Deep link and custom-scheme authorization | [`../AGENT.md`](../AGENT.md) §16 |
| Local data storage and secret exposure | [`guides/ANDROID-TESTING.md`](guides/ANDROID-TESTING.md) |
| Mapping mobile findings to MASVS and OWASP Mobile | [`guides/REFERENCE-MAPPINGS.md`](guides/REFERENCE-MAPPINGS.md) §3 |

## 7. Evidence and reporting

| Competency | Document |
|---|---|
| Capturing evidence that withstands review | [`guides/EVIDENCE.md`](guides/EVIDENCE.md) |
| Applying the minimum-evidence principle | [`guides/EVIDENCE.md`](guides/EVIDENCE.md) · [`../AGENT.md`](../AGENT.md) §14 |
| Hashing and validating real artifacts | [`guides/EVIDENCE.md`](guides/EVIDENCE.md) · [`guides/DIGITAL-FILE-VALIDATION.md`](guides/DIGITAL-FILE-VALIDATION.md) |
| Assigning the correct evidence status | [`../AGENT.md`](../AGENT.md) §5 · [`guides/DECISION-MATRIX.md`](guides/DECISION-MATRIX.md) |
| Rating severity from demonstrated impact | [`guides/SEVERITY-RATING.md`](guides/SEVERITY-RATING.md) |
| Writing a finding that is actionable | [`templates/FINDING.md`](../templates/FINDING.md) · [`guides/REPORTING.md`](guides/REPORTING.md) |
| Writing a complete engagement report | [`templates/FINAL-REPORT.md`](../templates/FINAL-REPORT.md) · [`guides/REPORTING.md`](guides/REPORTING.md) |
| Recording negative results as evidence | [`../AGENT.md`](../AGENT.md) §23 |
| Passing the pre-delivery quality gate | [`../AGENT.md`](../AGENT.md) §26 |

## 8. Remediation

| Competency | Document |
|---|---|
| Identifying root cause at the enforcement point | [`guides/REMEDIATION-AND-RETEST.md`](guides/REMEDIATION-AND-RETEST.md) |
| Recommending a fix that closes the class, not the instance | [`guides/REMEDIATION-AND-RETEST.md`](guides/REMEDIATION-AND-RETEST.md) |
| Designing a runnable regression test | [`guides/REMEDIATION-AND-RETEST.md`](guides/REMEDIATION-AND-RETEST.md) |
| Running a retest and classifying the outcome | [`guides/REMEDIATION-AND-RETEST.md`](guides/REMEDIATION-AND-RETEST.md) |

## 9. Professional practice

| Competency | Document |
|---|---|
| Refusing to fabricate a result | [`../AGENT.md`](../AGENT.md) §27 · [`guides/OPERATING-RULES.md`](guides/OPERATING-RULES.md) Rule 3 |
| Refusing to test outside authorization | [`../AGENT.md`](../AGENT.md) §2 · [`guides/SCOPE.md`](guides/SCOPE.md) |
| Reporting tool limitations honestly | [`guides/TOOL-AND-ENVIRONMENT.md`](guides/TOOL-AND-ENVIRONMENT.md) |
| Operating at controlled aggressiveness | [`guides/OPERATING-RULES.md`](guides/OPERATING-RULES.md) Rule 10 |
| Keeping assessment automation bounded | [`../AGENT.md`](../AGENT.md) §19 |
| Handling real personal data defensively | [`../AGENT.md`](../AGENT.md) §14 · [`../SECURITY.md`](../SECURITY.md) |
| Running a methodology without causing harm | [`../SECURITY.md`](../SECURITY.md) · [`../CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md) |

---

## The competency that holds the rest together

Every other row is technical. One is not, and it is the one the framework
treats as non-negotiable:

> **Knowing the difference between what you proved and what you suspect.**

A tester who confuses the two produces work that is not merely imprecise but
actively harmful — it sends engineering effort toward findings that do not
exist, and it teaches the recipient to distrust the reports that do.

If only one competency from this document is retained, retain that one.
