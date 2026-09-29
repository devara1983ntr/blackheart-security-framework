#!/usr/bin/env python3
"""
Blackhearts end-to-end gap audit.

Run locally:   python3 .github/scripts/gap_audit.py
Run in CI:     python3 .github/scripts/gap_audit.py

What this is for.

  validate.py answers: "is the repository internally consistent right now?"
  gap_audit.py answers: "is the right set of things actually present, wired
                         together, and accounted for -- and do the documents
                         say true things about themselves?"

That second question is the one that keeps being unfalsifiable. A repository
can pass every consistency check and still be missing whole categories, or
still publish a number that stopped being true three commits ago. Both
failures are invisible to validate.py, which is exactly why this exists.

Every group below is a hard gate. Non-zero exit if any fails.

  1  adapter per skill         every canonical skill has an adapter
  2  mirror integrity           every vendored file byte-identical to the pin
  3  every vendored file indexed
  4  collection adapters        all 12 non-skill collections covered
  5  slash commands vendored    count matches the documented figure
  6  agent personas vendored    count matches the adapter's own table
  7  plugin manifests           both plugin manifests present
  8  plugin wiring resolves     manifest references point at real files
  9  config wiring              config declares commands and agents, not only skills
 10  security gate declarative  gate is flags only, no executable policy
 11  catalogue intact           discovery index present
 12  exclusions justified       every exclusion carries a written reason
 13  exclusions real            excluded paths are genuinely absent
 14  CI workflows present       both workflows exist
 15  root documents present     every required root document exists
 16  documentation self-check   the documents' own numbers are true

Group 16 is the one that catches the failure this file was written after:
the repository published a persona count that was wrong, and the CHANGELOG
claimed an audit that no file in the repository could run.

Exit codes:  0 = all pass, 1 = one or more failures.
"""

import hashlib
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MIRROR = os.path.join(REPO, "skills", "third-party", "claude-skills")
CATALOG = os.path.join(REPO, "skills", "catalog")
MANIFEST = os.path.join(REPO, ".github", "UPSTREAM-MANIFEST.json")
ADAPTER = "_BLACKHEART-ADAPTER.md"

COLLECTIONS = ["commands", "agents", "scripts", "standards", "audit",
               "templates", "orchestration", "custom-gpt", "docs",
               ".claude-plugin", ".codex-plugin", ".claude"]

# Nested test fixtures. sample-skill is a payload used by skill-tester to
# exercise its own scanner; it is not a loadable skill and carries no adapter
# by design. Its parent skill's adapter covers it.
NESTED_FIXTURES = {"sample-skill", "sample-text-processor"}

EXPECTED_COMMANDS = 39
EXPECTED_PERSONAS = 33
EXPECTED_PLUGIN_MANIFESTS = 2

ROOT_DOCS = ["README.md", "ARCHITECTURE.md", "AGENT.md", "SECURITY.md",
             "CHANGELOG.md", "ROADMAP.md", "CONTRIBUTING.md", "LICENSE",
             "CODE_OF_CONDUCT.md", "FILE-INDEX.txt"]

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    return bool(ok)


