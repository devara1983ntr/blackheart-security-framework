# Supply Chain and Dependency Security

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`REFERENCE-MAPPINGS.md`](REFERENCE-MAPPINGS.md) · [`TOOL-AND-ENVIRONMENT.md`](TOOL-AND-ENVIRONMENT.md) · [`WEB-API-TESTING.md`](WEB-API-TESTING.md) · [`../templates/COVERAGE-MATRIX.md`](../../templates/COVERAGE-MATRIX.md)

> **Authorized use only.** Identifying a vulnerable dependency is assessment
> work. Proving exploitability against a live system, or interacting with a
> registry, package, or vendor, requires the authorization this guide does not
> grant.

## Why this is separate

A vulnerable dependency is not yet a vulnerability. The component may be
unreachable, unused, or mitigated by configuration. Reporting the dependency
alone produces a list that a client cannot act on and that crowds out real
findings.

The framework's rule applies directly:

> **Reachability decides whether a dependency is a finding.**

An unreachable CVE is `NOT VULNERABLE` with the reachability evidence stated. A
reachable one is a finding, with the reach demonstrated.

## Boundary — what is in scope

```text
IN SCOPE, once authorized
  The application's own dependencies
  Build and release pipeline
  Container base images actually deployed
  Third-party APIs, SDKs, and integrations
  Agent-connected tool and plugin supply chains      → see AGENTIC-AI-SECURITY.md

OUT OF SCOPE — never tested without explicit authorization
  Package registry infrastructure
  Vendor systems
  Shared CI/CD runners
  Third-party model endpoints
  Any system the organization does not own
```

A vulnerable package **found in a dependency list is not a mandate to
interact with the upstream project.** Advisory research and local analysis are
assessment work; contacting or probing a vendor's infrastructure is not.

## 1. Dependency inventory

```text
DECLARED      manifest and lockfile dependencies, by direct/transitive
RESOLVED      what is actually installed and built
VULNERABLE    which resolved versions match known advisories
ORPHANED      declared but unused
UNDECLARED    present in the build but not in any manifest
```

**Undeclared dependencies are the highest-value item in this section.** A
library present in the build but absent from the manifest is invisible to
scanning, unpinned, and unmaintained by the application's update process.

## 2. Reachability

This is the step that separates an assessment from a scan report.

For each vulnerable component, establish:

```text
Is the vulnerable code path present in the deployed artefact?
Is the affected function or feature reachable by an untrusted actor?
Is it reachable at all in the observed configuration?
Is it mitigated by configuration, version pinning, or compensating control?
```

Classify:

| Result | Status |
|---|---|
| Reachable and unmitigated | `CONFIRMED` dependency exposure |
| Present but not reachable by an untrusted actor | `CONFIRMED`, with reach stated |
| Present but the vulnerable path is not exercised | `PARTIALLY CONFIRMED` |
| Not present in the deployed build | `NOT VULNERABLE` |
| Cannot determine without unavailable tooling | `NOT TESTED`, capability named |

A finding that omits the reachability determination is incomplete. State it
even when the answer is "reachable" — the client needs the path.

## 3. Version and fingerprint accuracy

The most common error in this domain is a version claim that is wrong.

```text
Wrong  : header or lockfile suggests version X, therefore CVE-Y applies
Right  : version X confirmed in the resolved artefact, and the CVE's affected
         range confirmed to include X, and the vulnerable path confirmed
         present
```

Verify against the artefact that is actually deployed, not a manifest that may
be stale, a lockfile that may not match the build, or a banner that may be
spoofed or served by a different component behind a proxy.

**Never assert a CVE from memory.** Advisory data changes. Verify the
identifier, affected ranges, and fix version against the advisory at time of
testing, and record that the advisory was checked on a specific date.

## 4. Build and release integrity

