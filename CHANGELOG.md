# Changelog

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This repository is documentation-first, but it also carries executable content: a
complete mirror of a third-party catalogue (3,864 files), a validation gate, and
six automation workflows. Versions therefore track both documentation maturity
and the state of the executable layer.

## [Unreleased]

### Added
- **`upstream-watch.yml` and `watch_upstream.py` — the second pinned source was
  unwatched.** `upstream-sync.yml` covers the skill mirror. The catalogue
  (`VoltAgent/awesome-openclaw-skills`) had its commit recorded in
  `.github/UPSTREAM-MANIFEST.json` and nothing that ever checked it: a pin that
  is written down and never verified is a claim, not a control. The watch runs
  weekly and on demand, resolves the head of **both** sources, compares it with
  the recorded pin, and classifies what moved — added, removed, renamed,
  modified, type-changed, symlink, generated, licence/provenance,
  workflow/config, and security-sensitive, the last deliberately overlapping the
  others so a changed workflow is reported as both configuration and risk. It
  needs no dependencies, uses the standard library and `git` only, fetches no
  blob content, and writes nothing: it runs with `contents: read` and produces a
  report. A pin that upstream has rewritten or dropped is reported as its own
  condition, because a diff cannot describe it — and a source it *cannot read*
  fails the run rather than passing quietly, because a watch that cannot see
  upstream has established nothing.
- **`site-verify.yml` — the only gates that CI never ran.** `check_contrast.py`
  and `test_interactions.py` measure the published site in a real browser: WCAG
  AA across both themes including gradient-clipped text, and 81 behavioural
  checks covering overflow at four viewports, keyboard tab order, the tabs
  pattern, the error banner, and graceful degradation when a script throws. They
  were local-only, on the grounds that they need a browser — and a gate that
  runs when someone remembers is a gate that runs when it is least needed. The
  failures they catch are exactly the ones static analysis cannot see.
- **`authored-scan.yml`, `check_authored_config.py` and
  `verify_capability_audit.py` — the control was never itself controlled.**
  GitHub does not run a workflow whose YAML it cannot parse, and does not fail a
  build over it: the error appears in the Actions tab and the repository keeps
  looking healthy. A typo could therefore disable the gate protecting everything
  else, and every gate here lives inside the thing that would break. The scan
  parses every authored YAML/JSON/JSON5 file and checks the shape each workflow
  needs; it re-resolves every path cited by the capability audit and re-derives
  every count that document publishes; and it runs static analysis over the
  ~3,800 lines of first-party Python, failing on anything at MEDIUM or above.
- **`docs/CAPABILITY-AUDIT.md`.** What the framework can and cannot do, checked
  against the tree rather than against its own claims. Three families are
  classified — 27 security capabilities, 15 engineering capabilities and 18
  framework capabilities — and every ALREADY COVERED row cites the file that
  implements it. Every row names the file
  that implements the capability, so a reader can check the row instead of
  trusting it; capabilities that are **not** held are stated as plainly as those
  that are. Four real gaps were found and closed (the three above, plus the
  unscanned authored code); the rest were already covered, partial by design, or
  deliberately out of scope, with the reason recorded for each.

### Fixed
- **Four MEDIUM static-analysis findings in the authored tooling, none
  previously known** — two `urllib.request.urlopen` calls whose scheme is a
  constant chosen by the script, one `xml.dom.minidom.parseString` on this
  repository's own `sitemap.xml`, and a literal `/tmp` scratch path in a local
  screenshot helper. Each is suppressed **at its line** with the reason in a
  comment, never by disabling a check class globally, and the gate was
  negative-tested by injecting a real finding and watching it fail.
- **Published counts that the new workflows made stale**, each re-derived rather
  than adjusted to match: workflows `3` → `6`; verification scripts `6` → `9`;
  `FILE-INDEX.txt` `4,403` → `4,410` entries; local links `5,271` → `5,279`; the
  authored instruction set `54` → `55` files. `gap_audit.py` group 18's own
  detail line reported three workflows and now reports six.
- **The index total was published in two places and asserted in none.**
  `README.md` said 4,403 entries twice while `FILE-INDEX.txt` held 4,410, and
  `validate.py` computed the real total without ever comparing it to the copies
  it publishes. Both rows are corrected, and the figure is now asserted where it
  is counted, negative-tested by making README stale again.
- **The link check caught its own author.** The count assertion added in the
  previous change failed the build the moment this change added eight links,
  which is the entire point of asserting a published figure where it is counted
  instead of trusting a reader to notice.

### Fixed
- **Five published figures were wrong, and the audit that found them was the
  one commissioned to check whether anything was missing.** The cross-repository
  audit measured the catalogue at 5,267 unique URLs while five documents
  published 5,270 and 5,272; 32 catalogue files are byte-identical to upstream
  while two documents said 33; `README.md` published 5,272 local links while
  `validate.py` counted 5,271; `RELEASE-CHECKLIST.md` published 4,396 index
  entries while `FILE-INDEX.txt` declares 4,403; and `skills/VENDOR.md` §8
  advertised "seven checks" and "16 groups" long after there were eight and
  twenty. Every corrected number was re-derived from the tree rather than
  adjusted to match the document.
- **`skills/VENDOR.md` §2.0.1 claimed upstream's `.github/` was "vendored
  nowhere". It is vendored — all 23 files, byte-identical and manifest-tracked
  — and §2.0 now records the area.** The same table described the four symlink
  farms as 1,574 entries all in mode `120000`; each farm also holds one
  generated `skills-index.json`, so those farms hold 1,578 entries and the
  four derived indexes now have their own row. `.github/` keeps no collection
  adapter, and the reason is written down rather than implied. Recorded, not
  patched.
- **One dangling symlink, found by resolving all 1,574 by hand.**
  `.codex/skills/dsh-deepread` points at `research/dsh-deepread`, which does not
  exist upstream — the directory is `research/deepread`. 1,573 resolve; this one
  cannot, and it is now in §4 instead of being implied away.
- **Two new assertions make the figures falsifiable instead of decorative.**
  `validate.py` now fails when the link or allowlist figures published in
  `README.md`, the site, or `RELEASE-CHECKLIST.md` disagree with the values it
  counts, and audit group 16 now recomputes the catalogue URL totals, the
  byte-identical file count, and the index total from the tree. Both were
  negative-tested by falsifying a published number and confirming the gate
  failed.
- **`skills/VENDOR.md` §9 records the cross-repository capability review.**
  Seven items reviewed against both pinned sources; none integrated, each with
  the measured evidence and the reason. The largest is upstream's
  execute-every-script smoke gate, declined because it would run 696 unreviewed
  third-party scripts inside CI, including the teaching artefact whose adapter
  says never execute it.
