import json, subprocess, sys, tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

def story(fid, depends=(), status="todo", criteria="- [ ] Given an empty list, when I create an issue, then it appears with the next number.",
          edge="- Empty title: the issue is not created and an error is shown."):
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

## Edge cases
{edge}

## Differences from the original
- none

## Sources
- research/iss-issues.md, Flows
"""

def project(stage="stories", modules=("ISS",), features=(("F-ISS-01", "MVP"),), stories=None,
            research=None, files=None):
    """features: (id, priority); stories: {filename: text}; files: {relpath under docs: text}."""
    root = Path(tempfile.mkdtemp())
    docs = root / "docs"
    for d in ("research", "features", "decisions", "schemas"):
        (docs / d).mkdir(parents=True)
    (docs / "rspec.json").write_text(json.dumps({"product": "X", "goal": "learn", "stage": stage,
        "modules": [{"code": c, "name": c} for c in modules]}), encoding="utf-8")
    for name, text in (research if research is not None else {"iss-issues.md": "# ISS"}).items():
        (docs / "research" / name).write_text(text, encoding="utf-8")
    rows = "".join(f"| {i} | {i.split('-')[1]} | Feature | Does it | {p} | {'r' if p == 'Drop' else ''} |\n" for i, p in features)
    (docs / "features.md").write_text("| ID | Module | Feature | Behaviour | Priority | Reason |\n" + rows, encoding="utf-8")
    if stories is None:
        stories = {f"{i}-x.md": story(i) for i, p in features if p == "MVP"}
    for name, text in stories.items():
        (docs / "features" / name).write_text(text, encoding="utf-8")
    for rel, text in (files or {}).items():
        p = docs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root

def run(script, root, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / script), str(root), *args], capture_output=True, text=True)
