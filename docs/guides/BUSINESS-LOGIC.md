# Business-Logic and State-Machine Testing

## Goal
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

Identify flaws that arise because the workflow permits an impossible or unintended business state.

## Model

Represent the workflow explicitly:

```text
STATE A → STATE B → STATE C → STATE D
```

Then ask for each transition:

- Can it be skipped?
- Can it be repeated?
- Can it be reversed?
- Can it be replayed?
- Can it be performed by another actor?
- Can the object identifier be changed?
- Can state from another object be reused?
- Can simultaneous requests create inconsistent state?

## Common areas

- pricing;
- subscriptions;
- coupons;
- purchase quantities;
- refunds;
- cancellations;
- premium entitlements;
- download permissions;
- quotas;
- roles;
- workflow approvals;
- attendance/marks/record-management operations;
- administrative transitions.

## State validation

The agent should capture state immediately before and after a sensitive operation. If state cannot be observed, record the exact evidence that supports the conclusion and label uncertainty.
