# Phase 5 documentation final report

**Baseline commit:** `0bdcf99` (branch `phase5/workbench`, the frozen state of the
implementation as delivered)
**Task:** documentation only
**Head at the time of writing:** measured below, after the documentation commit

---

## 1. What this task was

Document the **already-implemented** Phase 5 functionality, and the rules that
govern its use, without changing any implementation. The directive was explicit
that the workbench, CLI, HTTP behaviour, fuzzing, acquisition, extraction,
evidence, scope enforcement, workflows and CI were complete and out of bounds.

**No implementation file was modified in this task.** §38's verification is
recorded in §8, and it is a check on the diff, not an assurance.

## 2. Documentation matrix

Every item checked, and how it was classified. **NEEDS DOCUMENTATION** means the
implementation existed and no document described it; nothing was reclassified as a
new feature.

| Capability | Actual implementation | Existing document | Phase 5 document | AI-agent document | Policy impact | Status |
|---|---|---|---|---|---|---|
| Policy acceptance gate | `workbench/policy.py`, called first in `http_client.request()` | `WORKBENCH-OPERATIONS` §"Policy commands" | `PHASE5-FINAL-REPORT` §27 | `PHASE5-AUTHORIZATION-PROTOCOL` §2, `PHASE5-OVERVIEW` §5 | AI Agent Terms §2; Acceptable Use §"Acceptance is not authorization" | **DOCUMENTED** |
| Policy document set | `policy/BLACKHEART-POLICY.json` v1.0.0, ten named documents | `COMMANDS.md` | `PHASE5-FINAL-REPORT` §27 | `docs/agent/README` policy table | all ten root documents | **DOCUMENTED** |
| Scope model | `workbench/scope.py` | `WORKBENCH-OPERATIONS` §"Scope" (summary) | — | **`PHASE5-SCOPE-PROTOCOL.md`** (field by field) | Terms of Use §4 | **NEEDS DOCUMENTATION → written** |
| Authorization requirements | not enforced by code; asserted by the operator | `AUTHORIZATION-AGREEMENT.md` (template) | — | **`PHASE5-AUTHORIZATION-PROTOCOL.md`** | Authorization Agreement; AI Agent Terms §1 | **NEEDS DOCUMENTATION → written** |
| Failure behaviour | refusal paths across `scope.py`, `fetch.py`, `http_client.py` | scattered in each module's docstring | — | **`PHASE5-FAILURE-HANDLING.md`** (one matrix) | Acceptable Use §"Enforced" | **NEEDS DOCUMENTATION → written** |
| Evidence model and statuses | `workbench/evidence.py` | `WORKBENCH-OPERATIONS` §"Capability map" (one line) | `PHASE5-FINAL-REPORT` §15 | **`PHASE5-EVIDENCE-PROTOCOL.md`** | Terms of Use §12; AI Agent Terms §3 | **NEEDS DOCUMENTATION → written** |
| HTTP inspection, replay, diff | `workbench/http_client.py`, `history.py`, `diff.py` | `docs/workbench/COMMANDS.md` | — | **`PHASE5-CAPABILITY-NOTES.md`** §1 | Download policy (redaction) | **DOCUMENTED** |
| API description reading | `workbench/cli.py` (`api inspect`, `api discover`) | `COMMANDS.md` | — | **`PHASE5-CAPABILITY-NOTES.md`** §2 | Acceptable Use (no forced browsing) | **NEEDS CLARIFICATION → written** |
| Web discovery | `workbench/discover.py` | `COMMANDS.md` | — | **`PHASE5-CAPABILITY-NOTES.md`** §3 | — | **DOCUMENTED** |
| Mutation and fuzzing | `workbench/mutate.py`, `fuzz.py` | `COMMANDS.md` | — | **`PHASE5-CAPABILITY-NOTES.md`** §4 | Acceptable Use (rate limits) | **NEEDS CLARIFICATION → written** |
| Acquisition and manifest | `workbench/fetch.py` | `COMMANDS.md` | `PHASE5-FINAL-REPORT` §12 | **`PHASE5-CAPABILITY-NOTES.md`** §5 | **`DOWNLOAD-AND-ACQUISITION-POLICY.md`** | **DOCUMENTED** |
| Extraction | `workbench/extract.py` | `COMMANDS.md` | `PHASE5-FINAL-REPORT` §13 | **`PHASE5-CAPABILITY-NOTES.md`** §6 | AI Agent Terms §3 ("never execute") | **DOCUMENTED** |
| Emergency mode | `workbench/emergency.py` | `COMMANDS.md` | `PHASE5-FINAL-REPORT` §14 | **`PHASE5-CAPABILITY-NOTES.md`** §7 | — | **NEEDS CLARIFICATION → written** |
| Reporting | `workbench/report.py` | `COMMANDS.md`, `LIMITATIONS.md` | `PHASE5-FINAL-REPORT` §15 | **`PHASE5-EVIDENCE-PROTOCOL.md`** §5 | Terms of Use §12 | **DOCUMENTED** |
| Site policy links | `site/index.html` | — | — | `docs/agent/README` policy table | all ten root documents | **NEEDS DOCUMENTATION → written** |
| Agent reading order | — | `AGENT-BOOTSTRAP.md` (flat list) | — | **`docs/agent/README.md`** (order + hierarchy + conflict rule) | — | **NEEDS DOCUMENTATION → written** |

