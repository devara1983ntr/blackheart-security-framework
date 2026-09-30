# Release checklist

Every gate below is **executed**, not eyeballed. The commands are in
[.github/scripts/validate.py](.github/scripts/validate.py),
[.github/scripts/gap_audit.py](.github/scripts/gap_audit.py),
[site/check_site.py](site/check_site.py),
[site/audit_seo.py](site/audit_seo.py) and
[site/test_interactions.py](site/test_interactions.py).

Run everything:

```bash
python3 -m pip install json5 playwright && python3 -m playwright install chromium
python3 .github/scripts/validate.py       # 8 checks
python3 .github/scripts/gap_audit.py      # 20 groups
python3 site/check_site.py                # static site gates
python3 site/audit_seo.py                 # links, metadata, budget
python3 site/check_contrast.py            # WCAG AA, measured in a real browser
python3 site/test_interactions.py         # real-browser behaviour
```

`playwright` is needed for the last two. The first four run on the standard
library alone and are what CI enforces on every push.

---

## 1. Functionality

| # | Check | How it is verified | Status |
|---|---|---|---|
| 1.1 | All 6 pages serve and render | `check_site.py`, HTTP probe of the live URL | ✅ |
| 1.2 | Theme toggle works on every page and persists | interaction suite | ✅ |
| 1.3 | Mobile section menu opens, closes on Escape, outside click and link activation | interaction suite, all 5 pages | ✅ |
| 1.4 | Tabs switch by click and by Arrow/Home/End, with roving tabindex | interaction suite | ✅ |
| 1.5 | Copy-to-clipboard reports success or a real failure | interaction suite, with clipboard permission | ✅ |
| 1.6 | Scroll spy marks the visible section | interaction suite | ✅ |
| 1.7 | Counters animate to their exact target | interaction suite | ✅ |
| 1.8 | Back-to-top appears, scrolls, and settles | interaction suite | ✅ |
| 1.9 | Site works with JavaScript disabled | no-JS render probe | ✅ |
| 1.10 | A thrown script error does not blank the page | interaction suite routes a throwing `app.js` | ✅ |
| 1.11 | Unknown URLs return a real 404 with `noindex` | live HTTP probe | ✅ |

## 2. UI / UX

| # | Check | Status |
|---|---|---|
| 2.1 | Hover, focus-visible, active and selected states on every control | ✅ |
| 2.2 | `:focus-visible` rather than `:focus` — no ring on mouse click, ring on keyboard | ✅ |
| 2.3 | Cross-page transition via the View Transitions API, absent where unsupported | ✅ |
| 2.4 | Scroll-reveal on scroll, disabled under `prefers-reduced-motion` | ✅ |
| 2.5 | Scroll progress indicator and back-to-top | ✅ |
| 2.6 | **Loading state** — n/a by design: the site fetches nothing, so there is no loading state to render. Anything shown for its own sake would be theatre. | ✅ |
| 2.7 | **Empty state** — n/a by design: no list is populated from data. | ✅ |
| 2.8 | **Error state** — a real error banner on unhandled rejection, failed stylesheet, or a throwing script; dismissible; announced via `role="status"` | ✅ |
| 2.9 | Consistent design system across all pages; zero unstyled class names | ✅ |

## 3. Responsive

| # | Check | Status |
|---|---|---|
| 3.1 | No horizontal overflow at **320, 390, 768, 1440px** on all 6 pages — 24 measured assertions | ✅ |
| 3.2 | Layout holds at 320px, the narrowest realistic viewport | ✅ |
| 3.3 | Long literals (regex, paths, SHAs) scroll inside their block, never widen the page | ✅ |
| 3.4 | Grid floors use `minmax(min(<n>rem, 100%), 1fr)` so they cannot exceed a narrow viewport | ✅ |
| 3.5 | Decorative glows clamped to the viewport | ✅ |
| 3.6 | Print stylesheet; header, nav and decoration dropped | ✅ |

## 4. Accessibility

