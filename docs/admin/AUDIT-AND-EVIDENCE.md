# Administrative records and evidence

**For:** administrators keeping the governance record, and operators producing
technical evidence
**Distinction this document is built on:** the **administrative record** says who
was permitted to do what; the **evidence record** says what happened. They are
different artefacts with different rules, and neither substitutes for the other
**Evidence rules:** [`PHASE5-EVIDENCE-PROTOCOL.md`](../agent/PHASE5-EVIDENCE-PROTOCOL.md)
is the operative protocol. This document does not restate it — it adds the
administrative layer and points at the source for the rest

---

## 1. Two records, two purposes

| | Administrative record | Evidence record |
|---|---|---|
| Answers | Who authorized this, when, for what, under what limits | What was observed, and how it can be verified |
| Produced by | The administrator and the authorizer | The workbench, from real responses |
| Contains target data? | **No.** It names the target, not its content | Yes. It is the target's data, which is why it is handled carefully |
| Enforced by software? | **No** — it is a human process | Partially: hashes, verification, and the rule that a failing record is not counted |
| Where it lives | The engagement's administrative record, outside the repository | The operator's history, bundle and manifest files |
| Retention | Per the engagement's governance rules | Per the engagement's data-handling rules |

**The administrative record never goes in this repository.** It contains
authorization references, names and target identities. The repository is public.

## 2. The administrative record — required fields

Keep one per approved activity. The directive's fields, with what each is for:

| Field | Why it exists |
|---|---|
| **Operator** | Who performed the work. One named person, not a team |
| **Authorizer** | Who approved it, and in what capacity. Required for high-risk work |
| **Target** | The named systems |
| **Authorization reference** | Where the underlying permission is recorded, so a third party can find it |
| **Operation** | What was done, specifically — not "assessment" |
| **Timestamp** | Start, in UTC, with the date |
| **Duration** | Elapsed, and whether it ran to the approved end |
| **Scope** | The perimeter that applied |
| **Result** | What was observed, at the level of a summary. The detail is in the evidence |
| **Evidence identifier** | The bundle or record id, so the two records cross-reference |
| **Stop reason** | If it stopped early, why. **Leave blank only if nothing stopped** |
| **Exceptions** | Anything done outside the approved envelope, and the approval for it |
| **Review status** | Reviewed, by whom, when |

**`Stop reason` is the field that gets omitted and never should.** A run that
stopped because a scope ambiguity appeared is the record that proves the control
worked. Omitting it makes the governance look cleaner and the record less true.

**Never log secrets.** Not a credential, not a token, not a session value, not in
a field, a note or an attachment. [`SECURITY-CONTROLS.md`](SECURITY-CONTROLS.md)
§3 applies to the administrative record exactly as it applies to code.

## 3. Where the technical evidence rules live

Stated once, not restated: the operative protocol for evidence is
[`../agent/PHASE5-EVIDENCE-PROTOCOL.md`](../agent/PHASE5-EVIDENCE-PROTOCOL.md).
The rules an administrator most needs to know are summarised here and specified
there.

| Rule | Specified in |
|---|---|
| Required fields on every record, including a non-empty `limitations` | Evidence protocol §1 |
| SHA-256 per record and per bundle, with verification on read | Evidence protocol §2 |
| The five statuses and the permitted transitions | Evidence protocol §3 |
| The prohibition on fabricating, promoting, hiding or altering | Evidence protocol §4 |
| What a report may and may not contain | Evidence protocol §5 |

### The four prohibitions, in the administrator's terms

These are the ones a governance layer must own, because they are organisational
failures rather than tooling failures:

| Prohibited | In administrative terms |
|---|---|
| **Never fabricate evidence** | No record is written for work that was not done. An unperformed test is `NOT TESTED`, not a guess |
| **Never modify evidence silently** | Editing a record breaks its hash, and the integrity failure is itself the finding. Changes are recorded as changes |
| **Never represent simulated evidence as real-world** | A fixture result is a fixture result. This repository's own tests are loopback-only and labelled; any demonstration must be labelled the same way |
| **Never promote a status** | `POTENTIAL` becomes `REPRODUCED` by a second observation, never by a decision. An administrator's opinion is not an observation |

**Chain of custody.** Where an engagement requires it: the bundle, its manifest,
the verification command, and a dated record of each transfer. The workbench
supports the first three; the transfer log is the administrator's.

## 4. Evidence requirements for the record

For each acquisition or observation that supports a finding:

| Requirement | How it is met |
|---|---|
| Immutable provenance | Every record carries `tool`, `tool_version`, `origin`, `generated_at` |
| Timestamp | UTC, at the moment of observation |
| Source | The URL or path, with the redirect chain where it applies |
| Target | The system, and the scope the request was authorised under |
| Authorization reference | In the administrative record; the manifest entry carries the scope summary |
| SHA-256 | Of the record, and of any acquired file, taken **from the bytes on disk** |
| Acquisition method | The scope decision, the request, and the response |
| Scope | The enforced values, from `scope validate` |
| Limitations | Required and non-empty, in the record's own words |
| Chain of custody | The administrator's transfer log, where the engagement requires one |

## 5. Reviewing evidence as an administrator

```text
[ ] every quoted record passes `evidence manifest --verify`
[ ] the bundle's count matches the records that verified — not the records present
[ ] no record was edited after the run; any edit is disclosed as an edit
[ ] every record states its limitation
[ ] statuses are the ones the records carry, not stronger ones
[ ] blocked operations are reported as results, with their authorized route
[ ] what was not tested is stated
[ ] no secret appears in the record, the manifest, the report or the log
[ ] no personal data beyond what the finding requires
[ ] evidence identifiers in the administrative record resolve
```

Two of these catch the most common real failures: an edited record still being
quoted, and a bundle's headline count including records that failed verification.
Both are implemented against, and both are the kind of thing that only gets caught
by a person checking.

## 6. Evidence that must not be kept

| Not kept | Why |
|---|---|
| A credential found in a response | Rotate it. Do not store it. Record that it was exposed |
| Personal data beyond the finding | Minimise at the point of collection |
| Another user's content | The finding is that it was reachable, not what it said |
| A copy of a restricted resource obtained outside an authorization | There is nothing to keep |
| Anything the engagement's rules exclude | The engagement's rules are stricter than this list, and they control |

## 7. What this document does not claim

- **The administrative record is not enforced by software.** Nothing checks that
  it exists or that its fields are filled. Its integrity is a human process, and
  the honest statement of that is worth more than an implied guarantee.
- **The evidence record is partly enforced** — hashes, verification, the exclusion
  of failing records from counts — and the parts that are not are named in the
  evidence protocol.
- **Neither record establishes that authorization existed.** They record what was
  asserted, by whom, and what was done. The truth of the assertion is outside any
  tool's reach, and this document will not pretend otherwise.
