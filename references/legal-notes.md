# Legal and ethical guardrails

Not legal advice. Apply these by default and surface them to the user in `<spec>/README.md`.

- **Ideas and features are generally not protected; expression is.** Describe behaviour in your own words. Never paste the vendor's docs text, UI copy, code, icons, images, illustrations or fonts into the spec.
- **Quotes**: if exact wording matters (e.g. a documented limit), quote at most one short phrase and cite it.
- **Branding**: the rebuild must not use the original name, logo or a confusingly similar identity if it is ever published. Use a working name.
- **Terms of service**: many products forbid reverse engineering, scraping or automated access. Observe the product only through normal use. Do not bypass auth, rate limits or paywalls. Do not run automated crawlers against the product.
- **Open source**: if the original (or parts of it) is OSS, record the licence in `<spec>/rspec.json`. Copyleft licences (GPL, AGPL) bind derivative works; reading code to understand behaviour is fine, copying it brings the licence with it.
- **Credentials and personal data**: never ask for, store or write the user's passwords or tokens into docs. Do not record other people's data seen in the product.
- **Production**: a rebuild that serves real users needs its own name and brand, reviewed licences, a privacy policy and terms. These are items in `production-readiness.md`; get legal advice before launch.
- **Publishing**: if the spec repo is public, add a disclaimer: "Independent learning project, not affiliated with or endorsed by <vendor>."
