#!/usr/bin/env python3
"""Report where an rspec pipeline stands, from the files on disk.

Usage: progress.py [project-root] [--build-order]
Prints JSON: stage, next step, pending units for that step, the saved pipeline
checkpoint, and build status. --build-order adds the MVP features in dependency
order. Used by /rspec:pipeline to resume in a new session and by /rspec:handoff.
"""
import json, sys
from pathlib import Path
from rspec_lib import (TEMPLATES, load_config, priorities, stories, dependencies, build_order, adr_statuses,
                       build_slices, sdlc_status)

NEXT = {"init": "discover", "discovered": "features", "features-approved": "stories",
        "stories": "tech", "tech": "handoff", "handoff": "check"}
CLAUDE_MARKER = "<!-- rspec:handoff -->"


def unchanged(path, template):
    if not path.exists():
        return True
    t = TEMPLATES / template
    return t.exists() and path.read_text(encoding="utf-8").strip() == t.read_text(encoding="utf-8").strip()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = Path(args[0] if args else ".")
    docs = root / "docs"
    if not (docs / "rspec.json").exists():
        print(json.dumps({"stage": None, "next": "init", "pending": [], "pipeline": {}}))
        return
    cfg = load_config(docs)
    stage = cfg.get("stage", "init")
    nxt = NEXT.get(stage, "init")
    build_cfg = cfg.get("build") or {}
    if stage == "handoff" and build_cfg.get("engine") == "sdlc":
        nxt = "build"
    prio = priorities(docs)
    mvp = [i for i, p in prio.items() if p == "MVP"]
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
        pending = [i for i in mvp if i not in story_map]
    elif nxt == "tech":
        if not (docs / "openapi.json").exists() or unchanged(docs / "api.md", "api.md"):
            pending.append("api")
        if not list((docs / "schemas").glob("*.json")) or unchanged(docs / "data-model.md", "data-model.md"):
            pending.append("data-model")
        if unchanged(docs / "nfr.md", "nfr.md"):
            pending.append("nfr")
        if not pending and not list((docs / "decisions").glob("*.md")):
            pending = ["adrs"]
    elif nxt == "handoff":
        if any(s.lower() == "proposed" for s in adr_statuses(docs).values()):
            pending.append("adr-approval")
        if not build_cfg.get("engine"):
            pending.append("build-engine")
        if not (docs / "build-plan.md").exists():
            pending.append("build-plan")
        claude = root / "CLAUDE.md"
        if not claude.exists() or CLAUDE_MARKER not in claude.read_text(encoding="utf-8"):
            pending.append("claude-md")
    elif nxt == "build":
        mapped = build_cfg.get("slices") or {}
        slices = []
        for num, name, ids in build_slices(docs):
            feature = mapped.get(num, "")
            state = sdlc_status(root, feature) if feature else ""
            slices.append({"slice": num, "name": name, "features": ids, "sdlc_feature": feature, "sdlc_status": state})
        pending = [s["slice"] for s in slices if s["sdlc_status"] != "done"]
        if not pending:
            nxt, pending = "check", ["check"]
    elif nxt == "check":
        pending = ["check"]

    status = {"todo": 0, "in-progress": 0, "done": 0}
    for fid in mvp:
        fm = story_map.get(fid, (None, None, None))[2] or {}
        s = fm.get("status", "todo")
        status[s if s in status else "todo"] += 1

    out = {"stage": stage, "next": nxt, "pending": pending, "pipeline": cfg.get("pipeline", {}), "build": status}
    if build_cfg.get("engine") == "sdlc" and stage == "handoff":
        out["slices"] = locals().get("slices", [])
    if "--build-order" in sys.argv:
        out["order"] = build_order(mvp, dependencies(story_map))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
