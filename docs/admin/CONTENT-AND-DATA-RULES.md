# Content and data rules

**For:** administrators and operators
**Scope:** paywalls, DRM, licensing, download restrictions, and private or
sensitive data
**Relationship to existing policy:** this layer **adds review requirements to**
[`ACCEPTABLE-USE.md`](../../ACCEPTABLE-USE.md) and
[`DOWNLOAD-AND-ACQUISITION-POLICY.md`](../../DOWNLOAD-AND-ACQUISITION-POLICY.md).
It does not relax anything in them, and where they are stricter, they control.

---

## 1. What may be acquired, and what is refused

The workbench's acquisition rules are implemented in `workbench/fetch.py` and
enforced on every request. Restated here for administrators deciding whether work
is appropriate — not as a second source of truth. The module is the source.

| Resource | Outcome |
|---|---|
| **Public resource** | Processed under the existing acquisition capability, with provenance recorded |
| **Authorized resource** | Same, with the authorization recorded in the manifest entry |
| **Resource whose licence permits it** | Same, with the licence note carried into the manifest |
| **Access-restricted resource** | The restriction is **recorded**. The status is `blocked`, no file is written, the authorized route is named |
| **Unauthorized resource** | **Stop** |
| **Private resource without authorization** | **Stop.** Out of scope by definition |
| **Premium resource without authorization** | **Stop.** `402` and entitlement markers are blocking |
| **DRM-protected resource without an authorized test basis** | **Stop.** The marker is recorded; the file is not obtained |
| **Signed URL expired** | **Record the expiration.** Do not extend, guess or reuse it |

**Blocking statuses:** `401` · `402` · `403` · `407` · `451`, plus paywall and
entitlement markers, DRM and licensing markers, challenge interstitials, and
expired signed access.

**A blocked resource is recorded as blocked.** No file is written. The entry names
no file. The authorized route is named. See
[`PHASE5-CAPABILITY-NOTES.md`](../agent/PHASE5-CAPABILITY-NOTES.md) §5.

## 2. There is no circumvention capability, and no recipe for one

This documentation contains **no generic circumvention instructions**, and none
will be added. That is not an omission to be fixed — it is the design position of
the entire framework, restated in
[`workbench/AUTHORIZED-USE.md`](../../workbench/AUTHORIZED-USE.md):

> This framework does not bypass authentication, authorization, paywalls, DRM,
> licensing controls, or other access restrictions.

An administrator asked to add a "recovery path" for a blocked resource is being
asked to convert this framework into a different one. The answer is no, and the
existing tests are written to fail if it happens.

### If an authorized assessment covers such a system

It is possible for an authorization to cover a paywalled, licensed or DRM-bearing
system — a media company testing its own entitlement service, for example. When
that is genuinely the case, all of the following are required:

| Required | |
|---|---|
| Written authorization | Naming this specific system and this specific activity class |
| A defined test environment or test resource | Provided by the owner for the purpose, or an authorized test entitlement |
| An independent authorizer | Per [`HIGH-RISK-RESEARCH.md`](HIGH-RISK-RESEARCH.md) §5 — payment and premium functionality is high-risk by trigger 7 |
| Explicit boundaries | What may be observed, and what must not be touched |
| The refusal still recorded | If the system refuses a request even inside the authorization, that is a **blocked** status. The authorization permits the *request*, never the *bypass* |

## 3. Data minimisation

Collect only what is necessary for the authorized purpose. This is both a legal
habit and a practical one: less to store, less to leak, less to explain.

### Avoid collecting

| Avoid | |
|---|---|
| Unrelated user information | Anyone not in the engagement's scope |
| Credentials of any kind | Anyone's, including ones found by accident |
| Unnecessary personal information | Names, addresses, identifiers — unless the finding requires them |
| Payment information | Card data, bank details, transaction records |
| Private communications | Messages, mail, chat, documents belonging to people |
| Unrelated files | The directory listing you saw is not an invitation |