| # | Check | Status |
|---|---|---|
| 4.1 | One `h1` per page; heading order intact | ✅ |
| 4.2 | Skip link to `#main` on every page | ✅ |
| 4.3 | Landmarks, `aria-label` on every nav | ✅ |
| 4.4 | Tabs implement the APG pattern: `tablist`/`tab`/`tabpanel`, `aria-selected`, roving tabindex, arrow keys | ✅ |
| 4.5 | Decorative SVG and glows `aria-hidden` | ✅ |
| 4.6 | `role="img"` blocks carry an accessible name | ✅ |
| 4.7 | Copy result announced via `role="status"` + `aria-live="polite"` | ✅ |
| 4.8 | Error banner announced politely | ✅ |
| 4.9 | `prefers-reduced-motion` honoured for every transition and animation | ✅ |
| 4.10 | Colour contrast meets AA in both themes, **measured** in a browser, not asserted | ✅ |
| 4.11 | All controls reachable and operable by keyboard | ✅ |
| 4.12 | Every document parses as well-formed HTML; `lang`, `charset` and viewport present on all six pages | ✅ |

## 5. SEO

| # | Check | Status |
|---|---|---|
| 5.1 | Unique title and meta description per page, each within SERP truncation limits | ✅ |
| 5.2 | Self-referential `canonical` and matching `og:url` on every page | ✅ |
| 5.3 | Sitemap lists every indexable page and only pages that exist | ✅ |
| 5.4 | 404 is `noindex` and absent from the sitemap | ✅ |
| 5.5 | Complete Open Graph and Twitter card metadata; real 1200×630 PNG card | ✅ |
| 5.6 | `apple-touch-icon` is a **PNG** — iOS ignores SVG and would fall back to a page screenshot | ✅ |
| 5.7 | JSON-LD `SoftwareSourceCode` parses | ✅ |
| 5.8 | `robots.txt` welcomes Googlebot and declares the sitemap | ✅ |
| 5.11 | `hreflang` declared on every indexable page; markup parsed for correct nesting, not pattern-matched | ✅ |
| 5.9 | No third-party runtime — no CDN, no webfont, no tracker | ✅ |
| 5.10 | Every page cross-links to every other; no orphan page | ✅ |

## 6. Performance

| # | Check | Measured |
|---|---|---|
| 6.1 | Visitor payload (HTML + CSS + JS + favicon) | **85 KB** uncompressed, budget 150 KB |
| 6.2 | Social card excluded from the visitor budget | 82 KB, crawler-only |
| 6.3 | No blocking third-party resource | ✅ |
| 6.4 | No webfont request; system font stack | ✅ |
| 6.5 | No layout shift from late-loading assets | ✅ |

## 7. Security

| # | Check | Status |
|---|---|---|
| 7.1 | No credential material in the repository or anywhere in history | ✅ |
| 7.2 | Credential used one-shot, never in a remote URL or git config, then shredded | ✅ |
| 7.3 | `secrets` validator check; 15 allowlisted placeholders only | ✅ |
| 7.4 | Pages deploy refuses to run if credential-shaped material appears in `site/` | ✅ |
| 7.5 | Dependabot security alerts **enabled**; 82 alerts triaged, all in one vendored fixture | ✅ |
| 7.6 | Accepted-risk disposition written down and enforced by audit group 20 | ✅ |
| 7.7 | The policy parses and all ten documents it names exist (`policy validate`) | ✅ |
| 7.8 | Active operations refused without a recorded acceptance, and refused again when an acceptance goes stale (`test_policy`) | ✅ |
| 7.9 | Local, read-only commands run without an acceptance; the exemption list matches the command parser | ✅ |
| 7.10 | No compliance badge, invented entity or absolute liability claim in authored content (`test_legal`) | ✅ |
| 7.11 | Independent security review — **outstanding; not claimed as performed** | ⬜ |
| 7.7 | Zero Blackhearts-authored dependency manifests | ✅ |
| 7.8 | Declarative security gate, no executable policy | ✅ |
| 7.9 | `innerHTML` avoided for dynamic content | ✅ |
| 7.10 | All external links carry `rel="noopener"` | ✅ |

## 8. Testing

| # | Suite | Count |
|---|---|---|
| 8.1 | `validate.py` | 8/8 |
| 8.2 | `gap_audit.py` | 20/20 |
| 8.3 | `check_site.py` | 118/118 |
| 8.4 | `audit_seo.py` | clean |
| 8.5 | `check_contrast.py` | clean, both themes, gradient stops included |
| 8.6 | `test_interactions.py` | 81/81 |
| 8.7 | Vendored integrity: 3,864 files byte-identical to `19392f7a` | ✅ |
| 8.8 | Link registry: 111 registered, 0 unregistered defects | ✅ |
| 8.9 | `upstream-watch.yml`: read-only, both pinned sources, drift classified | ✅ |
| 8.10 | `site-verify.yml`: browser gates run in CI, not only locally | ✅ |
| 8.11 | `authored-scan.yml`: authored config parses, capability audit claims hold, authored Python clean at MEDIUM+ | ✅ |

