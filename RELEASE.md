# Release runbook

How to ship a new version of the rspec plugin. Users install it from this repo's marketplace (`/plugin marketplace add tammai/rspec`), so whatever is on `main` with a matching version is what they get on their next `/plugin marketplace update rspec`.

## 0. Prerequisites

- `git`, `gh` (logged in with push rights to `tammai/rspec`), Python 3, Claude Code CLI.
- A clean working tree on `main`, up to date: `git switch main && git pull --ff-only && git status`.

## 1. Pick the version

SemVer, based on what changed since the last tag (`git log --oneline $(git describe --tags --abbrev=0)..HEAD`):

| Change | Bump |
|---|---|
| Breaking: renamed/removed a command, skill or agent; changed `docs/rspec.json` fields or stage names so existing specs need migration | major (`1.0.0`; while `0.x`, bump minor) |
| New command, skill, agent, option, template section | minor |
| Fixes, wording, docs | patch |

## 2. Prepare the release on a branch

```bash
git switch -c release/vX.Y.Z
```

1. Set the version in **both** places, they must match:
   - `.claude-plugin/plugin.json` → `version`
   - `.claude-plugin/marketplace.json` → `plugins[0].version`
2. If a skill's behaviour changed, bump its `metadata.version` too.
3. `CHANGELOG.md`: move the `[Unreleased]` entries into a new `## [X.Y.Z] - YYYY-MM-DD` section; leave an empty `[Unreleased]`.

## 3. Verify

All must pass before tagging:

```bash
python3 -m unittest discover tests       # script tests
claude plugin validate .                 # must end with "Validation passed"
```

Smoke test in a scratch folder, with the local checkout loaded:

```bash
mkdir -p /tmp/rspec-smoke && cd /tmp/rspec-smoke
claude --plugin-dir /path/to/rspec
```

In that session:
- `/rspec:pipeline status` with no spec reports that init is next.
- `/rspec:init Trello` creates `docs/` and `CHANGELOG.md`; `/rspec:check` reports the expected summary line.
- `/agents` lists `rspec:module-explorer`, `rspec:story-writer`, `rspec:tech-analyst` with their descriptions.
- If you changed a stage skill, run that stage once on a small product.

## 4. Merge, tag and publish

```bash
git commit -am "Release vX.Y.Z"
git push -u origin release/vX.Y.Z
gh pr create --fill --base main          # review, then merge
git switch main && git pull --ff-only
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file <(sed -n '/^## \[X.Y.Z\]/,/^## \[/p' CHANGELOG.md | sed '$d')
```

## 5. Check the published release

From a different folder, as a user would:

```
/plugin marketplace add tammai/rspec      # or: /plugin marketplace update rspec
/plugin install rspec@rspec
```

Confirm `/plugin` shows the new version and `/rspec:pipeline status` runs.

## 6. Roll back

A bad release reaches users on their next marketplace update, so fix forward quickly:

1. Revert the offending commits on `main` (`git revert <sha>`), bump the **patch** version, and release again from step 2. Do not move or delete a published tag.
2. If the release is unusable, mark it on GitHub: `gh release edit vX.Y.Z --prerelease` and add a note pointing to the fixed version.
3. Note the problem in `CHANGELOG.md` under the fixed version.

## Checklist

- [ ] Version bumped in `plugin.json` and `marketplace.json`, identical
- [ ] `CHANGELOG.md` section for the version, dated
- [ ] `python3 -m unittest discover tests` passes
- [ ] `claude plugin validate .` passes
- [ ] Smoke test done
- [ ] PR merged, tag `vX.Y.Z` pushed, GitHub release created
- [ ] Install from the marketplace shows the new version
