#!/usr/bin/env python3
"""Score one finished spec, or compare two runs on the same product.

Usage: scorecard.py <project-or-spec> [<other project-or-spec>]
Prints per-run numbers (modules, features, criteria, tagged criteria, inferred share, slices over budget) and,
for two runs, how far they agree: MVP overlap (matched by feature name) and feature-count spread.
Exit code 1 if a target is missed. Read-only.
"""
import re, sys
from rspec_lib import (TAG_RE, open_layout, feature_rows, stories, criteria_count, criteria_items, build_slices, slice_criteria,
                       SDLC_MAX_CRITERIA, SLICE_BUDGET)

TARGETS = {"inferred_max": 0.30, "tagged_min": 0.90, "mvp_overlap_min": 0.80, "count_spread_max": 0.15}
STOP = {"and", "the", "a", "of", "to", "in", "on", "for", "with", "by", "up", "out", "field", "fields", "property",
        "properties", "issue", "issues", "settings", "management", "basic", "core"}


def words(name):
    """Content words of a feature name, plural s dropped: "Teams and team keys" -> {team, key}."""
    ws = {w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w
          for w in re.findall(r"[a-z]+", name.lower()) if w not in STOP}
    return ws or set(name.lower().split())


def similar(x, y):
    """Names match when half the words of the shorter one appear in the other."""
    a, b = words(x), words(y)
    return len(a & b) / min(len(a), len(b)) >= 0.5


def score(arg):
    layout, cfg = open_layout(arg)
    if layout is None:
        sys.exit(f"ERROR no rspec.json under {arg}")
    docs = layout.spec
    rows = [cells for _, cells in feature_rows(docs)]
    prio = {}
    for c in rows:
        prio[c[4] if len(c) > 4 else "?"] = prio.get(c[4] if len(c) > 4 else "?", 0) + 1
    smap = stories(docs)
    crit = [criteria_count(t) for _, t, _ in smap.values()]
    items = [i for _, t, _ in smap.values() for i in criteria_items(t)]
    tags = [m.group(1) for i in items for m in TAG_RE.finditer(i)]  # criteria only: Differences are [inferred] by rule
    sdlc = (cfg.get("build") or {}).get("engine") == "sdlc"
    budget = SDLC_MAX_CRITERIA if sdlc else SLICE_BUDGET
    slices = build_slices(docs)
    over = [n for n, _, ids in slices if slice_criteria(smap, ids) > budget and len(ids) > 1]
    return {"path": arg, "modules": len(cfg.get("modules", [])), "features": len(rows), "priority": prio,
            "mvp": [c[2] for c in rows if len(c) > 4 and c[4] == "MVP"], "stories": len(smap),
            "criteria": sum(crit), "criteria_range": [min(crit), max(crit)] if crit else [0, 0],
            "tagged": round(sum(1 for i in items if TAG_RE.search(i)) / len(items), 2) if items else 1.0,
            "inferred": round(tags.count("inferred") / len(tags), 2) if tags else 0.0,
            "slices": len(slices), "budget": budget, "over_budget": over}


def overlap(a, b):
    """Share of MVP features in a that have a match by name in b (see similar)."""
    if not a:
        return 1.0
    hits = sum(1 for x in a if any(similar(x, y) for y in b))
    return round(hits / len(a), 2)


def main():
    runs = [score(a) for a in sys.argv[1:3]] or [score(".")]
    missed = []
    for r in runs:
        print(f"== {r['path']}")
        print(f"   modules {r['modules']}, features {r['features']} {r['priority']}, stories {r['stories']}, "
              f"criteria {r['criteria']} (per story {r['criteria_range'][0]}-{r['criteria_range'][1]})")
        print(f"   tagged criteria {r['tagged']:.0%}, inferred share {r['inferred']:.0%}, slices {r['slices']} (budget {r['budget']}), over budget {len(r['over_budget'])}")
        if r["tagged"] < TARGETS["tagged_min"]:
            missed.append(f"{r['path']}: tagged criteria {r['tagged']:.0%} < {TARGETS['tagged_min']:.0%}")
        if r["inferred"] > TARGETS["inferred_max"]:
            missed.append(f"{r['path']}: inferred share {r['inferred']:.0%} > {TARGETS['inferred_max']:.0%}")
        if r["over_budget"]:
            missed.append(f"{r['path']}: slices over budget: {', '.join(r['over_budget'])}")
    if len(runs) == 2:
        a, b = runs
        ov = min(overlap(a["mvp"], b["mvp"]), overlap(b["mvp"], a["mvp"]))
        spread = round(abs(a["features"] - b["features"]) / max(a["features"], b["features"], 1), 2)
        print(f"== agreement: MVP overlap {ov:.0%}, feature-count spread {spread:.0%}, modules {a['modules']} vs {b['modules']}")
        if ov < TARGETS["mvp_overlap_min"]:
            missed.append(f"MVP overlap {ov:.0%} < {TARGETS['mvp_overlap_min']:.0%}")
        if spread > TARGETS["count_spread_max"]:
            missed.append(f"feature-count spread {spread:.0%} > {TARGETS['count_spread_max']:.0%}")
    for m in missed:
        print("MISS ", m)
    print("OK" if not missed else f"{len(missed)} target(s) missed")
    sys.exit(1 if missed else 0)


if __name__ == "__main__":
    main()
