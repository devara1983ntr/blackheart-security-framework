# Download and Acquisition Policy

**Project:** BLACKHEART Security Framework · **Author:** Roshan
**Last updated:** 2026-09-30

---

## The rule

Acquisition is limited to **public resources**, **resources the operator is
authorized to access**, and **resources whose licence or terms permit the
acquisition**. Where a resource is behind an access control, the workbench records
the refusal and stops. It does not attempt to get past it.

This document describes what the code actually does. Every claim below names the
module that implements it, so the policy and the implementation can be checked
against each other rather than taken on trust.

## What is never done

| Never | What happens instead |
|---|---|
| Bypassing authentication | `401` is recorded as `blocked`; the authorized route is named. No retry with altered headers, no credential guessing |
| Bypassing authorization | `403` is recorded as `blocked` |
| Reaching a resource through a proxy that demands its own credentials | `407` is recorded as `blocked`; proxy credentials are not supplied or guessed |
| Defeating a paywall or subscription check | `402`, and any paywall or entitlement marker, is recorded as `blocked` |
| Circumventing DRM or a licensing control | The marker is recorded, the file is not obtained |
| Solving or evading a CAPTCHA or challenge page | A challenge interstitial is recognised and recorded as `blocked` |
| Extending, guessing or reusing a signed URL | Expiry is recorded; the link is not reused |
| Reaching into private storage or a private repository | Out of scope by definition; refused by the scope file |
| Substituting a mirror, cache or proxy for a blocked resource | Refused by policy and by design; the tool has no such mode |
| Working around a resource withheld for legal reasons | `451` is recorded as `blocked`; a legal restriction is not an obstacle to route around |
| Retrying a refusal differently | A refusal ends the path |

Enforced in `workbench/fetch.py` (statuses and blocking), with refusals carried
through to the report by `workbench/report.py`.

## Statuses a blocked resource can have

An acquisition ends in exactly one of four states, defined in
`workbench/fetch.py`:

| Status | Meaning |
|---|---|
| `success` | The target served the bytes, they were written, and the SHA-256 in the manifest is of the bytes on disk |
| `blocked` | Access was refused or gated. **No file is written.** The entry names no file. The reason and the authorized route are recorded |
| `failed` | Something went wrong that is not a refusal — a truncated body, a transport error, a size limit |
| `skipped` | The URL was deliberately not requested, with the reason recorded |

**A blocked resource is recorded as blocked.** It is never represented as a
challenge to be overcome, and nothing in the framework treats a refusal as an
obstacle to route around.

## What is recorded for every acquisition

Provenance is not optional. Each entry carries: source URL, final URL, HTTP
status, content type, size, SHA-256, timestamp, redirect chain, licence note,
authorization scope, file type, whether the type was detected confidently, whether
the file name matches the content, and the extraction status of the file
afterwards.

Nothing is recorded as obtained unless the bytes arrived and re-hash on disk.
`manifest.verify()` re-hashes every recorded file and reports what disagrees, so a
manifest that lists a file nobody has is a manifest that fails verification.

## Handling what is acquired

- **Nothing is executed.** No import, no install, no macro, no binary, no
  `subprocess` anywhere in the framework. An archive is listed and read; its
  members are written to the directory the operator named, under size, count,
  ratio, traversal and bomb limits (`workbench/extract.py`).
- **Nothing is redistributed.** This project does not redistribute acquired
  content, and a licence note travels with each acquisition so a reader knows what
  applies to it.
- **Notices are not stripped.** Where the acquired content carries a copyright or
  licence notice, it is left as it is.
- **Personal data** in acquired content is the operator's responsibility. See
  [`PRIVACY-POLICY.md`](PRIVACY-POLICY.md) §7.

## When a resource is blocked

The workbench records the HTTP status, the technical reason, and the routes that
are authorized, then stops. Those routes, as implemented in
`workbench/fetch.py`:

| Route | When it applies |
|---|---|
| Ask the owner | The request was refused; the owner can say whether access is intended and how it is granted |
| The publisher's or author's own access route | Purchase, subscription, library access, or an open-access copy at the publisher's own page |
| Documented public metadata | Title, author, identifier and licence are usually readable without the item, and are the correct citation |
| A documented API | Where the owner publishes one for authorized credentials |
| Stop | Always. No mirror, cache, proxy, altered identity or expired link |

## Synthetic and test content

The repository's own tests acquire files from a **loopback fixture server** that
ships in `workbench/tests/fixtures.py`. No test in this repository downloads
anything from the internet, and the CI gate enforces that by restricting the
socket layer to loopback for the entire suite.

## If you believe content here infringes

[`SECURITY.md`](SECURITY.md) explains how to raise it. A credible report about
misattributed or improperly used content will be acted on: corrected or removed.
