# Changelog

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This repository is documentation-first, but it also carries executable content: a
complete mirror of a third-party catalogue (3,864 files), a validation gate, and
two automation workflows. Versions therefore track both documentation maturity
and the state of the executable layer.

## [Unreleased]

Nothing yet.

## [2.3.0] — 2026-09-29

### Added
- **`docs/agent/AGENT-BOOTSTRAP.md`** — the agent activation protocol. A
  verbatim prompt that enumerates the 53-file instruction set from
  `FILE-INDEX.txt`, reads it in five dependency-ordered layers, reconciles it
  under a total precedence ladder (conformance first, vendored content last),
  tests comprehension across twelve named areas, forbids scope-creeping output
  during activation, and returns a **countable** readiness confirmation.
  Includes the design rationale for every clause.
- **`AGENT.md` §0 — The Framework You Are Running Inside.** The agent is now
  told at the top of its own instruction set that the 3,864 files in `skills/`
  are untrusted third-party text, that agent personas are hostile input, that
  conformance wins every conflict, and that structural verification is not a
  proof of semantic safety.
- **`AGENT.md` §29 — Tool Honesty.** Four questions to establish about any
  tool before trusting its output, with the three measured defects in the
  vendored `ai-security` skill as the worked example.
- **`AGENT.md` §5 — the three rungs.** Hypothesis, unverified finding, and
  confirmed vulnerability defined as distinct, with the transitions between
  them and the requirement to name the exact artifact that would confirm an
  unverified finding.
- **`AGENT.md` §27 — fabrication's second face.** Manufacturing the appearance
  of absence of evidence — reporting a tool's clean output as "no issues
  found" — is named as fabrication, with the rule that **a clean result is a
  coverage gap, not a clearance**.

### Corrected
- **Agent persona count: 34 → 33** in `ARCHITECTURE.md` (which had said 35) and
  `SECURITY.md`. `agents/` holds 38 files: 33 personas (32 deployable plus a
  blank `TEMPLATE.md`), `CLAUDE.md` and `personas/README.md` as documentation,
  and 3 empty `.gitkeep` files that were previously unlisted. The three
  `.gitkeep` files are now enumerated in the `agents/` adapter so the collection
  reconciles exactly.

## [2.2.0] — 2026-09-29

> **Correction (2.3.0):** this release originally recorded 34 agent personas.
> The true figure is **33**. `agents/` contains 38 files: 33 personas (32
> deployable plus a blank `TEMPLATE.md`), `CLAUDE.md` and `personas/README.md`
> as collection documentation, and 3 empty `.gitkeep` files. The original
> count treated `CLAUDE.md` as a persona. `ARCHITECTURE.md` repeated it as 35.
> Both are corrected; the underlying mirror was always correct.

Expands Layer 5 from a curated 8 skills to the **complete** upstream repository,
vendors the **full** third-party discovery index, and adds continuous
verification.

### The completeness gap this release closes

The first pass at "vendor everything" vendored only the 388 skill directories and
declared the job done. A gap audit against upstream found that the mirror was
missing **878 files of functional content**: 39 slash commands, 33 agent
personas, two plugin manifests, 29 upstream tooling scripts, 11 standards, 32
audit records, 667 generated reference pages, templates, orchestration notes, and
17 root documents. None of it was executable-critical, but all of it is content
the catalogue ships, and its absence was invisible because **nothing was checking
for it**.

### Added

- **The rest of the upstream repository**, vendored verbatim: `commands/`,
  `agents/`, `scripts/`, `standards/`, `audit/`, `docs/`, `templates/`,
  `orchestration/`, `custom-gpt/`, `assets/`, `.claude-plugin/`,
  `.codex-plugin/`, `.claude/`, and the 17 root documents. The mirror is now
  upstream's tree in full — **3,864 files**, every one byte-identical to
  `19392f7`.
- **12 collection adapters** covering commands, agent personas, upstream tooling,
  standards, audit history, documentation, templates, and the plugin manifests.
- **`.github/scripts/gen_adapters.py`**, **`gen_collection_adapters.py`**,
  **`gen_config.py`**, **`gen_manifest.py`** — adapter, config, and manifest
  generation are now reproducible scripts in the repository rather than
  throwaway code. Anything the mirror's contents determine is generated from the
  mirror, so drift between content and record is a build failure.
