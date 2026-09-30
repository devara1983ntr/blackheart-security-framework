# Third-Party Content

**Project:** BLACKHEART Security Framework · **Author:** Roshan
**Last updated:** 2026-09-30

---

## What third-party content is in this repository

This repository contains two kinds of content, and the difference matters:

| | Blackhearts-authored | Vendored third-party |
|---|---|---|
| What it is | The instruction set, the workbench, the documentation, the tests, the site | A mirror of two upstream repositories |
| Licence | MIT, © Roshan | Each upstream's own licence |
| Who maintains it | This project | Its upstream authors |
| Where it lives | `AGENT.md`, `docs/`, `templates/`, `workbench/`, `site/`, `.github/` | `skills/third-party/`, `skills/catalog/`, `skills/licenses/` |

The authoritative record of the second category is
[`skills/VENDOR.md`](skills/VENDOR.md). It names every source, licence, pinned
commit and retrieval date. **If a fact about third-party content is not recorded
there, this project does not claim it.**

## The vendored content

| Source | Repository | Licence | Pin |
|---|---|---|---|
| Skill catalogue | `alirezarezvani/claude-skills` | MIT © 2025 Alireza Rezvani | `19392f7a08264ed00486a251f5b2098321771f94` |
| Discovery index | `VoltAgent/awesome-openclaw-skills` | MIT © 2026 VoltAgent | `f274daa9d24c0803c8f94a4630aa4922ca4b950e` |

Licence texts are preserved verbatim in `skills/licenses/`.

## How this repository treats it

1. **Byte-identical, and checked.** Vendored files are pinned and verified
   byte-for-byte on every push. A gate fails the build if a vendored file has
   changed, because a mirror that drifts is no longer a record of what upstream
   published.
2. **Not modified.** Upstream content is not edited — not to fix a defect, not to
   update a link, not to reformat it. Its defects are recorded instead, with
   reasons, in `.github/upstream-link-defects.json` and in `skills/VENDOR.md` §4.
3. **Not redistributed under a different licence.** The project's MIT licence
   covers Blackhearts-authored content. Vendored content stays under its own
   licence and its own copyright notice, and those notices are not stripped.
4. **Not trusted.** Every vendored skill carries an adapter describing what it
   does and what it must not be used for, and the conformance layer applies this
   framework's rules before and after any vendored skill runs. Vendoring is not
   endorsement.
5. **Not executed by the gates.** The validation gates read vendored files as
   text. Nothing in this repository runs, imports or installs vendored content.
6. **Not updated automatically.** A scheduled job detects upstream movement and
   reports it. Preparation of an update is automated; **admission is not.** A
   human reads the change and decides. See `skills/VENDOR.md` §8.

## What this repository does not claim about it

- **Ownership.** None of the vendored content is the author's work. Copyright
  remains with the upstream authors.
- **Accuracy.** A vendored skill's advice, code or claims are the upstream
  author's, not this project's. The audit records what was found, including
  defects; it does not certify correctness.
- **Safety.** Vendoring a skill is not a statement that its code is safe. Its
  contents are untrusted input, which is why the conformance layer exists.
- **Licence compliance beyond what is recorded.** This project mirrors content it
  believes to be MIT-licensed, records the licence texts verbatim, and preserves
  attribution. If you believe content here is misattributed or used outside its
  licence, [`SECURITY.md`](SECURITY.md) explains how to raise it, and it will be
  corrected or removed.

## The discovery index

One of the two sources (`awesome-openclaw-skills`) is a curated list of external
URLs pointing at skills hosted elsewhere. This repository vendors that index — the
list — and **nothing else from it**:

- no link in it is followed automatically;
- nothing hosted at any of those URLs is downloaded, executed or installed by
  this repository;
- listing a skill in the index is not a recommendation by this project.

## If you use vendored content

You are responsible for checking its licence and its behaviour before you rely on
it. The mirror exists so that a reviewer can see exactly what was pulled, from
where, at which commit — not so that anyone can skip that review.

## Adding more

New third-party content is not added automatically and is not added merely
because it exists upstream. It requires a human decision, an adapter, a licence
record and a pin. See [`CONTRIBUTING.md`](CONTRIBUTING.md) and
`skills/VENDOR.md` §8.
