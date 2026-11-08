#!/usr/bin/env python3
"""Draw the fact-check sample for /rspec:audit, and turn the audit's verdicts into criterion levels.

Usage: audit_sample.py [project-root | spec-folder] [--seed 42]
       audit_sample.py [project-root | spec-folder] --levels
Draw: for each of [docs] [api] [observed] [code] [inferred], samples min(25, max(5, 20% rounded up)) criteria
(all of them when fewer) with a fixed seed, and writes <spec>/audit/sample.md for the fact-checker and
<spec>/audit/sample.json (each tag's population and sample) for --levels.
--levels: reads the verdict column of <spec>/audit/facts.md and writes <spec>/audit/levels.json, the criteria that
reach level 1 (contracts C3) with their text hash: sampled and confirmed, or unsampled in a population whose sample
has no CONTRADICTED; a criterion with its own finding, or edited since the draw, never does. check_spec.py writes the level into the lock.
"""
import json, math, random, sys
from rspec_lib import open_layout, table_cells, criteria, contracts

TAGS = ("docs", "api", "observed", "code", "inferred")
CONFIRMED = {"SUPPORTED", "NOT-CONTRADICTED"}


def arg(name, default):
    return int(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def sample_size(population):
    return min(population, 25, max(5, math.ceil(population * 0.2)))


def draw(spec, seed):
    rng = random.Random(seed)
    found = criteria(spec)
    tags, lines = {}, []
    for tag in TAGS:
        pop = [c for c in found if c[1] == tag]
        picked = rng.sample(pop, sample_size(len(pop)))
        tags[tag] = {"population": [c[0] for c in pop], "sample": [c[0] for c in picked],
                     "text_sha256": {c[0]: c[2] for c in pop}}
        lines.append(f"\n## [{tag}]: {len(picked)} of {len(pop)}\n")
        lines += [f"- {cid} ({name}): {line}" for cid, _, _, name, line in picked]
    out = spec / "audit"
    out.mkdir(exist_ok=True)
    (out / "sample.md").write_text("# Fact-check sample\n" + "\n".join(lines) + "\n", encoding="utf-8")
    (out / "sample.json").write_text(json.dumps({"seed": seed, "tags": tags}, indent=2) + "\n", encoding="utf-8")
    print(f"{out / 'sample.md'} " + " ".join(f"{t}={len(v['sample'])}/{len(v['population'])}" for t, v in tags.items()))


def verdicts(facts):
    """{criterion ID: verdict} from the facts.md table (the column headed Verdict)."""
    out, col = {}, None
    for line in facts.splitlines():
        if not line.lstrip().startswith("|"):
            col = None
            continue
        cells = table_cells(line)
        if col is None:
            col = next((k for k, c in enumerate(cells) if c.lower() == "verdict"), None)
            continue
        ids = [c for c in cells if contracts.SPEC_ID.fullmatch(c)]
        if ids and col < len(cells):
            out[ids[0]] = cells[col].upper()
    return out


def levels(spec):
    audit = spec / "audit"
    if not (audit / "sample.json").exists() or not (audit / "facts.md").exists():
        sys.exit("not run: levels need audit/sample.json and audit/facts.md; draw the sample and run the fact-checker first")
    tags = json.loads((audit / "sample.json").read_text(encoding="utf-8"))["tags"]
    found = verdicts((audit / "facts.md").read_text(encoding="utf-8-sig"))
    missing = [i for t in tags.values() for i in t["sample"] if i not in found]
    if missing:
        sys.exit(f"not run: {len(missing)} sampled criteria have no verdict in facts.md (e.g. {', '.join(missing[:3])})")
    sha = {c[0]: c[2] for c in criteria(spec)}
    level1 = {}
    for tag in tags.values():
        clean = not any(found[i] == "CONTRADICTED" for i in tag["sample"])
        for cid in tag["population"]:
            verdict = found.get(cid)
            ok = verdict in CONFIRMED if verdict else clean
            if ok and cid in sha and sha[cid] == tag["text_sha256"].get(cid):  # only text the audit saw
                level1[cid] = sha[cid]
    (audit / "levels.json").write_text(json.dumps({"criteria": level1}, indent=2) + "\n", encoding="utf-8")
    total = sum(len(t["population"]) for t in tags.values())
    print(f"{audit / 'levels.json'} level 1: {len(level1)} of {total} audited criteria")


def main():
    pos = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] != "--seed"]
    layout, _ = open_layout(pos[0] if pos else ".")
    if layout is None:
        sys.exit("ERROR no rspec.json found")
    if "--levels" in sys.argv:
        levels(layout.spec)
    else:
        draw(layout.spec, arg("--seed", 42))


if __name__ == "__main__":
    main()