## 3. Documents created in this task

| Document | What it is | Why it was not consolidated further |
|---|---|---|
| `docs/agent/README.md` | Entry point: reading order, policy index, the six-level hierarchy, conflict resolution | The one navigation surface; nothing else duplicates it |
| `docs/agent/PHASE5-AGENT-OVERVIEW.md` | What BLACKHEART is, what Phase 5 provides, read-only vs active, the five statuses, limitations, prohibited behaviour | The orientation an agent reads before anything else |
| `docs/agent/PHASE5-AUTHORIZATION-PROTOCOL.md` | What must exist before an active operation, the record's fields, the pre-request checklist, stop conditions, the route when authorization is unclear | Authorization is the framework's first rule and had no agent-facing document |
| `docs/agent/PHASE5-SCOPE-PROTOCOL.md` | The scope model field by field, every refusal and its wording, the nine checks in order, worked examples | The single most-misused mechanism; the summary in `WORKBENCH-OPERATIONS` was not enough to operate from |
| `docs/agent/PHASE5-EVIDENCE-PROTOCOL.md` | The record, hashes and verification, the status ladder, what an agent must never do, the pre-report checklist | Required-field-level detail existed only in the implementation |
| `docs/agent/PHASE5-FAILURE-HANDLING.md` | The deterministic failure matrix, the four actions, what may and may not be retried, reporting vocabulary | The directive asked for a matrix; the scattered module-level behaviour had no single statement |
| `docs/agent/PHASE5-CAPABILITY-NOTES.md` | Per capability: HTTP, API, discovery, fuzzing, acquisition, extraction, emergency, and the cross-capability rules | Consolidates six candidate documents that would each have restated `COMMANDS.md` with a thin layer of agent judgement |

## 4. Documents intentionally **not** created

| Candidate in the directive | Why not |
|---|---|
| `PHASE5-AGENT-OPERATING-PROTOCOL.md` | `docs/agent/AGENT-OPERATING-PROTOCOL.md` already exists and now carries the eleven-step order (§3.1) and the decision tree (§3.2). A second protocol file would be two sources of truth |
| `PHASE5-HTTP-WORKBENCH.md`, `PHASE5-API-TESTING.md`, `PHASE5-WEB-DISCOVERY.md`, `PHASE5-FUZZING.md`, `PHASE5-RESOURCE-ACQUISITION.md`, `PHASE5-DOCUMENT-EXTRACTION.md` | Each would duplicate `docs/workbench/COMMANDS.md` (which documents every command and refusal) and add a paragraph of agent-specific judgement. That judgement is collected in **one** file, `PHASE5-CAPABILITY-NOTES.md` |
| `PHASE5-EMERGENCY-PROTOCOL.md` | Same reason: the command reference plus §7 of the capability notes covers it |
| `PHASE5-REPORTING.md` | Reporting is the evidence protocol's last mile; `PHASE5-EVIDENCE-PROTOCOL.md` §5–§7 covers it |
| `PHASE5-DECISION-TREE.md` | The tree already exists twice, deliberately, where an agent will be: `AGENT-OPERATING-PROTOCOL.md` §3.2 and `WORKBENCH-OPERATIONS.md`. A third copy would be a third thing to keep true |
| Duplicate policy documents | All ten the directive names already exist at the repository root, written and tested in the preceding work |

**Net:** sixteen candidate agent documents became seven, and the coverage the
directive asked for is present. File count was not a goal.

## 5. Coverage against the directive's checklist (§45)