```text
SOURCE INTEGRITY      is the source provenance verifiable? Signed commits,
                      protected branches, provenance attestations
DEPENDENCY INTEGRITY   are dependencies pinned and integrity-verified? Hash or
                      signature checking on install
BUILD INTEGRITY       is the build reproducible or otherwise verifiable?
                      Is the build environment isolated from untrusted input?
PUBLISH INTEGRITY      who can publish, and under what controls? Could a
                      dependency publish a malicious version of the package?
UPDATE CHANNEL         how do updates arrive, and are they verified?
```

The last one is frequently the real finding: an automatic update path that
trusts a registry response without verification converts a single compromised
account into production access.

## 5. Secrets in dependencies and configuration

```text
Hardcoded keys in source
Keys in configuration or environment committed to a repository
Keys in build artefacts or client-side bundles
Keys in container images or image layers
Keys in dependency metadata
Credentials in CI/CD configuration
```

**A committed secret is always a finding, regardless of revocation status.**
Revoked or not, its presence proves the process is defective. Note current
status, but do not let rotation downgrade the finding.

Never publish a discovered secret. Redact while preserving enough to locate
and identify it. See [`../SECURITY.md`](../../SECURITY.md).

## 6. Known vulnerabilities without running code

Where the assessment is static-only — a black-box engagement, an APK without
a runtime — the honest output is bounded:

```text
CONFIRMED    the vulnerable component is present in the artefact
CONFIRMED    the component version matches an advisory's affected range
NOT TESTED   runtime reachability and exploitability
```

Do not upgrade this. A component known to be vulnerable and present in the
build is a legitimate finding; claiming it is *exploitable in this deployment*
without runtime evidence is not. The distinction is exactly the framework's
core rule, and dependency assessment is where it is most often abandoned.

## 7. Agent and plugin supply chains

Where an AI agent connects tools, plugins, or MCP servers, the supply chain
extends to the agent's dependencies:

```text
Can an unauthorised party register or substitute a tool?
Is tool output distinguishable from instruction?
Are tool definitions integrity-checked?
Can a tool's declared permissions be changed after review?
Can a connected server influence agent behaviour beyond its function?
```

This is covered in full in [`AGENTIC-AI-SECURITY.md`](AGENTIC-AI-SECURITY.md) §12.
It is called out here because it is a supply-chain problem as much as an
AI-security one.

## 8. Mapping and reporting

| Concern | Reference |
|---|---|
| Known vulnerabilities in shipped software | OWASP A06 Vulnerable and Outdated Components |
| Dependency and update integrity | OWASP A08 Software and Data Integrity Failures |
| Secrets exposure | [`REFERENCE-MAPPINGS.md`](REFERENCE-MAPPINGS.md) §1 |
| LLM and agent dependencies | [`AGENTIC-AI-SECURITY.md`](AGENTIC-AI-SECURITY.md) §13 |

Report each finding with:

```text
Component and exact resolved version
Advisory identifier, verified on (date)
Affected range and whether the resolved version falls inside it
Reachability determination, with evidence
Mitigation status
Recommended action: upgrade, replace, remove, or compensate
```

## 9. Constraints

```text
[ ] No interaction with vendor, registry, or upstream infrastructure
      without explicit authorization
[ ] Advisory data verified at time of testing, with the date recorded
[ ] No CVE asserted from memory
[ ] Reachability stated for every dependency finding
[ ] Discovered secrets redacted, never published
[ ] Tool availability limitations recorded as NOT TESTED, not as clean
```

## 10. Common failures

| Failure | Correction |
|---|---|
| Reporting every CVE in a dependency tree | Determine reachability; most are irrelevant |
| Asserting a version from a header | Verify against the deployed artefact |
| Rating an unreachable component as Medium | `NOT VULNERABLE`, with the reachability evidence |
| Treating a missing secret scan as a clean bill | Untested is untested |
| Testing a vendor's systems because their library is present | Out of scope without authorization |
| Publishing a discovered key | Redact; report the process defect |
