# Phase 5 final report

**Phase:** 5 — authorized-use workbench, evidence, and reporting
**Branch:** `phase5/workbench` → `main`
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Report generated:** 2026-09-30

Every number in this report was measured on the branch named above, by the
command cited beside it. Nothing here is estimated and nothing is rounded up.
Where a number could not be measured, that is stated as not measured rather than
approximated.

---

## 1. Declaration

**The phase is complete in substance and not yet complete in form.** §36 says not
to declare completion if any listed condition fails, and two conditions are open:

| §36 condition | State |
|---|---|
| Every capability classified, only genuine additions implemented | **Met** — §4 below, 39 requests classified in `docs/CAPABILITY-AUDIT.md` §6 |
| Mandatory scope file checked before every request; no bypass | **Met** — §7, asserted by test |
| No bypass switch, no hidden override | **Met** — §7, a test walks the argument tree |
| Findings stay potential; differences stay observable differences | **Met** — §10, §15 |
| Comprehensive positive and negative tests | **Met** — §18, 490 tests |
| Deterministic local fixtures only | **Met** — §18, §19 |
| `phase5-validation.yml` exists | **Met** — §19 |
| End-to-end test with deliberate failure paths | **Met** — §18 |
| Documentation with the required sentence, threat model and limitations | **Met** — §20 |
| Complete capability audit re-run | **Met** — §4 |
| No fake or placeholder production content | **Met** — §22 |
| **One Phase 5 PR opened** | **NOT MET** — the branch is committed and verified locally; the pull request is not open |
| **CI green on the PR, then post-merge verification** | **NOT MET** — depends on the PR |

The PR is not open because opening it needs a GitHub credential, and this
session's standing rule is that no token is ever held, printed or stored. The
branch is ready to push and the pull request description is written
(`/home/user/PHASE5-PR-BODY.md`). Everything that could be verified without a
credential — the suite, the gates, the end-to-end chain — is verified and
recorded below.

**This report therefore claims Phase 5 complete as work, and open as a
delivery.** Nothing is proposed for a Phase 6, per §37.

---

## 2. What the phase was asked to deliver

A new capability family for the framework: an authorized-use workbench covering
HTTP inspection and history, a request editor, a response inspector, a repeater
with deterministic comparison, parameter discovery, bounded fuzzing, discovery
under allowlists, an acquisition engine with full provenance, PDF and archive
reading, untrusted-file handling, normalized evidence, emergency mode, mandatory
scope enforcement, credential hygiene, a documented command surface, tests,
documentation, CI, and a final report — under an absolute prohibition on
bypassing any access control, on fabricating any result, and on describing a
potential finding as confirmed.

---

## 3. What was delivered

| Area | Delivered | Where |
|---|---|---|
| Authorization | Scope file, loader, guard, call-site helper, decision records | `workbench/scope.py` |
| HTTP | One socket path: pinned address, verified TLS, capped reads, re-checked redirects, TLS facts | `workbench/http_client.py` |
| History | Append-only JSON Lines, ids, summaries, replay | `workbench/history.py` |
| Comparison | Exact, normalised and JSON-structural, plus cookie and header comparison | `workbench/diff.py` |
| Parameters | Inventory, classification, value masking, suggested cases | `workbench/params.py` |
| Mutation | Catalogue, application, conflict detection, write-verb listing | `workbench/mutate.py` |
| Fuzzing | Bounded runs, budget, rate limit, cancellation, duplicate suppression | `workbench/fuzz.py` |
| Checks | Sixteen observable checks producing evidence records | `workbench/checks.py` |
| Evidence | Required fields, five statuses, transition ladder, hashing, bundles | `workbench/evidence.py` |
| Discovery | Published surfaces only, caps, refusals with reasons | `workbench/discover.py` |
| Acquisition | Provenance, type sniffing, blocking statuses, manifest, verification | `workbench/fetch.py` |
| Reading | PDF, zip, tar, gzip, OOXML and text under limits | `workbench/extract.py` |
| Emergency | Read-only collection, structurally read-only | `workbench/emergency.py` |
| Reporting | Report assembly with derived counts and verification | `workbench/report.py` |
| Surface | 21 commands, four exit codes, JSON output | `workbench/cli.py` |
| Tests | 15 modules, 490 tests, loopback fixtures | `workbench/tests/` |
| Documentation | 5 documents including a real transcript | `docs/workbench/` |
| CI | Workbench suite with a loopback-only socket layer, run twice, plus bandit | `.github/workflows/phase5-validation.yml` |

---

## 4. Capability classification

Every requested capability was classified before any code was written. The full
table is `docs/CAPABILITY-AUDIT.md` §6, checked by
`python3 .github/scripts/verify_capability_audit.py` (85 claims, all resolving).
Counts by classification:

