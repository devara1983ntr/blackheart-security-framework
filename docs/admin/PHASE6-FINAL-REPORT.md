# Phase 6 final report

## Administrative and emergency security governance — documentation only

**Branch:** `phase5/workbench` · **Baseline at the start of this task:** `3703312`
**Task:** governance documentation for high-risk **authorized** research, using
only already-implemented capabilities
**This phase adds no tool, no command, no flag, no workflow change and no bypass**
**Head at the time of writing:** the final tree at the current HEAD. Branch
figures are pinned to the named historical commit `8288c46` — see §10 — so that
editing this report cannot invalidate its own measurements

---

## 1. What this phase was, and what it was not

The accepted directive was *governance documentation for high-risk authorized
research*. This report covers that work.

**It was not** the other Phase 6 request — the one asking for documentation that
would enable aggressive bypass of authentication, paywalls, DRM, licensing and
access controls, protected by an administrator password. That request was
**refused in full**, on the reasoning recorded in §2. Administrative framing, an
"admin-only" scope and a password change nothing about it, because documentation
is itself the deliverable: an admin-only gate around a bypass still produces the
bypass.

## 2. The refusal, and why it is recorded here

| Element of the refused request | Position |
|---|---|
| Bypass of authentication, authorization or MFA | Prohibited by `ACCEPTABLE-USE.md`, `TERMS-OF-USE.md` and `DOWNLOAD-AND-ACQUISITION-POLICY.md`. No administrative role relaxes it |
| Paywall, subscription and premium-content circumvention | Same, plus the acquisition rules implemented in `workbench/fetch.py`, which record a blocked status and write no file |
| DRM and licensing-control circumvention | Same |
| Download-restriction and signed-URL circumvention | Same |
| Obtaining private or premium content without authorization | Out of scope for every role in this project |
| Gating any of the above behind an administrator password | Does not change the nature of the content. And a password in a chat transcript is a compromised credential, not a control — see §2.1 |
| "Documentation only" as a mitigating frame | Documentation of a bypass is a bypass recipe. The prohibition is on the outcome, not the medium |

**Nothing from that request was implemented, in whole or in part, in any form.**
The verified absence is recorded in §5.

### 2.1 The credential supplied with it

| | |
|---|---|
| Written to the repository? | **No.** Absent from the working tree, from all files, and from all commits on all refs |
| Present before this phase? | **No.** Searched working tree content, commit content across all refs, and the CI secrets gate |
| Grants anything here? | **No.** There is no administrator account, no login, no role, no privileged mode and no admin credential in this framework |
| Required action | **Rotate it.** It was transmitted in plain text over a chat interface and now exists in that record. If the same value is in use anywhere real, rotate it now |
| Replacement committed? | **No**, and never will be. A committed administrator credential would be the backdoor §5 forbids |
| Recorded as | A placeholder only — `<ADMIN_CREDENTIAL>` — in [`EMERGENCY-AUTHORIZATION-TEMPLATE.md`](EMERGENCY-AUTHORIZATION-TEMPLATE.md) and [`SECURITY-CONTROLS.md`](SECURITY-CONTROLS.md) |

## 3. Documents created in this phase

Ten numbered documents under `docs/admin/`, one template, and this report —
twelve files in total.