### If sensitive data is encountered unexpectedly

```text
1  STOP unnecessary collection
   The finding does not improve with the second record. Stop at one
2  PRESERVE only what is necessary for the authorized finding
   Often that is the response status and shape, not the content
3  REDACT the report
   The report goes to more people than the raw record ever should
4  FOLLOW the applicable rules
   The engagement's data-handling requirements, and the law that applies
5  RECORD the encounter
   That data of this kind was reachable is itself a finding, and it can be
   reported without reproducing the data
```

Step 5 is the one that gets skipped. "An object-level authorization gap exposed
another user's record" is a complete finding. Pasting the record into the report
is not more complete — it is a second incident.

### The workbench's role, and its limits

| It does | It does not |
|---|---|
| Redact header values named in `SENSITIVE_HEADERS` before anything is written | Recognise arbitrary sensitive data |
| Redact any value passed with `--secret`, wherever it appears | Know what you consider sensitive |
| Cap response bodies at the scope's `max_response_bytes` | Decide what you should have fetched |
| Record provenance for everything it writes | Judge whether collecting it was appropriate |

**Data minimisation is an operator decision.** The tool stores what it is asked to
store, redacted for what it was told about. See
[`PRIVACY-POLICY.md`](../../PRIVACY-POLICY.md) §7.

## 4. Retention and handling

| Rule | |
|---|---|
| Store where the engagement says | Not in a personal directory, not in a shared drive, not in a chat |
| Retain for the period the engagement says | Longer retention is a liability, not thoroughness |
| Delete on schedule, and record the deletion | "We deleted it" without a date is not a record |
| Treat every bundle as sensitive | It contains the target's data. Copying it copies the data |
| Do not transfer outside the engagement | Including to a cloud service the engagement did not name |
| Preserve the chain of custody | Hashes with the bundle, and the verification command — not a screenshot |

The workbench supports this: bundles carry SHA-256 hashes and a manifest, and
`evidence manifest --verify` re-checks them. Hand a recipient the bundle and the
command, not a picture of it.

## 5. Third-party content

Content acquired during an assessment may belong to someone who is not a party to
the engagement. The rules are in
[`THIRD-PARTY-CONTENT.md`](../../THIRD-PARTY-CONTENT.md): provenance is recorded,
attribution is preserved, nothing is redistributed, and a licence note travels
with each acquisition.

**A licence note is a record, not a permission.** Recording that a resource is
licensed under some terms does not make acquiring it authorized. The
authorization is separate, and it is the operator's to hold.

## 6. The administrator's specific obligations

Administrators hold a role; they do not hold extra access. What the role adds
here is review:

| Obligation | |
|---|---|
| Confirm the engagement's data-handling terms exist before work starts | Not after data has been collected |
| Ensure retention and deletion are defined | With dates, not intentions |
| Review evidence for over-collection before it leaves the engagement | Over-collection is a finding about the engagement, not a bonus |
| Require redaction before any report is shared | The raw record stays with the operator |
| Confirm that any acquisition was inside an authorization | Including the ones that succeeded, not just the ones that blocked |

## 7. What is not permitted, in one list

Every item below is prohibited at every authorization level, for every role,
including repository administrators:

| Prohibited |
|---|
| Circumventing a paywall, subscription or entitlement check |
| Circumventing DRM or a licensing control |
| Circumventing a download restriction, a rate limit, or a signed-URL expiry |
| Obtaining premium or private content without authorization |
| Obtaining another person's private information |
| Obtaining another person's credentials, session or token |
| Collecting personal data the engagement did not contemplate |
| Retaining data for longer than the engagement permits |
| Distributing acquired content to anyone outside the engagement |

None of these has an authorized version. An administrator cannot authorize them,
because the authority to permit them does not exist in this project — it would
have to come from the person whose data or control is at stake, which is exactly
what the restriction is.
