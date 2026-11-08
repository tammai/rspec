import json, subprocess, sys, tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

def story(fid, depends=(), status="todo", criteria=None, failure=None):
    criteria = criteria or (f'- [ ] **{fid}.AC1** Given team ENG with 11 issues, when a member creates "Fix login", '
                            'then it is shown as ENG-12. `[docs]`')
    failure = failure or f"- Empty title → {fid}.AC1"
    code = fid.split("-")[1]
    return f"""---
id: {fid}
module: {code}
priority: MVP
depends_on: [{", ".join(depends)}]
status: {status}
---
# {fid}: Feature

## Story
As a member, I want to do it so that work is tracked.

## Acceptance criteria
{criteria}

## Failure modes
{failure}

## Must never break
- none

## Differences from the original
- none

## Sources
- research/iss-issues.md, Flows
"""

MONOREPO = {"spec": "docs/specs/acme", "contracts": "packages/api-contract/v1",
            "decisions": "docs/adr", "changelog": "docs/specs/acme/CHANGELOG.md"}

def project(stage="stories", modules=("ISS",), features=(("F-ISS-01", "MVP"),), stories=None,
            research=None, files=None, config=None, root_files=None, layout="single"):
    """features: (id, priority); stories: {filename: text}; files: {path as in a single-repo docs/: text},
    routed to the layout's contracts and decisions folders. layout: "single" or "monorepo"."""
    root = Path(tempfile.mkdtemp())
    paths = MONOREPO if layout == "monorepo" else {"spec": "docs", "contracts": "docs",
                                                   "decisions": "docs/decisions", "changelog": "CHANGELOG.md"}
    docs, contracts, decisions = root / paths["spec"], root / paths["contracts"], root / paths["decisions"]
    for d in (docs / "research", docs / "features", decisions, contracts / "schemas"):
        d.mkdir(parents=True, exist_ok=True)
    cfg = {"product": "X", "goal": "learn", "stage": stage, "modules": [{"code": c, "name": c} for c in modules]}
    if layout == "monorepo":
        cfg["paths"] = dict(paths)
    cfg.update(config or {})
    (docs / "rspec.json").write_text(json.dumps(cfg), encoding="utf-8")
    for name, text in (research if research is not None else {"iss-issues.md": "# ISS"}).items():
        (docs / "research" / name).write_text(text, encoding="utf-8")
    rows = "".join(f"| {i} | {i.split('-')[1]} | Feature | Does it | {p} | {'r' if p == 'Drop' else ''} |\n" for i, p in features)
    (docs / "features.md").write_text("| ID | Module | Feature | Behaviour | Priority | Reason |\n" + rows, encoding="utf-8")
    if stories is None:
        stories = {f"{i}-x.md": story(i) for i, p in features if p == "MVP"}
    for name, text in stories.items():
        (docs / "features" / name).write_text(text, encoding="utf-8")
    for rel, text in (files or {}).items():
        if rel in ("openapi.json", "asyncapi.json") or rel.startswith("schemas/"):
            p = contracts / rel
        elif rel.startswith("decisions/"):
            p = decisions / rel.split("/", 1)[1]
        else:
            p = docs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    for rel, text in (root_files or {}).items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root

def run(script, root, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / script), str(root), *args], capture_output=True, text=True)