| Classification | Count | Examples |
|---|---|---|
| ALREADY COVERED (a document governs it; the code implements it) | 6 | Deterministic comparison labelled an observable difference; the `downloads` manifest schema; premium and licensed resources; evidence fields and statuses; credential redaction; the acquisition manifest's four statuses |
| EXTENSION (a document covers the method; code was needed to carry it out) | 14 | HTTP history; request editor; response inspector; repeater; parameters; bounded fuzzing; test modules; mutation records; discovery; acquisition; PDF and archive reading; untrusted-file handling; scope enforcement; the manifest as code |
| NEW CAPABILITY | 2 | Read-only emergency collection; the command surface |
| ALREADY COVERED as policy, EXTENSION as enforcement | 1 | Mandatory scope check before every request |
| OUT OF SCOPE, declined with a reason | 1 | The console UI — optional in the directive, and a second surface to keep truthful |
| UNSAFE-REJECTED | 12 | WAF/IDS/rate-limit/auth evasion; access-control circumvent­ion; automatic exploitation; executing a download; promoting a potential finding; `--ignore-scope`; crawling a linked domain; vendoring a third-party HTTP library; automatic replay of a destructive method |
| DUPLICATE | 0 | Nothing was implemented twice |

Two of these matter more than the rest. **Emergency mode is the only genuinely
new capability in the family**: everything else was a method the framework's own
documents already governed, and the code carries the method out rather than
redefining it. And **the console UI was declined**: it was optional, and the CLI
already reports real states without manufacturing any.

---

## 5. Architecture and module inventory

`workbench/` is standard-library Python. It starts no subprocess, imports no
third-party package, and has no build step.

| Measure | Value | How measured |
|---|---|---|
| Production modules | 18 | `ls workbench/*.py \| wc -l` |
| Production lines | 8,699 | `wc -l workbench/*.py` |
| Test modules | 15 | `ls workbench/tests/test_*.py \| wc -l` |
| Test lines | 6,965 | `wc -l workbench/tests/*.py` |
| Tests | 490 | `python3 workbench/run_tests.py --json` |
| Commands | 21 | `workbench/cli.py` `COMMANDS`, asserted equal to the parser by test |

The module set is listed in `docs/workbench/README.md`. The two modules a
reviewer should read first are `scope.py` and `http_client.py`, because they are
where every guarantee below is implemented.

---

## 6. The command surface

| Group | Commands |
|---|---|
| `scope` | `validate` |
| `http` | `inspect`, `replay`, `diff`, `mutate`, `fuzz` |
| `api` | `discover`, `inspect` |
| `web` | `crawl`, `scan` |
| `resource` | `inspect`, `download`, `extract` |
| `evidence` | `hash`, `manifest` |
| `emergency` | `collect` |
| `report` | `generate` |

Exit codes, uniform across the surface: `0` the command ran and produced output,
`1` it could not run, `2` the arguments were wrong, `3` the scope file refused a
request. A command that observes something worrying and reports it exits `0`,
because the exit code describes whether the command ran, not whether the target
looked healthy.

`--json` is available everywhere and prints one object on stdout with human
output on stderr. There is no duplicate command: the documented list is compared
against the parser by a test in both directions.

---

## 7. Scope and authorization enforcement

| Property | Implementation | Assertion |
|---|---|---|
| Every active request is checked before it is sent | `scope.require()` raises `ScopeError`; it never returns a flag to be checked later | `test_scope`, `test_http_client` |
| `--scope` is required by every command that sends a request | argparse `required=True` on those 12 commands; `_guard()` refuses without it | `test_cli::test_every_command_that_sends_a_request_requires_a_scope_file` |
| No flag disables a control | none exists; a test walks the argument tree for `ignore`, `bypass`, `skip`, `unsafe`, `insecure`, `disable` | `test_cli::test_no_flag_in_the_surface_is_named_after_a_control_it_switches_off` |
| A scope file that would disable a control is refused | `scope.py` rejects unknown control-disabling keys | `test_cli::test_a_scope_file_that_would_disable_a_control_is_refused` |
| No budget, no host or no method means refusal, not an inert scope | `ScopeError` at load: "an unbounded request budget is not a scope" | `test_scope` |
| Write methods need the scope *and* an explicit confirmation at the call site | `require(..., confirm_write=True)`, which no command sets | `test_cli`, `test_end_to_end` |
| Out-of-scope targets cost nothing | refused before a socket is opened | `test_cli::test_a_target_outside_the_scope_file_is_refused_with_the_scope_exit_code` |
| Private, loopback, link-local and multicast addresses are refused without an explicit opt-in | address vetting in `http_client` and `scope` | `test_scope`, `test_http_client` |

---

## 8. HTTP guarantees

One function opens sockets. Within it:

- **One connection per request**, to an address resolved once and vetted against
  the scope, with TLS verified against the name from the URL. Automatic
  reconnection is switched off, so a dropped connection raises instead of
  resolving the name a second time.
- **One TLS context**, built once for both the handshake and the connection
  object — an earlier version created two, one of which never performed a
  handshake.
