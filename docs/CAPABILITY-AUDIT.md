# Capability Audit

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Audited:** 2026-09-29 · **Baseline:** `9e54e5745082b7220c718fbb4b540753df957e54`

## What this document is

A record of what this framework can and cannot do, checked against the tree
rather than against its own claims, and of the decisions taken when a capability
turned out to be missing.

It exists because "we cover that" is not evidence. Every row below names the
document, script or collection that implements the capability, so a reader can
check the row instead of trusting it. Where a capability is **not** held, that is
stated as plainly as where it is — an unstated gap reads as coverage.

Three families are classified: the security work this framework does (29
capabilities), the engineering work it does on itself (15), and the framework
machinery that carries both (18). Sixty-two in total, none of them aspirational.

This is not a feature list and not a roadmap. Nothing here is aspirational.

## How it was checked

| Step | What was done |
|---|---|
| Inventory | Every authored document, script, workflow, manifest and template enumerated; the 388 vendored skills and 12 vendored collections listed from the mirror |
| Coverage | Each capability searched across `AGENT.md`, `ARCHITECTURE.md`, `README.md`, `SECURITY.md`, `docs/`, `templates/` and the vendored skill set — path-level hits, not impressions |
| Gaps | A capability is only called covered if a named file implements it; only called missing if nothing does |
| Verification | `python3 .github/scripts/verify_capability_audit.py` — read-only, re-derives the counts this document publishes |

## Classifications used

```text
ALREADY COVERED   a named file implements it; the row cites it
PARTIAL           implemented for part of the surface, with the limit stated
REAL GAP          nothing implemented it, and it belonged here  -> closed, see below
OPTIONAL          not held, and deliberately left to the vendored skills
OUT OF SCOPE      not held, with a reason that is about this framework's purpose
DUPLICATE         two implementations of the same thing  -> none found
```

## 1. Security capabilities

