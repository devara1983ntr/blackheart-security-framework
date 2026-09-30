# End-to-end: one run, against the fixture server

This is a real transcript. The target is the loopback fixture server that ships
in `workbench/tests/fixtures.py`, started on `127.0.0.1` with a scope file that
authorises it. No third party's system was touched, and no output below was
edited, summarised or reconstructed: it is what the commands printed.

The port changes between runs, and the timestamps and hashes below are from the
run this transcript was taken from. Everything else is reproducible by following
the commands.

The chain is the one an operator runs: authorise a target, record a request, look
at what the target publishes, run the observable checks, acquire what is
published, read what was acquired, take a read-only snapshot, verify the bundle,
and write the report. The failures are in there too — a refused resource, an
in-scope URL the target declined, a path that was not followed.

## 1. The authorization file, before anything uses it

```
$ blackheart scope validate --scope run/scope.json
scope file: run/scope.json
valid: yes
  allowed_hosts: ['127.0.0.1', 'localhost']
  allowed_methods: ['GET', 'HEAD', 'OPTIONS']
  allowed_paths: []
  authorized_until: None
  denials: 0
  max_concurrency: 4
  max_requests: 200
  requests_made: 0
  scope_file: run/scope.json
  there is no bypass: every request is checked against this file
```

`max_requests` is the lifetime budget for this scope object. `denials` is how many
requests were refused; it starts at zero and is printed again wherever the guard
is summarised.

## 2. One request, recorded

```
$ blackheart http inspect --scope run/scope.json \
      --url http://127.0.0.1:33693/soft --history run/history.jsonl
GET http://127.0.0.1:33693/soft
  history id    : H0001
  status        : 200 OK
  final url     : http://127.0.0.1:33693/soft
  content type  : text/plain
  bytes         : 13
  elapsed ms    : 1
  scope decision: allowed
  header        : Server: BlackheartsFixture/1.0
  header        : Date: Wed, 30 Sep 2026 03:46:13 GMT
  header        : Content-Type: text/plain; charset=utf-8
  header        : X-Blackheart-Fixture: true
  header        : Content-Length: 13
```

The history file is append-only JSON Lines, one exchange per line. `H0001` is the
id this exchange can be replayed, mutated and diffed by.

## 3. What the target publishes

```
$ blackheart web crawl --scope run/scope.json \
      --url http://127.0.0.1:33693/ --max-pages 10 --budget 25
Discovery from http://127.0.0.1:33693/
  pages fetched   : 10 of at most 10 (depth 2, 10 of 25 requests used)
  found           : 12 {'document': 1, 'robots': 1, 'sitemap': 1, 'missing': 6, 'api-description': 1, 'form': 1, 'external': 1}
  out of scope    : 1 reference(s) not followed
  unavailable     : 6 in-scope URL(s) the target declined
  stopped by caps : 6 reference(s) left in the frontier

  A crawl reports what it reached. Nothing here says that a path it did not reach does not exist.
```

Three numbers that matter: one reference was **not followed** because it was out of
scope (the fixture page links to another host), six paths the target named were
requested and declined, and six more were left unexplored when the page cap was
reached. All three are reported rather than smoothed over.

## 4. Observable checks, written as evidence

```
$ blackheart web scan --scope run/scope.json \
      --url http://127.0.0.1:33693/soft --out run/evidence
1 response(s), 2 record(s)
  records are observations; none of them is a validated finding
  OBSERVED   informational E-HEADERS-ABSENT           Response headers absent from the baseline: strict-transport-
  OBSERVED   informational E-HEADERS-BANNER           Technology disclosure in response headers: server
  written to run/evidence: 2 record(s), manifest e9f3d4eb226f...
  note: a handful of responses is a spot check, not coverage
```

Both records are `OBSERVED` and `informational`. Neither is a finding, and the
command says so before it prints them.

## 5. Acquiring a published document, and asking for a refused one

```
$ blackheart resource download --scope run/scope.json \
      --url http://127.0.0.1:33693/file.pdf --out run/downloads \
      --license "fixture document, not a real licence" --yes
[D0001] success 200 http://127.0.0.1:33693/file.pdf | 2058 bytes -> file.pdf (pdf)
  manifest: run/downloads/manifest.json
  verified: clean
```

```
$ blackheart resource download --scope run/scope.json \
      --url http://127.0.0.1:33693/forbidden --out run/downloads --yes
[D0002] blocked 403 http://127.0.0.1:33693/forbidden | access forbidden
  manifest: run/downloads/manifest.json
  verified: clean
  this manifest already held 1 acquisition(s); the new entry is D0002
  authorized route: ask the asset owner: The request was refused. Ask the owner whether the resource is meant to be reachable, and whether your identity or network is expected to reach it. Do not retry with altered headers.
  authorized route: documented public metadata: The item's public metadata (title, author, identifier, licence) is usually readable without the item itself. Record that, and record the official page for it as the citation.
  authorized route: stop: This tool stops here. It does not use mirrors, caches, proxies, altered identities or expired links to obtain a copy.
```

