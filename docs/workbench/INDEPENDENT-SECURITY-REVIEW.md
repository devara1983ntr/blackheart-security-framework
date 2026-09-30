# Independent security review

**Subject:** the BLACKHEART workbench — `workbench/`, `policy/`, and the policy
documents it names
**Date:** 2026-09-30
**Review type:** adversarial self-review, with a second pass by a different
implementation route
**Independent review status:** **outstanding** — see §1

---

## 1. What this document is, and what it is not

This document records an adversarial review of the workbench. It separates three
things that are easy to blur together:

| | What happened | Status |
|---|---|---|
| **Self-review** | The author attacked their own implementation, using the claims in `docs/workbench/` as the list of things to falsify | **Complete.** Findings and fixes in §4–§6 |
| **Cross-implementation pass** | The attack code was written against the public interface rather than the internals, so it exercises the same boundary a third party would | **Complete** |
| **Independent review** | A review performed by someone with no part in building this | **Outstanding. Not performed.** |

**The independent review has not been performed.** No separate reviewer has been
available in this environment, and inventing one would be worse than not having
one. The self-review above is not a substitute for it and must not be described as
one: an author attacking their own design shares every assumption that produced
the design, and the assumptions are exactly what an independent reviewer is for.

**No claim in this repository should be read as "independently reviewed" or
"independently verified".** The gate is open, and §8 says what would close it.

## 2. Scope

In scope: `workbench/` (17 modules), the policy layer (`policy/`,
`workbench/policy.py`) and the ten documents it names, the CLI surface, the
evidence and reporting path, and the CI workflow that runs the suite.

Out of scope, and not reviewed here: vendored third-party content under
`skills/` (audited separately, `skills/VENDOR.md`), the site, and anything outside
the loopback fixture environment — **no test in this repository sends a request to
the internet, and none was sent during this review.**

## 3. Method

Working from the guarantees the documentation makes, in the order a reader would
meet them:

1. **Read the claim.** "A blocked acquisition writes no file." "No credential
   reaches disk." "The policy gate is at the socket."
2. **Write the attack.** Not "does the feature work" but "what would make this
   claim false", including the boring routes: an environment variable, a relative
   path, a hand-edited JSON file, a direct module call that skips the CLI.
3. **Observe at the boundary, not at the interface.** Where the claim is "nothing
   was sent", the evidence is the fixture server's own request log, not the tool's
   account of itself.
4. **Fix only what is real.** A false positive in the review is a defect of the
   review; §7 lists two claims that did not survive contact with the code and were
   withdrawn rather than "fixed" into the implementation.

The attacks are checked in as `workbench/tests/test_adversarial.py` (23 tests) and
`workbench/tests/test_policy.py` (28 tests), so the review is re-run on every
push rather than existing only as prose.

## 4. Findings

Six defects were found. All six are fixed, and each has a regression test that
fails against the previous behaviour.

| # | Finding | Why it mattered | Fix | Test |
|---|---|---|---|---|
| F-1 | `fetch.acquire` only tested for a challenge interstitial when the URL was expected to carry a document. A challenge served where a **page** was expected was written to disk and recorded as `success`. | The manifest — the framework's record of what it obtained — called an interstitial a successful acquisition of the page. A reader had no way to see it. | The marker is now detected regardless of what was expected and recorded in the entry's warnings. The blocking decision is unchanged, deliberately (§7). | `test_a_page_that_carries_a_challenge_marker_says_so` |
| F-2 | `Evidence.as_dict()` did not validate. A record built by hand and serialised — the route that skips `Bundle.add` — reached JSON with an empty limitation, a missing reproduction step, or validated language on an unvalidated record. | Serialisation is the moment a claim becomes quotable. A record with no stated limitation reads as complete coverage. | `as_dict()` validates before it serialises. | `test_a_record_without_limitations_cannot_be_validated_or_serialised` |
| F-3 | `report.add_bundle` appended every record file to the report and verified afterwards, so a record edited after the bundle was written still supplied the report's counts and severity table while the report printed a hash mismatch beside them. | The counts in a report were partly the product of tampered files. The module's own docstring said "Nothing from an incomplete bundle is adopted as evidence" — the implementation and its stated rule disagreed. | Records are verified before adoption, through one shared `Bundle.verify_record_file`, and the report states that failing records are excluded from the counts. | `test_a_record_edited_after_the_bundle_was_written_is_caught` |
| F-4 | `History.add` redacted the exchange and then wrote the caller's `tag` verbatim. | The tag lands in the same file as the redacted record, so a credential typed into a tag was stored in the clear in a file that is otherwise redacted end to end. `--secret` exists precisely to cover values the operator knows are sensitive. | The tag is scrubbed with the same helper through the new public `http_client.redact_text`. | `test_no_credential_reaches_disk_by_any_route` |
| F-5 | `policy.acceptance_status` compared hashes only when the recorded hash was present, so deleting `policy_sha256` from the acceptance record defeated the change check: a policy edited after acceptance still read as accepted. | This is the bypass route the hash exists to close, reachable with a text editor. | A record without a policy hash is refused as not accepted, with a reason that says why. | `test_the_blocker_cannot_be_skipped_by_editing_the_acceptance_by_hand` |
| F-6 | `cli.py` referenced the policy module without importing it. Every `policy` subcommand raised `NameError`. | The commands that record and report acceptance did not run at all. Found while verifying the layer end to end rather than in a test. | Import added; `policy validate`, `status`, `accept` and `show` verified against the parser, the exit codes and the on-disk record. | `test_policy.py` (28 tests) |

