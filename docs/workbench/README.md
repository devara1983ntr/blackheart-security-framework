# The Blackhearts workbench

An authorized-use toolkit for examining HTTP services, their API descriptions and
the documents they serve — and for recording what was observed in a form that can
be checked by somebody who was not there.

This framework does not bypass authentication, authorization, paywalls, DRM,
licensing controls, or other access restrictions.

| Document | Purpose |
|---|---|
| [`THREAT-MODEL.md`](THREAT-MODEL.md) | What this code must not do, and what it protects against |
| [`LIMITATIONS.md`](LIMITATIONS.md) | What it cannot establish, stated plainly |
| [`COMMANDS.md`](COMMANDS.md) | The command surface, with exit codes and worked examples |
| [`END-TO-END.md`](END-TO-END.md) | A real run against the built-in fixture server, output included |

## What it is

`workbench/` is first-party Python in this repository. It is not a wrapper around
another tool, it starts no subprocesses, and it has no dependencies outside the
standard library. Every request it makes goes through one function,
`scope.require()`, which reads an authorization file the operator supplies and
raises `ScopeError` when the request is not covered by it.

Nothing in it is a scanner that decides things on your behalf. It collects
observations, records them with their limits, and refuses to turn an observation
into a finding: a record that says `POTENTIAL` or `UNVERIFIED` has not been
validated, and the report says so in those words.

## The rules it is built around

1. **Authorization is an argument, not a default.** Commands that send requests
   require `--scope <file>`. There is no default scope, no in-memory override and
   no flag that skips the check; `.github/scripts/gap_audit.py` and the test
   suite both assert that no option string anywhere in the command surface is
   named after a control it disables.
2. **Stop at a refusal.** A `401`, `402`, `403`, `407`, `451`, a challenge page,
   an expired signed URL or a paywall ends that path. The tool records the status
   and the reason, names the route that is authorised (the publisher's own page,
   public metadata, a library), and stops. It does not try the next header, the
   next identity, or a mirror.
3. **Nothing is executed.** A downloaded file is read as bytes: no import, no
   `subprocess`, no macro, no installer, no archive member written outside the
   directory it was extracted into. Extraction refuses archives that expand past
   their limits, and refuses members with absolute paths or `..` in them.
4. **Credentials are not persisted.** `Authorization`, `Cookie`, `Set-Cookie`,
   `X-API-Key` and `Proxy-Authorization` values are redacted in every record,
   report and log. `Set-Cookie` keeps its attributes — the flags are the evidence
   — and loses the value. A replay of a stored request drops a redacted header
   rather than transmitting the literal string `[redacted]`.
5. **Bounds everywhere.** A request budget, a concurrency of one, an interval
   between requests, response-size caps, a redirect cap, a timeout, page and
   depth caps for discovery, and size/file/ratio caps for archives.
6. **Counts are measured, never estimated.** Every number in a generated report
   is derived from the records that report holds.
7. **No session degradation.** The tool does not retry a failed request, does not
   reconnect after a failure, and pins each connection to the address the scope
   allowed — a second connect would go wherever DNS pointed at that moment.

## Where it lives

| Path | What it is |
|---|---|
| `workbench/scope.py` | The authorization file and the guard every request passes through |
| `workbench/http_client.py` | The one HTTP path: redirects, TLS facts, redaction, recording |
| `workbench/history.py` | The append-only record of every exchange, and replay |
| `workbench/diff.py` | Deterministic comparison of two responses |
| `workbench/params.py`, `workbench/mutate.py`, `workbench/fuzz.py` | Parameters, mutations, and bounded mutation runs |
| `workbench/checks.py` | The observable checks and the evidence they produce |
| `workbench/evidence.py` | Record fields, status transitions, hashing, bundles |
| `workbench/discover.py` | Bounded discovery from what a target publishes |
| `workbench/fetch.py`, `workbench/extract.py` | Acquisition with provenance, and safe reading of documents and archives |
| `workbench/emergency.py` | Read-only collection |
| `workbench/report.py` | The report assembler |
| `workbench/cli.py` | The command surface |
| `workbench/tests/` | The suite, with a loopback fixture server |

## Running it

```bash
# Check that a scope file is valid before anything else uses it.
python3 -m workbench.cli scope validate --scope scope.json

# One request, recorded.
python3 -m workbench.cli http inspect --scope scope.json \
    --url https://target.example/ --history run/history.jsonl

# What a target publishes, within a page and depth cap.
python3 -m workbench.cli web crawl --scope scope.json \
    --url https://target.example/ --max-pages 25 --max-depth 2

# Observable checks over responses, written as an evidence bundle.
python3 -m workbench.cli web scan --scope scope.json \
    --url https://target.example/ --out run/evidence

# A report over what the run produced.
python3 -m workbench.cli report generate --bundle run/evidence \
    --scope scope.json --out run/report.md
```

A scope file is JSON. The fields are documented in
[`../../guides/SCOPE.md`](../guides/SCOPE.md); `scope validate` prints the
summary the tool will enforce:

```json
{
  "targets": ["https://target.example"],
  "allowed_hosts": ["target.example"],
  "excluded_hosts": ["status.target.example"],
  "excluded_paths": ["/admin", "/logout"],
  "allowed_methods": ["GET", "HEAD"],
  "max_requests": 200,
  "max_concurrency": 1,
  "max_response_bytes": 5000000,
  "max_redirects": 5,
  "timeout_s": 10.0,
  "min_interval_s": 1.0,
  "authorized_until": "2026-12-31T00:00:00Z"
}
```

`max_requests` defaults to `0`, which allows nothing. A scope file that does not
name a budget authorises no requests at all, rather than an unlimited number.

## What this documentation does not claim

The tools record what happened; they do not judge it. A missing security header
is recorded as absent from one response, not as a vulnerability. A response that
differs after a mutated request is an *observable response difference*, not a
finding — see [`LIMITATIONS.md`](LIMITATIONS.md) for the full list, and
[`../../guides/OPERATING-RULES.md`](../guides/OPERATING-RULES.md) for the
rules an operator is held to when using it.