- **`.github/scripts/sync_upstream.py` rewritten** to compare the **whole mirror
  file by file**. The previous version compared per-skill digests, which would
  have let all the non-skill content drift undetected — the same blind spot that
  allowed the gap above.
- **The example config now loads `commands/` and `agents/`**, and declares that
  vendored personas are *not* enabled by default: adopting a persona is an
  explicit decision, not a default.

### Changed

- **Integrity is now file-level, not per-skill.** `.github/UPSTREAM-MANIFEST.json`
  records a SHA-256 for all 3,864 vendored files and 399 adapters. The
  validator distinguishes vendored files, Blackhearts-local adapters, and
  unaccounted extras, so "extra file" always means "unaccounted for".
- **The adapter gate now requires collection adapters too.** A vendored
  command, persona, or plugin manifest without one fails the build.

### Fixed

- **`sync_upstream.py` was left broken** by the manifest schema change — it read
  `manifest["skills"]`, which no longer exists. Found by running the script
  rather than assuming it worked.
- **The config generator emitted invalid JSON5** on first run: the
  `commands/` and `agents/` paths were emitted *after* the `extraDirs` array was
  closed, so they were not being loaded at all. Caught by parsing the file.
- **`playwright-pro/skills/coverage` lost its adapter** during bulk extraction,
  because `tar` replaced the directory. Caught by the integrity check, restored
  from git, and verified.

### Deliberately not vendored

| Excluded | Files | Reason |
|---|---:|---|
| `.gemini/`, `.codex/`, `.vibe/`, `.hermes/` | 1,574 | Symlink farms — all mode `120000`, each pointing at a skill already vendored. Verified by mode, not assumed. |
| `.gitignore` | 1 | Would apply to this repository's git behaviour across the mirror subtree, silently untracking vendored files. |
| `.github/` | 23 | Upstream's own CI, not catalogue content. |

Recorded in the manifest under `exclusions` so the sync workflow will not
reintroduce them.

### Security note

**Agent personas are the sharpest edge in this release.** A persona can redefine
an agent's identity, widen its scope, or instruct it to act without asking — the
exact failure the authorization gate exists to prevent, and a persona is a natural
place for that to be smuggled in. All 33 are treated as untrusted instruction,
none is enabled by default, and none may override the conformance layer. This is
documented in the collection adapter, in `SECURITY.md`, and in the example
config.

### Design decision (unchanged)

**Upstream sync opens a pull request and never merges.** Auto-merge on green CI
was rejected: it would admit unreviewed third-party code to the engagement
surface with no human reading it, defeating the control the framework exists to
enforce. Automation fetches, diffs, re-vendors, re-audits, and regenerates
adapters; a human decides. A file removed upstream is reported and left in
place, because deleting content is a human decision and not a side effect of a
cron job. Recorded as invariant 14.

### Also landed earlier in this release

- **Vendored scope: 8 → 388 skills**, byte-for-byte at `19392f7a`, with
  hand-written analysis kept for the eight promoted security skills. Full
  catalogue audit: **354 PASS, 21 WARN, 13 FAIL**, every CRITICAL and HIGH
  finding adjudicated by hand. No backdoor, covert channel, credential
  exfiltration, or safety override anywhere.
- **Third-party discovery index: 1 category → all 30**, ~5,270 URLs, all
  byte-identical to `f274daa`, still reference-only. Per-category counts in
  `skills/catalog/CATEGORY-INDEX.md`.
- **The seven-check validation gate and the daily upstream-sync workflow**, both
  canary-tested: tampering with a vendored skill, tampering with a vendored
  catalogue file, deleting an adapter, planting a realistic token, breaking the
  config, and removing an index entry each fail the build.
- **`README.md` no longer claims the repository contains no third-party code.**
  It does.

### Known issues

- 159 unresolved links inside verbatim upstream content, reported rather than
  patched so the mirror stays byte-comparable to its source. None is in
  Blackhearts-authored documentation.
- 13 skill names are defined at two upstream paths each. Both copies are
  vendored; one config entry enables both. Mapped in `skills/VENDOR.md` §5.
- `tech-debt-tracker` ships a sample codebase containing working code that POSTs
  to live Stripe, Square, and PayPal endpoints. A teaching artefact; its adapter
  marks it **never execute**.

## [2.1.0] — 2026-09-28

Integrates audited third-party skills into the framework as a new Layer 5.

### Added