## 9. Links & documentation

| # | Check | Status |
|---|---|---|
| 9.1 | 5,424 local links; 0 broken in Blackhearts-authored docs | ✅ |
| 9.2 | 111 vendored defects registered individually with reasons | ✅ |
| 9.3 | 48 authored defects fixed | ✅ |
| 9.4 | Every internal link resolves; every anchor matches a real `id` | ✅ |
| 9.5 | `FILE-INDEX.txt` in sync (4,475 entries) | ✅ |
| 9.6 | Every documented figure verified against the tree by audit group 16 | ✅ |
| 9.7 | No unfinished-work markers or placeholders outside templates | ✅ |

## 10. Configuration & repository hygiene

| # | Check | Status |
|---|---|---|
| 10.1 | JSON5 config parses; 374/374 skills declared | ✅ |
| 10.2 | 7 workflows: `validate`, `pages`, `upstream-sync`, `upstream-watch`, `site-verify`, `authored-scan`, `phase5-validation` | ✅ |
| 10.3 | `.gitattributes` marks vendored files `linguist-vendored` | ✅ |
| 10.4 | `CODEOWNERS`, Dependabot config, issue/PR templates present | ✅ |
| 10.5 | No temp, backup, log or editor-dropping files in the tree | ✅ |
| 10.6 | Working tree clean; local `main` == `origin/main` == `5921dd4` | ✅ |
| 10.7 | Commit messages accurate and readable; `validate.py` `history` fails on any unexpanded `$(name)` token in any ref | ✅ |
| 10.8 | Branches: `main` only — `jules-*` deleted after re-verifying `ahead_by == 0` at the moment of deletion | ✅ |
| 10.9 | No leftover backup refs (`refs/original/`) keeping superseded commits reachable | ✅ |
| 10.10 | Repository settings (description, 20 topics, branch protection) applied via `repo_settings.py` and verified live against the API | ✅ |

## 11. Deployment

| # | Check | Status |
|---|---|---|
| 11.1 | GitHub Pages enabled, `build_type: workflow` | ✅ |
| 11.2 | `pages` workflow green on every `site/**` push (`d30e1d7`: success) | ✅ |
| 11.3 | All assets 200; unknown paths 404 — verified against the live site | ✅ |
| 11.4 | Deployed pages verified in a real browser, not just locally | ✅ |
| 11.5 | Canonical URL consistent across site, sitemap, robots and 404 — build fails otherwise | ✅ |

## 12. Known limitations — stated, not hidden

| # | Limitation | Why it is not fixed here |
|---|---|---|
| 12.1 | **Search Console ownership is unverified.** The site is crawlable but not claimed. | The `google-site-verification` token is issued by Google to a site owner. No repository or GitHub token can generate one, and it was not invented. Verified: Google's anonymous `ping?sitemap=` endpoint is retired and returns HTTP 404. Requires the owner's Search Console or DNS access. |
| 12.2 | 82 Dependabot alerts remain open. | All are in one vendored test fixture that is the corpus for a dependency-auditing skill. Patching breaks the byte-identical mirror and deletes the corpus. Registered, reasoned and enforced by audit group 20. |
| 12.3 | 111 dead links remain in vendored files. | Editing them breaks the mirror. Registered individually with reasons. |
| 12.4 | No load, fuzz or DoS testing. | Out of scope by policy. |
| 12.5 | Browser tests and the contrast audit run locally, not in CI. | They need a ~150 MB Playwright download on every push for a static site. `check_site.py` and `audit_seo.py` cover the regression classes that matter most without it. **Consequence: a contrast or interaction regression will pass CI and be caught only if someone runs the browser suite.** |
| 12.6 | A clean scan is a coverage gap. | Stated on the [disclosure page](site/disclosure.html) and in the README. Nothing here claims the vendored content is safe — only that it is byte-identical to a known SHA, which is a provenance claim, not a safety one. |
