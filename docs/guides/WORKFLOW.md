# End-to-End Assessment Workflow

## Phase 0 — Scope intake
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

Capture target, authorization, environment, accounts, allowed assets, payment scope, file-delivery scope, and prohibited actions.

## Phase 1 — Capability discovery

Inventory the actual tools, runtime, credentials, source artifacts, traffic visibility, and file-handling capabilities.

## Phase 2 — Asset discovery

Map domains, routes, APIs, application components, downloads, payment paths, storage, authentication, and external dependencies.

## Phase 3 — Trust-boundary mapping

For each sensitive operation identify:

- actor;
- object;
- trust boundary;
- enforcement point;
- state transition;
- sensitive output.

## Phase 4 — Baseline behavior

Record normal successful and failed workflows before manipulation.

## Phase 5 — Attack hypotheses

Generate prioritized hypotheses from the discovered architecture. Do not use blind random payloads.

## Phase 6 — Controlled exploitation

Change one relevant variable at a time and preserve the evidence.

## Phase 7 — Validation

Validate the actual security impact rather than stopping at an intermediate behavior.

## Phase 8 — Alternative paths

Explore alternate endpoints, state representations, workflow orderings, identifiers, and authorized roles.

## Phase 9 — Chain analysis

Assess whether multiple weaknesses combine into a stronger impact.

## Phase 10 — Artifact validation

For successful protected-file acquisition, verify the actual file and calculate a cryptographic hash.

## Phase 11 — Root cause and remediation

Identify the actual failed control and the design-level fix.

## Phase 12 — Reporting

Produce evidence-linked findings plus clear coverage and limitations.