- **Bodies capped on the read**, not after it, so a target cannot exhaust memory
  by lying about `Content-Length`. A short read after a `Content-Length` is
  reported as short, not as a clean 200.
- **Redirects re-checked per hop** against the scope; an out-of-scope hop is
  refused and recorded, not followed.
- **TLS facts recorded**: protocol version, cipher, certificate subject, issuer,
  validity and fingerprint, as observed.

---

## 9. History, replay and comparison

The history is append-only JSON Lines: one exchange per line, with ids that
survive across runs because `History.load` resumes numbering from what is on
disk. A second invocation cannot reuse an id — that was a defect, fixed and
tested.

Replay re-sends a stored request as a new record linked to the original, and
reports the difference. Two refusals protect it:

- a stored header whose value was redacted is **dropped**, never transmitted, so
  a replay cannot send the literal string `[redacted]` and produce a `401` that
  reads like a finding;
- a stored URL containing the marker is **refused outright** (`test_http_client`),
  with the instruction to capture the request again with the value supplied.

Comparison reports exact, normalised and JSON-structural differences, and every
output says *observable response difference*. No comparison output is described
as a vulnerability or a finding.

---

## 10. Parameters, mutation and fuzzing

- Parameter inventory and classification over query, body, headers and cookies;
  sensitive names and values are masked and stay masked through mutation and
  reporting.
- The mutation catalogue generates eight kinds — header, query, JSON, form,
  cookie, method, encoding, content-type — and **never generates a write verb**;
  it lists the write verbs a run would need a decision about.
- `http mutate` sends nothing at all, including with `--apply`, which only prints
  the request a mutation would produce.
- `http fuzz` sends within `--limit` and `--budget`, spaced by the scope's
  `min_interval_s`, suppresses duplicates, checks cancellation between requests,
  and records every result with its difference.
- `allow_state_changing` defaults to false and is only reachable through an
  explicit `--confirm-write`.

---

## 11. Discovery

Discovery reaches what a target publishes: `robots.txt`, sitemaps, forms,
OpenAPI and Swagger documents at conventional locations, script references, and
the assets a page links to. There is no wordlist, no extension sweep and no name
guessing. GraphQL endpoints are reported only when the target references one, and
are never queried.

Caps: pages, depth, budget and asset inclusion, all with defaults. Refusals are
recorded in three distinct categories rather than collapsed: references not
followed because they were out of scope, in-scope URLs the target declined, and
references left unexplored when a cap was reached.

---

## 12. Acquisition and the manifest

Every acquisition records source URL, final URL, status, content type, size,
SHA-256, timestamp, redirect chain, licence note, authorization scope, file type,
type confidence, whether the extension matches the content, and the extraction
status.

Nothing is recorded as obtained unless the bytes arrived and re-hash on disk. A
`401`, `402`, `403`, `407`, `451`, a challenge page, a subscription wall, a
signed-URL expiry or a DRM notice ends that path: the entry is `blocked`, it names
no file, and the output lists the route that *is* authorised — the owner, the
publisher's own page, the item's public metadata, a library. Statuses are exactly
`success`, `failed`, `blocked`, `skipped`.

---

## 13. Document and archive reading

PDF, zip, tar, gzip, OOXML (`docx`, `xlsx`, `pptx` and their macro variants),
EPUB, JAR and text are read with the standard library. Limits: 50 MB per file,
500 files, 100 MB total, a 200:1 expansion ratio, depth 2, 200,000 characters of
text, 500 PDF pages.

Guards, each with a test: absolute paths, `..`, empty names, null bytes, symlinks
and device nodes are never written; a bomb is refused with nothing extracted; an
encrypted member is skipped and said so; an extension that contradicts the
content is flagged whether or not the type was detected confidently; and
`resource extract` refuses to parse a file whose hash no longer matches its
manifest entry — checked **before** the file is read, because the earlier order
printed an inventory of a file whose output said it had not been read.

Nothing is executed, imported, installed, or interpreted. No subprocess exists.

---

## 14. Emergency mode

`workbench/emergency.py` can send `GET` and `HEAD` and nothing else.
`READ_ONLY_METHODS` is a module constant rather than a parameter,
`_read_only_request` is the only send path, and a test parses the module's AST to
assert that every call site passes one of those two literals. A collection reads
the target URL, `/robots.txt` and `/.well-known/security.txt` within
`min(scope.max_requests, 20)` requests, emits evidence records in the standard
format, and describes itself as a snapshot, not an assessment.

---

## 15. Evidence and reporting

Records carry 14 required fields, empty limitations and missing reproduction
steps are hard errors, and a status can only move along `ALLOWED_TRANSITIONS`:
`POTENTIAL` may become `REPRODUCED`, `UNVERIFIED` or `INFERRED`, and `REPRODUCED`
requires a second observation rather than a change of mind. No check in
`checks.py` can produce `REPRODUCED` — asserted by test.

