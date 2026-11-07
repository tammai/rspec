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