| Capability | Status | Evidence |
|---|---|---|
| Reconnaissance | ALREADY COVERED | `AGENT.md` §4 · `guides/SCOPE.md` · `modes/ZERO-CREDENTIAL-ESCALATION-MODE.md` |
| OSINT | PARTIAL | `guides/METHODOLOGY-STANDARDS.md` names it; there is no standalone OSINT procedure. Deliberate: `AGENT.md` §14 and `guides/EVIDENCE.md` bound collection to the minimum needed to prove a boundary |
| Web security | ALREADY COVERED | `guides/WEB-API-TESTING.md` · `AGENT.md` §8 |
| API security | ALREADY COVERED | `guides/WEB-API-TESTING.md` · `AGENT.md` §8 · BOLA/BFLA in `guides/AUTH-AUTHZ.md` |
| Authentication testing | ALREADY COVERED | `guides/AUTH-AUTHZ.md` · `AGENT.md` §9 |
| Authorization testing | ALREADY COVERED | `guides/AUTH-AUTHZ.md` §4–§6 · `AGENT.md` §10 |
| Access-control testing | ALREADY COVERED | as above, horizontal and vertical boundaries |
| Vulnerability assessment | ALREADY COVERED | `modes/SECURITY-AUDIT.md` · `modes/SECURITY-RESEARCH-MODE.md` |
| Source-code analysis | ALREADY COVERED | `AGENT.md` §17 Source and Static Analysis · `modes/SECURITY-AUDIT.md` |
| Dependency analysis | ALREADY COVERED | `guides/SUPPLY-CHAIN.md` §2 reachability · vendored `dependency-auditor` with its own vulnerable corpus |
| Secrets detection | ALREADY COVERED | `AGENT.md` §18 · `SECURITY.md` · the `secrets` check in `validate.py` · `.github/secret-allowlist.json` |
| Supply-chain security | ALREADY COVERED | `guides/SUPPLY-CHAIN.md` · `skills/VENDOR.md` · `.github/UPSTREAM-MANIFEST.json` · 399 adapters · Rule 0 in `AGENT.md` §0 |
| Cloud security | ALREADY COVERED | `guides/CLOUD-IDENTITY.md` §2–§8 · vendored `cloud-security`, `aws-solution-architect`, `azure-cloud-architect`, `gcp-cloud-architect`, `ms365-tenant-manager` |
| Container security | PARTIAL | `guides/CLOUD-IDENTITY.md` and `guides/SUPPLY-CHAIN.md` touch image and registry integrity; there is no container-specific procedure. The vendored `docker-development` and `senior-devops` skills carry the depth. Deliberate — see §5 |
| Infrastructure security | PARTIAL | Covered through `guides/CLOUD-IDENTITY.md` and `guides/SUPPLY-CHAIN.md` §4 rather than as a standalone infrastructure guide |
| Network security | PARTIAL | Named across 11 authored documents; no standalone network-assessment procedure. Deliberate — engagements in scope are web, API, mobile, payment and agentic surfaces |
| Mobile security | ALREADY COVERED | `guides/ANDROID-TESTING.md` · `AGENT.md` §15, §16 · MASVS and OWASP Mobile in `guides/REFERENCE-MAPPINGS.md` §3 |
| Configuration security | ALREADY COVERED | `AGENT.md` §4 · `guides/TOOL-AND-ENVIRONMENT.md` · and this repository's own configuration, now parse-checked (see §4) |
| Threat modeling | ALREADY COVERED | `templates/AGENT-THREAT-MODEL.md` · `guides/AGENTIC-AI-SECURITY.md` §4 · `guides/METHODOLOGY-STANDARDS.md` |
| Secure development | PARTIAL | `guides/REMEDIATION-AND-RETEST.md` gives fix patterns and regression tests; this is an assessment framework, not an SDLC. Vendored `security-guidance`, `tdd-guide`, `code-reviewer` carry the authoring side |
| DevSecOps | PARTIAL | Assessment-side: `guides/SUPPLY-CHAIN.md` §4 build and publish integrity. Repository-side: the six workflows in §4 |
| CI/CD security | ALREADY COVERED | `guides/SUPPLY-CHAIN.md` §4 · and enforced on this repository by `validate.yml`, `authored-scan.yml` |
| Evidence collection | ALREADY COVERED | `guides/EVIDENCE.md` · `AGENT.md` §20 · `templates/TEST-LOG.md`, `templates/COVERAGE-MATRIX.md` |
| Reporting | ALREADY COVERED | `guides/REPORTING.md` · `AGENT.md` §24 · `templates/FINDING.md`, `templates/FINAL-REPORT.md` |
| Remediation guidance | ALREADY COVERED | `guides/REMEDIATION-AND-RETEST.md` — root cause, class-level fix, retest classification |
| Security validation | ALREADY COVERED | `AGENT.md` §21 Exploit Validation Standard · §29 Tool Honesty · the status ladder in `conformance/SKILL.md` |
| Malware analysis | OUT OF SCOPE | Zero authored coverage, and correctly so: analysing live malware needs isolation this framework does not provide and would not claim. The vendored `threat-detection` and `incident-response` skills cover the detection side |
| Reverse engineering | PARTIAL | Named in `modes/SECURITY-AUDIT.md` and `modes/SECURITY-RESEARCH-MODE.md`; the worked case is static APK analysis in `AGENT.md` §15–§17. No general RE procedure, deliberately |
| Incident response | PARTIAL | Named in `docs/agent/AGENT-OPERATING-PROTOCOL.md` and the adversary-emulation mode as a detection question. Response playbooks are the vendored `incident-response` and `incident-commander` skills; this framework assesses, it does not run response |

## 2. Engineering capabilities

