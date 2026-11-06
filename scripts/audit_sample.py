#!/usr/bin/env python3
"""Draw the fact-check sample for /rspec:audit.

Usage: audit_sample.py [project-root | spec-folder] [--n 25] [--seed 42]
Writes <spec>/audit/sample.md: up to N acceptance criteria tagged [docs] and N tagged [api],
drawn with a fixed seed so a rerun checks the same criteria. Prints the path and counts.
"""
import random, sys
from rspec_lib import open_layout, stories, criteria_items


def arg(name, default):
    return int(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    pos = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] not in ("--n", "--seed")]
    layout, _ = open_layout(pos[0] if pos else ".")
    if layout is None:
        sys.exit("ERROR no rspec.json found")
    n, rng = arg("--n", 25), random.Random(arg("--seed", 42))
    pool = {"docs": [], "api": []}
    for fid, (path, text, _) in stories(layout.spec).items():
        for item in criteria_items(text):
            for tag in pool:
                if f"[{tag}]" in item:
                    pool[tag].append(f"- {fid} ({path.name}) [{tag}]: {item}")
    lines = [l for tag in pool for l in rng.sample(pool[tag], min(n, len(pool[tag])))]
    out = layout.spec / "audit" / "sample.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("# Fact-check sample\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"{out} docs={min(n, len(pool['docs']))}/{len(pool['docs'])} api={min(n, len(pool['api']))}/{len(pool['api'])}")


if __name__ == "__main__":
    main()