- **`skills/`** — executable analysis skills, vendored and bound to the
  framework. The method stays in Layer 0; these are the tools that perform
  analysis.
- **`skills/conformance/SKILL.md`** — mandatory wrapper. Vendored skills were
  written by other authors and none knows BLACKHEART's evidence rules, so this
  converts tool output into evidence status, computes severity separately within
  the status ceiling, enforces the authorization gate, and requires an
  enforcement point on every finding carried forward. Marked `always: true`.
- **8 vendored skills** from
  [claude-skills](https://github.com/alirezarezvani/claude-skills) (MIT, Alireza
  Rezvani), pinned to commit `19392f7a`: `ai-security`, `red-team`,
  `cloud-security`, `security-pen-testing`, `dependency-auditor`,
  `threat-detection`, `senior-security`, `incident-response`. Chosen for direct
  overlap with the framework's weakest-covered areas.
- **8 `_BLACKHEART-ADAPTER.md` files** — per-skill provenance, interface,
  authorization gate, maximum claim, skill-specific cautions, and coverage
  contribution. Every adapter states what the skill's output may **not** be used
  to claim.
- **`skills/VENDOR.md`** — attribution, licences, provenance, and the reasoning
  behind every inclusion and non-inclusion decision.
- **`skills/openclaw.example.json5`** — working agent allowlists, per-skill
  gating, and install-policy configuration. Contains no secrets.
- **`skills/catalog/`** — the second source, recorded as reference only.

### Changed

- `ARCHITECTURE.md` adds Layer 5 (skills) to the layering diagram, inserts
  skill conformance into the precedence order between Layer 1 and the modes,
  and adds a thirteenth invariant: a tool's output is a hypothesis, not a
  finding.
- `README.md`, `SECURITY.md`, and `FILE-INDEX.txt` updated. Index now 76 entries.
- `AUTHOR` corrected: it previously stated the repository contained no
  third-party source code, which became untrue when the skills were vendored.
  It now records both sources, their authors, and their licences.

### Integration audit

Both sources were audited before anything was vendored. No live credentials, no
malicious code, and no exfiltration paths were found. The security scanner
raised two flags, both independently verified as **false positives** and
recorded in the adapters so they are not re-raised on every audit:

- `senior-security` — `__import__('datetime')` flagged as dynamic module
  loading. The argument is a string literal, not a variable.
- `security-pen-testing` — `pickle.load()` / `yaml.load()` flagged as unsafe
  deserialisation. Both are string literals in the scanner's own detection
  guidance for other people's code; the file makes no such call.

All 13 vendored scripts were executed and verified to run. All 8 vendored skill
directories were diffed against upstream and confirmed byte-for-byte identical.

### Deliberately not integrated

`awesome-openclaw-skills` contains **zero skills** — it is an index of roughly
5,265 links to skills on external registries. None were vendored: there is no
version pinning, no provenance verification, and no way to audit content before
it executes. Its `security-and-passwords` category lists skills whose purpose is
credential handling (`credential-manager`, `1password`, `bitwarden`, `dashlane`),
which is the highest-consequence integration mistake available. The catalogue is
preserved as a reference index with a documented vetting process instead.

## [2.0.0] — 2026-09-28

Third-pass expansion. Adds the offensive thinking layer (RED HEART), a new
Layer 0 for AI agent execution, and six new domain guides covering ground
the framework previously left to improvisation. Closes four ROADMAP gaps.

### Added — RED HEART, the offensive thinking layer

- **`docs/modes/RED-HEART-ADVERSARY-EMULATION.md`** — the framework's
  adversarial counterpart. BLACKHEART governs what may be claimed; RED HEART
  governs how an assessor thinks about the adversary. Covers adversary
  modelling, operational objectives, engagement goals (Expose / Affect /
  Elicit), path construction, chaining discipline, evasion reasoning,
  post-exploitation within authorization, human and process targets, and rules
  of engagement with hard abort conditions. Closes the failure mode where each
  control holds individually but the chain walks straight past the boundary.
- **`docs/guides/ATTACK-PATHS.md`** — path construction as a graph, with four
  explicit evidence states per edge (Demonstrated / Inferred / Hypothesised /
  Blocked). Establishes that a path is only as strong as its weakest evidenced
  edge, and that severity follows the demonstrated destination rather than the
  component findings.