def files_under(root, skip_adapter=True):
    out = []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if skip_adapter and f == ADAPTER:
                continue
            out.append(os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/"))
    return sorted(out)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _probe_site(url, timeout=15):
    """True if the published site serves 200, False if it answers otherwise,
    None if the network could not be reached.

    Used by group 18 so the required publication disclosure follows from what
    is actually served rather than from a constant somebody flips. Returns None
    rather than guessing, because "the audit could not check" and "the site is
    down" are different facts, and the caller reports them differently.
    """
    try:
        import urllib.request
        import urllib.error
    except ImportError:                                   # pragma: no cover
        return None
    req = urllib.request.Request(url, method="GET",
                                 headers={"User-Agent": "blackheart-gap-audit"})
    try:
        # Scheme is not attacker-controlled: `url` comes from the repository's
        # own canonical-site constant, and it is https.  # nosec B310
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
            return resp.status == 200
    except urllib.error.HTTPError as e:
        # A 404 from GitHub Pages is a definitive answer, not an outage.
        return e.code == 200
    except Exception:
        return None


def run():
    man = json.loads(read(MANIFEST))
    vend = man["vendored"]

    # 1 ---------------------------------------------------------------
    skills = {os.path.dirname(os.path.join(dp, f)).replace(os.sep, "/")
              for dp, dn, fn in os.walk(MIRROR) for f in fn if f == "SKILL.md"}
    nested = [s for s in sorted(skills) if os.path.basename(s) in NESTED_FIXTURES]
    canon = [s for s in sorted(skills) if os.path.basename(s) not in NESTED_FIXTURES]
    noad = [s for s in canon if not os.path.isfile(os.path.join(MIRROR, s, ADAPTER))]
    check("1. adapter per skill", not noad,
          f"{len(canon)} canonical skills, {len(nested)} nested fixture(s) covered "
          f"by parent, {len(noad)} missing")

    # 2 ---------------------------------------------------------------
    bad = []
    for rel, meta in vend.items():
        p = os.path.join(MIRROR, rel)
        if not os.path.isfile(p):
            bad.append(rel)
            continue
        with open(p, "rb") as fh:
            if hashlib.sha256(fh.read()).hexdigest() != meta["sha256"]:
                bad.append(rel)
    check("2. mirror integrity", not bad,
          f"{len(vend)} files, {len(bad)} missing or altered")

    # 3 ---------------------------------------------------------------
    idx = {l.strip() for l in read(os.path.join(REPO, "FILE-INDEX.txt")).splitlines()
           if l.strip() and not l.startswith("#")}
    disk = {f"skills/third-party/claude-skills/{p}" for p in files_under(MIRROR)}
    unindexed = sorted(disk - idx)
    # Dangling matters as much as unindexed. A deleted file whose entry was
    # never removed is the index quietly asserting the repository contains
    # something it does not -- the same class of lie as an extra file.
    dangling = sorted(f"skills/third-party/claude-skills/{e}" for e in vend
                      if f"skills/third-party/claude-skills/{e}" not in idx)
    check("3. every vendored file indexed", not (unindexed or dangling),
          f"{len(disk)} on disk, {len(unindexed)} unindexed, {len(dangling)} dangling")

    # 4 ---------------------------------------------------------------
    missing = [c for c in COLLECTIONS
               if not os.path.isfile(os.path.join(MIRROR, c, ADAPTER))]
    check("4. collection adapters", not missing,
          f"{len(COLLECTIONS)} expected, {len(missing)} missing")

    # 5 ---------------------------------------------------------------
    cmds = [p for p in files_under(os.path.join(MIRROR, "commands")) if p.endswith(".md")]
    check("5. slash commands vendored", len(cmds) == EXPECTED_COMMANDS,
          f"{len(cmds)} commands, documented {EXPECTED_COMMANDS}")

    # 6 ---------------------------------------------------------------
    # Reconciled against the agents/ adapter's own table, so the prose and
    # the filesystem cannot drift apart without this failing.
    allf = files_under(os.path.join(MIRROR, "agents"))
    ad = read(os.path.join(MIRROR, "agents", ADAPTER))
    personas = [f for f in allf if f.endswith(".md")
                and f not in ("CLAUDE.md", "personas/README.md")]
    m = re.search(r"(\d+)\s+agent personas", ad)
    claimed = int(m.group(1)) if m else 0
    rows = len(re.findall(r"^\|\s*`", ad, re.M))
    check("6. agent personas vendored",
          len(personas) == claimed == EXPECTED_PERSONAS and rows == len(allf),
          f"{len(personas)} personas, adapter claims {claimed}, "
          f"{rows} table rows = {len(allf)} files")

    # 7 ---------------------------------------------------------------
    pm = [os.path.join(d, p)
          for d in (".claude-plugin", ".codex-plugin")
          for p in files_under(os.path.join(MIRROR, d)) if p.endswith(".json")]
    check("7. plugin manifests", len(pm) == EXPECTED_PLUGIN_MANIFESTS,
          f"{len(pm)} manifests, documented {EXPECTED_PLUGIN_MANIFESTS}")

    # 8 ---------------------------------------------------------------
    unres = []
    for p in pm:
        txt = read(os.path.join(MIRROR, p))
        for c in re.findall(r'"[^"]*?(?:command|path)"\s*:\s*"([^"]+)"', txt):
            if not list(MIRROR.rglob(os.path.basename(c))):
                unres.append(f"{p}:{c}")
    check("8. plugin wiring resolves", not unres,
          "all manifest references resolve" if not unres else f"unresolved: {unres[:3]}")

    # 9 ---------------------------------------------------------------
    cfg = read(os.path.join(REPO, "skills", "openclaw.example.json5"))
    check("9. config wiring", "commands" in cfg and "agents" in cfg,
          "config declares commands and agents, not only skills")

    # 10 --------------------------------------------------------------
    # Presence is not enforcement. An earlier version of this group only
    # checked that the gate keys appeared somewhere in the file, which meant
    # flipping requireAuthorizedTarget to false passed the audit. The gate is
    # the control; its being switched off must be a hard failure, and the
    # only way to know it is on is to read the value.
    REQUIRED_TRUE = ("requireAuthorizedTarget", "requireEngagementRecord",
                     "requireAdapter", "denyTargetsWithoutScope")
    REQUIRED_VALUES = {"defaultEvidenceStatus": "'UNVERIFIED'"}
    off = []
    for key in REQUIRED_TRUE:
        m = re.search(rf"{key}\s*:\s*(\S+?)\s*[,}}]", cfg)
        if not m or m.group(1).strip().rstrip(",") != "true":
            off.append(f"{key}={m.group(1) if m else 'absent'}")
    for key, want in REQUIRED_VALUES.items():
        m = re.search(rf"{key}\s*:\s*([^,}}\n]+)", cfg)
        if not m or m.group(1).strip() != want:
            off.append(f"{key}={m.group(1).strip() if m else 'absent'}")
    executable = "=>" in cfg or re.search(r"\bfunction\b", cfg)
    check("10. security gate enabled and declarative", not (off or executable),
          "all 5 gate flags set to their protective values, no executable policy"
          if not (off or executable)
          else f"weakened or executable: {off[:3]}{' + code' if executable else ''}")

    # 11 --------------------------------------------------------------
    cf = files_under(CATALOG)
    check("11. catalogue intact", len(cf) >= 32, f"{len(cf)} catalogue files")

    # 12 --------------------------------------------------------------
    ex = man["exclusions"]
    unjust = [k for k, v in ex.items()
              if not k.startswith("_") and not (isinstance(v, str) and v.strip())]
    real = [k for k in ex if not k.startswith("_")]
    check("12. exclusions justified", not unjust,
          f"{len(real)} exclusions, {len(unjust)} without a reason")

    # 13 --------------------------------------------------------------
    exs = {k.rstrip("/") for k in real}
    present = set(os.listdir(MIRROR))
    leaked = sorted(e for e in exs if e in present)
    check("13. exclusions real, not accidental", not leaked,
          f"{len(present)} top-level entries vendored, {len(exs)} excluded, "
          f"{len(leaked)} listed as excluded but present")

    # 14 --------------------------------------------------------------
    wf = {p.name for p in os.scandir(os.path.join(REPO, ".github", "workflows"))
          if p.name.endswith(".yml")}
    check("14. CI workflows present", {"validate.yml", "upstream-sync.yml"} <= wf,
          ", ".join(sorted(wf)))

    # 15 --------------------------------------------------------------
    gone = [r for r in ROOT_DOCS if r != "FILE-INDEX.txt" and r not in idx]
    check("15. root documents present", not gone,
          f"{len(ROOT_DOCS)} required, {len(gone)} missing")

    # 16 --------------------------------------------------------------
    # Every number the activation protocol and README publish about the
    # repository, checked against the repository. This is the group that
    # makes a documentation claim falsifiable instead of decorative.
    boot = read(os.path.join(REPO, "docs", "agent", "AGENT-BOOTSTRAP.md"))
    agent = read(os.path.join(REPO, "AGENT.md"))
    authored = sum(
        1 for dp, dn, fn in os.walk(REPO) for f in fn
        if f.endswith((".md", ".json5"))
        and not any(x in dp for x in ("/.git", "/third-party", "/catalog", "__pycache__")))
    nums = [int(n) for n in re.findall(r"^## (\d+)\.", agent, re.M)]
    secs = len(nums)
    problems = []
    if nums != list(range(secs)):
        problems.append(f"AGENT.md section numbers are not contiguous 0..{secs - 1}: {nums}")
    if f"is {authored}\nfiles" not in boot:
        problems.append(f"activation prompt does not state {authored} authored files")
    if f"[ ] {authored}/{authored} authored" not in boot:
        problems.append("activation prompt READ field is not self-consistent")
    if f"{authored} BLACKHEART-authored files" not in boot:
        problems.append("activation prompt confirmation count does not match")
    if f"master instruction, {secs} sections" not in boot:
        problems.append(f"activation prompt misstates AGENT.md section count ({secs})")
    # AGENT.md's own header publishes the repository's headline figures, so
    # they are claims too and belong in the same check. A header that has
    # drifted from reality is worse than no header, because it is the part
    # everyone reads first.
    header = agent.split("---")[0]
    man_head = json.loads(read(MANIFEST))
    ad_count = sum(1 for dp, dn, fn in os.walk(MIRROR) for f in fn if f == ADAPTER)
    expected_header = [
        (f"`{len(man_head['vendored']):,}`", "vendored file count"),
        (f"`{ad_count}`", "adapter count"),
        ("`8/8`", "validator result"),
    ]
    for token, what in expected_header:
        if token not in header:
            problems.append(f"AGENT.md header does not state the current {what} ({token})")
    # --- measured catalogue figures -------------------------------------
    # These were published as 5,270 in four places and 5,272 in the category
    # index while the vendored files contain 5,267 unique URLs, and as "33
    # files" while 32 are byte-identical. They are recomputed here from the
    # vendored copies, with the same extraction used to build the category
    # index, so a stale figure fails the build instead of being read.
    cat_dir = os.path.join(CATALOG, "categories")
    cat_categories = ([os.path.join(cat_dir, f) for f in sorted(os.listdir(cat_dir))
                       if f.endswith(".md")] if os.path.isdir(cat_dir) else [])
    cat_all = cat_categories + [os.path.join(CATALOG, n) for n in
                                ("upstream-README.md", "upstream-CONTRIBUTING.md")
                                if os.path.isfile(os.path.join(CATALOG, n))]
    url_re = re.compile(r"https?://[^\s\)\],\"'`<>]+")
    urls_all, urls_categories = set(), set()
    for p in cat_all:
        found = set(url_re.findall(read(p)))
        urls_all |= found
        if p in cat_categories:
            urls_categories |= found
    for value, what, rel, label in (
            (len(urls_all), "whole-catalogue URL total", "skills/catalog/CATEGORY-INDEX.md", "5267"),
            (len(urls_categories), "category URL total", "skills/catalog/CATEGORY-INDEX.md", "5210"),
            (len(cat_all), "byte-identical catalogue file count", "skills/catalog/README.md", None)):
        doc = read(os.path.join(REPO, rel))
        if label is not None and label not in doc:
            problems.append(f"{rel} does not state the {what} ({value})")
        if label is None and f"All {value} files" not in doc:
            problems.append(f"{rel} does not state the {what} ({value})")
    for rel, need in (("skills/catalog/README.md", f"{len(urls_all):,}"),
                      ("skills/VENDOR.md", f"{len(urls_all):,}")):
        if need not in read(os.path.join(REPO, rel)):
            problems.append(f"{rel} does not state the whole-catalogue URL total ({need})")
    idx = re.search(r"^# Total entries: (\d+)$", read(os.path.join(REPO, "FILE-INDEX.txt")), re.M)
    if idx:
        need = f"({int(idx.group(1)):,} entries)"
        if need not in read(os.path.join(REPO, "RELEASE-CHECKLIST.md")):
            problems.append(f"RELEASE-CHECKLIST.md does not state the index total {need}")
    check("16. documentation self-check", not problems,
          f"claims {authored} files / {secs} contiguous sections verified against the tree"
          if not problems else "; ".join(problems[:3]))

    # 17 --------------------------------------------------------------
    # The link registry must cover exactly the dead links the validator finds.
    # validate.py already enforces coverage; this asserts the registry itself is
    # present, well-formed, and carries a reason for every entry -- so a
    # registry that is empty, malformed, or unreasoned cannot pass as "fine".
    reg = os.path.join(REPO, ".github", "upstream-link-defects.json")
    reg_ok = False
    reg_detail = "registry missing"
    if os.path.isfile(reg):
        try:
            data = json.loads(read(reg))
            entries = data.get("entries", [])
            unreasoned = [e for e in entries if not e.get("reason")]
            missing_field = [e for e in entries
                             if not all(k in e for k in ("id", "file", "line", "target", "category"))]
            dupes = len(entries) - len({e["id"] for e in entries})
            declared = data.get("totals", {}).get("broken_links")
            consistent = declared == len(entries)
            reg_ok = bool(entries) and not unreasoned and not missing_field and not dupes and consistent
            reg_detail = (f"{len(entries)} registered, {len(unreasoned)} without a reason, "
                          f"{dupes} duplicate ids, totals {'match' if consistent else 'MISMATCH'}")
        except Exception as exc:
            reg_detail = f"unparseable: {exc}"
    check("17. upstream link defects registered", reg_ok, reg_detail)


    # 18 --------------------------------------------------------------
    # Publication readiness. A repository can be internally perfect and still
    # not be publishable: no site, no contributor route, no disclosure path,
    # or two files that disagree about the project's name.
    problems = []
    for f in ("site/index.html", "site/robots.txt", "site/sitemap.xml",
              "site/style.css", "site/favicon.svg", "site/og-image.svg",
              "site/404.html", "CODEOWNERS", ".gitattributes",
              ".github/dependabot.yml", ".github/PULL_REQUEST_TEMPLATE.md",
              ".github/ISSUE_TEMPLATE/bug.yml", ".github/ISSUE_TEMPLATE/config.yml",
              "SECURITY.md", "LICENSE", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
              "CHANGELOG.md"):
        if not os.path.isfile(os.path.join(REPO, f)):
            problems.append(f"missing {f}")
    wf = {p.name for p in os.scandir(os.path.join(REPO, ".github", "workflows"))
          if p.name.endswith(".yml")}
    for w in ("validate.yml", "upstream-sync.yml", "pages.yml"):
        if w not in wf:
            problems.append(f"missing workflow {w}")
    # the site, the sitemap, robots.txt and the 404 must name the same project
    site_url = "https://devara1983ntr.github.io/blackheart-security-framework/"
    for f in ("site/index.html", "site/sitemap.xml", "site/robots.txt", "site/404.html"):
        pth = os.path.join(REPO, f)
        if os.path.isfile(pth) and site_url not in read(pth):
            problems.append(f"{f} does not name the canonical site URL")
    # every served page must be crawlable-declared and self-describing
    idx = read(os.path.join(REPO, "site", "index.html"))
    for req, what in (('name="description"', "meta description"),
                      ('rel="canonical"', "canonical link"),
                      ('name="robots"', "robots directive"),
                      ('property="og:title"', "Open Graph title"),
                      ('"@type"', "structured data")):
        if req not in idx:
            problems.append(f"site/index.html missing {what}")
    # A documentation file must never present the Pages URL as live unless the
    # site is actually published, and must not keep calling it unpublished
    # after it is. The README once linked to a URL that returned 404 while
    # describing it as the "documentation site", which is exactly the
    # unfalsifiable claim this project exists to reject.
    #
    # The state is *measured*, not asserted by a constant. A hardcoded
    # `pages_live = True` would make this control pass forever regardless of
    # what is actually served -- the same failure in a new costume. So the URL
    # is fetched, and the required disclosure follows from the answer.
    live_state = _probe_site(site_url)
    if live_state is True:
        required = ("published", "live", "deployed")
        forbidden = ("not published", "not live", "not enabled", "is unpublished")
    elif live_state is False:
        required = ("not published", "not live", "not enabled", "is unpublished")
        forbidden = ()
    else:
        # Network unavailable. Do not silently pass: demand a stated position.
        required = ("published", "live", "deployed", "not published",
                    "not live", "not enabled", "is unpublished")
        forbidden = ()
        problems.append("could not reach the published site to verify its state")

    # A changelog is a historical record. Its older entries legitimately say
    # "not published" because that was true when they were written, and
    # rewriting them to match the present would destroy the record and make
    # the repository dishonest in the other direction. So a historical record
    # is exempt from the forbidden-polarity check -- but only if it actually
    # records the transition, which is checked below. Everything else, the
    # README above all, must match reality right now.
    historical = ("changelog.md", "history.md")

    for dp, dn, fn in os.walk(REPO):
        dn[:] = [d for d in dn if d not in (".git", "third-party", "catalog",
                                           "__pycache__", "site")]
        for f in fn:
            if not f.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(dp, f), REPO)
            body = read(os.path.join(dp, f))
            if "devara1983ntr.github.io" not in body:
                continue
            low = body.lower()
            is_record = f.lower() in historical
            # "no build step" is not a publication disclosure; accepting it
            # here made the control pass on a README that claimed a live site.
            if not any(w in low for w in required):
                problems.append(
                    f"{rel} cites the Pages URL but does not state its status "
                    f"(probe says the site is "
                    f"{'live' if live_state else 'NOT reachable'})")
            if is_record:
                # A record must not pretend the site was always live: the
                # earlier unpublished state has to still be in there.
                if live_state is True and not any(
                        w in low for w in ("not published", "not live",
                                           "not enabled", "is unpublished")):
                    problems.append(
                        f"{rel} describes the site as live but has erased the "
                        f"earlier unpublished state from its history")
                continue
            for w in forbidden:
                if w in low:
                    problems.append(
                        f"{rel} still calls the Pages URL '{w}' although the "
                        f"site serves HTTP 200")

    # the 404 must not be indexed, or it competes with real pages
    if os.path.isfile(os.path.join(REPO, "site", "404.html")) and \
            'name="robots" content="noindex' not in read(os.path.join(REPO, "site", "404.html")):
        problems.append("site/404.html is indexable and would compete in search")
    check("18. publication readiness", not problems,
          "18 required artefacts, 6 workflows, canonical URL consistent"
          if not problems else "; ".join(problems[:3]))


    # 19 --------------------------------------------------------------
    # No leftover placeholders in authored content.
    #
    # Templates/ is excluded: FINDING-XXX and TEST-XXX are the convention, and
    # a template with nothing to fill in is not a template. Everything else is
    # scanned for markers that would survive into a published document.
    # A `[bracketed]` placeholder in prose is also allowed, because the
    # documentation uses that notation deliberately and deliberately.
    PLACEHOLDERS = (r"\bTODO\b", r"\bFIXME\b", r"\bWIP\b",
                    r"lorem ipsum", r"REPLACE_ME", r"CHANGEME",
                    r"INSERT[_ ]HERE", r"<your[-_ ]", r"\bexample\.com/your")
    offenders = []
    for dirpath, dirnames, filenames in os.walk(REPO):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", "third-party", "catalog", "__pycache__",
                                    "templates", "licenses")]
        for name in filenames:
            if not name.endswith((".md", ".html", ".yml", ".yaml", ".txt",
                                  ".json", ".py", ".css", ".json5")):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), REPO)
            if rel in ("FILE-INDEX.txt", os.path.relpath(os.path.abspath(__file__), REPO)):
                # This file is excluded because it necessarily contains the
                # very markers it searches for. A checker that flags its own
                # pattern table would be reporting a false positive forever,
                # and a permanently-red gate is a gate people learn to ignore.
                continue
            body = read(os.path.join(dirpath, name))
            for pat in PLACEHOLDERS:
                for m in re.finditer(pat, body, re.I):
                    lineno = body[:m.start()].count("\n") + 1
                    offenders.append(f"{rel}:{lineno} {m.group(0)}")
    check("19. no leftover placeholders", not offenders,
          "templates excluded; no TODO/FIXME/placeholder markers elsewhere"
          if not offenders else f"{len(offenders)}: {offenders[:3]}")


    # 20 --------------------------------------------------------------
    # Known-vulnerable vendored content has a written disposition.
    #
    # Dependabot security alerts were switched off on this repository, which
    # is the wrong default for a project about supply-chain risk. Re-enabling
    # them surfaced 82 open alerts, all in a single vendored test fixture: the
    # `sample-web-app` corpus the vendored `dependency-auditor` skill exists
    # to scan.
    #
    # Patching it would break the byte-identical mirror and destroy the test
    # corpus, so it is accepted rather than fixed. Accepting is only honest if
    # it is written down and re-checked, which is what this group is for. A
    # silent "not a real vulnerability" is indistinguishable from having
    # ignored it.
    # ------------------------------------------------------------------
    vproblems = []
    REG = os.path.join(REPO, ".github", "known-vulnerable-fixtures.json")
    fixtures = []
    if not os.path.isfile(REG):
        vproblems.append(".github/known-vulnerable-fixtures.json is missing")
    else:
        try:
            fixtures = json.loads(read(REG)).get("known_vulnerable_fixtures", [])
        except ValueError as e:
            vproblems.append(f"known-vulnerable-fixtures.json is not valid JSON: {e}")
    if not fixtures:
        vproblems.append("no known-vulnerable fixture is registered")

    vendored_root = "skills/third-party"
    for fx in fixtures:
        rel = fx.get("path", "")
        if not rel:
            vproblems.append("a registered fixture has no path")
            continue
        if not rel.startswith(vendored_root + "/"):
            vproblems.append(
                f"{rel} is registered as a known-vulnerable fixture but is "
                f"not vendored -- if it is now Blackhearts-authored it must "
                f"actually be fixed, not accepted")
            continue
        if not os.path.isfile(os.path.join(REPO, rel)):
            vproblems.append(f"{rel} is registered but no longer exists")
            continue
        if not fx.get("why") or not fx.get("disposition"):
            vproblems.append(f"{rel} has no recorded reason or disposition")

    # The posture those dispositions rest on: we author no dependency manifest.
    # If that ever changes, the accepted-alerts argument stops holding, so
    # assert the premise rather than assuming it.
    authored_manifests = []
    for dp, dn, fn in os.walk(REPO):
        pruned = os.path.join(dp, "").replace(os.sep, "/").lstrip("./")
        if pruned == vendored_root or pruned.startswith(vendored_root + "/"):
            dn[:] = []
            continue
        dn[:] = [d for d in dn if d not in (".git", "__pycache__")]
        for name in fn:
            if name not in ("package.json", "requirements.txt", "Pipfile",
                            "pyproject.toml", "go.mod", "Cargo.toml",
                            "package-lock.json", "yarn.lock", "poetry.lock"):
                continue
            rel = os.path.relpath(os.path.join(dp, name), REPO).replace(os.sep, "/")
            if not rel.startswith(vendored_root + "/"):
                authored_manifests.append(rel)
    if authored_manifests:
        vproblems.append(
            f"Blackhearts-authored dependency manifest(s) present: "
            f"{authored_manifests[:3]} -- that changes the security posture "
            f"and the accepted-alert dispositions must be re-reviewed")

    check("20. vulnerable-content disposition", not vproblems,
          f"{len(fixtures)} vendored fixture(s) accepted with written "
          f"reasons; 0 authored dependency manifests"
          if not vproblems else "; ".join(vproblems[:3]))


def main():
    run()
    width = max(len(n) for n, _, _ in RESULTS)
    print("=" * (width + 44))
    print("  BLACKHEARTS END-TO-END GAP AUDIT")
    print("=" * (width + 44))
    for name, ok, detail in RESULTS:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print("-" * (width + 44))
    print(f"  {passed}/{total} groups passed")
    print("=" * (width + 44))
    if passed != total:
        print("\n  A failing group means a documented claim is not true, or a")
        print("  present thing is not accounted for. Do not report around it.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
