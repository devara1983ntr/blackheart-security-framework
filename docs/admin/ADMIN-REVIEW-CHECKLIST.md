# Administrator review checklist

**For:** the administrator or reviewer signing off an activity
**Use:** copy the relevant section into the engagement's record. An unticked box
is a stop, not a note
**Companion:** [`AUDIT-AND-EVIDENCE.md`](AUDIT-AND-EVIDENCE.md) holds the field
definitions; this is the working list

---

## Before the work starts

### AUTHORIZATION

```text
[ ] The target is explicitly authorized — named in a record, in writing
[ ] The authorizing party is identified, and is entitled to grant it
[ ] Third parties in the path are accounted for (hosting, payments, APIs)
[ ] The authorization reference is recorded, so a third party can find it
```

### SCOPE

```text
[ ] Scope documented: hosts, paths, exclusions
[ ] Scope file written FROM the authorization, not from memory
[ ] `scope validate` output read, and it matches the authorization
[ ] Methods documented — and write methods specifically justified
[ ] Request/resource limits documented, set from the authorization
[ ] Exclusions listed explicitly, not left implied
```

### WINDOW

```text
[ ] Authorization start recorded, with timezone
[ ] Authorization end recorded, with timezone
[ ] `authorized_until` in the scope file matches the authorization
[ ] Any period when testing is not permitted is recorded
```

### ELEVATED REVIEW (high-risk work only)

```text
[ ] Every high-risk trigger identified (HIGH-RISK-RESEARCH.md §2)
[ ] An independent authorizer is named — not the operator
[ ] The approval is recorded with a reference
[ ] Expiry set, and it is before or equal to the authorization's
[ ] A lab reproduction was considered first
```

### DATA AND SENSITIVE INFORMATION

```text
[ ] Sensitive-data rules documented for this engagement
[ ] Personal data expected to be encountered is identified
[ ] Retention and deletion are defined — with dates
[ ] Handling requirements recorded (minimise, redact, encrypt, delete by)
```

### SAFETY

```text
[ ] Emergency contact documented, and reachable DURING the window
[ ] Stop conditions documented — the standard list plus engagement-specific ones
[ ] Rollback/containment plan where the work could affect availability
```

### SECURITY OF THE WORK ITSELF

```text
[ ] No credentials embedded in scope files, config, scripts or notes
[ ] Any credential needed is supplied at runtime, through a supported mechanism
[ ] No hidden bypass is being used — and none is being added
[ ] No universal password, master key or undocumented override exists in the work
[ ] The work uses only existing framework capability
[ ] Evidence handling is defined before collection begins
```

## During the work

```text
[ ] The scope decision is read, not skipped, on the first response
[ ] Budget and interval are the authorization's, not the tool's defaults
[ ] Every refusal is recorded as a refusal, with its authorized route
[ ] Evidence is captured as the run proceeds, not reconstructed afterwards
[ ] Stop conditions remain armed
[ ] The operator stops on: ambiguity, strain, cancellation, window expiry,
    an unexpected target, or anything they do not understand
```

## After the work

### FINDINGS AND EVIDENCE

```text
[ ] Every quoted record passes `evidence manifest --verify`
[ ] The bundle's count is of the records that verified
[ ] No record was edited after the run — or the edit is disclosed as an edit
[ ] Every record states its limitation
[ ] No status was promoted (POTENTIAL stays POTENTIAL without reproduction)
[ ] Blocked paths are reported as results, with their authorized route
[ ] What was NOT tested is stated
```

### DATA

```text
[ ] Sensitive data minimised — only what the finding requires
[ ] Reports redacted before sharing
[ ] Retention and deletion carried out on schedule, and recorded
[ ] Nothing outside the engagement's handling rules was stored or transferred
```

### CREDENTIALS

```text
[ ] No credential appears in evidence, reports, logs or the repository
[ ] Any credential exposed during the work has been ROTATED — not just noted
[ ] The incident record names the exposure and the rotation, never the value
[ ] Forks, caches, CI logs and artifacts checked for the exposure
```

### AUTHORIZATION CLOSURE

```text
[ ] Temporary access removed — accounts, tokens, entitlements, exceptions
[ ] The authorization is closed in the record, with the end time and the outcome
[ ] Any deviation from scope is recorded, with its approval or its incident
[ ] The stop reason is recorded if the work stopped early
```

### REVIEW

```text
[ ] Findings reviewed by someone other than the operator (high-risk work)
[ ] The reviewer's name and date recorded
[ ] The administrative record's review status updated
[ ] The report's limitations section survived editing intact
```

## The three boxes people tick without checking

Called out because each has been the source of a real problem, in this project or
in the pattern it models:

| Box | Why it gets ticked wrongly |
|---|---|
| **"No credentials embedded"** | The check is usually a glance. It needs the secrets gate to be run, not a memory of not having typed one |
| **"Any credential exposed has been rotated"** | Rotation gets logged; *assessing what the credential already reached* does not happen. Rotating is the first step, not the last |
| **"Evidence is intact"** | The bundle verifies — but the count may still include records that were excluded, or the report may quote a record the verification flagged. Read the verification output, not the headline |

## Sign-off

```text
Reviewed by     : ______________________   Date: ____________
Independently   : ______________________   Date: ____________
                   (required for high-risk work; the operator cannot sign this)
Authorization   : closed / open / revoked
Stop reason     : ______________________
Declared        : no bypass was used, and none was added
```