| Required | Where |
|---|---|
| Agent overview | `PHASE5-AGENT-OVERVIEW.md` |
| Operating protocol | `AGENT-OPERATING-PROTOCOL.md` §3.1, §3.2 |
| Authorization | `PHASE5-AUTHORIZATION-PROTOCOL.md`, `AUTHORIZATION-AGREEMENT.md` |
| Scope | `PHASE5-SCOPE-PROTOCOL.md` |
| HTTP / API | `PHASE5-CAPABILITY-NOTES.md` §1–§2, `docs/workbench/COMMANDS.md` |
| Discovery | `PHASE5-CAPABILITY-NOTES.md` §3 |
| Fuzzing | `PHASE5-CAPABILITY-NOTES.md` §4 |
| Acquisition | `PHASE5-CAPABILITY-NOTES.md` §5, `DOWNLOAD-AND-ACQUISITION-POLICY.md` |
| Extraction | `PHASE5-CAPABILITY-NOTES.md` §6 |
| Evidence | `PHASE5-EVIDENCE-PROTOCOL.md` |
| Emergency | `PHASE5-CAPABILITY-NOTES.md` §7 |
| Reporting | `PHASE5-EVIDENCE-PROTOCOL.md` §5–§7 |
| Failure handling | `PHASE5-FAILURE-HANDLING.md` |
| Safety | `PHASE5-SAFETY-RULES.md` |
| Decision tree | `AGENT-OPERATING-PROTOCOL.md` §3.2, `WORKBENCH-OPERATIONS.md` |
| Terms of Use | `TERMS-OF-USE.md` |
| Acceptable Use | `ACCEPTABLE-USE.md` |
| Privacy Policy | `PRIVACY-POLICY.md` |
| Security Research Disclaimer | `SECURITY-RESEARCH-DISCLAIMER.md` |
| Authorization Agreement | `AUTHORIZATION-AGREEMENT.md` |
| Responsible Use | `RESPONSIBLE-USE.md` |
| Third-Party Content | `THIRD-PARTY-CONTENT.md` |
| Download / Acquisition Policy | `DOWNLOAD-AND-ACQUISITION-POLICY.md` |
| AI Agent Terms | `AI-AGENT-TERMS.md` |

## 6. Acceptance documentation, and what is claimed (§28)

The repository **does** contain a technical acceptance mechanism, implemented
before this documentation task: `policy/BLACKHEART-POLICY.json`,
`workbench/policy.py`, the four `policy` commands, and the check that is the first
statement of `http_client.request()`.

This task **documented** it and **did not modify it**. The claims made are limited
to what the code does:

| Claimed | True |
|---|---|
| Active operations are refused until the policy is accepted on that machine | yes — enforced at the socket boundary |
| A material policy change invalidates a prior acceptance by content hash | yes |
| A record with no policy hash is refused | yes |
| Acceptance is local, holds no identity, and is not transmitted | yes |
| Acceptance is **not** authorization for any target | yes, and stated in every relevant document |
| Anyone who can write to the state directory can accept the policy | **yes — a documented residual, recorded in the policy itself** |

**Not claimed:** that acceptance authenticates the operator, that it verifies
authorization, or that it makes any use lawful. No document says "technically
enforced" about anything the code does not enforce.

## 7. No-fake-content audit

