# Site extraction snippets

Run each snippet with the Playwright MCP `browser_evaluate` tool (pass it as the `function`), after `browser_navigate` and `browser_wait_for` has let the page settle. They only read the DOM and computed styles; they never click, type or submit. Run snippet A once per viewport (375, 768, 1440) and keep the three results.

The results are raw evidence for `/rspec:site`. Colours come back as hex (`#rrggbb`, or `#rrggbbaa` when translucent); a radius of `9999px` or more (the browser may print `1.67772e+07px`) means a pill shape. Section and component entries carry no page text, only lengths. Still, do not commit the raw results: turn them into tokens and descriptions, then delete them.

## A. Design tokens and layout

```js
() => {
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const all = [...document.querySelectorAll('body *')].filter(vis).slice(0, 4000);
  const cv = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const hex = c => { if (!c || !/(rgb|lab|lch|oklab|oklch|color|hsl)a?\(/.test(c)) return c; // any CSS colour -> #rrggbb[aa]
    let a = 1; const m = c.match(/\/\s*([\d.]+)(%?)\s*\)$/) || c.match(/^(?:rgba|hsla)\((?:[^,]+,){3}\s*([\d.]+)\)$/);
    if (m) { a = parseFloat(m[1]) / (m[2] === '%' ? 100 : 1); c = c.replace(/\s*\/\s*[\d.]+%?\s*\)$/, ')').replace(/^(rgb|hsl)a\(((?:[^,]+,){2}[^,]+),[^)]*\)/, '$1($2)'); }
    if (a === 0) return 'transparent';
    cv.fillStyle = '#000'; cv.fillStyle = c; cv.fillRect(0, 0, 1, 1); const [r, g, b] = cv.getImageData(0, 0, 1, 1).data;
    return '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('') + (a < 1 ? Math.round(a * 255).toString(16).padStart(2, '0') : ''); };
  const hexAll = str => str.replace(/(rgba?|lab|lch|oklab|oklch|hsla?|color)\([^()]*\)/g, hex);
  const count = (m, k) => { if (k && k !== 'none' && k !== 'normal' && k !== '0px' && k !== 'transparent') m[k] = (m[k] || 0) + 1; };
  const top = (m, n = 12) => Object.entries(m).sort((a, b) => b[1] - a[1]).slice(0, n);
  const color = {}, bg = {}, border = {}, radius = {}, shadow = {}, space = {}, fontFam = {}, sizes = {}, trans = {}, anim = {};
  for (const el of all) {
    const s = getComputedStyle(el);
    count(color, hex(s.color)); count(bg, hex(s.backgroundColor)); count(bg, s.backgroundImage.includes('gradient') ? hexAll(s.backgroundImage).slice(0, 160) : '');
    if (s.borderTopWidth !== '0px') count(border, `${s.borderTopWidth} ${s.borderTopStyle} ${hex(s.borderTopColor)}`);
    count(radius, s.borderTopLeftRadius); count(shadow, hexAll(s.boxShadow).replace(/transparent 0px 0px 0px 0px,? ?/g, '').replace(/,\s*$/, '').trim());
    for (const p of ['paddingTop', 'paddingLeft', 'marginTop', 'marginBottom', 'rowGap', 'columnGap']) count(space, s[p]);
    count(fontFam, s.fontFamily.split(',')[0].trim()); count(sizes, s.fontSize);
    if (s.transitionDuration !== '0s') count(trans, `${s.transitionProperty} ${s.transitionDuration} ${s.transitionTimingFunction}`);
    if (s.animationName !== 'none') count(anim, `${s.animationName} ${s.animationDuration} ${s.animationTimingFunction}`);
  }
  const typo = sel => { const el = [...document.querySelectorAll(sel)].find(vis); if (!el) return null; const s = getComputedStyle(el);
    return { sel, family: s.fontFamily, size: s.fontSize, weight: s.fontWeight, lineHeight: s.lineHeight, letterSpacing: s.letterSpacing,
      transform: s.textTransform, color: hex(s.color), chars: (el.textContent || '').trim().length }; };
  const box = sel => { const el = [...document.querySelectorAll(sel)].find(vis); if (!el) return null; const s = getComputedStyle(el); const r = el.getBoundingClientRect();
    return { sel, w: Math.round(r.width), h: Math.round(r.height), padding: s.padding, radius: s.borderRadius, bg: hex(s.backgroundColor),
      color: hex(s.color), border: hexAll(s.border), shadow: hexAll(s.boxShadow).replace(/transparent 0px 0px 0px 0px,? ?/g, '').replace(/,\s*$/, '').trim(), font: `${s.fontWeight} ${s.fontSize}/${s.lineHeight}`, transition: s.transition }; };
  let blocks = [...document.querySelectorAll('header, nav, main > *, section, footer')].filter(vis)
    .filter((el, i, arr) => !arr.some(o => o !== el && o.contains(el) && o.tagName !== 'MAIN'));
  if (blocks.length < 4) { // div-based page: descend into the child holding most headings, then take its tall children
    const hs = el => el.querySelectorAll('h1,h2,h3').length;
    let root = document.querySelector('main') || document.body;
    for (;;) { const best = [...root.children].filter(vis).sort((a, b) => hs(b) - hs(a))[0];
      if (!best || hs(best) <= 0.5 * hs(root)) break; root = best; }
    blocks = [...root.children].filter(vis).filter(k => k.getBoundingClientRect().height > 80); }
  const sections = blocks
    .map(el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); const inner = el.firstElementChild ? getComputedStyle(el.firstElementChild) : s;
      return { tag: el.tagName.toLowerCase(), top: Math.round(r.top + scrollY), h: Math.round(r.height), bg: hex(s.backgroundColor), bgImage: s.backgroundImage !== 'none',
        paddingY: `${s.paddingTop} ${s.paddingBottom}`, display: s.display, gridCols: s.gridTemplateColumns, innerMaxW: inner.maxWidth,
        headings: [...el.querySelectorAll('h1,h2,h3')].length, buttons: el.querySelectorAll('a[class*=btn],button,[role=button]').length,
        images: el.querySelectorAll('img,svg,video,canvas,picture').length, sticky: s.position }; });
  const media = new Set(); const walkMedia = rules => { for (const r of rules) { if (r.media) media.add(r.media.mediaText); if (r.cssRules) walkMedia(r.cssRules); } };
  for (const sh of document.styleSheets) { try { walkMedia(sh.cssRules); } catch (e) { /* cross-origin sheet */ } }
  const vars = {}; const walk = rules => { for (const r of rules) { if (r.cssRules) walk(r.cssRules);
    if (r.selectorText && /(^|,)\s*(:root|html)/.test(r.selectorText) && r.style)
      for (const p of r.style) if (p.startsWith('--') && !p.startsWith('--tw-') && !/^--color-[a-z]+-\d+$/.test(p)) vars[p] = r.style.getPropertyValue(p).trim(); } };
  for (const sh of document.styleSheets) { try { walk(sh.cssRules); } catch (e) { /* cross-origin sheet */ } }
  return {
    viewport: [innerWidth, innerHeight], pageHeight: document.documentElement.scrollHeight,
    colorScheme: getComputedStyle(document.documentElement).colorScheme,
    body: typo('body'), type: ['h1', 'h2', 'h3', 'h4', 'p', 'a', 'small, .eyebrow, [class*=eyebrow], [class*=label]', 'li', 'blockquote', 'code'].map(typo).filter(Boolean),
    components: ['header', 'nav a', 'a[class*=btn], a[class*=button], button', '[class*=card]', 'input, textarea', '[class*=badge], [class*=pill], [class*=tag]', 'footer']
      .map(box).filter(Boolean),
    colors: top(color), backgrounds: top(bg), borders: top(border, 6), radii: top(radius, 8), shadows: top(shadow, 6),
    spacing: top(space, 20), fontFamilies: top(fontFam, 5), fontSizes: top(sizes, 14), transitions: top(trans, 8), animations: top(anim, 8),
    cssVars: Object.fromEntries(Object.entries(vars).slice(0, 150)), mediaQueries: [...media].slice(0, 30), sections
  };
}
```