| Capability | Status | Evidence |
|---|---|---|
| Coding | ALREADY COVERED | Vendored `senior-*` family (backend, frontend, fullstack, architect, data, ML, QA, DevOps); `AGENT.md` §19 bounds automation |
| Debugging | PARTIAL | `AGENT.md` §6 (enforcement-point location), §23 (failed tests are evidence). Deliberate: this is assessment debugging, not a debugger guide |
| Testing | ALREADY COVERED | The framework's own gates (§4) · differential testing in `modes/ZERO-CREDENTIAL-ESCALATION-MODE.md` · vendored `tdd-guide` |
| Code review | ALREADY COVERED | Vendored `code-reviewer`, `adversarial-reviewer` · `.github/PULL_REQUEST_TEMPLATE.md` · `CODEOWNERS` |
| Architecture | ALREADY COVERED | `ARCHITECTURE.md` · vendored `senior-architect` |
| Refactoring | OPTIONAL | Not authored here; vendored `fix` and `migrate` skills cover it. Adding an authored refactoring guide would duplicate them without new judgement |
| Documentation | ALREADY COVERED | `docs/` (3 agent docs, 5 modes, 22 guides) · `templates/` · generated `FILE-INDEX.txt` · the link check in `validate.yml` |
| Git/GitHub | ALREADY COVERED | `CONTRIBUTING.md` · `.github/ISSUE_TEMPLATE/` · `PULL_REQUEST_TEMPLATE.md` · `CODEOWNERS` · `.github/dependabot.yml` · `.github/scripts/repo_settings.py` · vendored `git-and-github` |
| CI/CD | ALREADY COVERED | Six workflows — see §4. Two dimensions were REAL GAPS and are closed there |
| Release management | ALREADY COVERED | `RELEASE-CHECKLIST.md`, twelve sections, with the command for every gate |
| Dependency management | ALREADY COVERED | `.github/dependabot.yml` (Actions weekly, pip monthly) · no authored runtime manifest by policy, enforced by audit group 20 |
| Automation | ALREADY COVERED | 14 authored scripts in `.github/scripts/` · 6 site scripts · the scheduled jobs in §4 |
| Performance analysis | OUT OF SCOPE | The one performance control is the payload budget in `site/audit_seo.py`: a 150 KB visitor budget, enforced on every run. Runtime performance analysis is not what this framework is for |
| Reliability | PARTIAL | Stated as generated artifacts, no build step, and gates that fail loudly. There is no uptime or SLO work, because there is no service to keep up |
| Observability | PARTIAL | The framework is static: CI logs, job summaries and the `upstream-watch` report are its telemetry. In the *assessed* systems, observability appears as a detection question in `guides/ADVERSARY-EMULATION.md` |

## 3. Framework capabilities

The machinery that carries the other two families: how content is admitted,
bound to this framework's rules, checked, and regenerated. Eighteen capabilities,
all eighteen held — the four that were not are in §4.