- **Two copy buttons shipped with no class and rendered as raw default browser
  buttons.** `case-study.html` and `disclosure.html` each had
  `<button type="button" data-copy>` where the design system expects
  `class="cb-copy"`. It looked like a deliberate part of the page. Static
  checks, the unstyled-class scan and the link audit all passed while it was
  broken; only reading the computed style of the live page exposed it. Added a
  check to `check_site.py` that fails on any class used in markup but not
  defined in `style.css`, and on any `<button>` with no class at all. The
  guard was negative-tested against both shapes of the original defect.
- **`apple-touch-icon` pointed at an SVG.** iOS does not render SVG for the
  home-screen icon — it ignores the link and falls back to a screenshot of the
  page. Generated a real 180x180 PNG from `gen_og.py` and pointed every page at
  it.
- **Four WCAG AA contrast failures in the light theme**, found by measuring
  rather than by reading the palette: the two status badges on their own tinted
  backgrounds (4.41:1 and 4.34:1), the skip link (3.54:1), and the primary
  button, which hardcoded a near-black label colour that works on the bright
  dark-theme accent and fails on the deep light-theme one. Darkened
  `--warn`/`--good`, reduced the badge tint from 15% to 10%, inverted the skip
  link against the surface, and added an `--on-accent` token.
- **The hero gradient word was invisible without `background-clip: text`.**
  `color: transparent` was declared unconditionally, so any engine without
  the property rendered nothing. The accent colour is now the declared value
  and the gradient is applied inside `@supports`.

### Fixed
- **`RELEASE-CHECKLIST.md` still claimed repository settings "need a token"
  after they had been applied and verified.** A stale "not done" line is
  worse than no line: it is a claim about the project that the project had
  already disproved. Branch protection, the description, 20 topics, the
  `jules-*` deletion, the green workflows and the live-site checks are all
  now marked done, with the commit and run they were verified against.
- **`repo_settings.py` applied cleanly only on the fourth attempt, and the
  first three failures were all in the script rather than the API.** Worth
  recording, because each looked like a GitHub restriction and none was:
  - the description `PATCH` built a bare `https://api.github.com` URL,
    because an empty path is not a path; both `""` and `"/"` now resolve to
    the repository URL, since the trailing-slash form also 404s on `PATCH`;
  - 25 topics were sent and GitHub accepts at most 20, so the whole call
    failed with 422 — now 20, chosen to be the 20 a reader would search for;
  - the branch-protection body was built by dropping `nil` values, and
    GitHub requires `required_pull_request_reviews` and `restrictions` to be
    *present* rather than defaulted. The assertion that would have caught
    this is now in the script.

  The stale-branch deletion succeeded first time and only after re-verifying
  `ahead_by == 0` at the moment of deletion.

### Added
- **HTML is now parsed, not pattern-matched.** `check_site.py` grew three
  checks that no regex can do: whether every document nests correctly, whether
  each declares `lang`, `charset` and a viewport, and whether every indexable
  page declares `hreflang`. The audit that motivated them found the markup
  already well-formed on all six pages, and one real gap — no `hreflang`
  anywhere. This is a single-language site, so it now says so explicitly on all
  five indexable pages with `hreflang="en"` and `hreflang="x-default"`. Both
  new checks were negative-tested: an unclosed `<div>` and a removed
  `hreflang` each fail the build.

### Added
- **`.github/scripts/guard_clean.py` — generators can no longer record a damaged
  tree as fact.** `gen_manifest.py` and `gen_index.py` turn the working tree into
  published claims. Neither warned: run either over an incomplete tree and it
  faithfully describes the damage, and the damage becomes the committed truth.

  That is not hypothetical. A working tree was missing two vendored files, a
  manifest was regenerated over it, and the counts dropped from 3,864 to 3,863
  with a single diff line as the only evidence. Both generators now refuse
  while the mirror or catalogue differs from `HEAD`, and name the offending
  paths and the command to restore them. `--allow-dirty` exists for generating
  an index that must include a file being added right now.

  `gen_manifest.py` also ended with a bare `main()` call, so its return value
  was discarded: the guard could refuse correctly and the script would still
  exit 0, reporting success to CI having written nothing. It now ends with
  `sys.exit(main())`.

  Tested in both directions on a deliberately deleted vendored file: blocked
  with exit 1 and the manifest left byte-identical, then allowed with exit 0
  once restored. Regenerating on a clean tree is a byte-identical no-op,
  which is also the proof that the committed manifest is not stale.

- **`validate.py` `history` check (now 8 checks).** Four Dependabot squash
  subjects had shipped as the literal `ci: bump $(title)`; they were corrected
  in an earlier history-only rewrite, and this check keeps them corrected. It
  reads every ref rather than only the default branch, so a leftover backup ref
  carrying the old subjects fails the build as well.

  The first version of the guard was `\$\{?\w+\}?`, which **cannot match
  `$(title)`** — after `$` comes `(`, not a word character — so it passed on
  exactly the history it was written to catch. A negative test pointing a ref
  back at the pre-rewrite state caught it; the corrected pattern matches both
  `$(name)` and `${name}` and now fails on all four commits with a non-zero
  exit.
- **`.github/CODEOWNERS`** was added; the local `refs/original/` backup ref left
  behind by the history rewrite was removed, since it was the only thing
  keeping the pre-rewrite commits reachable.
- **`.github/scripts/repo_settings.py`** — applies the repository settings a
  commit cannot: the page description, 25 topics, branch protection on `main`
  (require green checks, refuse force-push and deletion, resolve conversations),
  and deletion of a stale branch. Idempotent, `--dry-run` supported, token read
  from the environment and never written anywhere. The stale-branch deletion
  re-compares the branch tip against `main` immediately beforehand and refuses
  if the branch holds any commit `main` does not; both outcomes were tested
  against a mocked API.
- **`.github/CODEOWNERS`** — names the files where a plausible change could
  quietly weaken the guarantee: the published site, the gates themselves, and
  the activation contract. The vendored mirror deliberately has no owner,
  because a hand edit there is wrong by construction and `validate.py` fails
  the push regardless of who approved it.
- **The repository page itself** — a Pages status badge, the published site's
  social card as a hero image, a navigation bar into the sections a visitor
  most likely wants, and a rewritten CI section listing all six gates with what
  each one actually proves and whether it runs in CI or locally.
- **`RELEASE-CHECKLIST.md`** — a full pre-release checklist across
  functionality, UI/UX, responsive, accessibility, SEO, performance, security,
  testing, links, documentation, configuration, hygiene and deployment, with
  the command for every gate and an explicit list of what is *not* fixed.
- **`site/audit_seo.py`** — a new gate, also wired into the `pages` workflow.
  Resolves every internal link and anchor against the filesystem, checks that
  canonical and `og:url` agree with each page's own address, that titles and
  descriptions are unique and within SERP truncation limits, that the sitemap
  and the shipped pages describe the same set, and that a visitor's payload
  stays under 150 KB. Running it found four meta descriptions between 176 and
  263 characters, all of which Google truncates mid-sentence; all rewritten.