Note the exit codes, which are the same character in every command: the
acquisition that succeeded and the one that was refused both exit `0`. The
command ran. Whether the resource was obtained is stated in the output, in the
manifest, and in the report — not in the exit code. `D0002` has no file: a blocked
entry never names one.

## 6. Reading what was obtained

```
$ blackheart resource extract --manifest run/downloads/manifest.json \
      --out run/extracted
file.pdf: pdf, extracted
  sha256          : 78699835fb2d41103fe891cbc1299ac62666c26c29d34eb2fcffeeafb806ac6a
  pages read      : 2
  attachments     : 1 (not written out)
  links           : 1
  flagged         : an embedded file
  nothing was executed, imported or installed

manifest updated: run/downloads/manifest.json
  a file whose hash no longer matches the manifest was not read
```

The PDF was read, not opened: page text, links and an embedded attachment were
recorded with their hashes, the attachment was not written out, and nothing was
executed. Only the `success` entry was read; `D0002` stays `not_started`, because
a blocked acquisition has no file to read.

## 7. A read-only snapshot

```
$ blackheart emergency collect --scope run/scope.json \
      --url http://127.0.0.1:33693/soft --out run/emergency --yes
EMERGENCY COLLECTION (read-only, one pass)
  target          : http://127.0.0.1:33693/soft
  started         : 2026-09-30T03:46:13Z
  finished        : 2026-09-30T03:46:13Z
  requests        : 4 of 20

  requested url                http://127.0.0.1:33693/soft
  final url                    http://127.0.0.1:33693/soft
  status                       200
  reason                       OK
  content type                 text/plain
  elapsed ms                   0
  header server                BlackheartsFixture/1.0
  header date                  Wed, 30 Sep 2026 03:46:13 GMT
  scope decision               allowed
  body bytes                   13
  body prefix sha256           3e6156ae93916ac6d83b60494946a6f6
  document /robots.txt         served

  published documents read
    http://127.0.0.1:33693/robots.txt: 200
    http://127.0.0.1:33693/.well-known/security.txt: 404

  This is a snapshot, not an assessment. It does not discover, fuzz or compare identities, and an empty section means the collection did not cover it — not that nothing is there.
  evidence: run/emergency (2 record(s))
```

Four requests: a `HEAD`, one bounded `GET` for the body-prefix hash, and the two
published documents. `GET` and `HEAD` are the only methods the module can send —
there is no code path that takes a method from anywhere else.

## 8. Verify the bundle, then write the report

```
$ blackheart evidence manifest --directory run/evidence --verify
run/evidence: verified, every record hashes to what the manifest says
```

```
$ blackheart report generate --bundle run/evidence \
      --manifest run/downloads/manifest.json --scope run/scope.json \
      --out run/report.md --title "Fixture assessment"
report written: run/report.md
  records       : 2
  validated     : 0
  not validated : 0
  acquisitions  : {'blocked': 1, 'failed': 0, 'skipped': 0, 'success': 1}
  verification  : downloads_manifest: clean
  verification  : evidence_bundle: clean
```

The report it wrote opens with the statements it is written under, including the
one this framework is held to:

```
> This framework does not bypass authentication, authorization, paywalls, DRM, licensing controls, or other access restrictions.
```

and closes with what it does not establish:

| Section | What it contains in this run |
|---|---|
| Summary | `- Evidence records: 2`, `- Validated (REPRODUCED): 0`, `- Not validated (POTENTIAL or UNVERIFIED): 0`, counts by status and severity |
| Observations | Both records, with status, severity, confidence, target and title |
| Record detail | Every field of each record, verbatim, including its limitations |
| Acquisitions | `Obtained: 1`, `Blocked: 1`, then **Blocked paths, and the authorised route** for `D0002` |
| Verification | Both `evidence_bundle: clean` and `downloads_manifest: clean` |
| What this report does not establish | That an observation is a finding, that the count of reached paths is the count of existing paths, and that absence of an observation is evidence of absence |

## 9. The deliberate failures in the same run

| Command | Result |
|---|---|
| A link on the fixture page pointing at another host | recorded as out of scope, **not followed**; `1 reference(s) not followed` |
| `/private/notes`, named by the sitemap and excluded by the scope | **not requested**; the crawl reports it as out of scope |
| `/forbidden` returning `403` | recorded `blocked`, no file written, route to the owner stated, exit `0` |
| A `POST` replay of a stored `GET` without `--confirm-write` | refused before the request exists, exit `3` |
| A URL outside `allowed_hosts` | refused, nothing sent, exit `3` |
| A YAML API description handed to `api inspect` | exit `1`, "a YAML description is not parsed by this reader" |
| A record edited after its bundle was written | `evidence manifest --verify` exits `1` with the mismatched hash; the report is still produced and states the problem in it |

## Reproducing this

```bash
python3 -m workbench.cli --help
python3 workbench/run_tests.py                 # the whole suite, loopback fixtures only
python3 workbench/run_tests.py test_end_to_end # this chain, as a test, with its assertions
```

`test_end_to_end.py` runs the same sequence with assertions on each step,
including that no request method other than `GET` and `HEAD` ever reached the
fixture server, that the refused resource left no file behind, and that a bundle
edited afterwards is reported rather than read as evidence.
