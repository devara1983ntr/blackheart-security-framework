# Engagement Record

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`../AGENT.md`](../AGENT.md) §3–§4 · [`../guides/SCOPE.md`](../docs/guides/SCOPE.md) · [`../guides/TOOL-AND-ENVIRONMENT.md`](../docs/guides/TOOL-AND-ENVIRONMENT.md)

## What this is for

`AGENT.md` requires a scope record and a capability inventory before active
testing begins, and requires that unavailable tools be reported honestly rather
than assumed.

This template makes both concrete. It is filled in once, at the start, and it is
the document that answers "was this even possible?" before any test is attempted
— which is what turns an honest `NOT TESTED` into a defensible one.

**Fill it in before testing. Not after.**

---

## 1. Engagement identity

```text
Engagement name / reference:
Client or authorizing party:
Assessor:
Assessment start date:
Assessment end date:
Assessment type: web | api | mobile | apk | source | digital-product | mixed
Report version:
```

## 2. Authorization

```text
Authorization status:  confirmed | unclear
Authorization reference (ticket, email, SOW):
Authorizing party named in the document:
Date authorization was provided:
Expiry or end date of authorization:
```

**If authorization is `unclear`, testing does not begin.** Record the specific
ambiguity and stop. See [`../guides/SCOPE.md`](../docs/guides/SCOPE.md).

```text
Prohibited actions stated in the authorization:
Rate limits or time windows:
Approved test accounts or roles:
Approved data-handling requirements:
```

## 3. Target

```yaml
target:
  type: website | web-app | api | mobile | apk | aab | source | digital-product | file-delivery | other
  identifiers: []

environments:
  production:   { url: "", in_scope: false }
  staging:      { url: "", in_scope: false }
  sandbox:      { url: "", in_scope: false }
  local:        { path: "", in_scope: false }
```

## 4. In-scope assets

```yaml
allowed_assets:
  domains: []
  subdomains: []
  applications: []
  apis: []
  repositories: []
  storage: []
  products: []
  payment_systems: []
  file_delivery_systems: []
```

## 5. Explicitly excluded

```yaml
excluded_assets:
  assets: []
  reasons: ""
```

## 6. Third-party classification

Every external dependency discovered must be classified. Discovery happens
during testing, so this section is filled in as dependencies are found — it is
not complete at kickoff.

```yaml
third_parties:
  - dependency: ""
    host: ""
    class: AUTHORIZED THIRD-PARTY | DEPENDENCY / OBSERVATION ONLY | OUT OF SCOPE
    observed_use: ""
    active_testing_permitted: false
    notes: ""
```

**A technical relationship never creates authorization.** If a vendor endpoint
appears in application traffic, it is recorded here as observation-only unless
the authorization document names it.

## 7. Accounts and roles

```yaml
accounts:
  synthetic_accounts_available: false
  roles_in_scope: []
  matrix:
    - role: ""
      account_identifier: ""      # reference only, never a credential
      created_by: "client" | "assessor (if authorized)" | "not available"
      notes: ""
```

**Never record a password, token, or session cookie in this record or anywhere
else in the engagement output.** Reference accounts by role and identifier.

## 8. Capability inventory

Recorded before testing. This is the section that makes honest `NOT TESTED`
entries possible later.

```yaml
capabilities:
  browser: { available: false, version: "" }
  http_client: { available: false, version: "" }
  source_access: { available: false, location: "" }
  apk_aab_access: { available: false }
  archive_handling: { available: false }
  proxy_interception: { available: false, product: "" }
  packet_capture: { available: false }
  emulator_or_device: { available: false, version: "" }
  adb: { available: false }
  dex_decompiler: { available: false, product: "" }
  bytecode_tooling: { available: false }
  java_kotlin_analysis: { available: false }
  javascript_tooling: { available: false }
  database_access: { available: false }
  test_credentials: { available: false }
  staging_environment: { available: false }
  payment_sandbox: { available: false }
  download_storage_access: { available: false }
  scripting_runtime: { available: false, version: "" }
```

### Tool substitutions

Any case where a preferred tool was unavailable and a substitute was used.

```yaml
substitutions:
  - preferred_tool: ""
    available: false
    substitute_used: ""
    impact_on_conclusions: ""
    must_be_stated_in_methodology: true
```

Known substitutions the framework anticipates:

| Preferred | Substitute | Conclusion that remains unprovable |
|---|---|---|
| Intercepting proxy | Controlled HTTP capture/replay | Traffic from other apps, certificate behaviour |
| Android runtime / emulator | Static APK analysis | Runtime behaviour, dynamic component loading, actual network calls |
| DEX decompiler | Other static inspection | Complete control-flow recovery |
| Browser automation | Direct HTTP analysis | Client-side behaviour, rendering, UI-only state |

## 9. Environment and reproducibility

```yaml
environment:
  assessor_platform: ""
  os_version: ""
  network_position: ""
  proxy_configuration: ""
  clock_timezone: ""
  target_version_or_hash: ""
  notes: ""
```

## 10. Constraints register

```text
Data minimization requirement:
Redaction requirement:
Evidence retention requirement:
Retention period:
Production-access constraint:
Time-window constraint:
Any instruction that limits what may be proven:
```

If any constraint prevents demonstrating a required impact, record it here so
it appears in the report as a stated limitation rather than an unexplained gap.

## 11. Pre-engagement sign-off

Complete before the first active test.

```text
[ ] Authorization confirmed and referenced
[ ] Scope and exclusions recorded
[ ] Third-party boundary understood
[ ] Accounts and roles available, or absence recorded
[ ] Capability inventory complete
[ ] Tool substitutions recorded
[ ] Environment recorded
[ ] Data-handling and redaction requirements understood
[ ] Constraints register complete
[ ] Coverage matrix opened
```

Any unchecked box is a reason the corresponding area will read `NOT TESTED` in
the final report. That is an acceptable outcome. Discovering it afterwards is
not.

## 12. Deviations log

Anything that departed from this record during the engagement — scope found
mid-test, an assumption invalidated, a constraint encountered, an
operator-authorized exception.

```text
Date:
What was assumed or planned:
What actually happened:
Why it was acceptable:
Recorded in report as:
```

**An operator-authorized deviation is legitimate and belongs here.** Hiding one
is not. The framework's integrity requirements apply to process as much as to
technical results.