A bundle writes each record with its hashes and an aggregate manifest, and
`Bundle.verify()` re-hashes on read. The report assembled from a bundle states
both verifications; when a record was edited after the run it reports the
mismatch instead of reading it as evidence, and it still produces the report,
because a reader needs to know what happened rather than receive an exception.

Every count in a report is derived from the records it holds. No record is
promoted: each is printed with its own status, confidence and limitations
verbatim.

---

## 16. Redaction and secret handling

`Authorization`, `Cookie`, `Set-Cookie`, `X-API-Key` and `Proxy-Authorization`
values are redacted by name in every record, report and log. `Set-Cookie` keeps
its attributes and loses its value, because `HttpOnly`, `Secure` and `SameSite`
are the evidence a cookie check reads.

`--secret` scrubs literal values anywhere they appear: request bodies, response
bodies, the URL, the final URL, the query string, every URL in a redirect chain
(under both `location` and `from`), and the URL inside the scope decision. `host`,
`scheme` and `port` are deliberately untouched — they are not secrets, and a
record that cannot say what it connected to is not evidence.

This was wrong until it was tested: the URL-bearing fields held the value in
plain text while the field beside them showed `[redacted]`.

---

## 17. What was not done

| Not done | Why |
|---|---|
| The console UI | Optional in the directive. A second surface whose states have to be kept truthful, against a CLI that already reports them |
| WAF, IDS, rate-limit or authentication evasion | Refused. Named in the threat model as something the code must never do |
| Any circumvention of an access control | Refused in the code, in the documentation and in the standing statements of every report |
| Automatic exploitation | No exploit surface exists |
| Vendoring any third-party HTTP or parsing library | Nothing was vendored; the workbench is standard-library only |
| A required CI status check for the new workflow | Adding one changes branch protection, which needs approval first |
| Post-merge verification of the published site | Depends on the PR |

---

## 18. The test suite

`python3 workbench/run_tests.py` — **490 tests, 15 modules, 0 failures**, ~100
seconds.

| Module | Tests | What it covers |
|---|---|---|
| `test_scope` | 70 | Host, path, method, budget, rate, address vetting, refusal of control-disabling keys |
| `test_workbench` | 54 | The first modules end to end: guard usage, record shape, bounded reads |
| `test_evidence` | 52 | Required fields, the status ladder, validated-language, hashing, bundles, every check's negative case |
| `test_http_client` | 47 | The socket path: one connection, pinning, TLS, caps, redirects, redaction of bodies, headers and URLs |
| `test_mutation` | 39 | Catalogue, application, state-changing protection, fuzzing bounds |
| `test_fetch` | 35 | Type sniffing, blocked paths, no file on refusal, manifest round trip, verification |
| `test_extract` | 32 | Traversal, links, bombs, encrypted and malformed archives, OOXML routing, the no-execution policy |
| `test_discovery` | 29 | Published surfaces, caps, refusal categories, no guessing |
| `test_cli` | 26 | The surface, exit codes, JSON output, per-command refusals, manifest accumulation |
| `test_emergency` | 18 | Read-only by AST, no write verb on the wire, budget, cancellation, evidence format |
| `test_report` | 18 | Derived counts, zero cases, no promotion, verification problems, output round trip |
| `test_end_to_end` | 1 | The whole chain, with the deliberate failure paths |

Negative tests are the majority of the value and are named in each module's
assertions: refusals, absences, mismatches, tampering and unavailability, not only
the happy paths.

---

## 19. CI and determinism

`.github/workflows/phase5-validation.yml`:

1. the suite is run inside a process where `socket.socket.connect` has been
   wrapped so only loopback addresses can be reached, which turns "the tests
   never contact anything else" from a reading of the source into a property of
   the run — verified locally, exit 0 with 421 passed;
2. the suite is run a second time and the two machine-readable results are
   compared, with the failure count checked first so two identical failures
   cannot pass as deterministic;
3. bandit runs over `workbench/` at MEDIUM and above.

Every fixture is a loopback `ThreadingHTTPServer` in `workbench/tests/fixtures.py`,
identified by an `X-Blackheart-Fixture: true` header. No test performs a DNS
lookup for a real name, and no test contacts a third party.

---

## 20. Documentation

`docs/workbench/` holds five documents, all linked from `docs/README.md`:

| Document | Contents |
|---|---|
| `README.md` | What the workbench is, the seven rules it is built around, the module map, and how to run it |
| `COMMANDS.md` | Every command, the shared flags, exit codes, worked examples, and the deliberate refusals |
| `THREAT-MODEL.md` | What the code is trusted with, the eight things it must never do, and the threats considered |
| `LIMITATIONS.md` | What an observation is not, what the checks cannot decide, that bounds are real limits, and how secrets are handled |
| `END-TO-END.md` | A real transcript of one run against the fixture server, with the failures included |

