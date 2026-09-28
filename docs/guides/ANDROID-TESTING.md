# Android / APK / AAB Security Testing

## Static assessment
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

Inventory:

- package name;
- version/version code;
- signing metadata;
- manifest;
- activities;
- services;
- receivers;
- providers;
- intent filters;
- permissions;
- network security configuration;
- WebViews;
- JavaScript interfaces;
- storage mechanisms;
- API clients;
- payment components;
- file/download handlers;
- deep links;
- embedded secrets and endpoints.

## Runtime assessment

Where an authorized Android runtime is available, validate:

- exported-component access;
- intent manipulation;
- deep-link authorization;
- WebView navigation;
- JavaScript bridge exposure;
- storage of tokens/secrets;
- certificate/TLS behavior;
- API authorization;
- premium state enforcement;
- payment callbacks;
- file handling.

## Important interpretation rules

`exported=true` is an exposure indicator, not automatically a vulnerability.

`usesCleartextTraffic=true` is a configuration weakness indicator, not proof that sensitive credentials traverse insecure HTTP.

A hardcoded endpoint is not necessarily a secret.

Client-side premium checks are security-relevant only when protected operations can actually be invoked without equivalent server-side controls.