- **`docs/guides/ADVERSARY-EMULATION.md`** — engagement structure adapted from
  the MITRE Engage model: prepare / operate / understand, the five approaches,
  blended objectives, safety planning, and the detection review that ordinary
  assessment does not produce.
- **`templates/ATTACK-PATH.md`** — path record with per-edge evidence, blocked
  steps as results, unproven edges with the test that would close them, and a
  detection review table.

### Added — Layer 0, the AI agent layer

- **`docs/agent/AGENT-OPERATING-PROTOCOL.md`** — an agent fails differently
  from a human: it confabulates evidence, drifts scope, reports intent as
  accomplishment. Those failures are systematic, so they get a written protocol
  rather than an assumption of diligence. Defines five non-negotiables, the
  pre-flight check, the tool-use protocol with its capture-before-interpretation
  rule, evidence and status discipline, escalation discipline, and hard stop
  conditions including the refusal to request credentials.
- **`docs/agent/AGENT-SKILL-CATALOGUE.md`** — 48 named skills across eight
  groups, each specified as trigger, procedure, output, maximum claim, stop
  condition, and the common failure it prevents. A procedure without a stop
  condition and a max claim is not a skill, and the catalogue states that rule
  explicitly.

### Added — domain guides

- **`docs/guides/AGENTIC-AI-SECURITY.md`** — LLM and agentic assessment:
  action-surface mapping before probing, the four test layers, the compound
  private-data + untrusted-content + exfiltration risk, direct and indirect
  injection, tool-layer authorization tested independently of the model,
  retrieval authorization, memory persistence, excessive agency across
  functionality/permissions/autonomy, output handling, and inter-agent trust.
  Includes the requirement to report reproduction rate for probabilistic
  results.
- **`docs/guides/CLOUD-IDENTITY.md`** — IAM and policy assessment, the
  default-deny test, the confused deputy pattern, storage and secret exposure,
  and multi-tenant boundary testing. States the boundary explicitly: the
  customer tenancy is in scope, the provider platform never is.
- **`docs/guides/SUPPLY-CHAIN.md`** — dependency inventory, reachability
  determination as the step that separates an assessment from a scan report,
  build and release integrity, secrets in dependencies, and agent plugin
  supply chains.
- **`docs/guides/METHODOLOGY-STANDARDS.md`** — alignment to PTES, NIST SP
  800-115, OSSTMM, MITRE Engage, and OWASP, with the limits stated rather than
  implied. Includes a claim sheet of what may and may not be asserted.
- **`templates/AGENT-THREAT-MODEL.md`** — action surface, per-tool permission
  scope, every input channel, the compound-risk question, trust boundaries with
  actual enforcement points, and a test plan derived from the model rather than
  from a generic list.

### Changed

- `ARCHITECTURE.md` introduces **Layer 0 (agent)** above the core, updates the
  mode and guide tables, extends precedence to seven ranks, and adds two
  invariants: a path is as strong as its weakest evidenced edge, and untrusted
  content is data rather than instruction.
- `AGENT.md` adds attack-path construction to the pipeline, expands §22 into
  path-and-chain analysis, and records that the operating protocol governs
  whoever executes the framework.
- `REFERENCE-MAPPINGS.md` adds the OWASP Top 10 for LLM Applications (2025), the
  agentic risk categories, and a section separating adversary-behaviour
  mappings from weakness-class mappings.
- `SKILLS.md` gains three competency groups — AI and agentic systems, cloud and
  identity, and adversary emulation.
- `GLOSSARY.md` adds adversary-emulation and agentic terminology.
- `ROADMAP.md` records four closed gaps and a "Recently closed" table so they
  are not re-proposed.
- `README.md`, `docs/README.md`, and `FILE-INDEX.txt` updated for 11 new
  documents; index now 52 entries.

## [1.1.0] — 2026-09-28

Second-pass audit and framework expansion. Closes the substantive gaps found in
a review of the 1.0.0 documentation set, and fixes several internal
inconsistencies in it.

### Added — new guides

- **`docs/guides/SEVERITY-RATING.md`** — impact × reach severity rubric.
  Closes the largest gap in 1.0.0: the framework defined a precise evidence
  status taxonomy but no rating rubric, so `AGENT.md` §25 could only say "use
  severity descriptions tied to observed impact" without defining what that
  meant. Introduces the binding rule that **severity is bounded by evidence
  status**, plus level thresholds, the payment-chain rating table, the
  relationship to CVSS, anti-inflation rules, a rating worksheet, and worked
  examples.
