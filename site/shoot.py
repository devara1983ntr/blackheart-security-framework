#!/usr/bin/env python3
"""Screenshot the site so the design can actually be looked at.

Run:  python3 site/shoot.py [outdir]

Captures each viewport-sized section by scrolling the way a reader does, rather
than one tall full-page image. A full-page shot is misleading here: the scroll
reveal never fires for content below the fold, so the page looks emptier than
it is.
"""
import os
import subprocess
import sys
import time

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/shots"
os.makedirs(OUT, exist_ok=True)
PORT = 8099

subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "-d", "site",
                  "--bind", "127.0.0.1"], stdout=subprocess.DEVNULL,
                 stderr=subprocess.DEVNULL)
time.sleep(1.5)

from playwright.sync_api import sync_playwright

BASE = f"http://127.0.0.1:{PORT}"

SECTIONS = ["problem", "model", "coverage", "evidence", "casestudy", "verify", "start", "use"]

VIEWS = [
    ("desktop", "index.html", 1440, 900, "dark", 1),
    ("desktop-light", "index.html", 1440, 900, "light", 1),
    ("tablet", "index.html", 820, 1100, "dark", 1),
    ("mobile", "index.html", 390, 844, "dark", 2),
]

errors = []
with sync_playwright() as p:
    br = p.chromium.launch()
    for name, page, w, h, theme, dsf in VIEWS:
        ctx = br.new_context(viewport={"width": w, "height": h},
                             device_scale_factor=dsf)
        pg = ctx.new_page()
        pg.on("console", lambda m: errors.append(f"{m.type}: {m.text}")
              if m.type == "error" else None)
        pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        pg.goto(f"{BASE}/{page}", wait_until="networkidle")
        pg.evaluate("t => { localStorage.setItem('bh-theme', t);"
                    "document.documentElement.setAttribute('data-theme', t); }", theme)
        pg.wait_for_timeout(600)

        # hero
        pg.screenshot(path=os.path.join(OUT, f"{name}-0-hero.png"))
        # each section, scrolled into view so reveals fire naturally
        for i, sec in enumerate(SECTIONS, start=1):
            if pg.query_selector(f"#{sec}") is None:
                continue
            pg.evaluate(f"""() => {{
                const el = document.getElementById('{sec}');
                el.scrollIntoView({{behavior:'instant', block:'start'}});
            }}""")
            pg.wait_for_timeout(900)
            pg.screenshot(path=os.path.join(OUT, f"{name}-{i}-{sec}.png"))
        print(f"  {name}: {1 + len(SECTIONS)} shots")
        ctx.close()

    # 404
    ctx = br.new_context(viewport={"width": 1440, "height": 760})
    pg = ctx.new_page()
    pg.goto(f"{BASE}/404.html", wait_until="networkidle")
    pg.wait_for_timeout(400)
    pg.screenshot(path=os.path.join(OUT, "notfound.png"))
    ctx.close()
    br.close()

if errors:
    print("\n  CONSOLE ERRORS:")
    for e in dict.fromkeys(errors):
        print("   ", e)
    sys.exit(1)
print("\n  no console errors")
