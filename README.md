<div align="center">

# ⬢ BLACKHEART

## A governed security-supply-chain framework for AI agents

**388 vendored skill directories · 39 commands · 33 agent personas · 3,864 verified files · 399 audited adapters**

*Skills are not the problem. Unvetted skills are.*

[![validate](https://github.com/devara1983ntr/blackheart-security-framework/actions/workflows/validate.yml/badge.svg)](https://github.com/devara1983ntr/blackheart-security-framework/actions/workflows/validate.yml)
[![pages](https://github.com/devara1983ntr/blackheart-security-framework/actions/workflows/pages.yml/badge.svg)](https://devara1983ntr.github.io/blackheart-security-framework/)
[![license](https://img.shields.io/badge/licence-MIT-00d4a5.svg)](LICENSE)

**Live site:** [devara1983ntr.github.io/blackheart-security-framework](https://devara1983ntr.github.io/blackheart-security-framework/)

</div>

<p align="center">
  <a href="https://devara1983ntr.github.io/blackheart-security-framework/">
    <img src="https://devara1983ntr.github.io/blackheart-security-framework/og-image.png"
         alt="BLACKHEART — a governed security-supply-chain framework for AI agents"
         width="640">
  </a>
</p>

---

## Why this exists

A security agent is only as trustworthy as the skills it loads. Install an
unvetted skill and you have handed an autonomous system a third-party
instruction — one that can read files, run shell commands, and exfiltrate
data. There is no lockfile, no signature, and no audit trail.

The industry currently answers this with a README. That is not a control.

Blackhearts treats every third-party skill as **untrusted code** and makes the
governance mechanical rather than aspirational.

> **The premise:** you cannot make untrusted instructions safe. You can only
> make them *legible, bounded, and accountable* before they run.

---

## What it does

| Problem | Blackhearts' answer |
|---|---|
| Unvetted instructions reach the agent | Every skill ships a reviewed `_BLACKHEART-ADAPTER.md` declaring what it does and what it must never do |
| Upstream changes silently | 3,864 files pinned to a commit SHA and compared byte-for-byte on every push |
| Agent personas quietly widen scope | 33 personas treated as **hostile input** — none enabled by default, none may authorise a target or disable the gate |
| A scanner's clean bill of health is trusted | Findings are hypotheses; clean results are recorded as **coverage gaps** |
| Nobody can prove coverage | Eight CI checks and twenty audit groups that fail loudly |

---

## Coverage

Everything upstream ships, verified and accounted for — not just the skills.

<div align="center">

| Collection | Files | | Collection | Files |
|---|---:|---|---|---:|
| Skills | **388** directories | | Standards | **11** |
| Slash commands | **39** | | Audit records | **32** |
| Agent personas | **33** (+1 template) | | Doc pages | **667** |
| Plugin manifests | **2** | | Test fixtures | **1** |
| Upstream scripts | **29** | | Catalogue files | **32** |
| `.claude/` config | **13** | | Templates | **3** |
| Orchestration | **1** | | Custom GPT | **1** |
| | | | **Total vendored** | **3,864** |
| | | | **Blackhearts adapters** | **399** |

</div>

**53 of 58 upstream top-level areas vendored; 5 excluded, each with a recorded
reason.** See [`skills/VENDOR.md`](skills/VENDOR.md) §2.0.1.

> **On the two skill counts.** **388** is the number of vendored `SKILL.md`
> *directories* on disk. **374** is the number of *configured entries* in
> `skills/openclaw.example.json5` — 373 distinct skill names plus the
> `blackheart-conformance` layer. They differ because of upstream path
> duplication, not because anything is missing: 14 names are defined at two
> paths each (28 directories), so 373 names cover 387 loadable directories, and
> one nested test fixture brings the on-disk total to 388.

---

## Architecture

```
                    untrusted upstream
                            │
                            ▼
                 ┌──────────────────────┐
                 │   PIN + VERIFY       │   3,864 files vs commit SHA
                 │   no drift allowed   │   byte-for-byte, in CI
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │   ADAPTER LAYER      │   399 reviewed contracts
                 │   one per skill      │   declared capability
                 │   and collection     │   declared prohibitions
                 └──────────┬───────────┘
                            ▼
        ┌────────────────────────────────────────────┐
        │              CONFORMANCE                   │  wins every conflict
        │   evidence vocabulary · status ladder      │
        │   no-scope no-test · no claim without proof │
        └──────────┬─────────────────────────────────┘
                   ▼
        ┌────────────────────────────────────────────┐
        │             SECURITY GATE                  │  declarative
        │  requireAuthorizedTarget · requireRecord   │  not advisory
        │  requireAdapter · denyTargetsWithoutScope  │
        └──────────┬─────────────────────────────────┘
                   ▼
                   agent
```

### The conformance layer wins

Where a vendored persona, command, or skill conflicts with
[`skills/conformance/SKILL.md`](skills/conformance/SKILL.md), **conformance
wins.** No vendored content can widen scope, disable the gate, or authorise a
target. This is the single most important design decision in the framework.

---

## Known accepted risk

**Dependabot reports 82 open vulnerability alerts on this repository. All 82
are in one file, and none is a defect in Blackhearts.**

They all resolve to
`skills/third-party/claude-skills/engineering/skills/dependency-auditor/test-project/package.json`
— a `sample-web-app` fixture that exists so the vendored `dependency-auditor`
skill has something to scan. Its deliberately outdated `axios`, `nodemailer`,
`multer`, `mongoose`, `lodash` and `jsonwebtoken` pins *are* the test data. Two
critical, 36 high, 37 moderate, 7 low.

Patching it would be wrong twice over: it would break the byte-identical mirror
that `validate.py` enforces, and it would delete the corpus the skill exists to
analyse. Nothing installs, builds, or executes it; no lockfile is committed and
no build step could pull it in.

The fixture is registered in
[`.github/known-vulnerable-fixtures.json`](.github/known-vulnerable-fixtures.json)
with written reasons, and **audit group 20 enforces that registration** — it
fails if the registry goes missing, if an entry stops being vendored, if an
entry loses its reason, or if a Blackhearts-authored dependency manifest ever
appears.

---

## Quick start

```bash
git clone https://github.com/devara1983ntr/blackheart-security-framework.git
cd blackheart-security-framework

python3 -m pip install json5

# prove the mirror is intact — 8/8 checks
python3 .github/scripts/validate.py

# prove nothing is missing and the docs tell the truth — 20/20 groups
python3 .github/scripts/gap_audit.py

# report upstream drift — read-only, never mutates
python3 .github/scripts/sync_upstream.py

# site gates: static, then a real browser
python3 site/check_site.py        # 118 checks
python3 site/audit_seo.py         # links, metadata, payload budget
python3 -m pip install playwright && python3 -m playwright install chromium
python3 site/check_contrast.py    # WCAG AA, measured in both themes
python3 site/test_interactions.py # 81 behavioural checks
```

`json5` is the only required dependency; `playwright` is needed for the two
browser-based gates only. The file index is generated, not hand-maintained:

```bash
python3 .github/scripts/gen_index.py --check   # what CI runs
python3 .github/scripts/gen_index.py --write   # regenerate
```

[`RELEASE-CHECKLIST.md`](RELEASE-CHECKLIST.md) holds the full pre-release
checklist with the command for every gate.

## Activate an agent

Hand the agent the prompt in
[`docs/agent/AGENT-BOOTSTRAP.md`](docs/agent/AGENT-BOOTSTRAP.md). It enumerates
the 55-file authored instruction set from `FILE-INDEX.txt`, reconciles it under
a stated precedence order, and returns a **countable** readiness confirmation
instead of an unfalsifiable one.

It activates nothing: the agent will not ask for a target and will not begin
work until you supply one and say so explicitly.

<details>
<summary><b>Starting an authorised engagement</b></summary>

```yaml
engagement:
  id: ENG-2026-001
  target: https://example.com
  authorizedBy: <named owner>
  window: 2026-09-29T00:00Z/2026-10-06T00:00Z
```

Without a target, a window, and a named authoriser, **the gate refuses to run.**
That refusal is the feature.

</details>

---

## The gate

`skills/openclaw.example.json5` — 374 configured entries, generated and
CI-verified.

```json5
security: {
  requireAuthorizedTarget: true,
  requireEngagementRecord: true,
  requireAdapter: true,
  denyTargetsWithoutScope: true,
  defaultEvidenceStatus: 'UNVERIFIED',
}
```

Declarative flags, not executable policy — a configuration that can run code is
not a control, it is a vulnerability.

---

## Verification

Six workflows, nine verification scripts.

`validate.py` — 8 checks, on every push and pull request:

| Check | What it proves |
|---|---|
| `adapters` | every skill and collection has a reviewed adapter |
| `integrity` | 3,864 files byte-identical to the pinned SHA, plus 399 adapters |
| `catalog` | 32 catalogue files unmodified |
| `links` | 5,279 local links; **0 broken in authored docs** |
| `index` | 4,403 entries; 0 unindexed, 0 dangling |
| `secrets` | no credential material outside a 7-entry allowlist (15 allowlisted placeholders suppressed) |
| `config` | JSON5 parses; 374/374 configured entries declared |
| `history` | no commit subject contains an unexpanded `$(name)` token |

`gap_audit.py` — 20 groups. It answers what `validate.py` cannot: is the right
set of things present and wired, and do the documentation's own numbers hold?
It reads no upstream and no network. Group 16 checks the figures published here
against the repository, which is what makes a documentation claim falsifiable
rather than decorative.

Three further workflows keep the repository honest over time, and none of them
can merge anything:

| Workflow | What it does |
|---|---|
| [`upstream-watch.yml`](.github/workflows/upstream-watch.yml) | Weekly, read-only. Resolves the head of **both** pinned sources, compares it with the recorded pin, classifies what moved, and opens one tracking issue. `contents: read` — it has no path to a commit. |
| [`site-verify.yml`](.github/workflows/site-verify.yml) | Runs the two browser gates in CI: WCAG AA across both themes, and 81 behavioural checks in Chromium. |
| [`authored-scan.yml`](.github/workflows/authored-scan.yml) | Parses every authored configuration file and every workflow, checks the capability audit's claims still hold, and runs static analysis over the authored Python. |

**Detection is automatic. Preparation is automatic. Admission is not.** No
workflow in this repository merges third-party content, and `upstream-sync.yml`
is configured never to merge its own pull request.

Four further gates cover the published site. `check_site.py` and `audit_seo.py`
run in `pages.yml` on every change; `check_contrast.py` and
`test_interactions.py` measure the site in a real browser and run in
`site-verify.yml`. **All six workflows are in CI. Nothing is local-only.**

| Gate | What it proves | Result |
|---|---|---|
| [`check_site.py`](site/check_site.py) | 118 static checks — canonical, `og:url`, sitemap membership, cross-linking, exactly one `h1`, and no class used in markup but undefined in the stylesheet | 118 passed |
| [`audit_seo.py`](site/audit_seo.py) | internal links resolve, anchors match real `id`s, canonical and `og:url` agree with the page address, titles unique and within SERP limits, payload under budget | clean |
| [`check_contrast.py`](site/check_contrast.py) | WCAG AA in a real browser across both themes, including gradient-clipped text measured through its stops | clean |
| [`test_interactions.py`](site/test_interactions.py) | 81 behavioural checks in Chromium: overflow at four viewports, keyboard tab order, the tabs pattern, the error banner, and graceful degradation when a script throws | 81 passed |

Generated files cannot lie by accident. `gen_manifest.py` and `gen_index.py`
turn the working tree into published numbers, so both refuse to run while the
mirror or catalogue differs from `HEAD`, and name the paths to restore.

Every gate here was tamper-tested: each was made to fail deliberately — a
vendored script altered, the gate switched off, a documented number falsified —
and each was confirmed to detect it. A gate that has never been observed
failing is an assumption, not a control.

### Evidence rules

- **A finding is a hypothesis, never a conclusion.** It becomes a finding only
  after independent demonstration.
- **A clean result is a coverage gap, not a clearance.**
- **Negative results and rejected hypotheses are preserved.** They are evidence.
- **Every claim traces to a log ID, or it is not a claim.**

The payoff: the most security-relevant vendored tool — a jailbreak detector —
still has three real defects after passing a full static audit. A framework
that only runs scanners would have shipped those silently. See
[`skills/VENDOR.md`](skills/VENDOR.md) §3.1.1.

### Repository settings

`main` is the publication target for GitHub Pages, so it requires green checks
and refuses force-pushes and deletions. Those are repository settings, not
files, so a commit cannot apply them;
[`repo_settings.py`](.github/scripts/repo_settings.py) sets the description,
topics, and branch protection in one idempotent pass:

```bash
GH_TOKEN=<token> python3 .github/scripts/repo_settings.py --dry-run   # show the plan
GH_TOKEN=<token> python3 .github/scripts/repo_settings.py             # apply
```

The token is read from the environment and never written to a file, a config,
or the remote URL. `upstream-sync.yml` runs daily and **opens a pull request —
it never auto-merges.** Detection is automated; judgement is not.

### Publication

The published site is static HTML deployed from `main` by GitHub Actions, with
canonical metadata, `robots.txt`, a sitemap, and JSON-LD `SoftwareSourceCode`.
Search Console ownership verification and sitemap submission are site-owner
operations and are not configured here; the site is crawlable but unclaimed.

---

## Documentation

| | |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | layers, data flow, invariants, trade-offs |
| [`AGENT.md`](AGENT.md) | how an agent is expected to behave |
| [`docs/agent/AGENT-BOOTSTRAP.md`](docs/agent/AGENT-BOOTSTRAP.md) | **activation prompt** — loads the framework and verifies the load |
| [`SECURITY.md`](SECURITY.md) | threat model, disclosure, secret handling |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | how to contribute safely |
| [`CHANGELOG.md`](CHANGELOG.md) | version history |
| [`ROADMAP.md`](ROADMAP.md) | what comes next |
| [`FILE-INDEX.txt`](FILE-INDEX.txt) | all 4,403 files, one per line |
| [`skills/VENDOR.md`](skills/VENDOR.md) | provenance, exclusions, upstream defects |
| [`skills/README.md`](skills/README.md) | the catalogue and its rules |
| [`skills/conformance/SKILL.md`](skills/conformance/SKILL.md) | the rules that win |
| [`docs/`](docs) · [`examples/`](examples) · [`templates/`](templates) | reference material |

---

## Responsible use

Blackhearts is for **authorised** security work. It is not for attacking systems
you do not own or have written permission to test.

- No target is engaged without explicit, recorded authorisation.
- No credential is ever requested, stored, or handled by this framework.
- No production data is modified. Write capability is answered by static
  analysis, not by writing.
- Findings default to `UNVERIFIED`. Claims require evidence.

Violating these constraints is both a security failure and a legal one.

---

## Provenance

Vendored content is **never modified.** Not one byte. If an upstream tool has a
defect, the defect is recorded and the code left alone — a mirror that patches
its source stops being a mirror, and stops being evidence.

| Source | Pin | Licence |
|---|---|---|
| [`alirezarezvani/claude-skills`](https://github.com/alirezarezvani/claude-skills) | `19392f7a` | MIT — [`claude-skills-LICENSE`](skills/licenses/claude-skills-LICENSE) |
| [`VoltAgent/awesome-openclaw-skills`](https://github.com/VoltAgent/awesome-openclaw-skills) | `f274daa` | MIT — [`awesome-openclaw-skills-LICENSE`](skills/licenses/awesome-openclaw-skills-LICENSE) |

Blackhearts-authored content is MIT, © 2026 Devara.

---

<div align="center">

**Blackhearts** — *verify before you enable.*

</div>