Two further defects were found in the review's *own* test code and are recorded
because they were the same class of mistake: two tests saved and then **deleted**
the suite-wide `BLACKHEART_STATE_DIR`, which left every later module without an
acceptance and reported it as a failure of the code under test. Both were rewritten
around one save-and-restore context manager.

## 5. Bypass campaign

The directive for this phase named a specific set of attacks against the policy
gate. Each was attempted; each failed safely. "Failed safely" means: refused, no
socket opened, no file written, and a message a reader can act on.

| Attack | Result |
|---|---|
| Alternate command (`scope validate`, `http inspect`, `resource acquire`) | Each goes through one guard; refused before any request |
| Direct module invocation (`http_client.request(...)`, bypassing the CLI) | Refused at the socket boundary with the same error |
| Environment variables (`BLACKHEART_POLICY_ACCEPTED`, `BLACKHEART_IGNORE_POLICY`, `BLACKHEART_SKIP_POLICY`) | No effect; the variables are not read |
| Relocating the state directory to an empty or missing path | Blocks; nothing is written into it |
| Malformed policy JSON | Refused by name, with the parse error |
| Missing policy document | Refused, naming the document |
| Acceptance recorded against an older version | Stale, with both versions named |
| Acceptance recorded before the policy changed | Stale, by content hash |
| Acceptance record with the hash deleted | Refused: no hash, no acceptance |
| Symlinked acceptance record | Refused rather than followed |
| Relative path, and a different working directory | Resolved absolutely; the answer does not change |
| JSON manipulation of the acceptance record | Version and hash both checked |
| Command ordering (accept, then remove the record) | Re-checked per request; the next request is refused |
| Direct HTTP call through the replay path | Same gate, same refusal |
| CLI flags that look like bypasses | None exist; asserted over every registered option string |

## 6. What the campaign does not cover

The campaign is limited by the same fixture environment the suite runs in. In
particular it does **not** cover: a hostile target, TLS interception, DNS-based
attacks, a compromised host, a determined attacker with write access to the
operator's filesystem, or the vendored skills. Anyone relying on the gate should
read this paragraph as part of the finding.

## 7. Claims that were checked and withdrawn

Two review hypotheses did not survive contact with the code. They are recorded so
that a later reviewer does not spend time on them again:

- **"A challenge marker blocks any page containing the word `captcha`."** True of
  the old code path for documents and false for pages, and that asymmetry is
  deliberate: the framework's own documentation pages mention captchas, and
  refusing to fetch them would be a false positive with a real cost. The finding
  that survived was narrower — the page was *silent* about the marker — and that
  is what F-1 fixes. The design decision is left alone.
- **"Secrets leak through the response body."** Not reproducible: `record()`
  scrubs known secret values from the body, and the earlier apparent leak was the
  history *tag*, which is F-4. Reported as one finding, not two.

## 8. How to perform the independent review

What would close the gate, stated so it can be handed to someone:

1. **Read `docs/workbench/README.md`, `LIMITATIONS.md` and this file**, then take
   the guarantees as a list of things to falsify.
2. **Run the suite** and confirm the fixtures are what they claim:
   `python3 workbench/run_tests.py test_` — 14 modules, 472 tests, loopback only.
3. **Attack the boundary independently**, with code written from the public
   interface rather than from these tests. The gate is the first statement of
   `http_client.request()`; scope enforcement sits below it in `scope.require()`.
4. **Check the policy claims against the code**, document by document. The mapping
   a reviewer needs is in `policy/BLACKHEART-POLICY.json` and §6 of
   `DOWNLOAD-AND-ACQUISITION-POLICY.md`.
5. **Try the bypass list in §5** and add routes that are not on it.
6. **Record what you find**, including "nothing", and say which claims you could
   not falsify rather than only which you broke.

A review performed this way by someone outside the project can be recorded here by
replacing this section. Until then the status at the top of this document is
**outstanding**, and it should stay that way.

## 9. Residual limitations

Carried forward honestly, and not fixed by this review:

- The policy acceptance is a **local acknowledgement**, not authentication of the
  operator and not authorization for anything. A person who can write to the state
  directory can accept the policy. That is documented in
  `policy/BLACKHEART-POLICY.json` under `enforcement.documented_residual` and
  cannot be fixed inside the tool.
- Scope enforcement is only as good as the scope file the operator writes. The
  tool checks arithmetic and structure; it cannot check whether the operator is
  telling the truth about their authorization.
- Redaction covers what the tool was told about. An unnamed credential in a body
  is stored as received; `docs/workbench/LIMITATIONS.md` says so.
- The six findings above were found by one author with the code in front of them.
  The most likely remaining defects are the ones that author is not looking for.