- **`site/check_contrast.py`** — measures WCAG AA contrast in a real browser
  across both themes and all six pages. Two measurement bugs were fixed before
  its output was trusted: `color-mix(in oklab, ...)` computes to a syntax
  canvas `fillStyle` silently rejects and leaves the *previous* colour in
  place, which made every element under the sticky header measure as pure
  black; and translucent ancestor layers were being flattened by taking the
  nearest opaque one rather than composited. The instrument self-tests against
  colour pairs with known-correct ratios and reports any syntax it cannot
  resolve rather than guessing. Gradient-clipped text is measured through its
  gradient stops instead of its (transparent) colour.
- **Interaction states that were missing rather than wrong.** `:focus-visible`
  on every control, `:active` pressed states, cross-page transitions via the
  View Transitions API, a scroll progress indicator, and a back-to-top control.
- **An error state.** The site fetches nothing, so the only runtime failures
  are a script error or a lost stylesheet — both of which previously left a
  blank panel with no explanation. There is now a dismissible banner saying
  what failed and that the content below is complete, announced via
  `role="status"`. Every enhancement is wrapped so a throw degrades to a
  readable page instead of a silent one.


### Added
- **Four content pages, turning a one-URL site into five.** The sitemap listed a
  single URL, which is thin indexable surface for a project whose whole argument
  is that unread content is where risk lives. Added, in the same design system:
  - `site/architecture.html` — the five layers in depth, the precedence ladder,
    and why each design choice was made.
  - `site/evidence.html` — the mandatory evidence vocabulary and the status
    ladder, including why there is deliberately no "confirmed safe" rung.
  - `site/case-study.html` — F-01, F-02 and F-03 with evidence and consequence.
  - `site/disclosure.html` — the 82-alert triage, as a public page rather than
    a README table, plus the limits of what the assurance is worth.

  `sitemap.xml` now lists all five. Every page carries its own canonical URL,
  description, Open Graph and Twitter metadata, and is cross-linked from the
  home page and from every other page's footer, so a crawler can reach any of
  them from any other.
- `site/check_site.py` extended from 43 to **114 checks**. It now holds every
  page to the same metadata and asset rules as the home page, and fails if a
  page drops out of the sitemap, if a sitemap entry points at a file that does
  not exist, or if two pages stop linking to each other.
- `site/test_interactions.py` extended from 35 to **68 checks**, including a
  **horizontal-overflow assertion on every page at 320, 390, 768 and 1440px**,
  and a mobile-menu check on all five pages.

### Fixed
- **A CSS class-name collision shipped a broken mobile layout.** The row
  component introduced for the evidence page was called `.rung`, which was
  already a small uppercase pill badge used by the precedence stack. The badge's
  `white-space: nowrap` won, forcing those rows to 1,295px wide inside a 390px
  viewport. The static checks could not see it — it only showed up when the page
  was rendered. Renamed to `.rung-item`, and the overflow assertion above now
  fails the suite if it recurs.
- **The scroll-spy threw on every subpage.** It resolved nav hrefs with
  `querySelector`, which throws on a relative path like `./`. It was written when
  every nav link was a same-page fragment. Now resolved with `getElementById`,
  and non-fragment links are ignored.
- **A 592px `<code>` element and eight `minmax()` grid floors** could exceed a
  320px viewport. Grid items now carry `min-width: 0`, every `minmax()` floor is
  `minmax(min(<n>rem, 100%), 1fr)`, the coverage tables scroll inside their
  panel, and the decorative glows are clamped to the viewport.
- `body` used `overflow-x: hidden`, which papered over all of the above by
  hiding it. Changed to `overflow-x: clip`, which prevents the stray scrollbar
  without making body a scroll container — and without the sticky header
  breaking. The underlying overflows are now actually fixed rather than masked.
- The 320px header no longer pushes the page sideways: the brand and buttons
  compress instead.

### Fixed
- **Five published figures had drifted from the repository they describe, and
  the no-JavaScript hero counters showed zero.** These were found by re-running
  every gate and re-measuring each number rather than trusting the previous
  audit, and each was correct when it was written:
  - The case-study hit counts for `AGENT.md` (`11` → `24`) and `README.md`
    (`9` → `8`). `AGENT.md` gained the three-defect table that quotes the
    signature itself, which alone accounts for 5 of its hits; the README was
    redesigned after its count was taken.
  - The site's CI and audit figures (`7` → `8` checks, `19` → `20` groups) in
    the prose, in the animated counters and in the quickstart comments.
    `AGENT.md`'s header now states validator `8/8` and end-to-end audit `20/20`
    for the same reason, and `gap_audit.py` group 16 asserts the corrected
    validator token instead of the stale one.
  - The link count (`5,262` → `5,271`) on the site and in
    `RELEASE-CHECKLIST.md`.
  - The PR template's own checklist, which asked for `7/7` and `17/17`.
- **The F-03 case-study claim now states the scope it requires.** Score `0.0`
  with zero findings reproduces with `--scope jailbreak`; unscoped, the same
  phrase scores `0.1667` through a different category. The underlying finding —
  the canonical instruction-override phrase is not covered — is unchanged and
  was re-measured.
- **The hero counters carried `0` in the markup.** With JavaScript disabled the
  landing page therefore published `0 files verified` / `0 CI checks` as this
  repository's measurements. The markup now carries the measured values
  (`3,864` · `399` · `8` · `20`) and JavaScript still animates to them; under
  `prefers-reduced-motion` they are set immediately, as before.
- **The case study now describes the defects that are actually documented.**
  Its F-02 and F-03 sections described a "confidence score that is never low"
  and "instructions that are logged as data, and vice versa". Neither matches
  the record: the scanner emits no confidence value (the word appears once, in
  a risk-description string) and it has no instruction/untrusted-content
  channel logic at all — `scan_prompts()` regex-matches input and divides
  matches by signatures in scope. The home page and the adapter already
  documented the real pair: the constant standard-input path (`0.8333`, 7
  findings, an excerpt absent from the input) and the uncovered
  instruction-override phrasing (`0.0` with `--scope jailbreak`, `0.1667`
  unscoped). The page now states those, and the Method summary no longer
  repeats the unsupported claims.

### Changed
- The four commits whose messages read `ci: bump $(title)` were rewritten to
  their real messages via a history rewrite, pushed with `--force-with-lease`.
  The resulting tree is **byte-identical** to what was published before
  (`9f7545b`), so no file content changed — only commit messages. A backup of
  the original `.git` was kept during the operation.

## [2.4.0] — 2026-09-29

## [2.4.0] — 2026-09-29

### Added
- **The site is live.** `https://devara1983ntr.github.io/blackheart-security-framework/`
  now serves the published rendering, deployed from `main` by GitHub Actions.
  This is the first release in which the published URL in the README is true.