§28's sentence appears **verbatim** in `docs/workbench/README.md`,
`docs/workbench/END-TO-END.md` and as the first standing statement in every
generated report:

> This framework does not bypass authentication, authorization, paywalls, DRM,
> licensing controls, or other access restrictions.

---

## 21. Defects found and fixed

Thirty-one named defects across the phase. Those found before this report period
are listed in the branch's commit messages; those found during it are:

| # | Defect | Consequence if unfixed |
|---|---|---|
| 22 | `resource extract` parsed a file before checking its manifest hash | The output printed an inventory of a file whose own text said it had not been read |
| 23 | The same path wrote `refused_hash_mismatch`, a value the extraction-status schema does not define | A consumer validating the field would reject the manifest rather than read it |
| 24 | `Extraction.summary()` gave the refusal count but not the reasons | `--json` could not answer "why" without the prose output a pipeline discards |
| 25 | `--secret` did not scrub the URL, final URL, query string, redirect chain or scope decision | A credential in a query string was written to the history verbatim beside a redacted body |
| 26 | A record whose URL was redacted could still be replayed or fuzzed | The literal `[redacted]` would be sent, producing a response that reads like a finding |
| 27 | `report.add_bundle` raised when a bundle's manifest was missing | A report over a tampered bundle could not be produced at all, so the tampering was not reported |
| 28 | The zero case in the report read "0 record(s) are not validated findings. They record …" | A count presented as a claim |
| 29 | The all-validated case said "No record here is a validated finding" | False for a bundle whose records were REPRODUCED |
| 30 | `report.write` wrote markdown into any non-`.json` path | `report.html` would have produced a file rendering as one paragraph |
| 31 | A scope refusal printed "(HTTP None)" in the acquisitions table | Reads as though a request had been made and answered nothing |
| 32 | Documentation said a scope file without a budget "authorises nothing" | It is refused outright; a reader would hunt for a fault in a scope that was never loaded |

Defects 1–21, including multicast passing `is_global`, a short read reported as a
clean 200, `only=[]` running every check, `budget` accepted and ignored, and
`.docm` bypassing the OOXML reader, are recorded in the commit messages on this
branch.

---

## 22. No fabricated content

A scan for leftover placeholder and work-in-progress markers — the same scan
`gap_audit.py` group 19 runs over the authored documentation — returns nothing
across `workbench/` and `docs/workbench/`. Every fixture is
labelled as a fixture; every transcript is captured output; the fixture server
identifies itself in a response header. No simulated traffic is presented as
real, no scan result is invented, and no sample finding appears anywhere — the
example records in the tests are generated by the checks themselves against the
fixture target.

---

## 23. Repository gates, measured

| Gate | Command | Result |
|---|---|---|
| Workbench suite | `python3 workbench/run_tests.py` | 490 passed, 0 failed, 15 modules |
| Static analysis | `python3 -m bandit -r workbench -ll` | exit 0; 0 issues at MEDIUM or above; 5 line-level suppressions, each with its reason on the preceding line; 97 LOW findings at the full-severity run, expected in test tooling |
| Repository validation | `python3 .github/scripts/validate.py` | 8/8 — adapters 387, integrity 3,864 vendored files byte-identical, catalogue 32, links 5,381 with 0 broken in authored docs, index 4,467 with 0 unindexed and 0 dangling, secrets, config, history |
| Gap audit | `python3 .github/scripts/gap_audit.py` | 20/20 |
| Capability audit | `python3 .github/scripts/verify_capability_audit.py` | 85 claims; every cited path resolves; every published count current |
| Authored config | `python3 .github/scripts/check_authored_config.py` | 17 files parse; every workflow well-formed |
| Policy gate | `python3 -m workbench.cli policy validate` | the policy parses; all ten documents it names exist |
| Policy enforcement | `python3 workbench/run_tests.py test_policy` | 28 passed — including every route the directive named for getting past the gate |
| Index | `python3 .github/scripts/gen_index.py --check` | in sync, 4,467 entries |
| End-to-end | `python3 workbench/run_tests.py test_end_to_end` | 1 passed |

---

## 24. Repository figures updated in this phase

Every figure below was re-derived from the gate that measures it, never typed
from memory.

| Figure | Before the phase | At the phase commit | Final | Derived from |
|---|---|---|---|---|
| `FILE-INDEX.txt` entries | 4,435 | 4,449 | 4,467 | `gen_index.py --check` |
| Local links checked | 5,279 | 5,297 | 5,381 | `validate.py` |
| Workflows | 6 | 7 | 7 | `.github/workflows/*.yml` |
| Authored files (activation prompt) | 55 | 60 | 74 | the walk `gap_audit.py` performs |
| Capability rows | 62 (29/15/18) | 74 (40/16/18) | 74 (40/16/18) | section row counts |
| Commands | 14 | 17 | 21 | `cli.build_parser()` |
| Test modules | 10 | 12 | 15 | the test registry |
| Tests | 352 | 421 | 490 | `run_tests.py` |
| Policy documents | 0 | 0 | 10 | `policy/BLACKHEART-POLICY.json` |
| Agent documents | 3 | 3 | 5 | `docs/agent/*.md` |

