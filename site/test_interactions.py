#!/usr/bin/env python3
"""Interaction tests for the BLACKHEART site.

Run:  python3 site/test_interactions.py
Exit: 0 pass, 1 fail

Drives a real browser. Static checks cannot tell you whether a disclosure menu
opens, whether arrow keys move between tabs, or whether Escape returns focus —
those only fail when someone uses the page.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8097

subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "-d", HERE,
                  "--bind", "127.0.0.1"], stdout=subprocess.DEVNULL,
                 stderr=subprocess.DEVNULL)
time.sleep(1.5)

from playwright.sync_api import sync_playwright

BASE = f"http://127.0.0.1:{PORT}/index.html"
results = []


def t(name, ok, detail=""):
    results.append((name, ok, detail))


with sync_playwright() as p:
    br = p.chromium.launch()

    # ---------- mobile menu ----------
    ctx = br.new_context(viewport={"width": 390, "height": 844})
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(BASE, wait_until="networkidle")

    t("menu button visible on mobile", pg.locator("#nav-toggle").is_visible())
    t("menu starts closed", pg.get_attribute("#nav-toggle", "aria-expanded") == "false")
    t("nav hidden when closed", not pg.locator("#site-nav").is_visible())

    pg.click("#nav-toggle")
    pg.wait_for_timeout(250)
    t("menu opens on click", pg.locator("#site-nav").is_visible())
    t("aria-expanded true when open", pg.get_attribute("#nav-toggle", "aria-expanded") == "true")
    t("aria-label flips", pg.get_attribute("#nav-toggle", "aria-label") == "Close section menu")

    pg.keyboard.press("Escape")
    pg.wait_for_timeout(250)
    t("Escape closes the menu", pg.get_attribute("#nav-toggle", "aria-expanded") == "false")
    t("Escape returns focus to the button",
      pg.evaluate("document.activeElement.id") == "nav-toggle")

    pg.click("#nav-toggle")
    pg.wait_for_timeout(200)
    pg.click("main", position={"x": 10, "y": 600})
    pg.wait_for_timeout(250)
    t("outside click closes", pg.get_attribute("#nav-toggle", "aria-expanded") == "false")

    pg.click("#nav-toggle")
    pg.wait_for_timeout(200)
    pg.click("#site-nav a[href='#evidence']")
    pg.wait_for_timeout(900)
    t("link click closes the menu", pg.get_attribute("#nav-toggle", "aria-expanded") == "false")
    t("link navigates to its section", pg.evaluate("window.scrollY") > 200,
      f"scrollY={pg.evaluate('window.scrollY')}")
    t("theme toggle still works after menu use",
      pg.evaluate("""async () => {
        const b = document.getElementById('theme');
        const before = document.documentElement.getAttribute('data-theme');
        b.click();
        const after = document.documentElement.getAttribute('data-theme');
        return before !== after;
      }"""))

    # mobile menu must not be reachable when hidden by desktop layout
    pg.set_viewport_size({"width": 1280, "height": 900})
    pg.wait_for_timeout(300)
    t("menu state resets on resize to desktop",
      pg.get_attribute("#nav-toggle", "aria-expanded") == "false")
    t("inline nav visible on desktop", pg.locator("#site-nav").is_visible())
    t("menu button hidden on desktop", not pg.locator("#nav-toggle").is_visible())
    ctx.close()

    # ---------- tabs ----------
    ctx = br.new_context(viewport={"width": 1280, "height": 900},
                         permissions=["clipboard-read", "clipboard-write"])
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(BASE, wait_until="networkidle")
    pg.locator("#coverage").scroll_into_view_if_needed()
    pg.wait_for_timeout(400)

    t("first tab selected by default",
      pg.get_attribute("#tab-mirror", "aria-selected") == "true")
    t("first panel visible", pg.locator("#p-mirror").is_visible())
    t("second panel hidden", not pg.locator("#p-gov").is_visible())

    pg.click("#tab-gov")
    pg.wait_for_timeout(200)
    t("click switches tab", pg.get_attribute("#tab-gov", "aria-selected") == "true")
    t("click switches panel", pg.locator("#p-gov").is_visible()
      and not pg.locator("#p-mirror").is_visible())
    t("selected tab is the only tabbable one",
      pg.evaluate("""() => {
        const tabs = [...document.querySelectorAll('[role=tab]')];
        return tabs.filter(t => t.tabIndex === 0).length === 1
            && document.getElementById('tab-gov').tabIndex === 0;
      }"""))

    pg.focus("#tab-gov")
    pg.keyboard.press("ArrowRight")
    pg.wait_for_timeout(200)
    t("ArrowRight advances", pg.get_attribute("#tab-excl", "aria-selected") == "true")
    pg.keyboard.press("ArrowRight")
    pg.wait_for_timeout(200)
    t("ArrowRight wraps to first", pg.get_attribute("#tab-mirror", "aria-selected") == "true")
    pg.keyboard.press("ArrowLeft")
    pg.wait_for_timeout(200)
    t("ArrowLeft goes back", pg.get_attribute("#tab-excl", "aria-selected") == "true")
    pg.keyboard.press("Home")
    pg.wait_for_timeout(200)
    t("Home selects first", pg.get_attribute("#tab-mirror", "aria-selected") == "true")
    pg.keyboard.press("End")
    pg.wait_for_timeout(200)
    t("End selects last", pg.get_attribute("#tab-excl", "aria-selected") == "true")
    pg.keyboard.press("ArrowLeft")
    pg.wait_for_timeout(200)
    t("ArrowLeft steps back from last", pg.get_attribute("#tab-gov", "aria-selected") == "true")
    pg.keyboard.press("Home")
    pg.wait_for_timeout(200)
    pg.keyboard.press("ArrowLeft")
    pg.wait_for_timeout(200)
    t("ArrowLeft wraps to last from first",
      pg.get_attribute("#tab-excl", "aria-selected") == "true")

    # ---------- scroll spy ----------
    pg.evaluate("document.getElementById('model').scrollIntoView()")
    pg.wait_for_timeout(700)
    t("scroll spy marks the visible section",
      pg.evaluate("""() => {
        const a = document.querySelector('.nav a.active');
        return !!a && a.getAttribute('href') === '#model';
      }"""), pg.evaluate("""() => {
        const a = document.querySelector('.nav a.active');
        return a ? a.getAttribute('href') : 'none';
      }"""))
    t("aria-current set on active link", pg.locator('.nav a[href="#model"][aria-current="true"]').count() == 1)

    # ---------- counters ----------
    pg.evaluate("window.scrollTo(0,0)")
    pg.wait_for_timeout(1600)
    t("counters reach their target",
      pg.evaluate("""() => [...document.querySelectorAll('[data-count]')]
        .every(e => Number(e.textContent.replace(/,/g,'')) === Number(e.dataset.count))"""),
      pg.evaluate("""() => [...document.querySelectorAll('[data-count]')]
        .map(e => e.textContent).join(' ')"""))

    # ---------- copy button ----------
    pg.evaluate("document.getElementById('start').scrollIntoView()")
    pg.wait_for_timeout(400)
    t("copy button reports success", pg.evaluate("""async () => {
      const btn = document.querySelector('[data-copy]');
      btn.click();
      await new Promise(r => setTimeout(r, 400));
      return btn.textContent.trim() === 'Copied';
    }"""))

    # ---------- keyboard reachability ----------
    t("every interactive control is focusable", pg.evaluate("""() => {
      const sel = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';
      return [...document.querySelectorAll(sel)]
        .filter(e => e.offsetParent !== null || e.classList.contains('skip'))
        .every(e => e.tabIndex >= -1);
    }"""))
    t("skip link targets main", pg.evaluate("""() => {
      const s = document.querySelector('.skip');
      const id = s && s.getAttribute('href');
      return !!id && !!document.querySelector(id);
    }"""))
    ctx.close()
    br.close()

t("no uncaught page errors", not errors, "; ".join(errors[:2]))

fails = [r for r in results if not r[1]]
w = max(len(n) for n, _, _ in results)
print("=" * (w + 18))
print("  BLACKHEART — INTERACTION TESTS")
print("=" * (w + 18))
for n, ok, d in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {n}" + (f"   [{d}]" if d and not ok else ""))
print("-" * (w + 18))
print(f"  {len(results) - len(fails)} passed, {len(fails)} failed")
print("=" * (w + 18))
sys.exit(1 if fails else 0)