- **A rebuilt landing page** (`site/index.html`, `site/style.css`,
  `site/app.js`) — hero, the five-layer model, coverage, the evidence rules,
  the F-01/F-02/F-03 case study, verification and canaries, quickstart, and a
  responsible-use section. Dark and light themes, responsive from 390px,
  print styles, and a `prefers-reduced-motion` path. No third-party runtime:
  no CDN, no webfont request, no bundler.
- **A real social preview.** `site/og-image.png` is a 1200×630 card generated
  by `site/gen_og.py`. Platforms that do not render SVG show an empty box for
  an SVG `og:image`, so the PNG is what the metadata points at.
  `site/og-image.svg` is kept as the vector original and is no longer
  referenced.
- **`site/manifest.webmanifest`**, complete Open Graph and Twitter card
  metadata, JSON-LD, canonical URL, and a rewritten `noindex` 404.
- **A mobile section menu.** The inline nav was hidden below 56rem with only a
  footer nav behind it, so in-page navigation was simply absent on a phone.
- **Verification tooling, because the above is not trustworthy unverified:**
  - `site/check_site.py` — 43 static checks covering structure, metadata, asset
    resolution, self-containment, and that the layer count the page claims
    matches the layers it draws. Wired into `pages.yml`, so it gates deploys.
  - `site/test_interactions.py` — 35 checks driving a real browser: the
    disclosure menu, tab keyboard behaviour, scroll spy, counters, clipboard.
  - `site/shoot.py` — captures each section the way a reader sees it.
- **A documentation-site claim gate.** The Pages workflow now runs
  `site/check_site.py` before it will publish.

### Changed
- `FILE-INDEX.txt` regenerated to **4,391** entries (was 4,384).
- CI actions bumped by Dependabot, each verified to be a real published
  release and each confirmed green afterwards: `actions/checkout` 4 → 7,
  `actions/setup-python` 5 → 7, `actions/upload-pages-artifact` 3 → 5,
  `actions/deploy-pages` 4 → 5, `peter-evans/create-pull-request` 6 → 8.
- **Dependabot security alerts enabled, and the 82 alerts they surfaced triaged.**
  They were switched off on a repository whose entire subject is supply-chain
  risk. Re-enabled via the API.

  All **82 open alerts** (2 critical, 36 high, 37 moderate, 7 low) resolve to a
  single vendored file: the `sample-web-app` corpus belonging to the vendored
  `dependency-auditor` skill, whose entire purpose is to find vulnerable
  dependencies. Its stale `axios`, `nodemailer`, `multer`, `mongoose`, `lodash`
  and `jsonwebtoken` pins are the input it is demonstrated against. Patching it
  would break the byte-identical mirror *and* delete the corpus, so it is
  accepted, not fixed — the same "fix ours, account for theirs" rule already
  applied to the 111 registered dead links.

  Recorded in `.github/known-vulnerable-fixtures.json` with written reasons, and
  enforced by **audit group 20**, which fails if the registry is deleted, if a
  registered entry stops being vendored, if an entry loses its reason, or if a
  Blackhearts-authored dependency manifest ever appears. That last check is the
  load-bearing one: the acceptance argument rests on this repository declaring
  no dependencies of its own, so the audit asserts that premise rather than
  trusting it. All four failure modes were tested by deliberately breaking them.
- The README's publication and Search Console wording now states what is true:
  the site is live, and it is **crawlable but not claimed** in Search Console.

### Fixed
- The architecture diagram drew the agent as a numbered sixth layer while the
  heading said five and the canonical architecture docs describe five layers
  plus the agent. The agent is now drawn as an endpoint rather than `06`, and
  `site/check_site.py` fails the build if the two ever disagree again.
- Three `<button>` elements in the tab strip had no `type`, so they defaulted
  to `type="submit"`.

### Known issues
- **The four Dependabot squash-merge commits on `main` have malformed
  messages** — each reads `ci: bump $(title)`. The `commit_title` passed to the
  merge API used a shell-style placeholder that GitHub did not expand. The
  *content* of all four is correct and CI is green on the tip; only the
  messages are wrong. Correcting them requires rewriting published history on
  `main`, so it was not done unilaterally. The substantive change is recorded
  under **Changed** above. The cause was passing `commit_title: "ci: bump
  $(title)"` to the merge API, which GitHub does not expand. Merging
  `deploy-pages` without a `commit_title` produced the correct message,
  `ci: bump actions/deploy-pages from 4 to 5 (#7)`, which confirms the fix for
  any future bump.
- **Search Console ownership is not verified.** The `google-site-verification`
  token is issued by Google to a site owner and cannot be generated by this
  repository. It was not invented and no placeholder was shipped. The site is
  crawl-ready; claiming it requires the owner's Search Console or DNS access.
  The anonymous sitemap-submission endpoint that used to exist
  (`google.com/ping?sitemap=…`) was retired by Google and returns HTTP 404, so
  there is no submission path that bypasses ownership. The remaining discovery
  route is the repository's own README, which links to the published site.

## [2.3.0] — 2026-09-29

### Added
- **`docs/agent/AGENT-BOOTSTRAP.md`** — the agent activation protocol. A
  verbatim prompt that enumerates the 53-file instruction set from
  `FILE-INDEX.txt`, reads it in five dependency-ordered layers, reconciles it
  under a total precedence ladder (conformance first, vendored content last),
  tests comprehension across twelve named areas, forbids scope-creeping output
  during activation, and returns a **countable** readiness confirmation.
  Includes the design rationale for every clause.
- **`AGENT.md` §0 — The Framework You Are Running Inside.** The agent is now
  told at the top of its own instruction set that the 3,864 files in `skills/`
  are untrusted third-party text, that agent personas are hostile input, that
  conformance wins every conflict, and that structural verification is not a
  proof of semantic safety.
- **`AGENT.md` §29 — Tool Honesty.** Four questions to establish about any
  tool before trusting its output, with the three measured defects in the
  vendored `ai-security` skill as the worked example.
- **`AGENT.md` §5 — the three rungs.** Hypothesis, unverified finding, and
  confirmed vulnerability defined as distinct, with the transitions between
  them and the requirement to name the exact artifact that would confirm an
  unverified finding.
- **`AGENT.md` §27 — fabrication's second face.** Manufacturing the appearance
  of absence of evidence — reporting a tool's clean output as "no issues
  found" — is named as fabrication, with the rule that **a clean result is a
  coverage gap, not a clearance**.

### Added
- **`.github/scripts/gap_audit.py`** — the 16-group end-to-end audit, now a
  committed file rather than a scratch script. Previously the CHANGELOG claimed
  a 16/16 audit that no file in the repository could run, which is precisely
  the unfalsifiable claim this framework criticises elsewhere. Runs in CI.