The finalization pass also removed two tests and rewrote two others rather than
leaving them passing for the wrong reason — the counts above are of the suite as it
stands, not of the suite plus the tests that were withdrawn.

---

## 25. Review

The security review was a **self-review** — an adversarial pass by the same
author, with the checks written to fail first — and it is labelled as such rather
than as an independent review. It found four of the defects above (25, 26, 28 and
32 were found by writing the test that should have existed, and 22–24 and 27–31
were found by running the tools against their own fixtures and reading the
output).

What the pass verified directly:

| Claim | How it was checked |
|---|---|
| Only `http_client` opens a socket | Every module searched for socket use; all call sites route through `hc.request(guard, ...)` |
| No path disables a control | A test walks the argument tree; `grep` for `--ignore`, `--bypass`, `--skip`, `--unsafe`, `--insecure`, `--disable` returns nothing |
| Nothing executes a download | `grep` for `subprocess`, `exec`, `eval`, `__import__`, `pickle`, `marshal`, `os.system`, `ctypes` returns nothing outside the policy test that asserts their absence |
| Extraction cannot write outside its directory | `_unsafe_member_name` (name-level) and `_resolve_inside` (`realpath`-level) are both checked at every member write site |
| A credential cannot reach disk through a URL | A test asserts the secret is absent from the whole serialised record and that the history written with `--secret` carries the marker |
| A refusal costs no request | Fixture-server hit counts asserted at zero after every refusal path |

An independent review has not been performed. §34 asks for one, and the honest
state is that it is outstanding; the report would otherwise be claiming a second
pair of eyes that was not there.

The finalization pass ran a second, adversarial review written from the reviewer's
side rather than the implementer's, and it is recorded in full — method, findings,
withdrawn hypotheses, the bypass campaign and what it does not cover — in
`docs/workbench/INDEPENDENT-SECURITY-REVIEW.md`. It found six defects, all fixed,
each with the test that fails against the earlier behaviour; the findings are
numbered F-1 to F-6 in that document and described in §30 below. It is still a
self-review, and that document says so in its first section rather than in a
footnote.

---

## 26. Freeze

**This section records the state at the phase commit. The final declaration, made
after the finalization pass and after every gate had been re-run on the frozen
tree, is §34.**

Per §37, after this phase: no Phase 6, no new backlog, no cosmetic features, no
dependency upgrades for freshness, no speculative skills, and no duplicate
commands. The Phase 4 upstream watcher is preserved and nothing third-party was
vendored — nothing in this phase added a vendored file, and admission of upstream
content still requires a human reading it.

The workbench is frozen at the state described above. Any later change to it is a
new engagement with its own authorization, not an extension of this one.

---

## 27. The policy layer

A framework that documents its rules and does not enforce them is documenting an
intention. This phase closed that gap: the rules are now a machine-readable policy,
and the workbench refuses to open a socket until they have been accepted.

| Component | What it is |
|---|---|
| `policy/BLACKHEART-POLICY.json` | Policy version 1.0.0. Ten named documents, the requirements, the acceptance block, the enforcement block, the prohibited and exempted operations, and the acquisition rules |
| `workbench/policy.py` | The acceptance engine: load, validate, record, and `require_acceptance()`, which is the gate |
| `workbench/http_client.py` | `require_acceptance()` is the first statement of `request()` — the socket boundary, not the CLI |
| `workbench/cli.py` | Four commands: `policy validate`, `policy status`, `policy accept`, `policy show`; the parser now has 21 commands and the count is asserted against the parser, not typed |
| `workbench/tests/__init__.py` | The suite performs a real acceptance into a temporary state directory. The gate is exercised, never stubbed |

**Two requirements, deliberately separate.** An active operation needs a recorded
acceptance *and* a valid scope. Acceptance establishes that the rules were read on
that machine; the scope file is the operator's assertion of authorization. Neither
substitutes for the other, and the difference is tested rather than described.

**The acceptance record** is local: policy version, the policy document's SHA-256,
and a timestamp. No identity, no hostname, no target, nothing transmitted. It is
written atomically with mode 600, and a symlinked record is refused rather than
followed — the record decides whether requests go out, so it is not something to
resolve through a link.

**A material change invalidates it.** The version and the content hash are both
checked, so editing the policy after acceptance leaves the acceptance stale and
active work refused. A record with no hash is refused for the same reason: it
cannot be checked, and an unchecked record is not an acceptance.

**What this does not do.** It is not authentication of the operator and not
authorization for anything. Anyone who can write to the state directory can accept
the policy. That residual is recorded in the policy itself under
`enforcement.documented_residual` rather than left for a reader to discover.

## 28. The agent documentation layer

Two documents, both new, and the existing ones extended rather than duplicated:

