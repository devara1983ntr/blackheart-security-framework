# Phase 5 evidence protocol

**For:** an AI agent, or a human operating one
**Implementation:** `workbench/evidence.py`, `workbench/report.py`,
`workbench/history.py`
**Rule of the whole document:** evidence is what was recorded, not what was
concluded

---

## 1. The record

Every observation the workbench produces is an evidence record with these fields.
The first group is required — a record missing any of them fails validation.

| Field | Carries |
|---|---|
| `id` | Stable identifier, unique within the bundle |
| `title` | One line, descriptive, no claim beyond the observation |
| `severity` | `informational`, `low`, `medium`, `high`, `critical` |
| `confidence` | `low`, `medium`, `high` |
| `status` | One of the five states in §3 |
| `target` | The URL or resource the observation is about |
| `scope` | The scope the request was authorised under |
| `timestamp` | UTC, at the moment of the observation |
| `expected` | What the framework expected to see |
| `observed` | What actually came back |
| `impact` | Why it might matter — stated as a possibility, not a conclusion |
| `limitations` | What this record does not establish. **Required, and non-empty** |
| `remediation` | What a reader could do about it |
| `provenance` | `tool`, `tool_version`, `origin`, `generated_at` |

Optional, and populated where the observation came from a request or an
acquisition: `request`, `response`, `reproduction` (the steps taken), `notes`, and
the record's `hashes`.

**`limitations` is required because a record without one reads as complete
coverage.** "The target returned this header once, on this path, from this address,
at this time" is evidence. "The target misconfigures its headers" is not.

## 2. Hashes, and what they are for

A record carries a SHA-256 of itself, computed over its own fields. A bundle
carries a manifest that names each record and its digest.

- `evidence manifest --verify` re-hashes every record and reports what disagrees.
- `report generate` verifies **before** it counts. A record whose hash does not
  match is *not adopted* into the report's figures, and the report states which
  records it excluded and why.

An agent must not walk around a verification failure. A record that fails its own
hash check is not evidence of anything, including the thing it describes.

## 3. The statuses, and the ladder

| Status | Means |
|---|---|
| `OBSERVED` | Recorded from a real response, once |
| `POTENTIAL` | Might matter. Nothing established |
| `INFERRED` | Derived from other observations, with the derivation stated |
| `REPRODUCED` | A second matching observation was made |
| `UNVERIFIED` | Recorded, with no basis to say more. The honest default |

Allowed transitions, from the implementation — reproduction is the only path
upward, and it requires a second observation:

```text
POTENTIAL    -> REPRODUCED, UNVERIFIED, INFERRED
OBSERVED     -> REPRODUCED, INFERRED, UNVERIFIED
INFERRED     -> REPRODUCED, UNVERIFIED
REPRODUCED   -> UNVERIFIED
UNVERIFIED   -> REPRODUCED, INFERRED
```

**A transition to `REPRODUCED` requires reproduction steps.** The transition
refuses without them, so "I ran it again" cannot be asserted without saying what
was run.

**Validated language is reserved.** A record that is not `REPRODUCED` may not
contain "vulnerable", "vulnerability", "confirmed", "exploitable", "exploit works",
"attack succeeded" or "proof of concept works" in its title, impact or observed
text. The record fails validation rather than passing review with a stronger claim
than the evidence supports. A `critical` severity is likewise refused unless the
status is `REPRODUCED`.

## 4. What an agent must never do

| Never | Specifically |
|---|---|
| **Fabricate evidence** | No invented record, hash, response, status code, statistic, timestamp or exploitation |
| **Promote a status** | `POTENTIAL` becomes `REPRODUCED` by a second observation, never by argument, seniority or enthusiasm |
| **Hide a limitation** | The record's limitations are reported in its own words. Trimming them for an audience is misrepresentation |
| **Change evidence after the fact** | Bundles are append-only. Editing a record breaks its hash, and the failure is the finding |
| **Quote a record that failed verification** | Not its counts, not its severity, not its conclusion |
| **Report a blocked operation as a result about the target** | "The target refused" and "the scope refused" are different findings |
| **Present a simulation as real traffic** | A fixture result is a fixture result. The repository's own fixtures are loopback-only and are labelled |
| **Claim coverage that was not achieved** | Say what was not tested, and what the caps left unexplored |

## 5. What a report contains, and what it does not

A report is generated from the records it holds. Every count in it is derived, not
supplied:

- counts by status and severity, from the records that verified;
- the limitations of each record, in full;
- the blocked paths, with the authorized route for each;
- verification results, including which records were excluded;
- a statement of what the report does **not** establish.

It does not contain a severity rating for something nobody validated, a
vulnerability claim, or a fabricated summary. If a report's numbers look useful,
that is because the records support them.

## 6. Provenance

Every record carries where it came from: the tool, its version, the origin of the
run, and when the record was generated. Acquisitions additionally carry source URL,
final URL, status, content type, size, SHA-256, redirect chain, licence note, the
scope they were authorised under, the detected type and whether the detection was
confident, whether the filename matches the content, and the extraction status
afterwards.

Provenance is not decoration. It is what lets a reader who was not present for the
run check the claim, and it is the difference between evidence and an assertion.

## 7. Before an agent reports anything

```text
[ ] every quoted record verified against its manifest
[ ] every status is the one the record carries, not a stronger one
[ ] every limitation is included, in its own words
[ ] observations and inferences are labelled separately
[ ] every refusal is reported as a result
[ ] what was not tested is stated
[ ] the report's own "what this does not establish" section survived editing
```

If a claim in the narrative is not supported by a record in the bundle, delete the
claim. It is cheaper than defending it.
