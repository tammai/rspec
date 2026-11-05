#!/usr/bin/env bash
# Usage: init_spec.sh <project-root>
# Creates the docs/ skeleton from templates. Never overwrites existing files.
set -euo pipefail
ROOT="${1:-.}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TPL="$HERE/../templates"
DOCS="$ROOT/docs"
mkdir -p "$DOCS/research" "$DOCS/features" "$DOCS/decisions"
copy() { # src dest
  if [ -e "$2" ]; then echo "keep   $2"; else cp "$1" "$2"; echo "create $2"; fi
}
copy "$TPL/rspec.json"   "$DOCS/rspec.json"
copy "$TPL/README.md"    "$DOCS/README.md"
copy "$TPL/screens.md"   "$DOCS/screens.md"
copy "$TPL/features.md"  "$DOCS/features.md"
copy "$TPL/api.md"       "$DOCS/api.md"
copy "$TPL/data-model.md" "$DOCS/data-model.md"
copy "$TPL/nfr.md"       "$DOCS/nfr.md"
copy "$TPL/CHANGELOG.md" "$ROOT/CHANGELOG.md"
echo "templates: $TPL"
