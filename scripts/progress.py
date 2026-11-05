#!/usr/bin/env python3
"""Report where an rspec pipeline stands, from the files on disk.

Usage: progress.py [project-root]
Prints JSON: stage, next step, pending units for that step, and the saved
pipeline checkpoint. Used by /rspec:pipeline to resume in a new session.
"""
import json, re, sys
from pathlib import Path

NEXT = {"init": "discover", "discovered": "features", "features-approved": "stories",
        "stories": "tech", "tech": "check"}
TEMPLATES = Path(__file__).resolve().parent.parent / "templates"

def mvp_ids(docs):
    f = docs / "features.md"
    ids = []
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) > 4 and cells[0].startswith("F-") and cells[4] == "MVP":
                ids.append(cells[0])
    return ids

def unchanged(path, template):
    if not path.exists():
        return True
    t = TEMPLATES / template
    return t.exists() and path.read_text(encoding="utf-8").strip() == t.read_text(encoding="utf-8").strip()

def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    docs = root / "docs"
    cfg_path = docs / "rspec.json"
    if not cfg_path.exists():
        print(json.dumps({"stage": None, "next": "init", "pending": [], "pipeline": {}}))
        return
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    stage = cfg.get("stage", "init")
    nxt = NEXT.get(stage, "init")
    pending = []

    if nxt == "discover":
        codes = [m.get("code", "") for m in cfg.get("modules", [])]
        if not codes:
            pending = ["module-map"]
        else:
            names = [p.name.lower() for p in (docs / "research").glob("*.md")]
            pending = [c for c in codes if not any(n.startswith(c.lower() + "-") for n in names)]
            if not pending:
                pending = ["screens"]
    elif nxt == "features":
        pending = ["approval"] if cfg.get("pipeline", {}).get("status") == "awaiting-approval" else ["features"]
    elif nxt == "stories":
        have = {re.match(r"(F-[A-Z]{2,4}-\d{2,3})", p.name).group(1)
                for p in (docs / "features").glob("F-*.md") if re.match(r"F-[A-Z]{2,4}-\d{2,3}", p.name)}
        pending = [i for i in mvp_ids(docs) if i not in have]
    elif nxt == "tech":
        pending = [a for a, f in (("api", "api.md"), ("data-model", "data-model.md"), ("nfr", "nfr.md"))
                   if unchanged(docs / f, f)]
        if not pending and not list((docs / "decisions").glob("*.md")):
            pending = ["adrs"]
    elif nxt == "check":
        pending = ["check"]

    print(json.dumps({"stage": stage, "next": nxt, "pending": pending,
                      "pipeline": cfg.get("pipeline", {})}, indent=2))

if __name__ == "__main__":
    main()