| Capability | Status | Evidence |
|---|---|---|
| Skills | ALREADY COVERED | 388 vendored skills under `skills/third-party/claude-skills/`; `skills/README.md` explains the two-layer design, `docs/SKILLS.md` the selection rules |
| Commands | ALREADY COVERED | 39 vendored slash commands, catalogued in `docs/agent/AGENT-SKILL-CATALOGUE.md`. The authored command surface is the scripts below |
| Scripts | ALREADY COVERED | 14 authored in `.github/scripts/`, 6 in `site/`; eleven authored scripts are wired into CI (§4) |
| Agents | ALREADY COVERED | `AGENT.md` · `docs/agent/AGENT-BOOTSTRAP.md` · `docs/agent/AGENT-OPERATING-PROTOCOL.md` |
| Personas | ALREADY COVERED | 33 vendored agent personas, listed in the catalogue; the authored stance is carried by the five engagement modes |
| Adapters | ALREADY COVERED | 399 `_BLACKHEART-ADAPTER.md` files binding vendored content to this framework's non-negotiables; drift-checked by `validate.py` |
| Templates | ALREADY COVERED | 7 in `templates/`: threat model, attack path, coverage matrix, engagement record, finding, test log, final report |
| Standards | ALREADY COVERED | `docs/guides/METHODOLOGY-STANDARDS.md` · `modes/SECURITY-AUDIT.md` |
| Collections | ALREADY COVERED | `skills/catalog/` carries the upstream catalogue with per-collection adapters generated by `.github/scripts/gen_collection_adapters.py` |
| Engagement modes | ALREADY COVERED | 5 in `docs/modes/` |
| Conformance | ALREADY COVERED | `skills/conformance/SKILL.md` — the mandatory wrapper applied before and after any vendored skill runs |
| Manifests | ALREADY COVERED | `.github/UPSTREAM-MANIFEST.json` is the single source for pins, counts and exclusions; `skills/openclaw.example.json5` is generated from the mirror by `.github/scripts/gen_config.py` |
| Integrity | ALREADY COVERED | `validate.py` adapter-drift and digest checks · `.github/scripts/gen_manifest.py` |
| Provenance | ALREADY COVERED | `skills/VENDOR.md` §8 · `skills/licenses/claude-skills-LICENSE` · the per-source pins in the manifest · the licence/provenance bucket in `.github/scripts/watch_upstream.py` |
| Indexing | ALREADY COVERED | `FILE-INDEX.txt`, 4,441 entries, reconciled by `.github/scripts/gen_index.py --check` in CI |
| Registry | ALREADY COVERED | The link defect registry, 111 registered, reconciled by `.github/scripts/gen_link_registry.py --check` in CI |
| Audit gates | ALREADY COVERED | `validate.py` · `gap_audit.py` · `check_site.py` · `audit_seo.py` · `check_contrast.py` · `test_interactions.py` · `check_authored_config.py` · `verify_capability_audit.py` — all in CI (§4) |
| Doc generation | ALREADY COVERED | `gen_index.py` · `gen_link_registry.py` · `gen_manifest.py` · `gen_adapters.py` · `gen_collection_adapters.py` · `gen_config.py` |

## 4. The real gaps, and what closed them

Four capabilities were missing. Each is now implemented, and each was verified
before being added.

| # | Gap | Why it mattered | Closed by |
|---|---|---|---|
| 1 | **Nothing watched the catalogue pin.** `upstream-sync.yml` covers the skill mirror; the second pinned source (`VoltAgent/awesome-openclaw-skills`) had its commit recorded in the manifest but never checked. A pin that is written down and never verified is a claim, not a control | Silent movement in a source this framework vendors verbatim | `.github/scripts/watch_upstream.py` + `.github/workflows/upstream-watch.yml` — weekly, read-only, both sources, classified |
| 2 | **The browser gates never ran in CI.** `check_contrast.py` and `test_interactions.py` were local-only | The failures they catch — a colour at 4.41:1, a control the keyboard cannot reach, a layout that breaks at 320px — are invisible to every static check | `.github/workflows/site-verify.yml` |
| 3 | **The workflows were themselves unvalidated.** GitHub does not run a workflow whose YAML it cannot parse, and does not fail a build over it. A typo could disable the control that protects everything else, and every gate here lives inside the thing that would break | The failure mode is a repository that looks healthy with no CI at all | `.github/scripts/check_authored_config.py` + `authored-scan.yml` |
| 4 | **The authored tooling was unscanned as code.** ~3,800 lines of first-party Python with filesystem access, subprocesses and network probes | A defect in a gate is a defect in every claim that gate underwrites | `authored-scan.yml` (bandit, failing on MEDIUM and above) |

### What the new scanner found on first run

Four MEDIUM findings, none previously known, all in test tooling: two
`urllib.request.urlopen` calls whose scheme is a constant chosen by the script,
one `xml.dom.minidom.parseString` on this repository's own `sitemap.xml`, and one
literal `/tmp` scratch path in a local screenshot helper.