- **`docs/guides/REFERENCE-MAPPINGS.md`** — maps the framework's own weakness
  classes onto CWE, OWASP Top 10 (2021), OWASP API Security Top 10 (2023), OWASP
  Mobile Top 10 (2024), MASVS v2, ASVS v4, PCI DSS v4.0, and GDPR. Verified
  against the publishing bodies; carries an explicit instruction to re-verify
  identifiers before client-facing use, since CWE entries are revised.
- **`docs/guides/REMEDIATION-AND-RETEST.md`** — 1.0.0 required `Remediation`
  and `Regression Test` fields and a reporting section, but no methodology
  existed for producing them. Adds root-cause identification at the enforcement
  point, fix patterns by layer, chain-specific remediation for the payment and
  entitlement stages, anti-patterns, a regression-test design method, the
  retest protocol, and the five retest outcomes.

### Added — new reference documents

- **`docs/GLOSSARY.md`** — the framework used a dense specialist vocabulary
  (BOLA, BFLA, entitlement, enforcement point, proof strength, method
  escalation, coverage control, and others) across roughly 8,000 lines with no
  terminology reference. Every entry is a term the repository actually uses.
- **`docs/SKILLS.md`** — competency-to-document map across nine domains, for
  learning and self-direction. Explicitly not a claim of experience or
  certification.
- **`ARCHITECTURE.md`** — documents the four-layer structure (core → modes →
  guides → artefacts), the precedence order that resolves conflicts between
  documents, the engagement flow, and ten framework invariants. The precedence
  order formalises a rule the zero-credential mode already declared informally.
- **`ROADMAP.md`** — recognised gaps and explicitly out-of-scope items, with no
  dates and no delivery promises. Records what will *not* be built (scanners,
  exploit collections, automated severity scoring) so it is not repeatedly
  proposed.

### Added — new templates

- **`templates/ENGAGEMENT-RECORD.md`** — operationalises the scope and
  capability requirements in `AGENT.md` §3–§4, including a capability
  inventory and a tool-substitution register. Recording capabilities before
  testing is what makes an honest `NOT TESTED` defensible afterwards.
- **`templates/COVERAGE-MATRIX.md`** — per-boundary coverage across
  authentication, authorization, API/input integrity, payment and delivery,
  mobile, and evidence handling. "Coverage control" was a named pillar of the
  framework with no artefact to track it.

### Fixed

- **Status taxonomy inconsistency.** `README.md` listed eight statuses while
  `AGENT.md` §5 defines six. `BLOCKED BY ENVIRONMENT` and `INCONCLUSIVE` were
  presented as canonical but exist nowhere in the governing document. The
  README now lists the six canonical statuses and maps both variants to their
  correct equivalent, noting that a blocker is a *reason* recorded under
  `NOT TESTED`, not a status in its own right.
- **`DECISION-MATRIX.md` structure.** An author metadata line had been appended
  into the final row of the status table, corrupting it. Restored the table,
  and added worked examples plus an explicit note that status and severity are
  separate axes.
- **`SECURITY-AUDIT.md` and `DIGITAL-ASSET-DELIVERY-MODE.md` rendering.** Both
  were plain-text documents with no Markdown heading, so they rendered without
  a title, carried no author metadata, and were unreachable from documentation
  navigation. Both now have proper headings and metadata blocks; the original
  body text is unchanged.

### Changed

- `AGENT.md` §3 now points to the engagement-record template.
- `AGENT.md` §25 now binds severity to the new rubric and states the
  evidence-ceiling rule as normative.
- `AGENT.md` §26 quality gate gained five checks covering severity discipline
  and coverage reporting, and now names the coverage matrix as a required
  deliverable.
- `templates/FINDING.md` gained `Enforcement point`, `Standard mappings`, and
  an explicit evidence-ceiling check, and its severity field now states when to
  leave the rating blank.
- `templates/FINAL-REPORT.md` gained severity and mapping columns, a
  distribution block, a remediation table, and a required coverage statement.
- `docs/README.md` gained reference sections and a suggested reading order.
- `README.md` gained severity and reporting-chain sections, updated navigation
  and directory tree, and a corrected status taxonomy.
- `FILE-INDEX.txt` updated to 41 entries.

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