| Document | Why it exists |
|---|---|
| `docs/agent/PHASE5-SAFETY-RULES.md` | The rules an agent must meet before it meets a target: AUTHORIZATION FIRST, the never-do list, acceptance-is-not-authorization, the stop conditions, and the reporting obligations |
| `docs/agent/PHASE5-WORKBENCH-OPERATIONS.md` | The capability map: each command group, what it refuses, what the agent records when it refuses, and the deterministic blocked/ambiguous tree |
| `docs/agent/AGENT-OPERATING-PROTOCOL.md` (extended) | The eleven-step operating order and the decision tree, added where an agent already reads before it acts |
| `docs/agent/AGENT-BOOTSTRAP.md` (extended) | A Layer 0 for the binding rules, the policy and workbench documents in the reading list, and the authored-file count re-derived to 74 |

The candidates in the directive that would have restated an existing document —
a separate protocol, a separate failure-handling guide, per-capability agent
guides — were folded into these two rather than written as duplicates. The test is
whether a document contains judgement that is not already published; where the
answer was no, nothing was written.

## 29. Independent review

**Status: outstanding.** No genuinely separate reviewer exists in this
environment, and the gate is not marked passed. The wording used in
`docs/workbench/INDEPENDENT-SECURITY-REVIEW.md` is that independent review remains
outstanding, and §8 of that document sets out what a reviewer would need to do to
close it.

What was performed instead, and what the report claims for it:

| | Performed | Claim |
|---|---|---|
| Adversarial self-review, CLI and module boundaries | yes | complete |
| Bypass campaign against the policy gate (fifteen routes named in the directive) | yes | every route fails safely |
| Cross-implementation attacks written from the public interface | yes | 23 tests, kept in the suite |
| Review by a person with no part in building this | **no** | **not claimed** |

## 30. Defects found in the finalization pass

Six, all fixed, each with a regression test that fails against the previous
behaviour. They are numbered F-1 to F-6 in the review document; summarised here:

| # | Defect | Consequence before the fix |
|---|---|---|
| F-1 | A challenge interstitial served where a *page* was expected was written and recorded as a successful acquisition | The manifest called an interstitial the page; nothing in the entry said otherwise |
| F-2 | `Evidence.as_dict()` serialised without validating | A hand-built record reached JSON with no limitation, no reproduction step, unchecked |
| F-3 | `report.add_bundle` adopted every record before verifying it | A record edited after writing still supplied the report's counts, beside the hash mismatch warning |
| F-4 | `History.add` wrote the operator's tag verbatim | A credential typed into a tag sat in the clear in a file otherwise redacted end to end |
| F-5 | `policy.acceptance_status` skipped the hash check when the record had no hash | Deleting one JSON field defeated the change check on the policy |
| F-6 | `cli.py` used the policy module without importing it | Every `policy` subcommand raised `NameError`; the acceptance commands did not run at all |

Two further defects were found in the review's own test code: two tests deleted the
suite-wide state-directory variable instead of restoring it, which presented as
thirteen failures in an unrelated module. Both were rewritten around one
save-and-restore context manager. Recorded because the failure mode — a test that
breaks a later test — is worth recognising.

## 31. Privacy and legal audits

**Privacy.** The privacy policy describes only audited behaviour. The audit
covered: the workbench's storage (history, bundles, manifests, downloads,
extractions, reports, acceptance record), the socket layer (one connection path,
checked against the scope first), the site (no analytics, no cookies, no forms, no
third-party embeds, one `localStorage` entry for the theme), the workflows (what
each one reads and writes, and which have write permissions), and the acceptance
record (local, no identity, nothing transmitted). Two claims were withdrawn during
the audit as unsupported: an apparent tracker on the site, which was the word
"plausible" in a sentence of prose, and a secret leak in a response body, which
was the history tag and became F-4.

**Legal.** Ten documents, written to state what the project is and what it does not
claim. No entity, attorney, certification, jurisdiction or approval is invented;
the project is identified as BLACKHEART Security Framework, GitHub owner
`devara1983ntr`, author Roshan. Every document that carries a legal effect says
that it has not been reviewed by a lawyer and that its effect depends on
jurisdiction. Liability is stated as an allocation of responsibility between the
user and the author, not as a promise that liability cannot arise. Tests assert
that no compliance badge, company form, legal professional or absolute claim
appears in authored content, and that the README and the site link every document
the policy names.

## 32. Policy enforcement, tested

The gate was attacked from every route the directive named. Each failed safely —
refused, no socket, no file written:

