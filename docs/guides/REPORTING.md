# Reporting Standard

## Required report sections
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

1. Cover / assessment identity
2. Scope and authorization summary
3. Environment and capabilities
4. Target inventory
5. Methodology
6. Trust boundaries
7. Attack-surface map
8. Authentication results
9. Authorization results
10. API results
11. Business-logic results
12. Payment/premium results
13. File-delivery results
14. Android/mobile results
15. WebView/deep-link results
16. Secrets/storage results
17. Confirmed vulnerabilities
18. Confirmed attack chains
19. Failed hypotheses
20. Untested/unverified areas
21. Root causes
22. Remediation
23. Regression tests
24. Evidence index
25. Final coverage and limitations

## Finding structure

```markdown
# FINDING-001 — [Title]

Status: CONFIRMED

## Summary

## Affected Asset

## Security Property

## Preconditions

## Normal Workflow

## Attack Hypothesis

## Reproduction

## Observed Evidence

## Security Boundary Failure

## Root Cause

## Actual Impact

## Attack-Chain Analysis

## Artifact Evidence

## Remediation

## Regression Test

## Limitations
```

## Writing rules

Use concrete factual language.

Avoid:

- “obviously vulnerable”;
- “complete takeover” unless actually proven;
- “critical” without an impact basis;
- “hacked” when only an intermediate condition was demonstrated.

Prefer:

- “confirmed”;
- “observed”;
- “not observed”;
- “not tested”;
- “partially confirmed”;
- “the evidence indicates”;
- “the remaining chain could not be validated because …”.
