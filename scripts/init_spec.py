#!/usr/bin/env python3
"""Create the spec skeleton from templates. Never overwrites existing files.

Usage: init_spec.py [project-root] [--layout auto|single|monorepo] [--name <working name>]
                    [--track rspec|modernize] [--strategy rewrite|strangler|refactor]

single:   the spec in docs/, contracts beside it, ADRs in docs/decisions/, CHANGELOG.md at the root.
monorepo: sdlc's layout: the spec in docs/specs/<name>/, contracts in packages/api-contract/v1/,
          ADRs in docs/adr/, the spec's changelog inside its folder.
auto (default): monorepo when .sdlc/config.json lists packages, or packages/api-contract/ or apps/ exists.
Prints JSON: layout, paths, created and kept files.
"""
import json, re, shutil, sys
from pathlib import Path
from rspec_lib import TEMPLATES, SINGLE_PATHS, monorepo_paths


def option(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def is_monorepo(root):
    cfg = root / ".sdlc" / "config.json"
    if cfg.exists():
        try:
            if json.loads(cfg.read_text(encoding="utf-8")).get("packages"):
                return True
        except json.JSONDecodeError:
            pass
    return (root / "packages" / "api-contract").is_dir() or (root / "apps").is_dir()


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main():
    positional = [a for i, a in enumerate(sys.argv[1:], 1)
                  if not a.startswith("--") and sys.argv[i - 1] not in ("--layout", "--name", "--track", "--strategy")]
    root = Path(positional[0] if positional else ".")
    layout = option("--layout", "auto")
    if layout == "auto":
        layout = "monorepo" if is_monorepo(root) else "single"
    if layout == "monorepo":
        name = option("--name")
        if not name or not slug(name):
            print("ERROR a monorepo needs --name <working name> for docs/specs/<name>/"); sys.exit(2)
        paths = monorepo_paths(slug(name))
    else:
        paths = dict(SINGLE_PATHS)

    spec, contracts = root / paths["spec"], root / paths["contracts"]
    for d in (spec / "research", spec / "features", root / paths["decisions"], contracts / "schemas"):
        d.mkdir(parents=True, exist_ok=True)

    created, kept = [], []

    def copy(template, dest):
        if dest.exists():
            kept.append(dest.relative_to(root).as_posix())
        else:
            shutil.copyfile(TEMPLATES / template, dest)
            created.append(dest.relative_to(root).as_posix())

    for t in ("README.md", "screens.md", "features.md", "api.md", "data-model.md", "nfr.md"):
        copy(t, spec / t)
    copy("CHANGELOG.md", root / paths["changelog"])

    cfg_path = spec / "rspec.json"
    if cfg_path.exists():
        kept.append(cfg_path.relative_to(root).as_posix())
    else:
        cfg = json.loads((TEMPLATES / "rspec.json").read_text(encoding="utf-8"))
        cfg["paths"] = paths
        cfg["working_name"] = option("--name", "")
        cfg["track"] = option("--track", "rspec")
        if cfg["track"] == "modernize":
            cfg["strategy"] = option("--strategy", "rewrite")
            cfg["goal"] = "production"
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        created.append(cfg_path.relative_to(root).as_posix())

    print(json.dumps({"layout": layout, "paths": paths, "created": created, "kept": kept}, indent=2))


if __name__ == "__main__":
    main()