## B. Fonts loaded

```js
() => [...document.fonts].filter(f => f.status === 'loaded').map(f => `${f.family} ${f.weight} ${f.style}`)
```

Record the families and weights only. Never download or commit the font files.

## C. Motion and scroll behaviour

```js
() => {
  const out = { smoothScroll: getComputedStyle(document.documentElement).scrollBehavior, reducedMotionRules: 0, observers: [], parallax: 0, sticky: [] };
  const walk = rules => { for (const r of rules) { if (r.media && r.media.mediaText.includes('prefers-reduced-motion')) out.reducedMotionRules++; if (r.cssRules) walk(r.cssRules); } };
  for (const sh of document.styleSheets) { try { walk(sh.cssRules); } catch (e) { /* cross-origin sheet */ } }
  for (const el of document.querySelectorAll('body *')) { const s = getComputedStyle(el);
    if (s.position === 'sticky' || s.position === 'fixed') out.sticky.push(`${el.tagName.toLowerCase()} ${s.position} top:${s.top}`);
    if (s.transform !== 'none' && el.getBoundingClientRect().top > innerHeight) out.parallax++;
    if (el.style.opacity === '0' || s.opacity === '0') out.observers.push(el.tagName.toLowerCase()); }
  out.observers = out.observers.length; out.sticky = out.sticky.slice(0, 10);
  out.libs = ['gsap', 'ScrollTrigger', 'Lenis', 'lenis', 'AOS', 'framerMotion', 'anime', 'Swiper', 'lottie'].filter(k => k in window);
  return out;
}
```

