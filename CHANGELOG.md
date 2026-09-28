# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Because this repository contains documentation only, versions track
documentation maturity rather than software releases.

## [Unreleased]

Nothing yet.

## [1.0.0] — 2026-09-28

Initial public release of the BLACKHEART adversarial security research
framework as a documented, structured project.

### Added

**Core operational modes**

- `docs/modes/SECURITY-AUDIT.md` — full-spectrum adversarial vulnerability
  assessment: attack-surface mapping, technical vulnerability classes,
  mobile/APK analysis, and exploit chaining.
- `docs/modes/SECURITY-RESEARCH-MODE.md` — structured research methodology:
  deep investigation loop, trust-boundary mapping, authentication lifecycle,
  API state-machine testing, and safe exploit validation.
- `docs/modes/DIGITAL-ASSET-DELIVERY-MODE.md` — end-to-end payment integrity,
  entitlement creation, download authorization bypass, and real-artifact
  validation for digital-product platforms.
- `docs/modes/ZERO-CREDENTIAL-ESCALATION-MODE.md` — three consolidated control
  layers: zero-credential attack-surface discovery from absolute zero
  privilege; continuous adversarial method escalation where a failed technique
  never closes an objective; and the gap-closure coverage-control engine
  (objective matrices, proof-strength levels, differential testing, chaining,
  coverage accounting, and formal stop conditions).

**Domain guides** (`docs/guides/`)

- `OPERATING-RULES.md` — behavioural safety rules and non-fabrication
- `SCOPE.md` — target intake schema and authorization verification
- `WORKFLOW.md` — end-to-end assessment lifecycle
- `EVIDENCE.md` — evidence hierarchy, chain of custody, redaction
- `AUTH-AUTHZ.md` — authentication lifecycle, BOLA/IDOR, RBAC
- `BUSINESS-LOGIC.md` — workflow skipping, races, state machines
- `WEB-API-TESTING.md` — endpoint discovery, parameter tampering, API testing
- `ANDROID-TESTING.md` — APK/AAB, WebView, intent and IPC security
- `PAYMENT-PREMIUM-TESTING.md` — payment, entitlement, premium access
- `DIGITAL-FILE-VALIDATION.md` — real artifact verification and hashing
- `TOOL-AND-ENVIRONMENT.md` — capability discovery and tool honesty
- `DECISION-MATRIX.md` — finding classification rules
- `REPORTING.md` — report structure and writing standards

**Templates** (`templates/`)

- `FINDING.md` — individual finding record
- `TEST-LOG.md` — hypothesis/execution journal
- `FINAL-REPORT.md` — full assessment report skeleton

**Examples** (`examples/`)

- `NEW-PROJECT-BOOTSTRAP.md` — engagement bootstrap prompt

**Project governance**

- `AGENT.md` — master agent instruction and execution standard
- `README.md` — project overview, structure, and navigation
- `FILE-INDEX.txt` — authoritative document index
- `LICENSE` — MIT License
- `SECURITY.md` — security policy and responsible-use policy
- `CONTRIBUTING.md` — contribution guidelines
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1
- `AUTHOR` — authorship and third-party attribution
- `CHANGELOG.md` — this file

### Changed

- Reorganised the repository into `docs/modes/`, `docs/guides/`, `examples/`,
  and `templates/`, replacing the previous flat `BLACKHEART-AGENT-DOCUMENTATION/`
  package layout. All file content preserved; all internal links updated.
- Registered the zero-credential/escalation/coverage mode as Core Mode 4 in
  `README.md` and `FILE-INDEX.txt`.
- Standardised authorship to **Roshan** across project metadata.

### Notes

- No third-party code, vendored libraries, or external datasets are included.
- No original document content was removed during the reorganisation.

[Unreleased]: https://github.com/devara1983ntr/blackheart-security-framework/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/devara1983ntr/blackheart-security-framework/releases/tag/v1.0.0
