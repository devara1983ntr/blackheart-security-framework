# Scope and Authorization Rules

## 1. Scope hierarchy
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

Use this order of authority:

1. Explicit user-provided assessment scope.
2. Written authorization and engagement rules.
3. Explicitly identified systems/accounts/products.
4. Technical relationships discovered during reconnaissance.

A technical relationship does not automatically create authorization.

## 2. Allowed target categories

The agent may deeply assess explicitly authorized:

- websites;
- web applications;
- APIs;
- mobile applications;
- APK/AAB packages;
- repositories;
- digital-product systems;
- premium-feature systems;
- file-delivery services owned/authorized by the user;
- payment integrations where payment testing is explicitly authorized;
- staging and sandbox environments.

## 3. Third-party services

If a target calls an outside provider, classify it as:

- `AUTHORIZED THIRD-PARTY`
- `DEPENDENCY / OBSERVATION ONLY`
- `OUT OF SCOPE`

Do not actively test vendor infrastructure merely because the target uses it.

## 4. Production

Production testing is allowed only to the extent explicitly authorized.
When production validation is authorized, minimize real-user exposure and prefer canary/synthetic data.

## 5. Scope change

When a newly discovered asset would materially expand scope, record:

- asset;
- relationship to target;
- why it matters;
- authorization status;
- whether active testing is permitted.

Never silently convert a discovered dependency into a new attack target.
