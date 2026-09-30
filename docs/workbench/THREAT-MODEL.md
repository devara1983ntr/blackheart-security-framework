# Threat model

This document describes what the workbench is built to prevent, what it is
trusted with, and what an operator has to do themselves. It is written for
someone deciding whether to run it against a system they are authorised to test.

## What it is trusted with

| Asset | Where it lives | What the code does with it |
|---|---|---|
| The authorization file | A path given on the command line | Read before any request. Every request is checked against it. Never written to, never modified, and never cached across runs. |
| Credentials for an authorised identity | Supplied per run (`--header`, a secret list) | Sent to the target when the operator supplies them; redacted in everything written to disk. |
| Downloaded content | A directory the operator names | Written, hashed, and read as bytes. Never executed, imported, installed or interpreted. |
| Evidence | A bundle directory | Hashed on write; re-hashed and compared on read. |
| The target | Reachable over the network | Requests are counted, spaced, capped and refused outside the scope file. |

## What this code must never do

These are properties the design enforces, and the test suite asserts:

1. **Bypass an access control.** No retry with an altered identity, no header
   manipulation to defeat a `401`/`403`, no CAPTCHA or challenge solving, no
   paywall or DRM circumvention, no proxy or mirror substitution for a blocked
   resource, no reuse of an expired signed URL.
2. **Reach past the scope file.** Every active request calls `scope.require()`,
   which raises on an unlisted host, an excluded path, a method that is not
   allowed, an exhausted request budget, a private address without the explicit
   opt-in, or an expired authorization window. There is no skip flag and no
   environment variable that changes this.
3. **Replay a state-changing request by accident.** A write method needs the
   scope to allow it *and* `confirm_write=True` at the call site, which no command
   sets except the one documented as doing so. The mutation catalogue does not
   generate write verbs at all; it lists them so the operator can decide.
4. **Connect somewhere other than the address that was vetted.** The address is
   resolved once, checked against the scope, and pinned. The socket is opened to
   that address, TLS is verified against the *name* from the URL, and automatic
   reconnection is switched off, so a connection that is not in place raises
   instead of resolving the name again.
5. **Write a credential to disk.** Values for `Authorization`, `Cookie`,
   `Set-Cookie`, `X-API-Key` and `Proxy-Authorization` are replaced with
   `[redacted]` in records. `Set-Cookie` retains its attributes, because
   `HttpOnly`, `Secure` and `SameSite` are the evidence a cookie check reads.
   A replay of a stored request drops a redacted header rather than sending the
   marker.
6. **Follow a target's instruction to go somewhere else.** A redirect to a host
   outside the scope is refused and recorded. Discovery does not follow links to
   other domains because a page linked to them.
7. **Execute what it fetches.** No `subprocess`, no `import` of downloaded
   content, no archive member written outside the extraction directory, no
   document macro, no JavaScript. Archive extraction refuses absolute paths,
   `..`, symlinks, device nodes, expansion past a ratio, and too many files.
8. **Fabricate a result.** A `401` is never recorded as a successful download; a
   challenge page is not a document; a failure is recorded as a failure with its
   reason. Counts in a report are derived from the records the report holds.

## Threats considered

### The tool is pointed at the wrong thing

An operator, or a page the crawler read, supplies a URL that resolves to a cloud
metadata service, a loopback service, or another host inside a private network.
*Mitigation:* only hosts in `allowed_hosts` are requested; private, loopback,
link-local and multicast addresses are refused unless the scope file carries the
explicit `allow_private_networks` opt-in, which exists for engagements on
internal ranges and for the test fixtures. Redirects are re-checked per hop.

### The target instructs the tool to attack a third party

The target returns a redirect, a link, a `sitemap` entry or a form action
pointing elsewhere.
*Mitigation:* every hop and every discovered reference is checked against the
scope before it is requested. Out-of-scope references are recorded as refused,
with their address, instead of being followed.

### Malicious or malformed content

A downloaded PDF, zip, tar, docx or HTML page is crafted to exploit the reader,
or a zip bomb is served as a small file that expands without limit.
*Mitigation:* content is read with the standard library's parsers, never
executed; sizes and ratios are capped; extraction stops and writes nothing when a
cap is hit; a document that is refused is recorded as refused with the reason.

### Credential leakage

A token appears in a header, in a request body, in a response body, or in prose
an operator types into a note; a report is later shared.
*Mitigation:* header values are redacted by name; a `--secret` list redacts
literal values anywhere they appear in a recorded body; the report generator
prints record fields as they were recorded, so a value that was redacted stays
redacted.

### Denial of service by the tool itself

A run with no bounds hammers a target, or a crawl multiplies without limit.
*Mitigation:* `max_concurrency` defaults to 1; `min_interval_s` defaults to 1.0
second; `max_requests` defaults to 0 (nothing); the CLI caps pages, depth,
mutations and file size; fuzzing stops at its budget, and cancellation is checked
between requests.

### False confidence in the output

The dangerous failure for a security tool is a quiet one: a count that came from
nothing, a record that reads as a stronger claim than the evidence supports, or
an empty result taken for a clean bill of health.
*Mitigation:* records carry a status (`OBSERVED`, `REPRODUCED`, `INFERRED`,
`POTENTIAL`, `UNVERIFIED`) and a status can only move along a defined ladder;
`POTENTIAL` records are never reported as validated; every report carries the
standing statements it is written under, including that absence of an
observation is not evidence of absence; a bundle whose hashes no longer match is
reported as a problem rather than read as evidence.

## What is out of scope for this code

- **Deciding whether something matters.** Severity and impact are human
  judgements; the tool records what it saw and the limits of that observation.
- **Testing an identity you do not hold.** The tool uses the credentials it is
  given. It does not acquire, guess, reuse or escalate credentials.
- **Testing anything you are not authorised to test.** The scope file is the
  operator's assertion of authority; the tool enforces what is in it, and cannot
  know whether it is true.
- **Holding a secret safely.** A credential passed on a command line is visible
  to the local process list. This is a property of the shell, not of the tool;
  see `LIMITATIONS.md` for how the tool handles it and what it cannot.