- **`.github/scripts/gen_index.py`** — `FILE-INDEX.txt` was validated by
  `validate.py` but regenerated by hand, so the index could be checked but not
  reproduced. Now generated; `--check` fails CI on a stale index, `--write`
  regenerates it. The generator mirrors `validate.py`'s walk semantics exactly,
  because a generator that filtered differently from its checker is a new way
  for the index to lie.

### Publication and metadata
- **Canonical repository URL established and applied everywhere.**
  `My-Hack` was renamed to `blackheart-security-framework`; the old name still
  resolves via a GitHub 301 redirect, but the canonical name is now used in
  every reference, and both the rename and the `git remote set-url` command are
  documented so existing clones converge.
- **Site source and deployment workflow** in `site/` and
  `.github/workflows/pages.yml`, building to
  `devara1983ntr.github.io/blackheart-security-framework`. **Not yet published:**
  GitHub Pages is not enabled on this repository, so that URL is not live. The
  build job's six checks all pass; only the deploy step awaits the one manual
  toggle. This is stated rather than implied, because a README claiming a live
  URL is exactly the kind of unfalsifiable claim this project exists to reject. Static HTML, no build
  step, no third-party runtime. The deploy job refuses to publish if the site,
  sitemap, `robots.txt` and 404 disagree about the canonical URL, or if
  credential-shaped material appears in `site/`.
- **SEO/discoverability** configured: canonical link, meta description, robots
  directive, Open Graph and Twitter cards, JSON-LD `SoftwareSourceCode`,
  `sitemap.xml`, `robots.txt`, an `og-image`, a favicon and a `noindex` 404.
  Search Console verification is deliberately **not** shipped — the token is
  issued to a site owner and was not invented.
- **Repository metadata** set through the API: description, homepage, 20 topics
  including `ai-security`, `llm-security`, `agent-security`, `agent-guardrails`,
  `prompt-injection`, `supply-chain` and `mitre-atlas`; discussions enabled,
  wiki disabled, delete-branch-on-merge on, squash enabled.
- **`.gitattributes`** added. Without it, GitHub attributes this repository
  mostly to vendored Python, so the language bar described the mirror rather
  than the project. Vendored content is now `linguist-vendored`, generated
  artefacts are marked generated, and the ~40 first-party Python lines are the
  code GitHub should be reporting.
- **Contributor routes**: `CODEOWNERS` separating governance and gate files
  from documentation, issue templates for bug reports and proposals, a pull
  request template carrying the five commands a contributor must run, and
  `dependabot.yml` scoped to Actions and pip — deliberately **not** the vendored
  mirror, which is pinned and reviewed by a human.
- **Publication-disclosure control** in audit group 18: no documentation file
  may cite the Pages URL without stating that it is not published, while Pages
  is disabled. The README described a 404 URL as the "documentation site" and
  the correction initially did not land, because an edit script reported success
  without its anchor matching. The control is now a gate, and the fix was
  confirmed by reading the committed file back rather than trusting the script.
- **Audit groups 18 and 19** added: publication readiness, and a placeholder
  sweep. Group 19 excludes `templates/`, where `FINDING-XXX` and `TEST-XXX` are
  the convention and a template with nothing to fill in is not a template, and
  excludes itself, because a checker that flags its own pattern table reports a
  false positive forever and a permanently-red gate is a gate people learn to
  ignore.
- **Audit group 18** added: publication readiness. Verifies the required
  artefacts exist, all three workflows are present, the canonical URL is
  consistent across the site, and the 404 cannot be indexed.

### Fixed
- **Two real holes in the gap audit itself**, found by tamper-testing it rather
  than trusting it: it checked that the security gate keys were *present* but
  not that they were *enabled*, so `requireAuthorizedTarget: false` passed; and
  it checked for unindexed files but not dangling ones, so a deleted file with
  a stale index entry passed. Both are now hard failures. Group 10 also verifies
  `defaultEvidenceStatus` is still `UNVERIFIED`, and group 16 now requires
  `AGENT.md`'s section numbers to be contiguous.

### Corrected
- **Agent persona count: 34 → 33** in `ARCHITECTURE.md` (which had said 35) and
  `SECURITY.md`. `agents/` holds 38 files: 33 personas (32 deployable plus a
  blank `TEMPLATE.md`), `CLAUDE.md` and `personas/README.md` as documentation,
  and 3 empty `.gitkeep` files that were previously unlisted. The three
  `.gitkeep` files are now enumerated in the `agents/` adapter so the collection
  reconciles exactly.

## [2.2.0] — 2026-09-29

> **Correction (2.3.0):** this release originally recorded 34 agent personas.
> The true figure is **33**. `agents/` contains 38 files: 33 personas (32
> deployable plus a blank `TEMPLATE.md`), `CLAUDE.md` and `personas/README.md`
> as collection documentation, and 3 empty `.gitkeep` files. The original
> count treated `CLAUDE.md` as a persona. `ARCHITECTURE.md` repeated it as 35.
> Both are corrected; the underlying mirror was always correct.

Expands Layer 5 from a curated 8 skills to the **complete** upstream repository,
vendors the **full** third-party discovery index, and adds continuous
verification.

### The completeness gap this release closes

The first pass at "vendor everything" vendored only the 388 skill directories and
declared the job done. A gap audit against upstream found that the mirror was
missing **878 files of functional content**: 39 slash commands, 33 agent
personas, two plugin manifests, 29 upstream tooling scripts, 11 standards, 32
audit records, 667 generated reference pages, templates, orchestration notes, and
17 root documents. None of it was executable-critical, but all of it is content
the catalogue ships, and its absence was invisible because **nothing was checking
for it**.

### Added

- **The rest of the upstream repository**, vendored verbatim: `commands/`,
  `agents/`, `scripts/`, `standards/`, `audit/`, `docs/`, `templates/`,
  `orchestration/`, `custom-gpt/`, `assets/`, `.claude-plugin/`,
  `.codex-plugin/`, `.claude/`, and the 17 root documents. The mirror is now
  upstream's tree in full — **3,864 files**, every one byte-identical to
  `19392f7`.
- **12 collection adapters** covering commands, agent personas, upstream tooling,
  standards, audit history, documentation, templates, and the plugin manifests.
- **`.github/scripts/gen_adapters.py`**, **`gen_collection_adapters.py`**,
  **`gen_config.py`**, **`gen_manifest.py`** — adapter, config, and manifest
  generation are now reproducible scripts in the repository rather than
  throwaway code. Anything the mirror's contents determine is generated from the
  mirror, so drift between content and record is a build failure.
- **`.github/scripts/sync_upstream.py` rewritten** to compare the **whole mirror
  file by file**. The previous version compared per-skill digests, which would
  have let all the non-skill content drift undetected — the same blind spot that
  allowed the gap above.
- **The example config now loads `commands/` and `agents/`**, and declares that
  vendored personas are *not* enabled by default: adopting a persona is an
  explicit decision, not a default.

### Changed

