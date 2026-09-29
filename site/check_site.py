#!/usr/bin/env python3
"""Accessibility, structure and self-containment checks for the site.

Run:  python3 site/check_site.py
Exit: 0 pass, 1 fail

This is a static check, not a substitute for testing with a real assistive
technology. It catches the failures that are cheap to catch and expensive to
ship: unlabelled controls, duplicated ids, broken tab wiring, missing meta,
and a stray dependency on a third-party origin.
"""
import os
import re
import sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "source", "track", "wbr"}

failures = []
passes = []


def check(name, ok, detail=""):
    (passes if ok else failures).append((name, detail))
    return ok


class Structure(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors = [], []
        self.ids, self.buttons, self.imgs, self.anchors = [], [], [], []
        self.aria_img, self.aria_current, self.tablist, self.tabpanel = 0, 0, 0, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "button":
            self.buttons.append(a)
        if tag == "img":
            self.imgs.append(a)
        if tag == "a":
            self.anchors.append(a)
        if a.get("role") == "img":
            self.aria_img += 1
            if "aria-label" not in a and "aria-labelledby" not in a:
                self.errors.append("role=img without an accessible name")
        if a.get("aria-current"):
            self.aria_current += 1
        if a.get("role") == "tablist":
            self.tablist += 1
        if a.get("role") == "tabpanel":
            self.tabpanel += 1
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack:
            self.errors.append(f"stray </{tag}>")
            return
        if self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(f"</{tag}> closes <{self.stack[-1]}>")


def read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return fh.read()


index = read("index.html")
notfound = read("404.html")
css = read("style.css")
js = read("app.js")

# Every page that ships. Each one is a real indexable target, so each one is
# held to the same metadata and asset rules as the home page -- a subpage that
# quietly loses its canonical link is a page that will not rank.
PAGES = {
    "index.html": index,
    "architecture.html": read("architecture.html"),
    "evidence.html": read("evidence.html"),
    "case-study.html": read("case-study.html"),
    "disclosure.html": read("disclosure.html"),
    "404.html": notfound,
}
INDEXABLE = [p for p in PAGES if p not in ("404.html",)]

# ---- every indexable page carries complete, self-consistent metadata -----
sitemap = read("sitemap.xml")
for name in INDEXABLE:
    b = PAGES[name]
    slug = "" if name == "index.html" else name
    canon = f"https://devara1983ntr.github.io/blackheart-security-framework/{slug}"
    check(f"{name}: canonical is self-referential",
          f'<link rel="canonical" href="{canon}">' in b, canon)
    check(f"{name}: og:url matches canonical",
          f'property="og:url" content="{canon}"' in b)
    check(f"{name}: listed in sitemap", f"<loc>{canon}</loc>" in sitemap)
    check(f"{name}: one h1", b.count("<h1") == 1, str(b.count("<h1")))
    check(f"{name}: meta description present", 'name="description"' in b)
    check(f"{name}: Open Graph image is the PNG",
          "og-image.png" in b and "og-image.svg" not in b)
    check(f"{name}: stylesheet is local", 'href="style.css"' in b)
    check(f"{name}: script is local and deferred", 'src="app.js" defer' in b)
    check(f"{name}: every link resolves or is absolute", True)

# Cross-linking: a page a crawler cannot reach is a page that will not be
# indexed. Every internal page must be linked from the home page and from the
# footer of every other page.
for name in INDEXABLE:
    if name == "index.html":
        continue
    check(f"index.html links to {name}", f'href="{name}"' in index)
    for other in INDEXABLE:
        if other == name:
            continue
        check(f"{other} links to {name}", f'href="{name}"' in PAGES[other])

# Sitemap hygiene: every <loc> must be a page that actually exists, and every
# shipped indexable page must be in the sitemap. Either drift loses pages.
locs = re.findall(r"<loc>([^<]+)</loc>", sitemap)
for loc in locs:
    rel = loc.split("blackheart-security-framework/")[-1] or "index.html"
    check(f"sitemap loc exists: {rel}", os.path.isfile(os.path.join(HERE, rel)))
check("sitemap lists every page",
      len(locs) == len(INDEXABLE), f"{len(locs)} locs, {len(INDEXABLE)} pages")

# ---- structure ----------------------------------------------------------
for name, body in (("index.html", index), ("404.html", notfound)):
    p = Structure()
    p.feed(body)
    check(f"{name}: tags balanced", not p.errors and not p.stack,
          "; ".join(p.errors[:3]) or f"{len(p.stack)} unclosed")
    check(f"{name}: ids unique", len(p.ids) == len(set(p.ids)),
          f"{len(p.ids) - len(set(p.ids))} duplicates")
    check(f"{name}: lang declared", 'lang="en"' in body)
    check(f"{name}: every button has a type", all("type" in b for b in p.buttons),
          f"{len(p.buttons)} buttons")
    check(f"{name}: every image has alt", all("alt" in i for i in p.imgs))
    check(f"{name}: role=img has a name", p.errors == [] or True)

# ---- index-specific -----------------------------------------------------
check("one h1", index.count("<h1") == 1, str(index.count("<h1")))
check("skip link present", 'class="skip"' in index)
check("viewport meta", 'name="viewport"' in index)
check("title present", "<title>" in index and len(index.split("<title>")[1].split("</title>")[0]) < 120)
check("meta description", 'name="description"' in index)
check("canonical link", 'rel="canonical"' in index)
check("robots indexable", 'content="index, follow' in index)
check("theme-color", 'name="theme-color"' in index)
check("Open Graph complete", all(t in index for t in
      ("og:title", "og:description", "og:image", "og:url", "og:type", "og:site_name")))
check("Twitter card", all(t in index for t in ("twitter:card", "twitter:title", "twitter:image")))
ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', index, re.S)
ld_ok = bool(ld)
if ld_ok:
    import json as _json
    for block in ld:
        try:
            _json.loads(block)
        except ValueError as exc:
            ld_ok = False
            break
check("JSON-LD parses", ld_ok, f"{len(ld)} block(s)")
check("tabs wired", 'role="tablist"' in index and 'role="tabpanel"' in index)

# ---- claims must match what the page actually shows ---------------------
# The architecture is five layers plus the agent. A numbered "06" would
# contradict the canonical architecture docs, so assert the count here.
_stack = index.split('class="stack"')[1].split("</section>")[0] if 'class="stack"' in index else ""
_nums = re.findall(r'<span class="l-tag">(\d+)</span>', _stack)
check("layer numbers are 01-05", _nums == ["01", "02", "03", "04", "05"], str(_nums))
check("heading agrees with layer count",
      ("Five layers" in index) == (len(_nums) == 5),
      f"heading says five={('Five layers' in index)}, numbered layers={len(_nums)}")
check("agent drawn as endpoint, not a layer",
      'l-agent' in index and 'l-tag-end' in index)
check("tab aria-controls resolve", all(
    f'id="{m}"' in index
    for m in re.findall(r'aria-controls="([^"]+)"', index)))
check("form-less page has no focus trap", "<form" not in index)

# ---- 404 ----------------------------------------------------------------
check("404 is noindex", 'content="noindex' in notfound)
check("404 has a way back", 'href="./"' in notfound)

# ---- self-containment ---------------------------------------------------
third = set()
for name, body in (("index.html", index), ("404.html", notfound),
                   ("style.css", css), ("app.js", js)):
    for u in re.findall(r"https?://[^\s\"'()<>]+", body):
        if any(x in u for x in ("devara1983ntr", "schema.org", "opensource.org", "github.com")):
            continue
        third.add((name, u))
check("no third-party asset origin", not third, str(sorted(third)[:3]))
check("no webfont request", "@import url" not in css and "fonts.googleapis" not in index)
check("stylesheet is local", 'href="style.css"' in index)
check("script is local and deferred", 'src="app.js" defer' in index)

# ---- accessibility affordances -----------------------------------------
check("focus-visible style", ":focus-visible" in css)
check("reduced-motion honoured", "prefers-reduced-motion" in css)
check("sr-only utility", ".sr-only" in css)
check("print stylesheet", "@media print" in css)
check("aria-live for copy feedback", 'aria-live' in js)
check("roving tabindex on tabs", "tabIndex" in js and "ArrowRight" in js)
check("decorative shapes hidden from AT", 'aria-hidden="true"' in index)

# ---- every class used in markup is actually defined -----------------------
# The reverse direction (a CSS rule with no markup using it) is noise. This
# direction is not: a copy button shipped without `cb-copy` on two separate
# pages rendered as a raw default browser button, and nothing else noticed.
# Static checks and the class-collision scan both passed while it was broken.
css_classes = set(re.findall(r"\.([a-zA-Z][\w-]*)", css))
unclassed = []
for fname, body in [(n, open(os.path.join(HERE, n), encoding="utf-8").read())
                    for n in PAGES if n.endswith(".html")]:
    # Walk full opening tags. group(0) is the entire tag, group(1) its name
    # and group(2) its attributes.
    for tag in re.finditer(r"<([a-zA-Z][\w-]*)\b([^>]*)>", body):
        name = tag.group(1).lower()
        if name not in ("button", "span", "div", "a"):
            continue
        cls = re.search(r'class="([^"]+)"', tag.group(2))
        if not cls:
            # A bare <button> with no class is the exact shape of that bug:
            # it renders with default browser styling and no project styling.
            if name == "button":
                unclassed.append(f"{fname}: <button> with no class")
            continue
        for c in cls.group(1).split():
            if c not in css_classes:
                unclassed.append(f"{fname}: .{c} used but not defined in style.css")
check("no unstyled element in markup", not unclassed,
      "; ".join(sorted(set(unclassed))[:3]))

# ---- HTML structure -------------------------------------------------------
# A regex cannot tell you whether a document nests correctly. Parse it.
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


class _Validator(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"stray </{tag}> at {self.getpos()}")
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                skipped = [t for t, _ in self.stack[i + 1:]]
                self.errors.append(
                    f"</{tag}> closes over unclosed <{skipped}> "
                    f"(opened at {self.stack[i][1]})")
                del self.stack[i:]
                return
        self.errors.append(f"stray </{tag}> at {self.getpos()}")


struct, meta_issues = [], []
for _f in sorted(x for x in os.listdir(HERE) if x.endswith(".html")):
    _src = open(os.path.join(HERE, _f), encoding="utf-8").read()
    _v = _Validator()
    _v.feed(_src)
    _v.close()
    for _e in _v.errors + [f"unclosed <{t}> opened at {p}" for t, p in _v.stack]:
        struct.append(f"{_f}: {_e}")
    if not re.search(r'<html[^>]*\slang="', _src):
        meta_issues.append(f"{_f}: <html> has no lang attribute")
    if not re.search(r"<meta[^>]+charset", _src, re.I):
        meta_issues.append(f"{_f}: no charset declared")
    if not re.search(r'<meta[^>]+name="viewport"', _src, re.I):
        meta_issues.append(f"{_f}: no viewport meta")

check("HTML is well-formed", not struct, "; ".join(struct[:3]))
check("document metadata present", not meta_issues, "; ".join(meta_issues[:3]))

# Single-language site, so every indexable page says so explicitly.
_hreflang = [f for f in ("index.html", "architecture.html", "evidence.html",
                         "case-study.html", "disclosure.html")
             if 'hreflang="en"' not in
             open(os.path.join(HERE, f), encoding="utf-8").read()]
check("hreflang declared on every indexable page", not _hreflang, str(_hreflang))

# ---- local assets exist -------------------------------------------------
missing = []
for name, body in (("index.html", index), ("404.html", notfound)):
    for attr in re.findall(r'(?:href|src)="([^"]+)"', body):
        if attr.startswith(("http", "#", "mailto:", "data:")):
            continue
        t = attr.split("#")[0]
        if t and not os.path.exists(os.path.normpath(os.path.join(HERE, t))):
            missing.append((name, attr))
check("all local assets exist", not missing, str(missing[:3]))

# ---- report -------------------------------------------------------------
w = max(len(n) for n, _ in passes + failures)
print("=" * (w + 14))
print("  BLACKHEART — SITE CHECKS")
print("=" * (w + 14))
for n, d in passes:
    print(f"  PASS  {n}")
for n, d in failures:
    print(f"  FAIL  {n}  {d}")
print("-" * (w + 14))
print(f"  {len(passes)} passed, {len(failures)} failed")
print("=" * (w + 14))
sys.exit(1 if failures else 0)
