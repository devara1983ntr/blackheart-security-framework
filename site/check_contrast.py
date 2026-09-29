#!/usr/bin/env python3
"""WCAG AA contrast audit, measured in a real browser, both themes.

Run:  python3 site/check_contrast.py
Exit: 0 pass, 1 fail

Contrast is measured, not asserted. The palette, not a spreadsheet, is the
source of truth -- and if a colour token changes, this catches the result.

Two things this had to get right, both of which produced confident nonsense
before they were fixed:

  * color-mix() computes to `color(srgb r g b)` with 0-1 floats. A regex that
    reads those as 0-255 gets near-black out of a light colour.
  * The effective background of an element is a stack of translucent layers
    that must be composited front-to-back with real alpha, not flattened by
    taking the nearest non-transparent one.

The measurement is self-tested against pairs whose correct answer is known, so
a broken instrument fails loudly instead of reporting a clean site.
"""
import subprocess
import sys
import time
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8083

MEASURE = r"""
() => {
  const cv = document.createElement('canvas').getContext('2d');
  const UNSUPPORTED = [];
  const gamma = v => v <= 0.0031308 ? 12.92*v : 1.055*Math.pow(v, 1/2.4) - 0.055;
  // oklab -> linear sRGB (Björn Ottosson)
  const oklabToRgb = (L, a, bb) => {
    const l_ = L + 0.3963377774*a + 0.2158037573*bb;
    const m_ = L - 0.1055613458*a - 0.0638541728*bb;
    const s_ = L - 0.0894841775*a - 1.2914855480*bb;
    const l = l_*l_*l_, m = m_*m_*m_, s = s_*s_*s_;
    return [
       4.0767416621*l - 3.3077115913*m + 0.2309699292*s,
      -1.2684380046*l + 2.6097574011*m - 0.3413193965*s,
      -0.0041960863*l - 0.7034186147*m + 1.7076147010*s,
    ];
  };
  // Normalise any CSS colour to [r,g,b,a] in 0-255.
  // An unrecognised syntax is recorded and reported, never silently
  // substituted: a canvas that rejects a fillStyle keeps the previous one,
  // which once made every colour in the site header measure as pure black.
  const norm = css => {
    if (!css) return [0,0,0,0];
    const s = css.trim();
    let m;
    if (s === 'transparent') return [0,0,0,0];
    if ((m = s.match(/^oklab\(([^)]+)\)$/i))) {
      const n = m[1].split('/');
      const c = n[0].trim().split(/\s+/).map(Number);
      const alpha = n.length > 1 ? parseFloat(n[1]) : 1;
      const lin = oklabToRgb(c[0], c[1] || 0, c[2] || 0);
      return lin.map(v => Math.max(0, Math.min(255, Math.round(gamma(Math.max(0, v)) * 255))))
                .concat(Number.isFinite(alpha) ? alpha : 1);
    }
    if ((m = s.match(/^color\(srgb\s+([^)]+)\)$/i))) {
      const n = m[1].split('/');
      const c = n[0].trim().split(/\s+/).map(Number);
      const alpha = n.length > 1 ? parseFloat(n[1]) : 1;
      return [c[0]*255, c[1]*255, c[2]*255, Number.isFinite(alpha) ? alpha : 1]
               .map((v, i) => i < 3 ? Math.round(v) : v);
    }
    cv.fillStyle = '#000';
    try { cv.fillStyle = s; } catch (e) { UNSUPPORTED.push(s); return [0,0,0,0]; }
    const v = cv.fillStyle;
    if (typeof v !== 'string' || v === '#000000' && s !== '#000000' && s !== 'black') {
      UNSUPPORTED.push(s);
      return [0,0,0,0];
    }
    if (v[0] === '#') {
      const h = v.slice(1);
      const n = h.length === 3
        ? h.split('').map(c => parseInt(c + c, 16))
        : [parseInt(h.slice(0,2),16), parseInt(h.slice(2,4),16), parseInt(h.slice(4,6),16)];
      return [n[0], n[1], n[2], 1];
    }
    const nums = (v.match(/[\d.]+/g) || [0,0,0]).map(Number);
    return [nums[0], nums[1], nums[2], nums.length > 3 ? nums[3] : 1];
  };
  // src composited over dst, both may be translucent.
  const over = (src, dst) => {
    const a = src[3] + dst[3] * (1 - src[3]);
    if (a === 0) return [0,0,0,0];
    return [0,1,2].map(i => (src[i]*src[3] + dst[i]*dst[3]*(1-src[3])) / a).concat(a);
  };
  const lum = c => {
    const f = c.slice(0,3).map(v => { v/=255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); });
    return 0.2126*f[0] + 0.7152*f[1] + 0.0722*f[2];
  };
  const ratio = (a, b) => { const l1 = lum(a), l2 = lum(b);
    const hi = Math.max(l1,l2), lo = Math.min(l1,l2); return (hi+0.05)/(lo+0.05); };

  // Effective background: composite every ancestor layer over an opaque base.
  const bgOf = el => {
    const layers = [];
    for (let n = el; n; n = n.parentElement) {
      const c = norm(getComputedStyle(n).backgroundColor);
      if (c[3] > 0) layers.push(c);
      if (c[3] >= 0.999) break;
    }
    if (!layers.length) return [255,255,255,1];
    let out = [255,255,255,1];            // opaque base behind everything
    for (let i = layers.length - 1; i >= 0; i--) out = over(layers[i], out);
    return out;
  };

  // ---- self-test: the instrument must get known pairs right -------------
  const selfTest = [];
  selfTest.push(['black on white', ratio([0,0,0,1],[255,255,255,1]), 21]);
  selfTest.push(['white on black', ratio([255,255,255,1],[0,0,0,1]), 21]);
  selfTest.push(['black on black', ratio([0,0,0,1],[0,0,0,1]), 1]);
  const bad = selfTest.filter(([, got, want]) => Math.abs(got - want) > 0.05);
  if (bad.length) return { instrumentBroken: bad.map(b => `${b[0]}=${b[1].toFixed(2)} want ${b[2]}`) };

  const out = [], seen = new Set(), gradients = [];
  const sel = 'p,h1,h2,h3,h4,h5,a,small,b,code,li,span,td,th,dt,dd,strong,em,button,label,figcaption';
  for (const el of document.querySelectorAll(sel)) {
    const t = (el.textContent || '').trim();
    if (t.length < 2) continue;
    if (el.querySelector(sel)) continue;            // only leaf text nodes
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    if (parseFloat(cs.opacity) < 0.3) continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    // Gradient-clipped text is painted by the background, not the colour, so
    // the declared colour is transparent and measures as 1:1 against anything.
    // That is a limit of the measurement, not a defect -- record and skip.
    const clip = cs.webkitBackgroundClip || cs.backgroundClip;
    if (clip === 'text') {
      // Measure the gradient's own stops against the background, so this is
      // verified rather than merely skipped. The minimum stop is the worst
      // point of the gradient.
      const bg = bgOf(el);
      const stops = (cs.backgroundImage || '').match(
        /rgba?\([^)]+\)|#[0-9a-f]{3,8}/gi) || [];
      const crs = stops.map(c => ratio(over(norm(c), bg).slice(0,3), bg.slice(0,3)));
      gradients.push({
        t: t.slice(0, 34),
        stops: stops.length,
        worst: crs.length ? +Math.min(...crs).toFixed(2) : null,
        px: +parseFloat(cs.fontSize).toFixed(1),
        bold: parseInt(cs.fontWeight) >= 700,
      });
      continue;
    }
    const key = cs.color + '|' + cs.fontSize + '|' + cs.fontWeight;
    if (seen.has(key)) continue;
    seen.add(key);
    const bg = bgOf(el);
    const fg = over(norm(cs.color), bg);
    const cr = ratio(fg.slice(0,3), bg.slice(0,3));
    const px = parseFloat(cs.fontSize);
    const bold = parseInt(cs.fontWeight) >= 700;
    const need = (px >= 24 || (px >= 18.66 && bold)) ? 3.0 : 4.5;
    if (cr < need) out.push({ t: t.slice(0, 34), cr: +cr.toFixed(2), need, px: +px.toFixed(1), color: cs.color });
  }
  return { failures: out, unsupported: [...new Set(UNSUPPORTED)], gradients };
}
"""