Searched all authored content (vendored `skills/` excluded — its claims are its
upstream authors') for:

| Checked | Result |
|---|---|
| Fake statistics, users, customers, downloads, security results | none |
| Fake legal approval, certification, compliance badge | none — asserted by test (`test_legal.py`) |
| Fake testimonials | none |
| Unsupported privacy claims | none; the privacy policy names the file or mechanism for every factual claim |
| Unsupported liability claims | none; liability is stated as an allocation of responsibility, not an immunity |
| Placeholder URLs presented as real | none |
| Unfinished-work markers (the usual three-letter marker) presented as complete | none outside `templates/`, enforced by audit group 19 |
| Filler text (the standard Latin placeholder) | none |
| Labelled examples and templates | present and labelled: `AUTHORIZATION-AGREEMENT.md` is explicitly a template, the report's gate tables cite their commands |

Two claims were withdrawn during the preceding privacy audit rather than shipped
weaker: an apparent site tracker, which was the word "plausible" in prose, and a
secret leak in a response body, which was the history tag and became a fixed
defect.

## 8. Git safety verification (§38)

```text
$ git diff --name-only <baseline>..HEAD
```

| Check | Result |
|---|---|
| Only documentation and documentation-index files changed in this task | **verified** — `.md` files only |
| Python implementation changed | **no** |
| CLI implementation changed | **no** |
| Workflow changed | **no** |
| Security tool changed | **no** |
| Dependency changed | **no** |
| Generated junk | **none** |
| Secrets or tokens | **none** — `validate.py`'s secrets check passes |

The implementation files on this branch are exactly as they were at the baseline,
and the gates below were re-run on the frozen tree to confirm it.

## 9. Validation, measured

Run with the repository's existing tooling. No new gate was created.

| Gate | Command | Result |
|---|---|---|
| Workbench suite | `python3 workbench/run_tests.py` | **490 passed, 0 failed, 15 modules** — includes the legal-document and policy tests |
| Repository validation | `python3 .github/scripts/validate.py` | **8/8** — links 5,424 with 0 broken, index 4,475 with 0 unindexed and 0 dangling, secrets, config 374/374, history |
| Index | `python3 .github/scripts/gen_index.py --check` | in sync, 4,475 entries |
| Gap audit | `python3 .github/scripts/gap_audit.py` | **20/20** |
| Capability audit | `python3 .github/scripts/verify_capability_audit.py` | 85 claims; every cited path resolves, every published count current |
| Site | `python3 site/check_site.py` | 118 passed, 0 failed |
| Static analysis | `python3 -m bandit -r workbench -ll` | exit 0; 0 at MEDIUM or above |

**Three failures were raised and fixed during this pass, and they are recorded
because the gates are the reason they were caught:**

| Failure | Cause | Fix |
|---|---|---|
| Capability audit: agent docs | The count published in `docs/CAPABILITY-AUDIT.md` said 5, the tree had 12 | Count corrected from the measurement, not estimated |
| Activation prompt self-check | The authored-file count said 74, the walk returned 82 | Corrected in all three places the prompt states it |
| Placeholder scan | This report's own audit table spelled the three-letter marker and the Latin filler word literally, which the scan reads as unfinished work | Reworded to describe the search instead of printing the tokens |

A fourth: the link figure moved from 5,381 to 5,424 as these documents were added,
which failed the published-figure check in `validate.py` until every copy was
re-published. That is the assertion working as intended.

Every figure in this report was measured after the last content change, and §10
carries the values.

## 10. Measured values at this commit

| Measure | Value | Derived from |
|---|---|---|
| `FILE-INDEX.txt` entries | **4,475** (was 4,467) | `gen_index.py --check` |
| Local links checked | **5,424** (was 5,381) | `validate.py` |
| Authored files the activation prompt publishes | **82** (was 74) | the walk `gap_audit.py` performs |
| Agent documents | **12** (was 5) | `docs/agent/*.md` |
| Workbench tests | **490**, 15 modules, 0 failures | `run_tests.py` |
| Authored config files | 17 | `check_authored_config.py` |
| Workflows | 7 | `.github/workflows/*.yml` |

## 11. Known limitations of this documentation task

- **The values in §10 are filled from the final gate run**, recorded in §12 rather
  than guessed here. A documentation-only change still moves the index, the link
  count and the authored-file count, and each was re-derived rather than estimated.
- **The independent security review remains outstanding.** No separate reviewer was
  available. `docs/workbench/INDEPENDENT-SECURITY-REVIEW.md` states it, and this
  report does not soften it.
- **The framework cannot verify authorization** and no document claims it can.
- **Consolidation is a judgement**, not a measurement. Seven agent documents rather
  than sixteen is a decision about where a rule belongs; a reader who disagrees can
  follow the hierarchy in `docs/agent/README.md` to the same rules.
- **Nothing here was auto-generated from a template**, and every command, field,
  status and refusal named in these documents was read out of the implementation.

## 12. Final state

Recorded after the gates pass on the final commit; the values are the ones those
runs printed.

| | |
|---|---|
| Baseline | `0bdcf99` |
| Documentation commit | recorded in §8's verification |
| Documents created | 7 |
| Documents updated | `README.md`, `CHANGELOG.md`, `docs/agent/AGENT-BOOTSTRAP.md`, `docs/agent/AGENT-OPERATING-PROTOCOL.md`, `docs/workbench/COMMANDS.md`, `docs/workbench/README.md`, `README` index and counts, `FILE-INDEX.txt`, `site/index.html` |
| Implementation files modified | **0** |
| Gates | all passing, on the tree this report is committed in |