- **Integrity is now file-level, not per-skill.** `.github/UPSTREAM-MANIFEST.json`
  records a SHA-256 for all 3,864 vendored files and 399 adapters. The
  validator distinguishes vendored files, Blackhearts-local adapters, and
  unaccounted extras, so "extra file" always means "unaccounted for".
- **The adapter gate now requires collection adapters too.** A vendored
  command, persona, or plugin manifest without one fails the build.

### Fixed

- **`sync_upstream.py` was left broken** by the manifest schema change — it read
  `manifest["skills"]`, which no longer exists. Found by running the script
  rather than assuming it worked.
- **The config generator emitted invalid JSON5** on first run: the
  `commands/` and `agents/` paths were emitted *after* the `extraDirs` array was
  closed, so they were not being loaded at all. Caught by parsing the file.
- **`playwright-pro/skills/coverage` lost its adapter** during bulk extraction,
  because `tar` replaced the directory. Caught by the integrity check, restored
  from git, and verified.

### Deliberately not vendored

| Excluded | Files | Reason |
|---|---:|---|
| `.gemini/`, `.codex/`, `.vibe/`, `.hermes/` | 1,574 | Symlink farms — all mode `120000`, each pointing at a skill already vendored. Verified by mode, not assumed. |
| `.gitignore` | 1 | Would apply to this repository's git behaviour across the mirror subtree, silently untracking vendored files. |
| `.github/` | 23 | Upstream's own CI, not catalogue content. |

Recorded in the manifest under `exclusions` so the sync workflow will not
reintroduce them.

### Security note

**Agent personas are the sharpest edge in this release.** A persona can redefine
an agent's identity, widen its scope, or instruct it to act without asking — the
exact failure the authorization gate exists to prevent, and a persona is a natural
place for that to be smuggled in. All 33 are treated as untrusted instruction,
none is enabled by default, and none may override the conformance layer. This is
documented in the collection adapter, in `SECURITY.md`, and in the example
config.

### Design decision (unchanged)

**Upstream sync opens a pull request and never merges.** Auto-merge on green CI
was rejected: it would admit unreviewed third-party code to the engagement
surface with no human reading it, defeating the control the framework exists to
enforce. Automation fetches, diffs, re-vendors, re-audits, and regenerates
adapters; a human decides. A file removed upstream is reported and left in
place, because deleting content is a human decision and not a side effect of a
cron job. Recorded as invariant 14.

### Also landed earlier in this release

- **Vendored scope: 8 → 388 skills**, byte-for-byte at `19392f7a`, with
  hand-written analysis kept for the eight promoted security skills. Full
  catalogue audit: **354 PASS, 21 WARN, 13 FAIL**, every CRITICAL and HIGH
  finding adjudicated by hand. No backdoor, covert channel, credential
  exfiltration, or safety override anywhere.
- **Third-party discovery index: 1 category → all 30**, ~5,270 URLs, all
  byte-identical to `f274daa`, still reference-only. Per-category counts in
  `skills/catalog/CATEGORY-INDEX.md`.
- **The seven-check validation gate and the daily upstream-sync workflow**, both
  canary-tested: tampering with a vendored skill, tampering with a vendored
  catalogue file, deleting an adapter, planting a realistic token, breaking the
  config, and removing an index entry each fail the build.
- **`README.md` no longer claims the repository contains no third-party code.**
  It does.

### Known issues

- 159 unresolved links inside verbatim upstream content, reported rather than
  patched so the mirror stays byte-comparable to its source. None is in
  Blackhearts-authored documentation.
- 13 skill names are defined at two upstream paths each. Both copies are
  vendored; one config entry enables both. Mapped in `skills/VENDOR.md` §5.
- `tech-debt-tracker` ships a sample codebase containing working code that POSTs
  to live Stripe, Square, and PayPal endpoints. A teaching artefact; its adapter
  marks it **never execute**.

## [2.1.0] — 2026-09-28

Integrates audited third-party skills into the framework as a new Layer 5.

### Added

- **`skills/`** — executable analysis skills, vendored and bound to the
  framework. The method stays in Layer 0; these are the tools that perform
  analysis.
- **`skills/conformance/SKILL.md`** — mandatory wrapper. Vendored skills were
  written by other authors and none knows BLACKHEART's evidence rules, so this
  converts tool output into evidence status, computes severity separately within
  the status ceiling, enforces the authorization gate, and requires an
  enforcement point on every finding carried forward. Marked `always: true`.
- **8 vendored skills** from
  [claude-skills](https://github.com/alirezarezvani/claude-skills) (MIT, Alireza
  Rezvani), pinned to commit `19392f7a`: `ai-security`, `red-team`,
  `cloud-security`, `security-pen-testing`, `dependency-auditor`,
  `threat-detection`, `senior-security`, `incident-response`. Chosen for direct
  overlap with the framework's weakest-covered areas.
- **8 `_BLACKHEART-ADAPTER.md` files** — per-skill provenance, interface,
  authorization gate, maximum claim, skill-specific cautions, and coverage
  contribution. Every adapter states what the skill's output may **not** be used
  to claim.
- **`skills/VENDOR.md`** — attribution, licences, provenance, and the reasoning
  behind every inclusion and non-inclusion decision.
- **`skills/openclaw.example.json5`** — working agent allowlists, per-skill
  gating, and install-policy configuration. Contains no secrets.
- **`skills/catalog/`** — the second source, recorded as reference only.

### Changed

- `ARCHITECTURE.md` adds Layer 5 (skills) to the layering diagram, inserts
  skill conformance into the precedence order between Layer 1 and the modes,
  and adds a thirteenth invariant: a tool's output is a hypothesis, not a
  finding.
- `README.md`, `SECURITY.md`, and `FILE-INDEX.txt` updated. Index now 76 entries.
- `AUTHOR` corrected: it previously stated the repository contained no
  third-party source code, which became untrue when the skills were vendored.
  It now records both sources, their authors, and their licences.

### Integration audit

Both sources were audited before anything was vendored. No live credentials, no
malicious code, and no exfiltration paths were found. The security scanner
raised two flags, both independently verified as **false positives** and
recorded in the adapters so they are not re-raised on every audit:

- `senior-security` — `__import__('datetime')` flagged as dynamic module
  loading. The argument is a string literal, not a variable.
- `security-pen-testing` — `pickle.load()` / `yaml.load()` flagged as unsafe
  deserialisation. Both are string literals in the scanner's own detection
  guidance for other people's code; the file makes no such call.

All 13 vendored scripts were executed and verified to run. All 8 vendored skill
directories were diffed against upstream and confirmed byte-for-byte identical.

### Deliberately not integrated

