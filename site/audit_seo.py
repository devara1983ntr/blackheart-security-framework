#!/usr/bin/env python3
"""Whole-site and whole-repository link, URL and SEO audit.

Run:  python3 site/audit_seo.py
Exit: 0 clean, 1 problems found

Checks things the other gates do not: that every internal link resolves to
something that exists, that anchors match real element ids, that no page
references a missing asset, that canonical/og:url agree with the page's own
address, and that the sitemap and the shipped pages describe the same set.
"""
import os
import re
import sys
import xml.dom.minidom

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CANON = "https://devara1983ntr.github.io/blackheart-security-framework/"

problems = []
notes = []


def read(p):
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


pages = sorted(f for f in os.listdir(HERE) if f.endswith(".html"))


def resolve(target):
    """Resolve a site-relative href to a path. './' and '' mean the index."""
    if target in ("", "./"):
        return os.path.join(HERE, "index.html")
    return os.path.normpath(os.path.join(HERE, target))


# ---- internal links and anchors -------------------------------------------
for page in pages:
    body = read(os.path.join(HERE, page))
    ids = set(re.findall(r'\sid="([^"]+)"', body))
    for href in re.findall(r'href="([^"]+)"', body):
        if href.startswith(("http://", "https://", "mailto:", "data:")):
            continue
        target, _, frag = href.partition("#")
        if target:
            if not os.path.isfile(resolve(target)):
                problems.append(f"{page}: link to missing file {target}")
                continue
        if frag and frag not in ids:
            problems.append(f"{page}: anchor #{frag} has no matching id")

# ---- assets referenced but absent ----------------------------------------
for page in pages:
    body = read(os.path.join(HERE, page))
    for src in re.findall(r'(?:src|href)="([^"]+)"', body):
        if src.startswith(("http", "#", "mailto:", "data:")):
            continue
        t = src.split("#")[0]
        if t and not os.path.isfile(resolve(t)):
            problems.append(f"{page}: references missing asset {t}")

# ---- canonical / og:url / og:image consistency ---------------------------
for page in pages:
    if page == "404.html":
        continue
    body = read(os.path.join(HERE, page))
    slug = "" if page == "index.html" else page
    want = f"{CANON}{slug}"
    canon = re.search(r'<link rel="canonical" href="([^"]+)"', body)
    if not canon:
        problems.append(f"{page}: no canonical link")
    elif canon.group(1) != want:
        problems.append(f"{page}: canonical is {canon.group(1)}, expected {want}")
    og = re.search(r'property="og:url" content="([^"]+)"', body)
    if not og:
        problems.append(f"{page}: no og:url")
    elif og.group(1) != want:
        problems.append(f"{page}: og:url is {og.group(1)}, expected {want}")

# ---- sitemap agrees with the shipped pages --------------------------------
sm = read(os.path.join(HERE, "sitemap.xml"))
# Parses this repository's own sitemap.xml from disk, never untrusted input.
# A malformed file fails the gate, which is the whole purpose of the line.
xml.dom.minidom.parseString(sm)          # nosec B318
locs = re.findall(r"<loc>([^<]+)</loc>", sm)
indexable = [p for p in pages if p != "404.html"]
if len(locs) != len(indexable):
    problems.append(
        f"sitemap has {len(locs)} entries but {len(indexable)} pages ship")
for loc in locs:
    rel = loc.replace(CANON, "") or "index.html"
    if not os.path.isfile(os.path.join(HERE, rel)):
        problems.append(f"sitemap lists {rel}, which does not exist")

# ---- the 404 must not be in the sitemap ----------------------------------
if "404" in sm:
    problems.append("sitemap lists the 404 page")

# ---- titles and descriptions unique and sized -----------------------------
titles, descs = {}, {}
for page in pages:
    body = read(os.path.join(HERE, page))
    t = re.search(r"<title>(.*?)</title>", body, re.S)
    d = re.search(r'name="description" content="([^"]*)"', body)
    if not t:
        problems.append(f"{page}: no title")
    else:
        val = t.group(1).strip()
        if len(val) > 70:
            problems.append(f"{page}: title is {len(val)} chars (>70 truncates in SERPs)")
        if val in titles:
            problems.append(f"{page}: duplicate title, also used by {titles[val]}")
        titles[val] = page
    if d:
        val = d.group(1).strip()
        if len(val) > 175:
            problems.append(f"{page}: meta description is {len(val)} chars (>175)")
        if val in descs:
            problems.append(f"{page}: duplicate meta description, also used by {descs[val]}")
        descs[val] = page

# ---- performance budget ---------------------------------------------------
# Budget what a visitor actually downloads, not what sits on disk. The 1200x630
# social card is 82KB and is fetched by crawlers, never by a reader, so counting
# it would measure the wrong thing.
VISITOR_BUDGET = 150_000
visitor = 0
for f in ("index.html", "style.css", "app.js", "favicon.svg"):
    p = os.path.join(HERE, f)
    if os.path.isfile(p):
        visitor += os.path.getsize(p)
if visitor > VISITOR_BUDGET:
    problems.append(
        f"a visitor downloads {visitor:,}B, over the {VISITOR_BUDGET:,}B budget")
else:
    notes.append(f"visitor payload {visitor:,}B (budget {VISITOR_BUDGET:,}B, "
                 f"uncompressed; gzips to roughly a third)")

social = os.path.getsize(os.path.join(HERE, "og-image.png"))
notes.append(f"social card {social:,}B — fetched by crawlers, not by readers")

# ---- no third-party runtime ---------------------------------------------
# The site's own canonical and og: URLs are self-references, not requests.
ALLOWED = ("github.com", "opensource.org", "schema.org", "devara1983ntr.github.io")
for page in pages:
    body = read(os.path.join(HERE, page))
    for u in re.findall(r'(?:src|href)="(https?://[^"]+)"', body):
        if not any(x in u for x in ALLOWED):
            problems.append(f"{page}: third-party runtime request {u}")

# ---- report ---------------------------------------------------------------
print("=" * 64)
print("  SEO / LINK AUDIT")
print("=" * 64)
for n in notes:
    print(f"  note  {n}")
for p in problems:
    print(f"  FAIL  {p}")
if not problems:
    print(f"  clean — {len(pages)} pages, {len(locs)} sitemap entries, "
          f"{len(titles)} unique titles, {len(descs)} unique descriptions")
print("=" * 64)
sys.exit(1 if problems else 0)
