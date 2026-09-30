# Phase 5 failure handling

**For:** an AI agent, or a human operating one
**Companion:** [`PHASE5-SAFETY-RULES.md`](PHASE5-SAFETY-RULES.md) — the rules;
this is what they produce at the moment something goes wrong
**Shape:** deterministic. The same condition produces the same action, whoever is
driving

---

## 1. The matrix

Read the left column as what happened. The middle column is what the workbench
does — the implementation, not an aspiration. The right column is what the agent
does.

| Condition | The tool | The agent |
|---|---|---|
| **No authorization** | Active operations still run if the scope file accepts; the tool cannot verify authority | **STOP the active operation.** Report that authorization is not established |
| **No policy acceptance, or a stale one** | Refuses at the socket boundary, exit `2`, nothing sent | Tell the operator. Never work around it |
| **Out of scope** | Raises, exit `3`, nothing sent | Record the decision verbatim, name the authorized route, stop that path |
| **Budget exhausted** | Raises on the next request | Stop the run, report the counts and the cap reached |
| **Rate limit / interval reached** | Waits out the interval; the budget is the hard ceiling | Respect it. Do not shorten the interval to finish |
| **Authorization window closed** | Raises; requests stopped | Stop the run. A run that outlives its window is unauthorized from that moment |
| **Target under strain** | Records it; nothing forces a stop | **STOP.** Slow responses, timeouts and errors are the target asking you to stop |
| **`401`** | `blocked`, no file written, authorized route named | Record it as blocked. The route is the site's own login, with the operator's own credentials |
| **`403`** | `blocked` | Record it. Do not retry with a different header, method, identity or encoding |
| **`407`** | `blocked` | Record it. Proxy credentials are not supplied or guessed |
| **`402`, paywall marker** | `blocked` | Record it as blocked. Do not look for another copy |
| **`451`** | `blocked` | Record it. A legal restriction is not an obstacle to route around |
| **DRM or licence marker** | Recorded; the file is not obtained | Record it. Do not obtain the file by other means |
| **CAPTCHA or challenge interstitial** | Recognised and recorded as `blocked`. On a page where a page was expected, written **with a recorded warning** — never silently clean | **Do not bypass.** Do not solve, outsource, replay or evade |
| **Signed URL expired** | Recorded as unavailable or expired | Record the expiry. Do not extend, guess or reuse the link |
| **Malformed response or archive** | `failed`, with the reason; unsafe members are refused | Record the failure. Malformed input is a result, not a puzzle |
| **Traversal attempt in an archive** | Extraction refused for that member | Record it as a refusal. Do not extract "carefully by hand" |
| **Hash mismatch on an acquired or extracted file** | Refused **before** parsing; status `refused`, reasons in the summary | Do not read, quote or inventory the file |
| **Evidence integrity failure** | Reported; the record is not adopted into a report's counts | Report the integrity failure itself, with the record id and both hashes |
| **A secret in recorded output** | Redacted by header name, and by any value named with `--secret` | Redact before sharing. Re-check a share is intended |
| **Unexpected network behaviour** | Recorded; the redirect chain is captured per hop | **Preserve the evidence and stop the affected action.** Do not investigate on your own initiative |
| **The agent does not understand what it is seeing** | — | **STOP.** This is a first-class stop condition, not a gap in the operator's knowledge |

## 2. The four actions, and what each requires

Every row above reduces to one of four moves.

| Action | Means | Requires |
|---|---|---|
| **STOP** | Halt the affected action or the run, now | A recorded reason, in the terms the tool used |
| **RECORD** | Write what happened before interpreting it | The raw result verbatim, then the interpretation |
| **REPORT** | Say it in the output, in the record's own words | The limitation, and what was not tested |
| **REFUSE** | Decline a member, a path, an acquisition, a request | Say which rule refused it, and what the authorized route is |

**STOP is never a failure of the run.** A run whose most useful output is "three
paths were refused and here is why" is a successful run. A run that produced a
finding to avoid stopping empty-handed is a failed one.

## 3. Recovery: what may be retried, and what may not

| May be retried | May never be retried |
|---|---|
| A transport error with nothing changed, within the budget and interval | A refusal, with anything changed |
| A timeout, once, with a longer timeout **inside the scope's limit** | A `401`/`403` with another identity, header or session |
| A request cancelled by the operator, if they ask for it again | A blocked acquisition through another route |
| A mutating check with different, still-authorized input | A rate-limit response with a shorter interval |
| — | A challenge page, after waiting |
| — | Anything at all, "to see if it was a fluke" |

The right column is the bypass list under a different name. An agent that finds
itself planning a retry should read the row it is about.

## 4. When evidence fails verification

```text
1. Stop quoting the record. Not its counts, not its severity, not its conclusion.
2. Record the failure: the record id, both hashes, the file, the time.
3. Report the failure as a finding in its own right — the bundle is not intact.
4. Do not attempt to repair the record. Do not re-hash it. Do not explain it away.
5. Tell the operator, and say which conclusions depended on it.
```

A falsified record is not less relevant because it happened accidentally. It is
more, because nobody did it on purpose and nobody is watching for it.

## 5. When the agent is wrong

Agents are frequently, confidently wrong. Two obligations follow:

- **The agent** re-derives the affected conclusion from the evidence when
  corrected, rather than accepting the correction at face value. The operator may
  be wrong too; a revision made on deference is as unreliable as one invented.
- **The operator** treats a confident report as unverified. The evidence — the raw
  requests, responses, hashes — is the finding. The narrative is a summary, and the
  summary is what an agent is most able to get confidently wrong.

## 6. Reporting a failure, in the right words

| Say | Do not say |
|---|---|
| "The request was refused by the target: `403`, recorded as blocked" | "Access was denied, so the resource is protected" |
| "The scope file refused this host, so no request was sent" | "The host did not respond" |
| "A record failed its hash check, so the bundle's count excludes it" | "The bundle verified" |
| "The marker suggests an interstitial; the response is not the resource" | "The site is behind a WAF" |
| "One response differed in these fields, once" | "The endpoint is vulnerable" |
| "This was not tested; the page cap was reached" | "No issues were found there" |

The difference between the two columns is the whole point of the framework. The
left column is a fact someone can check. The right column is a claim someone will
act on.