`awesome-openclaw-skills` contains **zero skills** — it is an index of roughly
5,265 links to skills on external registries. None were vendored: there is no
version pinning, no provenance verification, and no way to audit content before
it executes. Its `security-and-passwords` category lists skills whose purpose is
credential handling (`credential-manager`, `1password`, `bitwarden`, `dashlane`),
which is the highest-consequence integration mistake available. The catalogue is
preserved as a reference index with a documented vetting process instead.

## [2.0.0] — 2026-09-28

Third-pass expansion. Adds the offensive thinking layer (RED HEART), a new
Layer 0 for AI agent execution, and six new domain guides covering ground
the framework previously left to improvisation. Closes four ROADMAP gaps.

### Added — RED HEART, the offensive thinking layer

- **`docs/modes/RED-HEART-ADVERSARY-EMULATION.md`** — the framework's
  adversarial counterpart. BLACKHEART governs what may be claimed; RED HEART
  governs how an assessor thinks about the adversary. Covers adversary
  modelling, operational objectives, engagement goals (Expose / Affect /
  Elicit), path construction, chaining discipline, evasion reasoning,
  post-exploitation within authorization, human and process targets, and rules
  of engagement with hard abort conditions. Closes the failure mode where each
  control holds individually but the chain walks straight past the boundary.
- **`docs/guides/ATTACK-PATHS.md`** — path construction as a graph, with four
  explicit evidence states per edge (Demonstrated / Inferred / Hypothesised /
  Blocked). Establishes that a path is only as strong as its weakest evidenced
  edge, and that severity follows the demonstrated destination rather than the
  component findings.
- **`docs/guides/ADVERSARY-EMULATION.md`** — engagement structure adapted from
  the MITRE Engage model: prepare / operate / understand, the five approaches,
  blended objectives, safety planning, and the detection review that ordinary
  assessment does not produce.
- **`templates/ATTACK-PATH.md`** — path record with per-edge evidence, blocked
  steps as results, unproven edges with the test that would close them, and a
  detection review table.

### Added — Layer 0, the AI agent layer

- **`docs/agent/AGENT-OPERATING-PROTOCOL.md`** — an agent fails differently
  from a human: it confabulates evidence, drifts scope, reports intent as
  accomplishment. Those failures are systematic, so they get a written protocol
  rather than an assumption of diligence. Defines five non-negotiables, the
  pre-flight check, the tool-use protocol with its capture-before-interpretation
  rule, evidence and status discipline, escalation discipline, and hard stop
  conditions including the refusal to request credentials.
- **`docs/agent/AGENT-SKILL-CATALOGUE.md`** — 48 named skills across eight
  groups, each specified as trigger, procedure, output, maximum claim, stop
  condition, and the common failure it prevents. A procedure without a stop
  condition and a max claim is not a skill, and the catalogue states that rule
  explicitly.

### Added — domain guides

- **`docs/guides/AGENTIC-AI-SECURITY.md`** — LLM and agentic assessment:
  action-surface mapping before probing, the four test layers, the compound
  private-data + untrusted-content + exfiltration risk, direct and indirect
  injection, tool-layer authorization tested independently of the model,
  retrieval authorization, memory persistence, excessive agency across
  functionality/permissions/autonomy, output handling, and inter-agent trust.
  Includes the requirement to report reproduction rate for probabilistic
  results.
- **`docs/guides/CLOUD-IDENTITY.md`** — IAM and policy assessment, the
  default-deny test, the confused deputy pattern, storage and secret exposure,
  and multi-tenant boundary testing. States the boundary explicitly: the
  customer tenancy is in scope, the provider platform never is.
- **`docs/guides/SUPPLY-CHAIN.md`** — dependency inventory, reachability
  determination as the step that separates an assessment from a scan report,
  build and release integrity, secrets in dependencies, and agent plugin
  supply chains.
- **`docs/guides/METHODOLOGY-STANDARDS.md`** — alignment to PTES, NIST SP
  800-115, OSSTMM, MITRE Engage, and OWASP, with the limits stated rather than
  implied. Includes a claim sheet of what may and may not be asserted.
- **`templates/AGENT-THREAT-MODEL.md`** — action surface, per-tool permission
  scope, every input channel, the compound-risk question, trust boundaries with
  actual enforcement points, and a test plan derived from the model rather than
  from a generic list.

### Changed

- `ARCHITECTURE.md` introduces **Layer 0 (agent)** above the core, updates the
  mode and guide tables, extends precedence to seven ranks, and adds two
  invariants: a path is as strong as its weakest evidenced edge, and untrusted
  content is data rather than instruction.
- `AGENT.md` adds attack-path construction to the pipeline, expands §22 into
  path-and-chain analysis, and records that the operating protocol governs
  whoever executes the framework.
- `REFERENCE-MAPPINGS.md` adds the OWASP Top 10 for LLM Applications (2025), the
  agentic risk categories, and a section separating adversary-behaviour
  mappings from weakness-class mappings.
- `SKILLS.md` gains three competency groups — AI and agentic systems, cloud and
  identity, and adversary emulation.
- `GLOSSARY.md` adds adversary-emulation and agentic terminology.
- `ROADMAP.md` records four closed gaps and a "Recently closed" table so they
  are not re-proposed.
- `README.md`, `docs/README.md`, and `FILE-INDEX.txt` updated for 11 new
  documents; index now 52 entries.

## [1.1.0] — 2026-09-28

Second-pass audit and framework expansion. Closes the substantive gaps found in
a review of the 1.0.0 documentation set, and fixes several internal
inconsistencies in it.

### Added — new guides

- **`docs/guides/SEVERITY-RATING.md`** — impact × reach severity rubric.
  Closes the largest gap in 1.0.0: the framework defined a precise evidence
  status taxonomy but no rating rubric, so `AGENT.md` §25 could only say "use
  severity descriptions tied to observed impact" without defining what that
  meant. Introduces the binding rule that **severity is bounded by evidence
  status**, plus level thresholds, the payment-chain rating table, the
  relationship to CVSS, anti-inflation rules, a rating worksheet, and worked
  examples.
- **`docs/guides/REFERENCE-MAPPINGS.md`** — maps the framework's own weakness
  classes onto CWE, OWASP Top 10 (2021), OWASP API Security Top 10 (2023), OWASP
  Mobile Top 10 (2024), MASVS v2, ASVS v4, PCI DSS v4.0, and GDPR. Verified
  against the publishing bodies; carries an explicit instruction to re-verify
  identifiers before client-facing use, since CWE entries are revised.
- **`docs/guides/REMEDIATION-AND-RETEST.md`** — 1.0.0 required `Remediation`
  and `Regression Test` fields and a reporting section, but no methodology
  existed for producing them. Adds root-cause identification at the enforcement
  point, fix patterns by layer, chain-specific remediation for the payment and
  entitlement stages, anti-patterns, a regression-test design method, the
  retest protocol, and the five retest outcomes.

### Added — new reference documents

