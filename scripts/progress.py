#!/usr/bin/env python3
"""Report where an rspec pipeline stands, from the files on disk.

Usage: progress.py [project-root | spec-folder] [--build-order]
Prints JSON: stage, next step, pending units for that step, the saved pipeline
checkpoint, and build status. --build-order adds the MVP features in dependency
order. Used by /rspec:pipeline to resume in a new session and by /rspec:handoff.
"""
import json, re, sys
from pathlib import Path
from rspec_lib import (STAGES, TEMPLATES, open_layout, priorities, stories, dependencies, build_order, adr_statuses,
                       build_slices, sdlc_status, readiness_open, parked_decisions, in_scope,
                       slice_criteria, SDLC_MAX_CRITERIA)

NEXT = {"init": "discover", "discovered": "features", "features-approved": "stories",
        "stories": "tech", "tech": "handoff", "handoff": "check"}
# next is "done" once the pipeline checkpoint says the final check passed.
CLAUDE_MARKER = "<!-- rspec:handoff -->"


def unchanged(path, template):
    if not path.exists():
        return True
    t = TEMPLATES / template
    return t.exists() and path.read_text(encoding="utf-8-sig").strip() == t.read_text(encoding="utf-8-sig").strip()


def triage_pending(docs, stage, prio, scoped, story_map):
    """Feature IDs whose priority changed after their stage: in scope without a story, or (from handoff)
    in scope but missing from build-plan.md, or Drop but still in it."""
    out = [i for i in scoped if i not in story_map]
    plan = docs / "build-plan.md"
    if stage == "handoff" and plan.exists():
        planned = set(re.findall(r"\bF-[A-Z]{2,4}-\d{2,3}\b", plan.read_text(encoding="utf-8-sig")))
        out += [i for i in scoped if i in story_map and i not in planned]
        sliced = {i for _, _, ids in build_slices(docs) for i in ids}
        out += [i for i, p in prio.items() if p == "Drop" and i in sliced]
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    layout, cfg = open_layout(args[0] if args else ".")
    if layout is None:
        print(json.dumps({"stage": None, "next": "init", "pending": [], "pipeline": {}}))
        return
    root, docs, contracts = layout.root, layout.spec, layout.contracts
    stage = cfg.get("stage", "init")
    nxt = NEXT.get(stage, "init")
    build_cfg = cfg.get("build") or {}
    if stage == "handoff" and build_cfg.get("engine") == "sdlc":
        nxt = "build"
    prio = priorities(docs)
    scoped = in_scope(prio, cfg)  # MVP first; Later too when scope is "full"
    story_map = stories(docs)
    pending = []

    if nxt == "discover":
        codes = [m.get("code", "") for m in cfg.get("modules", [])]
        if not codes:
            pending = ["module-map"]
        else:
            names = [p.name.lower() for p in (docs / "research").glob("*.md")]
            pending = [c for c in codes if not any(n.startswith(c.lower() + "-") for n in names)] or ["screens"]
    elif nxt == "features":
        pending = ["approval"] if cfg.get("pipeline", {}).get("status") == "awaiting-approval" else ["features"]
    elif nxt == "stories":
        pending = [i for i in scoped if i not in story_map]
    elif nxt == "tech":
        if not (contracts / "openapi.json").exists() or unchanged(docs / "api.md", "api.md"):
            pending.append("api")
        if not list((contracts / "schemas").glob("*.json")) or unchanged(docs / "data-model.md", "data-model.md"):
            pending.append("data-model")
        if unchanged(docs / "nfr.md", "nfr.md"):
            pending.append("nfr")
        if cfg.get("track") == "modernize" and not (docs / "data-migration.md").exists():
            pending.append("data-migration")
        if not pending and not adr_statuses(layout.decisions):
            pending = ["adrs"]
    elif nxt == "handoff":
        if any(s.lower() == "proposed" for s in adr_statuses(layout.decisions).values()):
            pending.append("adr-approval")
        if not build_cfg.get("engine"):
            pending.append("build-engine")
        if not (docs / "build-plan.md").exists():
            pending.append("build-plan")
        if cfg.get("track") == "modernize" and not (docs / "cutover-plan.md").exists():
            pending.append("cutover-plan")
        claude = root / "CLAUDE.md"
        if not claude.exists() or CLAUDE_MARKER not in claude.read_text(encoding="utf-8-sig"):
            pending.append("claude-md")
    elif nxt == "build":
        mapped = build_cfg.get("slices") or {}
        slices = []
        for num, name, ids in build_slices(docs):
            feature = mapped.get(num, "")
            state = sdlc_status(root, feature) if feature else ""
            slices.append({"slice": num, "name": name, "features": ids, "sdlc_feature": feature, "sdlc_status": state})
        pending = [s["slice"] for s in slices if s["sdlc_status"] != "done"]
        unstarted = [s for s in slices if not s["sdlc_feature"]]
        if any(slice_criteria(story_map, s["features"]) > SDLC_MAX_CRITERIA for s in unstarted):
            # e.g. the engine became sdlc after the plan was cut: re-cut the slices not started yet
            nxt, pending = "handoff", ["build-plan"]
        elif not pending:
            open_items = readiness_open(docs / "production-readiness.md") if cfg.get("goal") == "production" else {}
            if open_items:
                nxt, pending = "readiness", list(open_items)
            else:
                nxt, pending = "check", ["check"]
    elif nxt == "check":
        pending = ["check"]
    if stage in STAGES and STAGES.index(stage) >= 3:
        # features triaged after their stage: new ones in scope need a story, contracts and a place in the plan
        untriaged = triage_pending(docs, stage, prio, scoped, story_map)
        if untriaged:
            nxt, pending = "triage", untriaged
    if nxt == "check" and cfg.get("pipeline", {}).get("status") == "done":
        nxt, pending = "done", []

    status = {"todo": 0, "in-progress": 0, "done": 0}
    for fid in scoped:
        fm = story_map.get(fid, (None, None, None))[2] or {}
        s = fm.get("status", "todo")
        status[s if s in status else "todo"] += 1

    out = {"stage": stage, "next": nxt, "pending": pending, "pipeline": cfg.get("pipeline", {}), "build": status,
           "paths": layout.paths, "autopilot": bool((cfg.get("autopilot") or {}).get("enabled")),
           "parked": len(parked_decisions(docs))}
    if build_cfg.get("engine") == "sdlc" and stage == "handoff":
        out["slices"] = locals().get("slices", [])
    if "--build-order" in sys.argv:
        out["order"] = build_order(scoped, dependencies(story_map))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