`observers` counts elements hidden before they scroll in (a reveal-on-scroll pattern); `parallax` counts transformed elements below the fold. Confirm both by scrolling and taking a screenshot rather than trusting the count.

## D. Hover state of one element

Colours here come back in the browser's own notation (often `lab()` or `oklab()`); convert them with the `hex` helper of snippet A, or compare them as strings. Run this once at rest and once after `browser_hover` on the same element, passing the element's ref from `browser_snapshot` (or a unique selector) as `target` to `browser_evaluate` (it then calls the function with that element). Compare the two results:

```js
(el) => { const s = getComputedStyle(el);
  return { bg: s.backgroundColor, color: s.color, transform: s.transform, shadow: s.boxShadow, border: s.borderColor, textDecoration: s.textDecorationLine }; }
```

## E. Gradient-filled text

Finds text painted with a background clipped to the text (`background-clip: text`), the "gradient headline" technique. Run once at 1440. `fills` groups the elements by fill, so one entry with a high count means a single brand gradient used throughout; `image` means the text is filled with a picture rather than a CSS gradient.

```js
() => {
  const cv = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const hex = c => { let a = 1; const m = c.match(/\/\s*([\d.]+)(%?)\s*\)$/) || c.match(/^(?:rgba|hsla)\((?:[^,]+,){3}\s*([\d.]+)\)$/);
    if (m) { a = parseFloat(m[1]) / (m[2] === '%' ? 100 : 1); c = c.replace(/\s*\/\s*[\d.]+%?\s*\)$/, ')').replace(/^(rgb|hsl)a\(((?:[^,]+,){2}[^,]+),[^)]*\)/, '$1($2)'); }
    if (a === 0) return 'transparent';
    cv.fillStyle = '#000'; cv.fillStyle = c; cv.fillRect(0, 0, 1, 1); const [r, g, b] = cv.getImageData(0, 0, 1, 1).data;
    return '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('') + (a < 1 ? Math.round(a * 255).toString(16).padStart(2, '0') : ''); };
  const hexAll = str => str.replace(/(rgba?|lab|lch|oklab|oklch|hsla?|color)\([^()]*\)/g, hex);
  const els = [...document.querySelectorAll('body *')].filter(el => { const s = getComputedStyle(el); const r = el.getBoundingClientRect();
    return (s.webkitBackgroundClip === 'text' || s.backgroundClip === 'text') && r.width > 0 && r.height > 0; });
  const fills = {};
  const items = els.map(el => { const s = getComputedStyle(el); const fill = s.backgroundImage.startsWith('url(') ? 'image' : hexAll(s.backgroundImage);
    fills[fill] = (fills[fill] || 0) + 1;
    return { tag: el.tagName.toLowerCase(), y: Math.round(el.getBoundingClientRect().top + scrollY), font: `${s.fontWeight} ${s.fontSize}/${s.lineHeight}`, fill: fill.slice(0, 160), chars: el.textContent.trim().length }; });
  return { count: els.length, fills: Object.entries(fills).sort((a, b) => b[1] - a[1]), first: items.slice(0, 12) };
}
```

## F. Scroll-reveal timing

Measures how content below the fold animates in. It scrolls a few hidden headings and paragraphs into view one at a time and samples their opacity and vertical offset (summed over their ancestors) at 50 ms to 2.4 s. Run once at 1440; it moves the page, so run it last or scroll back afterwards.

- `waitingToReveal`: how many elements below the fold start hidden or offset. Zero means the page has no reveal effect.
- `before` and `curve`: the starting state and the path to rest. A positive `y` means the element rises into place; a negative `y` means it drops into place.
- `settledByMs`: the first sample at full opacity and no offset, so the duration lies between that sample and the previous one.
- `replaysOnScrollBack`: `true` means the effect is tied to scroll position (it reverses when the reader scrolls back up); `false` means it plays once.