Each is suppressed **at its line**, with the reason in a comment, rather than by
disabling a check class globally. Nothing was reported as clean by configuration;
the gate fails on anything new at MEDIUM or above, which was confirmed by
injecting a real finding and watching it fail.

### Why the watcher does not replace `upstream-sync.yml`

They answer different questions, and the boundary is deliberate:

```text
upstream-watch.yml    scheduled · read-only · both sources
                      answers "has anything moved, and what kind of change is it?"
                      can write nothing: contents: read, and a script that
                      writes no file

upstream-sync.yml     scheduled · writes a branch · the skill mirror
                      answers "prepare the update for a human to review"
                      re-vendors, re-audits, regenerates adapters, opens a PR,
                      and is configured never to merge
```

Detection is automatic. Preparation is automatic. **Admission is not.** Nothing in
this repository merges third-party content without a person reading it.

One more distinction the watcher's exit codes encode: a source it *cannot read* fails the
run (exit 1), while drift is information (exit 0, or 2 when a caller asks to be told
loudly). A watchdog that cannot see the thing it guards has established nothing, and
reporting silence as health would be worse than not watching at all.

## 5. Deliberate non-additions

Capabilities that were considered during this audit and **not** added. Each is a
decision with a reason, not an oversight.

| Not added | Reason |
|---|---|
| An authored OSINT procedure | The framework's collection rule is minimum-necessary data (`AGENT.md` §14, `guides/EVIDENCE.md`). A generic OSINT playbook would invite collection beyond what proves a boundary |
| An authored container/Kubernetes guide | Assessment of deployed container surfaces is reachable through `CLOUD-IDENTITY` and `SUPPLY-CHAIN` §4; the depth lives in the vendored `docker-development` and `senior-devops` skills. An authored guide would restate them without adding judgement |
| An authored network-assessment guide | Out of the engagement surface this framework targets: web, API, mobile, payment, agentic |
| Malware analysis and general reverse engineering | Requires isolation and handling discipline this framework does not provide and will not claim |
| Incident-response playbooks | Assessment-side framework; `incident-response` and `incident-commander` are vendored and cover it |
| Runtime performance and observability tooling | No service to observe. The static site's payload budget is the only performance control that means anything here |
| An authored refactoring guide | Duplicates vendored `fix` and `migrate` |
| Any new vendored skill | Nothing was missing: 3,864 of 3,869 in-scope upstream files were already byte-identical, and the catalogue was already complete at 32/32. Upstream presence is not a reason to add |
| A second manifest, index or provenance system | The manifest, `VENDOR.md`, `FILE-INDEX.txt` and the adapters are authoritative. New tooling reads them; none of it forks them |

Nothing was removed by this audit: no file, skill, command, script, template,
collection, adapter or document. The change is additive, apart from corrections
to published figures that were true of no commit in the repository's history.

## 6. Re-verifying this document

```bash
python3 .github/scripts/verify_capability_audit.py   # read-only, prints a table
python3 .github/scripts/watch_upstream.py            # read-only upstream watch
python3 .github/scripts/check_authored_config.py     # authored config parses
bandit -r .github/scripts site -ll                   # authored Python, MEDIUM+
```

Capabilities stated as ALREADY COVERED are re-checked by that script: it resolves
every cited path and fails if one has moved or disappeared. A capability row that
cites a file which no longer exists is a false claim, and the point of this
document is that its claims are checkable.

## Related

| Document | Purpose |
|---|---|
| [`../ARCHITECTURE.md`](../ARCHITECTURE.md) | The layered structure these capabilities sit inside |
| [`../RELEASE-CHECKLIST.md`](../RELEASE-CHECKLIST.md) | Every gate, with the command that runs it |
| [`../skills/VENDOR.md`](../skills/VENDOR.md) | Third-party provenance, the audit of the mirror, and §9's capability review |
| [`guides/SUPPLY-CHAIN.md`](guides/SUPPLY-CHAIN.md) | The reachability and provenance rules the vendoring follows |