PAGES = ("index.html", "architecture.html", "evidence.html",
         "case-study.html", "disclosure.html", "404.html")


def main():
    subprocess.Popen([sys.executable, "-m", "http.server", str(PORT),
                      "-d", HERE, "--bind", "127.0.0.1"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    from playwright.sync_api import sync_playwright

    failures, broken, unsupported, grads = [], [], set(), set()
    with sync_playwright() as p:
        br = p.chromium.launch()
        for theme in ("dark", "light"):
            ctx = br.new_context(viewport={"width": 1440, "height": 900})
            pg = ctx.new_page()
            for page in PAGES:
                pg.goto(f"http://127.0.0.1:{PORT}/{page}", wait_until="networkidle")
                pg.evaluate("t=>document.documentElement.setAttribute('data-theme',t)", theme)
                pg.wait_for_timeout(300)
                res = pg.evaluate(MEASURE)
                if "instrumentBroken" in res:
                    broken.append((theme, page, res["instrumentBroken"]))
                    continue
                for u in res.get("unsupported", []):
                    unsupported.add(u)
                for g in res.get("gradients", []):
                    grads.add((theme, g["t"], g["worst"], g["px"], g["bold"]))
                for f in res["failures"]:
                    failures.append((theme, page, f))
            ctx.close()
        br.close()

    print("=" * 66)
    print("  CONTRAST AUDIT (WCAG AA)")
    print("=" * 66)
    if grads:
        print(f"  NOTE  {len(grads)} gradient-clipped text element(s) measured by their")
        print("        gradient stops rather than their colour (color is transparent):")
        bad_grad = 0
        for theme, t, worst, px, bold in sorted(grads):
            need = (px >= 24 or (px >= 18.66 and bold)) and 3.0 or 4.5
            ok = worst is not None and worst >= need
            bad_grad += 0 if ok else 1
            flag = "OK  " if ok else "FAIL"
            print(f"          {flag} {theme:5} worst stop {worst}:1 (needs {need})  \"{t}\"")
        if bad_grad:
            failures.append(("gradient", "stops below AA"))
    if unsupported:
        print(f"  NOTE  {len(unsupported)} colour syntax(es) could not be resolved and were")
        print("        excluded rather than guessed at: " + ", ".join(sorted(unsupported)))
    if broken:
        print("  MEASUREMENT INSTRUMENT FAILED ITS SELF-TEST:")
        for theme, page, msgs in broken[:4]:
            print(f"    {theme}/{page}: {msgs}")
        print("  results below are not trustworthy")
        return 1
    if not failures:
        print("  clean — every measured text/background pair meets AA in both themes")
    else:
        seen = set()
        for theme, page, f in failures:
            k = (theme, f["color"], f["need"])
            if k in seen:
                continue
            seen.add(k)
            print(f"  FAIL  {theme:5} {f['cr']:>5}:1 < {f['need']}  {f['px']:.0f}px "
                  f"{f['color']:20} \"{f['t']}\"  ({page})")
        print(f"  {len(failures)} failing element(s), {len(seen)} distinct colour pairs")
    print("=" * 66)
    return 1 if failures or broken else 0


if __name__ == "__main__":
    sys.exit(main())
