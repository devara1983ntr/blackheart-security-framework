---
name: "blackheart-conformance"
description: "MANDATORY wrapper for every third-party skill used inside BLACKHEART. Use before and after running any vendored skill: enforces the framework's non-negotiables, converts tool output into BLACKHEART evidence status, applies the authorization gate, and constrains what a finding may claim. Load this first whenever a vendored skill is invoked."
metadata:
  {
    "openclaw":
      {
        "user-invocable": true,
        "always": true,
      },
  }
---

# BLACKHEART Conformance Layer

**Applies to:** every skill under [`../third-party/`](../third-party/).
**Governs:** [`../../../AGENT.md`](../../AGENT.md) · [`../../../docs/agent/AGENT-OPERATING-PROTOCOL.md`](../../docs/agent/AGENT-OPERATING-PROTOCOL.md)

> This skill **grants no authorization to test any system.** It governs how a
> vendored tool's output may be used inside a BLACKHEART engagement. It never
> widens scope.

## 1. Why this layer exists

Vendored skills were written by other authors, for their own purposes, under
their own assumptions. Most are competent. None were written knowing
BLACKHEART's evidence rules.

The gap is specific and predictable. A third-party scanner will:

```text
Report a match as a finding      → BLACKHEART needs a status, not a match
Have no authorization gate        → BLACKHEART requires one before any active step
Rate by CVSS or by tool convention → BLACKHEART severity is bounded by evidence
Ignore scope entirely             → BLACKHEART scope is absolute
Not know what it could not test   → BLACKHEART requires that stated explicitly
Not carry an enforcement point    → BLACKHEART remediation requires one
```

This layer closes that gap. It **does not modify the vendored skills.** Each
vendored `SKILL.md` and every script is preserved byte-for-byte from upstream;
attribution is preserved; behaviour is unchanged. What is added is this wrapper
and a per-skill adapter, which is additive and reversible.

## 2. Non-negotiables, restated for tool use

These are not modified for tool output. Apply them exactly.

1. **Never fabricate.** A vendored tool's output is evidence. If a tool did not
   run, its output does not exist. Do not reconstruct a plausible result.
2. **Never exceed authorization.** The engagement scope record governs tool
   actions exactly as it governs manual ones. A tool does not get a wider lane
   because it automates.
3. **Never claim beyond evidence.** A scanner match is a *hypothesis* until the
   framework's evidence standard is met.
4. **Never report a test that was not run.** Missing tooling is `NOT TESTED`.
5. **Never stop because a technique failed.** A tool returning clean is not a
   closed boundary.

## 3. Authorization gate — applies to every vendored skill

```text
BEFORE invoking any vendored skill:

[ ] Target is inside the engagement's allowed_assets
[ ] The specific action class is permitted by the authorization
[ ] Target is not a third-party dependency
[ ] Rate limits and maximum impact are known
[ ] The action is non-destructive, or destruction is authorized
[ ] The engagement record already exists
```

Any unticked box **blocks the invocation**. Record the blocker; do not work
around it.

A tool that ships its own gate — `ai-security` requires `--authorized` for
gray-box and white-box access and exits `2` without it — is a **floor, not a
substitute**. The tool's gate does not establish that *this engagement* is
authorized; only the engagement record does. The tool gate and the
conformance gate are both required.

## 4. Status conversion — the core rule

A vendored tool emits tool-native output. BLACKHEART needs
[evidence status](../../docs/guides/DECISION-MATRIX.md). Convert explicitly,
in writing, every time.

| What the tool found | BLACKHEART status | Not |
|---|---|---|
| Static pattern or signature match | `UNVERIFIED` | `CONFIRMED` |
| Signature match in *running* system output you supplied | `UNVERIFIED` → raise only with reproduction | `CONFIRMED` |
| Match reproduced against the target with recorded request/response | `CONFIRMED` for the demonstrated weakness | downstream impact |
| Component present, vulnerable path not shown reachable | `PARTIALLY CONFIRMED` | `CONFIRMED` |
| Component present, not present in deployed artefact | `NOT VULNERABLE` | a finding |
| Tool could not run (missing binary, no permission) | `NOT TESTED` + blocker | silent omission |
| Target outside authorization | `OUT OF SCOPE` | a finding |

**A scanner match is never `CONFIRMED` on its own.** Signature matching
establishes that a pattern exists, not that the boundary failed. The framework
rule applies: a hypothesis is not a finding until independently demonstrated.

Record the conversion explicitly:

```text
Tool:            <name>@<version/commit>
Command:         <exact invocation>
Raw output:      <file reference in EVIDENCE/>
Conversion:      match -> UNVERIFIED
To reach CONFIRMED, the test required is: <specific next step>
```

## 5. Severity

Vendored tools may emit CVSS or their own scale. Do not adopt it directly.

- BLACKHEART severity comes from [`SEVERITY-RATING.md`](../../docs/guides/SEVERITY-RATING.md).
- It is **bounded by evidence status** — an `UNVERIFIED` item is not rated.
- A tool's severity may be quoted as a technical supplement, clearly labelled,
  and never as the finding's severity.
- Report the conversion, not just the outcome.

## 6. Enforcement point and remediation

Every `CONFIRMED` finding carried forward must name its **enforcement point**
and cite [`REMEDIATION-AND-RETEST.md`](../../docs/guides/REMEDIATION-AND-RETEST.md).
A tool that reports a class of weakness does not tell you where the control
failed. Determining that is assessment work, and it is where the framework's
value is.

If a vendored tool cannot supply an enforcement point, the finding is
`PARTIALLY CONFIRMED` until you do.

## 7. Coverage

Tools have blind spots and the framework's coverage discipline still applies.

```text
Tools run            : <list, with versions>
Tool not available   : <list, with the blocking capability>
Layers NOT covered   : <from the coverage matrix>
Not tested, because  : <explicit reason>
```

A tool that scans one layer does not make the other layers tested. The
[coverage matrix](../../templates/COVERAGE-MATRIX.md) records boundaries,
not tools.

## 8. Handling tool findings safely

```text
Discovered credentials  → report location and type, never the value
Discovered PII          → prove the boundary with the minimum record, then stop
Discovered live secrets → redact, preserve enough to locate, state rotation need
Discovered endpoints    → record; do not expand scope to reach them
```

## 9. Output discipline

```text
Report the tool's raw output as evidence, unmodified.
Record the conversion separately.
Never let a tool's confidence language become the report's language.
```

If a tool says "high confidence vulnerability", the report says what was
observed and what it proves. Confidence is the tool's opinion; evidence is
yours.

## 10. Provenance

Every vendored skill carries a `_BLACKHEART-ADAPTER.md` recording upstream
commit, path, license, and local modifications. Local modifications to vendored
files are prohibited. If a vendored skill must be changed to function, fork it
explicitly, record the diff in its adapter, and state that the upstream
behaviour is no longer identical.

## Related

| Document | Purpose |
|---|---|
| [`../README.md`](../README.md) | Integration guide, loading, and layout |
| [`../VENDOR.md`](../VENDOR.md) | Attribution, licensing, and provenance |
| [`../../../docs/agent/AGENT-SKILL-CATALOGUE.md`](../../docs/agent/AGENT-SKILL-CATALOGUE.md) | BLACKHEART's own 48 skills |
| [`../../../AGENT.md`](../../AGENT.md) | Governing document |