```js
async () => {
  const sleep = t => new Promise(r => setTimeout(r, Math.max(0, t)));
  const state = el => { let op = 1, ty = 0; for (let e = el; e && e !== document.body; e = e.parentElement) { const s = getComputedStyle(e); op *= parseFloat(s.opacity);
      const m = s.transform.match(/^matrix\(([^)]+)\)$/); if (m) ty += parseFloat(m[1].split(',')[5]); }
    return { opacity: +op.toFixed(2), y: Math.round(ty * 10) / 10 }; };
  scrollTo(0, 0); await sleep(400);
  const below = [...document.querySelectorAll('h1, h2, h3, p, figure, img, video, picture')]
    .filter(el => el.getBoundingClientRect().width > 0 && el.getBoundingClientRect().top > innerHeight * 1.5);
  const waiting = below.filter(el => { const s = state(el); return s.opacity < 0.05 || Math.abs(s.y) >= 1; });
  const samples = [];
  for (const el of waiting.filter(e => /^(H1|H2|H3|P)$/.test(e.tagName)).slice(0, 3)) {
    const before = state(el);
    scrollTo(0, el.getBoundingClientRect().top + scrollY - innerHeight * 0.75);
    const t0 = performance.now(), curve = [];
    for (const t of [50, 150, 300, 600, 1000, 1600, 2400]) { await sleep(t - (performance.now() - t0)); curve.push({ t, ...state(el) }); }
    const done = curve.find(c => c.opacity > 0.98 && Math.abs(c.y) < 0.5);
    scrollTo(0, 0); await sleep(300); const replays = state(el).opacity < 0.05 || Math.abs(state(el).y) >= 1;
    samples.push({ tag: el.tagName.toLowerCase(), font: getComputedStyle(el).fontSize, before, curve, settledByMs: done ? done.t : '>2400', replaysOnScrollBack: replays });
  }
  scrollTo(0, 0);
  return { checked: below.length, waitingToReveal: waiting.length, samples };
}
```

## G. Carousels and rows that run off the edge

Finds horizontally scrolling rows: native scroll containers and rows moved by script (`overflow-x: hidden`). Run once at 1440 and once at 375. Each result gives:

- the item count, size, gap and corner radius;
- whether the row bleeds past the right edge of the viewport, and where the first item starts (which shows how it lines up with the page grid);
- the scroll-snap setting;
- the previous/next controls nearby, with their size and colour;
- the number of dot or tab indicators.

```js
() => {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const rows = [...document.querySelectorAll('body *')].filter(el => { const s = getComputedStyle(el); const r = el.getBoundingClientRect();
    return vis(el) && r.width > 240 && r.height > 120 && el.scrollWidth > el.clientWidth + 24 && ['auto', 'scroll', 'hidden'].includes(s.overflowX); })
    .filter((el, i, arr) => !arr.some(o => o !== el && o.contains(el) && o.scrollWidth - o.clientWidth >= el.scrollWidth - el.clientWidth));
  return rows.map(el => {
    let list = el; while (list.children.length === 1) list = list.firstElementChild;
    const items = [...list.children].filter(vis); const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    const ir = items.map(i => i.getBoundingClientRect());
    const gap = ir.length > 1 ? Math.round(ir[1].left - ir[0].right) : null;
    const box = el.closest('section, article, [class*=gallery], [class*=carousel]') || el.parentElement;
    const controls = [...box.querySelectorAll('button, [role=button], a')].filter(b => vis(b) && /next|prev|previous|forward|back|scroll|›|‹|→|←/i.test((b.getAttribute('aria-label') || '') + b.textContent))
      .map(b => { const bs = getComputedStyle(b); const br = b.getBoundingClientRect(); return `${(b.getAttribute('aria-label') || b.textContent).trim().slice(0, 20)} ${Math.round(br.width)}x${Math.round(br.height)} r${bs.borderRadius} ${bs.backgroundColor}`; });
    const dots = box.querySelectorAll('[role=tab], [class*=dot], [class*=paddle-nav] li').length;
    const radiusOf = it => { const w = it.getBoundingClientRect().width; const el = [it, ...it.querySelectorAll('*')].find(e => parseFloat(getComputedStyle(e).borderTopLeftRadius) > 0 && e.getBoundingClientRect().width > w * 0.6); return el ? getComputedStyle(el).borderTopLeftRadius : '0px'; };
    return { y: Math.round(r.top + scrollY), left: Math.round(r.left), width: Math.round(r.width), scrollWidth: el.scrollWidth, overflowX: s.overflowX,
      scrollSnap: s.scrollSnapType, mechanism: s.overflowX === 'hidden' ? 'transform or script' : 'native scroll',
      items: items.length, itemSize: ir[0] ? [Math.round(ir[0].width), Math.round(ir[0].height)] : null, gap, itemRadius: items[0] ? radiusOf(items[0]) : null,
      bleedsRight: ir.some(x => x.right > innerWidth), firstItemLeft: ir[0] ? Math.round(ir[0].left) : null,
      controls: controls.slice(0, 4), dots };
  }).filter(c => c.controls.length || c.dots || (c.gap !== null && c.gap >= 0 && c.mechanism === 'native scroll')).slice(0, 8);
}
```