- **`docs/GLOSSARY.md`** — the framework used a dense specialist vocabulary
  (BOLA, BFLA, entitlement, enforcement point, proof strength, method
  escalation, coverage control, and others) across roughly 8,000 lines with no
  terminology reference. Every entry is a term the repository actually uses.
- **`docs/SKILLS.md`** — competency-to-document map across nine domains, for
  learning and self-direction. Explicitly not a claim of experience or
  certification.
- **`ARCHITECTURE.md`** — documents the four-layer structure (core → modes →
  guides → artefacts), the precedence order that resolves conflicts between
  documents, the engagement flow, and ten framework invariants. The precedence
  order formalises a rule the zero-credential mode already declared informally.
- **`ROADMAP.md`** — recognised gaps and explicitly out-of-scope items, with no
  dates and no delivery promises. Records what will *not* be built (scanners,
  exploit collections, automated severity scoring) so it is not repeatedly
  proposed.

### Added — new templates

- **`templates/ENGAGEMENT-RECORD.md`** — operationalises the scope and
  capability requirements in `AGENT.md` §3–§4, including a capability
  inventory and a tool-substitution register. Recording capabilities before
  testing is what makes an honest `NOT TESTED` defensible afterwards.
- **`templates/COVERAGE-MATRIX.md`** — per-boundary coverage across
  authentication, authorization, API/input integrity, payment and delivery,
  mobile, and evidence handling. "Coverage control" was a named pillar of the
  framework with no artefact to track it.

### Fixed

- **Status taxonomy inconsistency.** `README.md` listed eight statuses while
  `AGENT.md` §5 defines six. `BLOCKED BY ENVIRONMENT` and `INCONCLUSIVE` were
  presented as canonical but exist nowhere in the governing document. The
  README now lists the six canonical statuses and maps both variants to their
  correct equivalent, noting that a blocker is a *reason* recorded under
  `NOT TESTED`, not a status in its own right.
- **`DECISION-MATRIX.md` structure.** An author metadata line had been appended
  into the final row of the status table, corrupting it. Restored the table,
  and added worked examples plus an explicit note that status and severity are
  separate axes.
- **`SECURITY-AUDIT.md` and `DIGITAL-ASSET-DELIVERY-MODE.md` rendering.** Both
  were plain-text documents with no Markdown heading, so they rendered without
  a title, carried no author metadata, and were unreachable from documentation
  navigation. Both now have proper headings and metadata blocks; the original
  body text is unchanged.

### Changed

- `AGENT.md` §3 now points to the engagement-record template.
- `AGENT.md` §25 now binds severity to the new rubric and states the
  evidence-ceiling rule as normative.
- `AGENT.md` §26 quality gate gained five checks covering severity discipline
  and coverage reporting, and now names the coverage matrix as a required
  deliverable.
- `templates/FINDING.md` gained `Enforcement point`, `Standard mappings`, and
  an explicit evidence-ceiling check, and its severity field now states when to
  leave the rating blank.
- `templates/FINAL-REPORT.md` gained severity and mapping columns, a
  distribution block, a remediation table, and a required coverage statement.
- `docs/README.md` gained reference sections and a suggested reading order.
- `README.md` gained severity and reporting-chain sections, updated navigation
  and directory tree, and a corrected status taxonomy.
- `FILE-INDEX.txt` updated to 41 entries.

## [1.0.0] — 2026-09-28

Initial public release of the BLACKHEART adversarial security research
framework as a documented, structured project.

### Added

**Core operational modes**

- `docs/modes/SECURITY-AUDIT.md` — full-spectrum adversarial vulnerability
  assessment: attack-surface mapping, technical vulnerability classes,
  mobile/APK analysis, and exploit chaining.
- `docs/modes/SECURITY-RESEARCH-MODE.md` — structured research methodology:
  deep investigation loop, trust-boundary mapping, authentication lifecycle,
  API state-machine testing, and safe exploit validation.
- `docs/modes/DIGITAL-ASSET-DELIVERY-MODE.md` — end-to-end payment integrity,
  entitlement creation, download authorization bypass, and real-artifact
  validation for digital-product platforms.
- `docs/modes/ZERO-CREDENTIAL-ESCALATION-MODE.md` — three consolidated control
  layers: zero-credential attack-surface discovery from absolute zero
  privilege; continuous adversarial method escalation where a failed technique
  never closes an objective; and the gap-closure coverage-control engine
  (objective matrices, proof-strength levels, differential testing, chaining,
  coverage accounting, and formal stop conditions).

**Domain guides** (`docs/guides/`)

- `OPERATING-RULES.md` — behavioural safety rules and non-fabrication
- `SCOPE.md` — target intake schema and authorization verification
- `WORKFLOW.md` — end-to-end assessment lifecycle
- `EVIDENCE.md` — evidence hierarchy, chain of custody, redaction
- `AUTH-AUTHZ.md` — authentication lifecycle, BOLA/IDOR, RBAC
- `BUSINESS-LOGIC.md` — workflow skipping, races, state machines
- `WEB-API-TESTING.md` — endpoint discovery, parameter tampering, API testing
- `ANDROID-TESTING.md` — APK/AAB, WebView, intent and IPC security
- `PAYMENT-PREMIUM-TESTING.md` — payment, entitlement, premium access
- `DIGITAL-FILE-VALIDATION.md` — real artifact verification and hashing
- `TOOL-AND-ENVIRONMENT.md` — capability discovery and tool honesty
- `DECISION-MATRIX.md` — finding classification rules
- `REPORTING.md` — report structure and writing standards

**Templates** (`templates/`)

- `FINDING.md` — individual finding record
- `TEST-LOG.md` — hypothesis/execution journal
- `FINAL-REPORT.md` — full assessment report skeleton

**Examples** (`examples/`)

- `NEW-PROJECT-BOOTSTRAP.md` — engagement bootstrap prompt

**Project governance**

- `AGENT.md` — master agent instruction and execution standard
- `README.md` — project overview, structure, and navigation
- `FILE-INDEX.txt` — authoritative document index
- `LICENSE` — MIT License
- `SECURITY.md` — security policy and responsible-use policy
- `CONTRIBUTING.md` — contribution guidelines
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1
- `AUTHOR` — authorship and third-party attribution
- `CHANGELOG.md` — this file

### Changed

- Reorganised the repository into `docs/modes/`, `docs/guides/`, `examples/`,
  and `templates/`, replacing the previous flat `BLACKHEART-AGENT-DOCUMENTATION/`
  package layout. All file content preserved; all internal links updated.
- Registered the zero-credential/escalation/coverage mode as Core Mode 4 in
  `README.md` and `FILE-INDEX.txt`.
- Standardised authorship to **Roshan** across project metadata.

### Notes

- No third-party code, vendored libraries, or external datasets are included.
- No original document content was removed during the reorganisation.

[Unreleased]: https://github.com/devara1983ntr/blackheart-security-framework/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/devara1983ntr/blackheart-security-framework/releases/tag/v1.0.0
