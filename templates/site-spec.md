# <Working name> site spec

Reference: <url> (observed <YYYY-MM-DD>, viewports 375 / 768 / 1440<, dark mode>)
Purpose of the page: <who it is for and the one action it wants, in own words>

Independent design study. The rebuild takes the design system and patterns, not the reference's text, images, logos, icons or fonts, and has its own name and brand.

## Vibe
- Three to five adjectives: <e.g. calm, technical, premium>
- Density: <airy | balanced | dense>, contrast: <soft | medium | stark>, corners: <sharp | soft | round> [observed]
- Imagery style: <product screenshots in device frames | abstract 3D | flat illustration | photography | none>, described only [observed]
- Copy voice: <short declarative headlines, second person, numbers as proof …>; no quoted text [inferred]
- What makes it feel this way: <3–5 decisions that carry the taste, e.g. one accent colour used only on CTAs, oversized headline with tight tracking> [inferred]

## Tokens
Full values in `tokens.json`. Summary:

| Group | Values | Tag |
|---|---|---|
| Colour roles | background, surface, text, muted text, border, accent, accent text, success … | [observed] |
| Type scale | display / h1 / h2 / h3 / body / small: size, weight, line-height, tracking | [observed] |
| Fonts | reference: <traits, e.g. geometric sans, tall x-height, 400/500/700>; rebuild: <free substitute> | [inferred] |
| Spacing | base <4 or 8>px, scale <…>, section padding <…> | [inferred] |
| Radii, borders, shadows | <…> | [observed] |
| Layout | container max-width <…>, gutter <…>, grid <12 col / …>, breakpoints <…> | [observed] |
| Headline fill | <solid | gradient <angle, from → to> on <which headlines> | image> | [observed] |
| Motion | durations <…>, easing <…>; scroll reveal <distance, direction, duration, once or scroll-linked>; reduced-motion handled: <yes/no> | [observed] |

## Components
One row per reusable component, with its states.

| Component | Anatomy | Variants | States (hover, focus, active, disabled) | Tag |
|---|---|---|---|---|
| Button | <…> | primary, secondary, ghost | <hover: bg darkens 8%, 150ms ease-out> | [observed] |
| Nav bar | <…> | <transparent → solid on scroll> | <…> | [observed] |

## Sections
Top to bottom, one subsection per section. Content is a placeholder the rebuild fills with its own words.

### S1 <Hero>
- Layout: <two columns 6/6 at ≥1024, stacked below; media right> [observed]
- Hierarchy: <eyebrow → headline (display) → subhead (≤2 lines) → two CTAs → trust line> [observed]
- Content slots: <headline ~6 words, subhead ~20 words, primary CTA, secondary CTA, product visual> [inferred]
- Spacing: <padding-top 128 / 72 mobile> [observed]
- Interaction and motion: <headline fades up 400ms on load; visual parallax> [observed]
- Responsive: <what changes at 768 and 375> [observed]

## Interactions
- Scroll: <smooth scroll, sticky header, reveal on scroll …> [observed]
- Carousels: <item size, gap, bleeds off the right edge, snap, previous/next controls, dots> [observed]
- Links and focus: <underline on hover, visible focus ring 2px accent> [observed]
- Forms: <inline email capture, validation style> [observed]

## Accessibility
- Contrast of the main text and CTA pairs against WCAG 2.2 AA: <ratios> [observed]
- Rebuild requirements beyond the reference: <e.g. respects prefers-reduced-motion> [inferred]

## Acceptance criteria
At most ten, each checked by comparing the rebuild's screenshots at 375, 768 and 1440 with this spec (not with the reference's pixels).
- [ ] Given the rebuild at 1440, when the page loads, then the hero shows <hierarchy> with the headline at <size/weight> and the primary CTA in the accent colour. [observed]
- [ ] …

## Differences
Deliberate departures from the reference, with the reason (own fonts, own imagery, better contrast, fewer animations).

## Open questions

## Sources
- <url>, observed <YYYY-MM-DD>, viewports, logged out