| # | Document | What it establishes |
|---|---|---|
| 1 | [`README.md`](README.md) | The four roles, the read order, the conflict rule, and what this layer does not claim |
| 2 | [`ADMIN-GOVERNANCE.md`](ADMIN-GOVERNANCE.md) | Administrative authority ≠ target authorization; what an admin role is and is not; there is no admin account, deliberately |
| 3 | [`HIGH-RISK-RESEARCH.md`](HIGH-RISK-RESEARCH.md) | Twelve high-risk triggers, the ten requirements, the ten procedural dual-authorization components, access-control research rules, payment and premium rules, when to decline |
| 4 | [`EMERGENCY-GOVERNANCE.md`](EMERGENCY-GOVERNANCE.md) | Emergency access as accelerated review of already-authorized work; the eight requirements; expiry; what `emergency collect` actually is; fourteen stop conditions; the decision tree; fail-closed |
| 5 | [`SECURITY-CONTROLS.md`](SECURITY-CONTROLS.md) | Nine invariants; the backdoor prohibition in detail; how each prohibition is verified; the credential policy and the rotate-never-reproduce rule |
| 6 | [`CONTENT-AND-DATA-RULES.md`](CONTENT-AND-DATA-RULES.md) | What may be acquired and what is refused; no circumvention recipes; data minimisation; retention; third-party content; no permitted version of the prohibited list |
| 7 | [`AUDIT-AND-EVIDENCE.md`](AUDIT-AND-EVIDENCE.md) | The administrative record and its fields; what the administrative record may never contain; where the technical evidence rules live; the four prohibitions in administrative terms |
| 8 | [`ADMIN-THREAT-MODEL.md`](ADMIN-THREAT-MODEL.md) | Twelve threats in THREAT/IMPACT/PREVENTION/DETECTION/RESPONSE/**LIMITATION** form, and the shared limitation beneath them |
| 9 | [`AI-ADMIN-PROTOCOL.md`](AI-ADMIN-PROTOCOL.md) | The administrator case for an AI agent: administrator status is not target authorization, how to ask for what is missing, what to refuse and report |
| 10 | [`ADMIN-REVIEW-CHECKLIST.md`](ADMIN-REVIEW-CHECKLIST.md) | The pre/during/post checklist, with the three boxes most often ticked wrongly |
| — | [`EMERGENCY-AUTHORIZATION-TEMPLATE.md`](EMERGENCY-AUTHORIZATION-TEMPLATE.md) | The bounded, expiring record for emergency access, including the declaration that disqualifies it when operator and authorizer are the same person |

### Consolidation: 20 suggested topics → 11 documents

| Suggestion | Consolidated into |
|---|---|
| Administrator governance, universal/master-password prohibition, no-backdoor policy, role separation | `ADMIN-GOVERNANCE.md` §2–§6; `SECURITY-CONTROLS.md` §2 |
| Access-control research rules, authentication and authorization boundaries | `HIGH-RISK-RESEARCH.md` §§2–3, §6 |
| Paywall and download-restriction policy, private-resource rules | `CONTENT-AND-DATA-RULES.md` §1 and §7 |
| Controlled test environments | `HIGH-RISK-RESEARCH.md` §4 |
| Emergency authorization procedure, emergency access conditions, expiry | `EMERGENCY-GOVERNANCE.md` §§1–3; the template |
| Audit requirements and evidence handling | `AUDIT-AND-EVIDENCE.md` §§2–4 |
| Stop conditions, emergency audit trail | `EMERGENCY-GOVERNANCE.md` §5 |
| Threat model, detection and response | `ADMIN-THREAT-MODEL.md` (own document) |
| AI administrator rules, agent constraints | `AI-ADMIN-PROTOCOL.md` (own document) |
| Review checklist | `ADMIN-REVIEW-CHECKLIST.md` (own document) |

**Fewer documents with distinct value, rather than one per topic.** Role separation
and the backdoor prohibition are the same argument seen from two sides and read
together; splitting them produced duplicated prose, not clearer rules.

## 4. Coverage against the directive

| Directive | Where | Status |
|---|---|---|
| §1 Admin authority ≠ target authorization | `ADMIN-GOVERNANCE.md` §§1–3; `README.md` | Covered |
| §2 Only docs with distinct value; consolidate duplicates | §3 above | Covered |
| §3 Four roles, not interchangeable | `README.md`; `ADMIN-GOVERNANCE.md` §3 | Covered |
| §4 High-risk classification: 12 triggers and 10 requirements | `HIGH-RISK-RESEARCH.md` §§2–3 | Covered |
| §5 Dual authorization, recorded fields, procedural only | `HIGH-RISK-RESEARCH.md` §5 | Covered |
| §6 Emergency access: documented incident, minimum necessary, time-limited, auto-expiring, audited, never a generic bypass | `EMERGENCY-GOVERNANCE.md` §§1–4 | Covered |
| §7 Absolute backdoor prohibition list | `SECURITY-CONTROLS.md` §2; `ADMIN-GOVERNANCE.md` §5 | Covered |
| §8 Credential policy; exposure → compromised, rotate, never reproduce | `SECURITY-CONTROLS.md` §3 | Covered |
| §9 Authentication vs authorization vs target authorization | `ADMIN-GOVERNANCE.md` §§1, 3 | Covered |
| §10 Access-control research: record, never obtain others' data, authorized test accounts only | `HIGH-RISK-RESEARCH.md` §6 | Covered |
| §11 Paywall and premium: no circumvention, no recipes | `CONTENT-AND-DATA-RULES.md` §§1–2 | Covered |
| §12 Download restrictions → record, stop, refuse | `CONTENT-AND-DATA-RULES.md` §1 | Covered |
| §13 Deterministic decision tree | `EMERGENCY-GOVERNANCE.md` §7; agent version in `AI-ADMIN-PROTOCOL.md` §5 | Covered |
| §14 Controlled test environments preferred | `HIGH-RISK-RESEARCH.md` §4 | Covered |
| §15 Audit-log fields, never secrets | `AUDIT-AND-EVIDENCE.md` §2 | Covered |
| §16 Evidence rules: immutable, hashed, never fabricated, modified or simulated-as-real | `AUDIT-AND-EVIDENCE.md` §3 | Covered |
| §17 Data minimisation, unexpected sensitive data | `CONTENT-AND-DATA-RULES.md` §3 | Covered |
| §18 Stop conditions | `EMERGENCY-GOVERNANCE.md` §5 | Covered |
| §19 Pre/during/post checklist | `ADMIN-REVIEW-CHECKLIST.md` | Covered |
| §20 Threat model with LIMITATION per threat | `ADMIN-THREAT-MODEL.md` T-1…T-12 | Covered |
| §21 `docs/admin/AI-ADMIN-PROTOCOL.md` | Created at that path | Covered |
| §22 Responsibility: identity exact, no invented entity, no immunity claims | `ADMIN-GOVERNANCE.md` §7 | Covered |
| §23 Policy consistency, stricter wins, no contradictions | `README.md` conflict rule; `ADMIN-GOVERNANCE.md` §8 | Covered |
| §24 No secret or password documentation; credential audit | `SECURITY-CONTROLS.md` §3; measured in §6 | Covered |
| §25 Documentation-only guarantee before commit | §7 below | Completed |
| §26 Final documentation audit | §8 below | Completed |
| §27 This report, including the no-implementation statement | This document, §5 | Completed |
| §28 Commit, push, PR, CI, merge, verify, freeze | §10; the operational state is recorded where it happened | In progress at the time of writing |

## 5. The no-implementation statement

Stated exactly, in the terms the directive requires, and verifiable against §6:

> **No bypass, circumvention, credential-access, private-content-acquisition or
> security-tool implementation was added.** No authentication bypass, paywall
> circumvention, DRM circumvention, licensing-control circumvention,
> download-restriction circumvention, credential-theft capability,
> private-content acquisition path, exploitation engine, authentication system,
> administrative backdoor, hidden override, password bypass, bypass CLI flag or
> control-disabling functionality was created, modified or documented.

**What this phase changed, in full:** Markdown files under `docs/admin/`, the
repository index that enumerates files, and the published counts that are derived
from those files. No Python, no CLI, no workflow, no dependency, no policy JSON,
no test, no script, no site content, no adapter, no skill.

## 6. Verified absence of the prohibitions

Each row is a command that was run on this tree. The results are the substance of
§5 — an absence claim is only worth the check behind it.

| Prohibition | Verification | Result |
|---|---|---|
| No hidden admin password | `grep -rniE "admin\|password" workbench/*.py` and the CLI walk | No administrator credential is accepted or referenced anywhere |
| No universal or master password | `grep -rniE "master[_ -]?key\|universal[_ -]?(password\|key)"` over authored files | No match |
| No undocumented bypass switch or secret CLI flag | `python3 workbench/run_tests.py test_policy` — walks the **live argparse tree**, every subparser at every depth | **184** option strings (41 distinct), **0** bypass-shaped |
| No magic header, env-var backdoor or emergency credential in source | `grep -rniE "backdoor\|bypass\|master_key\|universal_key" workbench/` | No match in production code |
| No authentication system, role or privileged mode added | `grep -rniE "def login\|authenticate\(\|is_admin\|privileged_mode" workbench/` | No match |
| No secret or credential in this documentation layer | `python3 .github/scripts/validate.py` secrets check | Passes; placeholders only |
| No credential from the refused request, anywhere | Working-tree search, `git log --all -S` content search, and the secrets gate | Absent from every file and from all history |
| No control-disabling change | §7 diff verification | Documentation files only |

**These checks are re-runnable.** `SECURITY-CONTROLS.md` §2 lists them so they can
be run before and after any future change to the command surface.

## 7. Documentation-only guarantee (§25)

The guarantee is a check on the diff, run before the commit — not an assurance.

```text
git diff --stat <baseline>..HEAD
```

Expected and observed content of this phase's diff:

| Path | Change type |
|---|---|
| `docs/admin/*.md` | **New** — twelve Markdown files |
| `FILE-INDEX.txt` | Regenerated — enumerates the new files |
| Published count sites (`README.md`, `RELEASE-CHECKLIST.md`, `site/index.html`, `docs/CAPABILITY-AUDIT.md`, `docs/agent/AGENT-BOOTSTRAP.md`, the two Phase 5 reports) | Counts only, reconciled against measured Git output |

**Any non-documentation change in the diff would have been reverted before
committing.** None was present; the branch-wide diff, with its measured file
counts, is in §10.

## 8. Final documentation audit (§26)

| Check | Result |
|---|---|
| Every file in `docs/admin/README.md`'s read order exists | Yes — all nine, plus the template and this report |
| Every relative link in `docs/admin/*.md` resolves | Verified by `validate.py`'s link check |
| The four roles are consistent across every document | Yes; `README.md` and `ADMIN-GOVERNANCE.md` §3 agree |
| Dual authorization is described as procedural everywhere | Yes — no document claims technical enforcement |
| Emergency access is never described as a bypass | Yes — `EMERGENCY-GOVERNANCE.md` §1 states the opposite |
| Every credential reference uses a placeholder | Yes — `<ADMIN_CREDENTIAL>`, and no realistic substitute value |
| No compliance badge, certification or legal-approval claim | Yes — none exists in the layer |
| Identity is exact: BLACKHEART Security Framework · `devara1983ntr` · Roshan | Yes — no company, entity, address or jurisdiction is invented |
| No absolute immunity claim | Yes — responsibility clause per `ADMIN-GOVERNANCE.md` §7 |
| No fabricated evidence, approval, finding or measurement | Yes — every number in this report is a command output |
| No contradiction with a Phase 5 or root policy document | Checked; where the two touch, the stricter rule is stated to win |
| No circumvention recipe, in whole or in part | Yes — `CONTENT-AND-DATA-RULES.md` §2 states the exclusion explicitly |

## 9. Validation, measured

Every gate below was run on **the final tree at the current HEAD**, locally, with
the exact dependency versions the workflows pin:

| Dependency | Pinned by | Version used |
|---|---|---|
| `json5` | `validate.yml`, `authored-scan.yml` | 0.15.0 |
| `bandit` | `phase5-validation.yml`, `authored-scan.yml` | 1.9.4 |
| `pyyaml` | `authored-scan.yml` | 6.0.3 |
| `playwright` + chromium | `site-verify.yml` | 1.63.0 |

### Gate results

| # | Gate | Command, as the workflow runs it | Result |
|---|---|---|---|
| 1 | Workbench suite | `python3 workbench/run_tests.py` | **490 passed, 0 failed**, 15 modules (~101 s: measured at 100.0, 100.6, 101.2 and 102.3 s across runs of this code; the spread is machine variance, not a change of state) |
| 2 | Loopback guard | verbatim `phase5-validation.yml` step | passed — the guard aborts on any non-loopback connect, and it did not trip |
| 3 | Determinism | two runs compared, as CI does | **two runs agree: 490 passed, 0 failed, 15 modules** |
| 4 | Repository validation | `python3 .github/scripts/validate.py` | **8/8** — adapters, integrity (3,864 files), catalogue, links **5,485** with 0 broken authored, index **4,488** with 0 unindexed and 0 dangling, secrets, config 374/374, history |
| 5 | Gap audit | `python3 .github/scripts/gap_audit.py` | **20/20** |
| 6 | Index | `python3 .github/scripts/gen_index.py --check` | in sync, **4,488** entries |
| 7 | Markdown links | verbatim `validate.yml` step | **0 broken** in Blackhearts-authored docs |
| 8 | Capability audit | `python3 .github/scripts/verify_capability_audit.py` | every cited path resolves; every published count current (agent docs **12**) |
| 9 | Authored configuration | `python3 .github/scripts/check_authored_config.py` | 17 files parse; every workflow well-formed |
| 10 | Vendored-skill re-audit | verbatim `validate.yml` step | 388 skill directories audited (advisory, per the workflow) |
| 11 | Static analysis | `bandit -r workbench -ll` | exit 0 — **0 MEDIUM, 0 HIGH** |
| 12 | Static analysis | `bandit -r .github/scripts site -ll` | exit 0 — **0 MEDIUM, 0 HIGH** |
| 13 | Site checks | `python3 site/check_site.py` | **118 passed, 0 failed** |
| 14 | SEO audit | `python3 site/audit_seo.py` | clean — 6 pages, 5 sitemap entries, unique titles and descriptions |
| 15 | Contrast | `python3 site/check_contrast.py` | clean — every measured pair meets AA in both themes |
| 16 | Interactions | `python3 site/test_interactions.py` | **81 passed, 0 failed** — 0 uncaught page errors |

Two modules are worth naming separately, because they test the guarantees this
layer rests on: `test_policy` **28/28**, and `test_adversarial` **23/23** — which
includes the attempts to skip the gate with an environment variable, with a
hand-edited acceptance record, and from an alternate working directory.

**These are local results, not CI results.** No workflow has run against this
branch. The local environment was given the same pinned dependencies CI declares,
which is the closest local approximation available — and it remains an
approximation.

### A correction made during this reconciliation

An earlier revision of this table named
`python3 .github/scripts/capability_audit.py` as the capability-audit command.
**That file does not exist at that path** — the check is
`verify_capability_audit.py`. The gate itself was always green; the *documentation
of the command* was wrong. It is corrected here rather than quietly.

## 10. Commit structure, and the state of the branch

Three things that earlier revisions of this report ran together:

| | Commit(s) | What it is |
|---|---|---|
| **(a) The original Phase 6 documentation commit** | `29e69e8` — `docs: add the Phase 6 administrator governance layer` | **18 files, +2,158 / −12.** The twelve `docs/admin/` files, `FILE-INDEX.txt`, and the five count-bearing carriers (`README.md`, `RELEASE-CHECKLIST.md`, `docs/CAPABILITY-AUDIT.md`, `docs/agent/AGENT-BOOTSTRAP.md`, `site/index.html`) |
| **(b) Report correction commits** | `2c05e1a`, `4bebc6e`, `e38f103`, `3321dca`, `8288c46`, and every later revision of this report | Commits that touch **only `docs/admin/PHASE6-FINAL-REPORT.md`**. The rule is stated so it cannot drift: **every commit after `29e69e8` changes exactly one file**, verifiable with `git diff --name-only 29e69e8..HEAD` however many revisions follow |
| **(c) The baseline Phase 6 started from** | `3703312` | The Phase 5 documentation head — 21 commits, 77 files, +21,001 / −31, complete through §39 |

### Branch state, measured at `8288c46`

`8288c46` is named deliberately: it is a **historical commit**, and pinning the
figures to it means no later edit to this report can invalidate them.

| | |
|---|---|
| Branch | `phase5/workbench` |
| Commits ahead of `main` | **27** — `git rev-list --count main..HEAD` |
| File changes | **89** — 78 added, 11 modified |
| Diff | **+23,224 / −32** — `git diff --shortstat main..HEAD` |
| Ahead of the Phase 6 baseline | `29e69e8` plus each commit that revises this report. **No total is given**, because it increases by one every time this report is corrected — which is exactly the drift that produced the stale figure this section replaces |
| Everything after `29e69e8` | `docs/admin/PHASE6-FINAL-REPORT.md`, and nothing else — the stable form of the claim above |
| Working tree | clean |

**This replaces a stale claim.** Earlier revisions said the branch was "one commit
ahead of `3703312`"; a later revision said six. Both were true when written and
both became false as the branch grew. The lesson is recorded rather than hidden:
**counts that a correction commit can change do not belong in a correction
document.** Figures here are pinned to the named commit `8288c46`, and claims about
the branch's shape are stated as rules that hold however much it grows.

**Note on the branch.** This work sits on top of the Phase 5 branch, complete
through §39 and awaiting its own push. Phase 6 added documentation, and the commits
after `29e69e8` added only this report's text.

## 10a. Delivery status — blocked at the credential boundary

The delivery directive required push → one PR → independent review → CI → merge →
verify → freeze. **Delivery could not be performed in this environment.** This
section records that fact, and the checks behind it, rather than an assumption.

| Delivery element | Actual state |
|---|---|
| Local branch | **Ready.** `phase5/workbench`, working tree clean, 27 commits ahead of `main` (`776c89f`), 89 files, +23,224 / −32 — figures measured at `8288c46`, with only this report changed since |
| Remote configuration | **Absent.** `git remote -v` returns nothing. Stale remote-tracking refs (`origin/main`) survive from an earlier session; they are references without a configured remote, and `git ls-remote origin` fails accordingly |
| Credential mechanism | **Unavailable.** No GitHub CLI, no credential helper, no `~/.git-credentials`, no `~/.netrc`, no SSH key or agent, no token in the environment |
| Live remote, verified read-only | **Public repository; live `main` is `776c89fedae7acf1be6dbc8c8ec90f3266bd9c17`, byte-identical to local `main`.** 0 open pull requests, and `refs/heads/phase5/workbench` does not exist remotely |
| Push | **Not performed, and not possible without a credential.** A push dry-run against the HTTPS URL returned `remote: No anonymous write access` / `fatal: Authentication failed` |
| Pull request | **Not created.** There is no PR number, and none is invented here |
| CI | **Not run.** No workflow has executed against this branch; no result is claimed |
| Merge | **Not performed.** `main` is unchanged on the remote and locally |
| Post-merge verification | **Not applicable** — there is nothing merged to verify |
| Deployment verification | **Not applicable to this branch.** The live site was checked read-only and corresponds to `main` as it stands, which does not include this branch |
| Independent review | **Outstanding — not performed.** No genuinely separate reviewer has been available; a self-review is not an independent review, and none is claimed |

**Nothing was fabricated to fill a gap.** No commit, push, PR number, CI run,
review approval, merge commit, verification result or deployment result appears in
this report, or anywhere in this repository, that did not actually happen.

### What remains, and the exact form it takes

A person holding the repository's credential can complete delivery without any
change to the tree:

```text
git remote add origin https://github.com/devara1983ntr/blackheart-security-framework.git
git push -u origin phase5/workbench          # normal push; no force, no rewrite
```

then open one pull request, base `main`, head `phase5/workbench`, using the
reconciled body; wait for the existing required checks; obtain the separate review
if the project can supply one; merge normally; and verify the published site
against the merged `main`. `/home/user/DELIVERY-RUNBOOK.md` holds the same steps
with the verification commands.

**Two conditions the merge depends on, stated because neither is met:**

1. The **independent security review remains outstanding**. If repository policy
   requires it before merge, the gate is open and the merge waits.
2. The **administrative credential from the refused request must be rotated** if
   the same value is in use anywhere real. It is absent from this repository and
   from all of its history — re-verified in §10b.

### A credential supplied in conversation during this work

A personal access token was later pasted into the delivery conversation. **It was
not used, not stored, not tested, and not reproduced**, and it appears nowhere in
the repository, the workspace artifacts, the history or git configuration. It is
exposed by virtue of having been transmitted as plain text, and it requires
rotation by the same rule §8 applies to every exposed credential. Using it would
also have made this branch's own `SECURITY-CONTROLS.md` §3 false at the moment of
merge.

### Gate state at this head

The gates in §9 were re-run on the final tree at the current HEAD, after the last
content change. All are green. **This is a local result, not a CI result**, and
the difference matters: CI has not run.

### 10b. Audits re-run for this reconciliation

| Audit | Method | Result |
|---|---|---|
| Credential — supplied admin password | `grep` over the working tree and `git log --all -S` | **absent** from every file and every commit on every ref |
| Credential — pasted token | prefix search over tree, history, workspace artifacts, `.patch`, `.sh` | **absent** (0 files, 0 commits) |
| Credential — token-shaped strings | `ghp_[A-Za-z0-9]{36}` over authored files | one match, in `.github/secret-allowlist.json`, and it is `ghp_` + 36 repeated `a` — a repeated-character placeholder used to exercise the secrets gate. **No real credential** |
| Credential — secrets gate | `validate.py` | passes; 15 allowlisted placeholders suppressed |
| Capability — bypass flags, method 1 | the test's walk of the **live argparse tree** (`test_no_command_line_flag_can_skip_the_policy`) | **184** option strings, 41 distinct, **0** bypass-shaped |
| Capability — bypass flags, method 2 | an independent AST scan of `workbench/cli.py` for string literals beginning `-` | **42** option-like literals, **0** bypass-shaped |
| Capability — credential access | search for credential-harvesting functions in `workbench/` | **none** |
| Capability — premium/DRM/paywall acquisition | search for premium, paywall, DRM or licence-bypass functionality | **none** — only refusal logic, and the blocking statuses `401`, `402`, `403`, `407`, `451` |
| Fabricated claims | search for CI-run, PR-number, merge-SHA and approval claims | one match, `CHANGELOG.md:566`, and it is **historical**: introduced by `e98214a`, which is an ancestor of `main`, and it describes an earlier merged state. Every other match is an explicit denial |

**A note on the content audit's method.** Prohibition lists, explicit denials,
absolute-path-encoding helpers for untrusted archive members, and `test_legal.py`'s
own banned-phrase fixtures all match naive searches for `bypass`, `unsafe`,
`hidden override`, `master key` and `universal password`. They were reviewed
individually rather than counted: none of them is an implementation of the thing
it names. Conversely, nothing was waved through because it appeared near a
prohibition — the environment-variable path in `policy.py` was tested directly,
and the tests that attack it (`test_adversarial.py`, 23/23) and the policy tests
(28/28) both pass.

## 11. Known limitations of this documentation task

1. **Nothing in this layer is technically enforced**, except the bounds of
   `emergency collect` and the existing scope and policy gates. The governance
   rules are procedural, and the documents say so wherever it matters.
2. **No authorization can be verified by any artefact in this project.** A scope
   file is an assertion.
3. **The independent security review of the workbench remains outstanding** —
   `docs/workbench/INDEPENDENT-SECURITY-REVIEW.md` records F-1…F-6.
4. **These documents do not replace legal advice.** Where enforceability depends
   on jurisdiction or a legal instrument, the documents say that rather than
   implying otherwise.
5. **The administrative record and the emergency process depend on people
   following them.** A threat model that claimed otherwise would be misleading;
   `ADMIN-THREAT-MODEL.md` §"What the threats have in common" says this plainly.

## 12. Freeze

**The freeze is not declared, because its precondition was not met.** A freeze is
declared only after the delivery gates pass, and delivery is blocked at the
credential boundary (§10a). The branch is complete and unmerged; nothing has been
published, reviewed independently, or verified against a merged `main`.

**What is already true and does not depend on delivery:**

- No backlog, no follow-on phase, no bypass tooling, no backdoors, no universal
  credentials and no hidden overrides exist, are added, or are planned.
- A future change to any of this is a separate engagement with its own
  authorization.

**What remains outstanding:** the push, the pull request, CI, the independent
review, the merge, post-merge verification, and deployment verification — in the
form set out in §10a.
