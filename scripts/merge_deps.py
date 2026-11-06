#!/usr/bin/env python3
"""Merge the cross-module dependencies story writers proposed into depends_on.

Usage: merge_deps.py [project-root | spec-folder]
Story writers may depend only on earlier modules, so parallel writers cannot form cycles. A
dependency on a later module goes in `also_needs: [IDs]`. After the last round, this script moves
each one into `depends_on` unless it is unknown, Drop, an MVP feature needing a non-MVP one, or
would close a cycle, then removes `also_needs`. Prints JSON: added and skipped (with reasons).
"""
import json, re, sys
from rspec_lib import open_layout, priorities, stories, dependencies, find_cycles


def set_line(text, key, value):
    """Replace (or with value None, delete) a `key:` line inside the frontmatter block."""
    end = text.index("\n---", 3)
    head, rest = text[:end], text[end:]
    pat = re.compile(rf"^{key}:.*(\n|$)", re.M)
    if value is None:
        head = pat.sub("", head).rstrip("\n")
    elif pat.search(head):
        head = pat.sub(lambda m: f"{key}: {value}{m.group(1)}", head)
    else:
        head += f"\n{key}: {value}"
    return head + rest


def main():
    layout, cfg = open_layout(sys.argv[1] if len(sys.argv) > 1 else ".")
    if layout is None:
        print("ERROR no rspec.json found"); sys.exit(1)
    prio = priorities(layout.spec)
    story_map = stories(layout.spec)
    deps = dependencies(story_map)
    added, skipped = [], []
    for fid, (path, text, fm) in story_map.items():
        wants = (fm or {}).get("also_needs")
        if fm is None or "also_needs" not in fm:
            continue
        wants = [wants] if isinstance(wants, str) and wants else list(wants or [])
        for d in wants:
            if d not in prio:
                skipped.append([fid, d, "unknown feature"]); continue
            if prio[d] == "Drop":
                skipped.append([fid, d, "Drop"]); continue
            if prio.get(fid) == "MVP" and prio[d] != "MVP":
                skipped.append([fid, d, f"MVP cannot depend on {prio[d]}"]); continue
            if d in deps[fid]:
                continue
            trial = dict(deps, **{fid: deps[fid] + [d]})
            if find_cycles(trial):
                skipped.append([fid, d, "would close a cycle"]); continue
            deps[fid].append(d)
            added.append([fid, d])
        text = set_line(text, "depends_on", "[" + ", ".join(deps[fid]) + "]")
        path.write_text(set_line(text, "also_needs", None), encoding="utf-8")
    print(json.dumps({"added": added, "skipped": skipped}, indent=2))


if __name__ == "__main__":
    main()