| Route | Result |
|---|---|
| Alternate command | Refused before any request |
| Direct module invocation (`http_client.request`) | Refused at the socket boundary |
| Environment variables (`*_POLICY_ACCEPTED`, `*_IGNORE_POLICY`, `*_SKIP_POLICY`) | Not read; no effect |
| A directory that does not exist, and one that is empty | Blocks; writes nothing into it |
| Malformed policy JSON, and a policy naming a missing document | Refused, with the reason |
| Old acceptance, and acceptance before a policy change | Stale, checked by version and by content hash |
| Acceptance record edited by hand, or with the hash deleted | Refused |
| Symlinked acceptance record | Refused rather than followed |
| Relative path, and a different working directory | Resolved absolutely; same answer |
| Command ordering (accept, then delete the record) | Re-checked per request |
| Direct replay through the history path | Same gate, same refusal |
| A flag that looks like a bypass | None exists, asserted over every option string |

The exemption for local, read-only work is tested too: the exempt commands run
without an acceptance, and a test holds the policy's exemption list against the
command parser so that a command requiring `--scope` cannot be described as exempt.

## 33. What remains, and why

| Step | State |
|---|---|
| Local gates on the frozen tree | **green** — suite 490, `validate.py` 8/8, `gap_audit.py` 20/20, capability audit current, `bandit -ll` exit 0 |
| Push of `phase5/workbench` | **not performed here.** The remote is configured, but the credential is the operator's and is not held by this environment. §29 forbids asking for it in a transcript |
| One pull request, base `main` | prepared — the body is reconciled to the measured values; opening it needs the same credential |
| CI on the pull request | **not run** — it runs when the push happens |
| Independent review | **outstanding**, per §29 |
| Merge | **not performed.** Normal merge only, and only after the review gate and every required check |
| Post-merge and live verification | **not performed** — it follows the merge |
| Policy documents deployed and reachable | **verified locally**; the live check follows the merge |

Nothing in this table is represented as done. The next command in the sequence is
the push, and it needs the operator.

## 34. Final freeze declaration

The declaration is made on the frozen tree at the commit this report is committed
in — the last commit on `phase5/workbench` before it is pushed. Every gate in §23
was re-run on that tree after the last content change, and the values in §23 and
§24 are the values those runs produced.

**Frozen at that commit:**

- the workbench: 18 production modules, 15 test modules, 490 tests, 21 commands;
- the policy layer: `policy/BLACKHEART-POLICY.json` v1.0.0, `workbench/policy.py`,
  the acceptance gate at the socket, and the ten documents it names;
- the agent layer: two new documents, two extended, and the activation prompt's
  reading list and counts re-derived;
- the repository figures in §24, each measured rather than recalled.

**After this point:** no Phase 6, no new backlog, no features, no cosmetic
redesign, no dependency upgrades for freshness, no speculative skills, no duplicate
commands, and no reopening of anything recorded here as complete. Any later change
is a separate engagement with its own authorization.

**The independent review is not declared complete, and this freeze does not depend
on that claim** — it depends on the gates above, all of which passed. If a
separate review is later performed, its findings are a new engagement, not an
amendment to this one.

---

## Appendix A: commit list

| Commit | Subject |
|---|---|
| `b36c773` | workbench: the authorization gate and the bounded HTTP client |
| `7ed2117` | Phase 5: analysis, mutation, fuzzing, evidence and checks modules |
| `8ee3b1b` | workbench: open the connection once and pin it, and verify with one TLS context |
| `1c6755b` | workbench: discovery under an allowlist, with provenance for every reference |
| `5e5b091` | workbench: acquisition with provenance, and the manifest that records it |
| `3d130ab` | workbench: reading documents and archives without trusting or executing them |
| `a35834b` | Phase 5: emergency collection, a report generator, and the command surface |
| `94866ee` | Phase 5: the workbench's own CI gate, its documentation, and the end-to-end test |
| `ee2b53d` | Phase 5: re-run the capability audit, and correct the roadmap's statement of what ships |
| `45101df` | workbench: check the manifest hash before parsing a file, not after |
| `06f4e1f` | workbench: redact a credential in the URL, not only in the body and headers |
| `ebd3a70` | workbench: document `--secret` and `--history`, and say what redaction now covers |
| `65db525` | docs: a scope file with no request budget is refused, not defaulted |
| — | the Phase 5 report and CHANGELOG entry |
| `85ebf32` | Phase 5: the policy layer, the legal documents, and the adversarial review |
| — | the finalization: figures reconciled, the review recorded, the freeze declared |

## Appendix B: reproducing every claim in this report

```bash
cd /path/to/blackheart-security-framework
git checkout phase5/workbench

python3 workbench/run_tests.py                 # 490 passed, 15 modules
python3 workbench/run_tests.py test_end_to_end # the whole chain, with its assertions
python3 -m bandit -r workbench -ll             # 0 at MEDIUM or above
python3 .github/scripts/validate.py            # 8/8
python3 .github/scripts/gap_audit.py           # 20/20
python3 .github/scripts/verify_capability_audit.py
python3 .github/scripts/check_authored_config.py
python3 .github/scripts/gen_index.py --check
python3 -m workbench.cli --help                # the 21 commands
python3 -m workbench.cli policy validate       # the policy and its ten documents
```
