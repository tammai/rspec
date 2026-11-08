# Legal and ethical guardrails

**Modernize track (your own product):** the rules about copying, branding and terms of service below do not apply; you may reuse your own code, text and brand. Still: check the licences of third-party code and libraries before carrying them over, never copy production data (users' records, messages, secrets) into the spec, and describe fields generically.

**rspec track (someone else's product):**

Not legal advice. Apply these by default and surface them to the user in `<spec>/README.md`.

- **Ideas and features are generally not protected; expression is.** Describe behaviour in your own words. Never paste the vendor's docs text, UI copy, code, icons, images, illustrations or fonts into the spec.
- **Quotes**: if exact wording matters (e.g. a documented limit), quote at most one short phrase and cite it.
- **Branding**: the rebuild must not use the original name, logo or a confusingly similar identity if it is ever published. Use a working name.
- **Terms of service**: many products forbid reverse engineering, scraping or automated access. Observe the product only through normal use. Do not bypass auth, rate limits or paywalls. Do not run automated crawlers against the product.
- **Open source**: reading an open-source product's code to understand its behaviour, data model and API is how the spec gets precise. Nothing is copied from it, whatever its licence: no code, schema files, migrations, UI text or assets. The spec describes behaviour in its own words and the rebuild writes its own code. Record the repo, the pinned commit and the licence in `rspec.json` for reference. The code licence never covers the name or logo.
- **Recording against a reference** (`/rspec:verify`): a `url` reference (a hosted product) is read only: tests may navigate and read, never create, change or delete, and use only the user's own accounts, at a pace a person would. Check the product's terms first; when they forbid automated access, use `kind: none` or a local copy you are allowed to run. Account tokens and cookies stay in `ACCEPT_ACCOUNT_<NAME>` environment variables, never in a file.
- **Credentials and personal data**: never ask for, store or write the user's passwords or tokens into docs. Do not record other people's data seen in the product.
- **Production**: a rebuild that serves real users needs its own name and brand, reviewed licences, a privacy policy and terms. These are items in `production-readiness.md`; get legal advice before launch.
- **Publishing**: if the spec repo is public, add a disclaimer: "Independent learning project, not affiliated with or endorsed by <vendor>."
