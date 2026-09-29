<!--
Every pull request is a claim that the repository is still correct. Answer
before you open it; the maintainer will ask otherwise.
-->

## What this changes

<!-- One paragraph. If it changes what an agent may do, say so in the first sentence. -->

## Checklist

- [ ] `python3 .github/scripts/validate.py` — 7/7
- [ ] `python3 .github/scripts/gap_audit.py` — 17/17
- [ ] `python3 .github/scripts/gen_index.py --check` — in sync
- [ ] `python3 .github/scripts/gen_link_registry.py --check` — in sync
- [ ] `python3 .github/scripts/sync_upstream.py` — no drift
- [ ] New or changed files are in `FILE-INDEX.txt`
- [ ] New or changed files are in `CHANGELOG.md` under Unreleased

## Vendored content

- [ ] **I have not modified any file under `skills/third-party/`.**

If this is false, stop and explain why in the PR body. The mirror is
byte-identical to upstream `19392f7` on purpose: a mirror that edits its
source stops being evidence. If upstream is wrong, record the defect — in
the relevant `_BLACKHEART-ADAPTER.md` or in
`.github/upstream-link-defects.json` — and leave the bytes alone.

## Evidence

- [ ] Every factual claim in the diff traces to something I actually ran.
- [ ] Numeric claims match the current repository, not a previous state.
- [ ] I have not written a number I did not measure.

## Scope

- [ ] This change does not widen agent capability, relax a gate, or lower an
      evidence standard. If it does, I have said so explicitly above and I am
      prepared to argue it on the merits.
