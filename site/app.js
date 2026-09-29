/* ═══════════════════════════════════════════════════════════════
   BLACKHEART — interaction
   No dependencies, no network. Progressive enhancement throughout:
   every feature degrades to plain, readable HTML if this fails.
   ═══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── error state ──────────────────────────────────────────
     The site is static and has nothing to fetch, so the only way it
     fails at runtime is a script error or a lost stylesheet. If that
     happens the reader gets a plain page with no explanation, which
     reads as "this site is broken and unhelpful" rather than "one
     enhancement failed". Say it instead. */
  var banner = null;
  function showError(msg) {
    if (!banner) {
      banner = document.createElement('div');
      banner.className = 'banner';
      banner.setAttribute('role', 'status');
      banner.setAttribute('aria-live', 'polite');
      banner.innerHTML =
        '<span><b>Partial failure.</b> <span class="js-err"></span> ' +
        'The page content below is complete and readable — an interactive ' +
        'enhancement did not run.</span>' +
        '<button type="button" class="btn btn-sm">Dismiss</button>';
      document.body.appendChild(banner);
      banner.querySelector('.js-err').textContent = msg;
      banner.querySelector('button').addEventListener('click', function () {
        banner.classList.remove('on');
      });
    }
    banner.classList.add('on');
  }
  window.addEventListener('error', function (e) {
    if (e && e.target && e.target !== window && e.target.tagName === 'LINK') {
      showError('A stylesheet failed to load, so the page is unstyled.');
    }
  });
  window.addEventListener('unhandledrejection', function () {
    showError('A deferred operation failed.');
  });

  // Everything below is an enhancement. If any part of it throws, the page is
  // still complete and readable, so say what failed rather than going quiet.
  try {

  /* ── theme ────────────────────────────────────────────────── */
  var KEY = 'bh-theme';
  var root = document.documentElement;
  var btn = document.getElementById('theme');

  function apply(t) {
    root.setAttribute('data-theme', t);
    if (btn) btn.setAttribute('aria-label', t === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
  }
  function stored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function preferred() {
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }
  apply(stored() || preferred());

  if (btn) {
    btn.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      apply(next);
      try { localStorage.setItem(KEY, next); } catch (e) { /* private mode */ }
    });
  }

  /* ── sticky header shadow ─────────────────────────────────── */
  var head = document.querySelector('.site-head');
  if (head) {
    var onScroll = function () {
      head.classList.toggle('stuck', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ── scroll reveal ────────────────────────────────────────── */
  var revealables = document.querySelectorAll(
    '.hero-stats, .layer, .flow, .card, .callout, .rule, .rungs, ' +
    '.finding, .gate, .canaries, .codeblock, .promises, .tabpanel, .foot-in'
  );
  if (revealables.length) {
    if (reduceMotion || !('IntersectionObserver' in window)) {
      revealables.forEach(function (el) { el.classList.add('in'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          var el = e.target;
          var delay = Number(el.dataset.reveal || 0);
          setTimeout(function () { el.classList.add('in'); }, delay);
          io.unobserve(el);
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
      revealables.forEach(function (el, i) {
        el.classList.add('reveal');
        el.dataset.reveal = String((i % 4) * 70);
        io.observe(el);
      });
    }
  }

  /* ── animated counters ────────────────────────────────────── */
  var counters = document.querySelectorAll('[data-count]');
  if (counters.length) {
    var fmt = function (n) { return n.toLocaleString('en-US'); };
    if (reduceMotion || !('IntersectionObserver' in window)) {
      counters.forEach(function (el) { el.textContent = fmt(Number(el.dataset.count)); });
    } else {
      var cio = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          var el = e.target, target = Number(el.dataset.count), t0 = null, dur = 1100;
          var step = function (ts) {
            if (t0 === null) t0 = ts;
            var p = Math.min((ts - t0) / dur, 1);
            var eased = 1 - Math.pow(1 - p, 3);
            el.textContent = fmt(Math.round(target * eased));
            if (p < 1) requestAnimationFrame(step);
          };
          requestAnimationFrame(step);
          cio.unobserve(el);
        });
      }, { threshold: 0.5 });
      counters.forEach(function (el) { el.textContent = '0'; cio.observe(el); });
    }
  }

  /* ── tabs (roving tabindex, arrow keys) ───────────────────── */
  var tablist = document.querySelector('[role="tablist"]');
  if (tablist) {
    var tabs = Array.prototype.slice.call(tablist.querySelectorAll('[role="tab"]'));

    var select = function (tab, focus) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute('aria-selected', String(on));
        t.tabIndex = on ? 0 : -1;
        var panel = document.getElementById(t.getAttribute('aria-controls'));
        if (panel) panel.hidden = !on;
      });
      if (focus) tab.focus();
    };

    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () { select(tab, false); });
      tab.addEventListener('keydown', function (ev) {
        var next = null;
        if (ev.key === 'ArrowRight') next = tabs[(i + 1) % tabs.length];
        else if (ev.key === 'ArrowLeft') next = tabs[(i - 1 + tabs.length) % tabs.length];
        else if (ev.key === 'Home') next = tabs[0];
        else if (ev.key === 'End') next = tabs[tabs.length - 1];
        if (next) { ev.preventDefault(); select(next, true); }
      });
    });
  }

  /* ── copy to clipboard ────────────────────────────────────── */
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    var block = btn.closest('.codeblock');
    var code = block && block.querySelector('pre');
    if (!code) return;
    var label = btn.textContent;
    var status = document.createElement('span');
    status.className = 'sr-only';
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    btn.after(status);

    btn.addEventListener('click', function () {
      var text = code.innerText.replace(/\s+$/, '');
      var done = function (ok) {
        btn.textContent = ok ? 'Copied' : 'Press ⌘C';
        btn.classList.toggle('ok', ok);
        status.textContent = ok ? 'Command copied to clipboard' : 'Copy failed — select the text manually';
        setTimeout(function () {
          btn.textContent = label;
          btn.classList.remove('ok');
        }, 1800);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); });
      } else {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly', '');
        ta.style.cssText = 'position:fixed;top:-1000px;opacity:0';
        document.body.appendChild(ta);
        ta.select();
        var ok = false;
        try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
        document.body.removeChild(ta);
        done(ok);
      }
    });
  });

  /* ── scroll progress + back to top ───────────────────────── */
  var bar = document.createElement('div');
  bar.className = 'progress';
  bar.setAttribute('aria-hidden', 'true');
  bar.hidden = true;
  document.body.appendChild(bar);

  var toTop = document.createElement('button');
  toTop.className = 'to-top';
  toTop.type = 'button';
  toTop.setAttribute('aria-label', 'Back to top');
  toTop.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" ' +
    'aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>';
  document.body.appendChild(toTop);
  toTop.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
  });

  var ticking = false;
  function onScrollProgress() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    var pct = max > 0 ? (h.scrollTop / max) * 100 : 0;
    bar.hidden = pct < 1;
    bar.style.width = pct + '%';
    toTop.classList.toggle('on', h.scrollTop > h.clientHeight * 0.8);
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(onScrollProgress);
  }, { passive: true });
  onScrollProgress();

  /* ── mobile section menu ──────────────────────────────────── */
  var navToggle = document.getElementById('nav-toggle');
  if (head && navToggle) {
    var setMenu = function (open) {
      head.classList.toggle('menu-open', open);
      navToggle.setAttribute('aria-expanded', String(open));
      navToggle.setAttribute('aria-label', open ? 'Close section menu' : 'Open section menu');
    };
    navToggle.addEventListener('click', function () {
      setMenu(navToggle.getAttribute('aria-expanded') !== 'true');
    });
    // Escape closes and returns focus to the control that opened it.
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && head.classList.contains('menu-open')) {
        setMenu(false);
        navToggle.focus();
      }
    });
    // A tap outside dismisses. A tap on another header control does not,
    // otherwise the menu closes before the theme button's own handler is
    // observable, which reads as a broken click.
    document.addEventListener('click', function (ev) {
      if (!head.classList.contains('menu-open')) return;
      if (head.contains(ev.target)) return;
      setMenu(false);
    });
    head.querySelectorAll('.nav a').forEach(function (a) {
      a.addEventListener('click', function () { setMenu(false); });
    });
    // Returning to the desktop layout must not leave the page in the
    // open state, because the inline nav ignores the class there.
    window.matchMedia('(min-width: 56.001rem)').addEventListener('change', function (ev) {
      if (ev.matches) setMenu(false);
    });
  }

  /* ── nav active section ───────────────────────────────────── */
  // On a subpage the nav links point at other documents ("./",
  // "architecture.html"), not at fragments. Those are not valid CSS
  // selectors, and feeding one to querySelector throws -- which used to take
  // down the rest of this script on every deep page. Resolve fragments with
  // getElementById and ignore anything that is not a fragment.
  var links = Array.prototype.slice.call(document.querySelectorAll('.nav a'));
  var targets = links
    .map(function (a) {
      var href = a.getAttribute('href') || '';
      if (href.charAt(0) !== '#' || href.length < 2) return null;
      return document.getElementById(href.slice(1));
    })
    .filter(Boolean);

  if (targets.length && 'IntersectionObserver' in window) {
    var visible = new Map();
    var nio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { visible.set(e.target.id, e.isIntersecting ? e.intersectionRatio : 0); });
      var best = null, bestRatio = 0;
      visible.forEach(function (ratio, id) {
        if (ratio > bestRatio) { bestRatio = ratio; best = id; }
      });
      links.forEach(function (a) {
        var on = best !== null && a.getAttribute('href') === '#' + best;
        a.classList.toggle('active', on);
        if (on) a.setAttribute('aria-current', 'true');
        else a.removeAttribute('aria-current');
      });
    }, { rootMargin: '-20% 0px -55% 0px', threshold: [0, 0.25, 0.6, 1] });
    targets.forEach(function (t) { nio.observe(t); });
  }
  } catch (err) {
    if (window.console && console.error) console.error(err);
    showError('Some interactive behaviour is unavailable on this page.');
  }
})();
