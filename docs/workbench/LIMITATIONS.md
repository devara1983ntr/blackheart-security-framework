# Limitations

What follows is what this code cannot do or cannot establish. It is deliberately
specific, because the failure mode this document exists to prevent is a reader
treating the output as stronger than it is.

## What an observation is not

- **An observable response difference is not a finding.** Two responses that
  differ after one parameter changed are recorded as different. Whether the
  difference matters, whether it is exploitable, and whether it is even caused by
  the change are questions for a person with the engagement's context.
- **A missing security header is not a vulnerability.** It is a header that was
  absent from the responses that were examined. HTTP security headers are one
  layer, and their absence may be compensated elsewhere or may be deliberate.
- **`POTENTIAL` and `UNVERIFIED` records are not validated.** The report says so
  in those words, and the status ladder makes it impossible to move such a record
  to `REPRODUCED` without recording a second observation.
- **Absence of an observation is not evidence of absence.** A clean run means the
  checks that ran found nothing to record about the responses they received. It
  says nothing about paths that were not requested, timings that were not
  exercised, or behaviour that depends on state the run did not reach.

## What the checks cannot decide

- **Reflection is not injection.** The reflection check reports that a value
  supplied by the caller appeared in the response body. It does not execute
  anything in a browser, and the record says the execution was not tested.
- **CORS and cookie findings are recorded as configured, not as exploitable.**
  The presence of a wildcard or a missing `HttpOnly` is read from one response.
  Whether it is reachable by an attacker depends on the application's own origin
  model.
- **The authorization-boundary check needs two identities.** It runs only when
  the operator supplies two labelled contexts and both were observed. Without
  them it produces nothing rather than a degraded guess, and where one identity
  was refused it says so instead of reporting a boundary.
- **Rate-limit observations are timing-dependent.** The check reports the calls
  it saw to one endpoint. A limiter that was not triggered in the window the run
  covered is not absent, only unobserved.
- **TLS facts are whatever the handshake reported.** The records carry the
  protocol version, cipher and certificate details of the connections this tool
  made. They are not a TLS configuration review.

## Bounds are real limits

- A run stops at its request budget, its page and depth caps, its mutation limit
  and its archive size and ratio caps. What was not reached is reported as not
  reached, with a count, and is not implied to be empty or safe.
- Discovery follows what a target *publishes*: `robots.txt`, sitemaps, OpenAPI
  and Swagger documents at conventional locations, forms, script references and
  the assets a page links to. There is no wordlist, no extension sweep and no
  name guessing. A path that is not advertised is not found, and a path that is
  advertised is not guessed at beyond the one request that confirms it.
- GraphQL is reported only when the target itself references an endpoint. The
  tool does not probe for one, and it does not send a query.
- The tool does not test for injection, deserialization, business-logic or
  authentication bypasses. It is not a scanner in that sense and does not claim
  to be a substitute for one.

## Access control is a stop, not an obstacle

When a resource is refused, the run records the status, the reason, and the
authorised route — the publisher's own page, the item's public metadata, a
library or an institutional subscription, a documented API for the owner's own
credentials. Then it stops that path. It does not try another header, another
identity, a cache, a mirror, a proxy, or a link that has not expired. Where an
acquired file is offered under a licence or a copyright notice, the notice is
recorded with the file and the file is not redistributed.

## Secrets and the local environment

- A credential supplied on the command line is visible to the local process list
  and may be captured by the shell's history. The tool redacts it from
  everything it writes; it cannot redact it from the shell.
- Redaction is by header name and by the literal values the operator lists with
  `--secret`, which covers request and response bodies, the URL, the query
  string and every URL in a redirect chain. A stored record whose URL was
  redacted cannot be replayed or fuzzed: the tool refuses rather than sending
  the marker, and tells you to capture the request again with the value.
- A secret that appears in a form the tool was not told about — a randomly
  generated token in a response body, for instance, with no `--secret` given
  for it — is not redacted by magic. Inspect a bundle before sharing it.
- The history file and evidence bundles contain the requests and responses that
  were made, with sensitive values removed. They do not contain credentials, but
  they do contain the target's own data, and they are the operator's
  responsibility to store and to share appropriately.

## Environment

- The suite and the CI gate use a loopback fixture server that ships with the
  repository. No test contacts the internet, and no result in this documentation
  was produced by testing a third party's system.
- The tool is standard-library Python (3.10 or newer). It has no dependency to
  pin and no build step; that also means no third-party parser, so a document
  format the standard library cannot read is reported as unsupported rather than
  parsed by something else.
- YAML descriptions are not parsed. `api inspect` reads JSON; a YAML OpenAPI
  document is reported as unread rather than half-read.
