#!/usr/bin/env python3
"""Validate an rspec docs/ folder.

Usage: check_spec.py [project-root] [--stage STAGE]
Exit code 1 if any ERROR is found. WARN lines do not fail.
"""
import json, re, sys
from pathlib import Path

PRIORITIES = {"MVP", "Later", "Drop"}
STAGES = ["init", "discovered", "features-approved", "stories", "tech"]
ID_RE = re.compile(r"^F-([A-Z]{2,4})-(\d{2,3})$")
STORY_TPL = Path(__file__).resolve().parent.parent / "templates" / "feature-story.md"
PLACEHOLDERS = set(re.findall(r"<[^<>\n]+>",STORY_TPL.read_text(encoding="utf-8"))) if STORY_TPL.exists() else set()

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = Path(args[0] if args else ".")
    docs = root / "docs"
    errors, warns = [], []
    E, W = errors.append, warns.append

    cfg_path = docs / "rspec.json"
    if not cfg_path.exists():
        print(f"ERROR {cfg_path} not found. Run /rspec:init first."); sys.exit(1)
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR rspec.json is not valid JSON: {e}"); sys.exit(1)

    stage = cfg.get("stage", "init")
    if stage not in STAGES: E(f"rspec.json: unknown stage '{stage}'")
    si = STAGES.index(stage) if stage in STAGES else 0
    if not cfg.get("product"): E("rspec.json: 'product' is empty")
    if cfg.get("goal") not in ("learn", "personal-use"): E("rspec.json: goal must be 'learn' or 'personal-use'")

    codes = {}
    for m in cfg.get("modules", []):
        c = m.get("code", "")
        if not re.fullmatch(r"[A-Z]{2,4}", c): E(f"module '{m.get('name')}': code '{c}' must be 2-4 uppercase letters")
        if c in codes: E(f"duplicate module code {c}")
        codes[c] = m.get("name", "")
    if si >= 1 and not codes: E("stage >= discovered but no modules defined")

    if si >= 1:
        for c in codes:
            if not list((docs / "research").glob(f"{c.lower()}*.md")) and not list((docs / "research").glob(f"{c}*.md")):
                W(f"no research file for module {c} in docs/research/")
        email = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
        for p in sorted((docs / "research").glob("*.md")):
            if email.search(p.read_text(encoding="utf-8")):
                W(f"research/{p.name}: contains an email address; remove personal data before committing")

    # features.md
    feats = {}
    fpath = docs / "features.md"
    if fpath.exists():
        for n, line in enumerate(fpath.read_text(encoding="utf-8").splitlines(), 1):
            if not line.startswith("|"): continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cells or not cells[0].startswith("F-"): continue
            fid = cells[0]
            mm = ID_RE.match(fid)
            if not mm: E(f"features.md:{n} bad ID '{fid}' (expected F-CODE-NN)"); continue
            if codes and mm.group(1) not in codes: E(f"features.md:{n} {fid} uses unknown module code {mm.group(1)}")
            if fid in feats: E(f"features.md:{n} duplicate ID {fid}")
            prio = cells[4] if len(cells) > 4 else ""
            reason = cells[5] if len(cells) > 5 else ""
            if prio not in PRIORITIES: E(f"features.md:{n} {fid} priority '{prio}' must be MVP/Later/Drop")
            if prio == "Drop" and not reason: E(f"features.md:{n} {fid} is Drop without a reason")
            feats[fid] = prio
    if si >= 2 and not feats: E("stage >= features-approved but features.md has no rows")

    mvp = sorted(k for k, v in feats.items() if v == "MVP")
    if len(mvp) > 25: W(f"{len(mvp)} MVP features; consider trimming (guideline ~25)")

    # stories
    story_ids = {}
    for p in sorted((docs / "features").glob("F-*.md")):
        m = re.match(r"(F-[A-Z]{2,4}-\d{2,3})", p.name)
        if not m: E(f"{p.name}: file name must start with feature ID"); continue
        fid = m.group(1)
        story_ids[fid] = p
        if feats and fid not in feats: E(f"{p.name}: {fid} not listed in features.md")
        text = p.read_text(encoding="utf-8")
        sec = re.search(r"^##\s*(Acceptance criteria|Tiêu chí[^\n]*)\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
        if not sec: E(f"{p.name}: missing '## Acceptance criteria' section")
        elif not re.search(r"^\s*-\s*\[[ xX]\]\s+\S", sec.group(2), re.M):
            E(f"{p.name}: acceptance criteria has no '- [ ]' items")
        left = sorted(ph for ph in PLACEHOLDERS if ph in text)
        if left: E(f"{p.name}: template placeholders left in file: {', '.join(left)}")
    if si >= 3:
        for fid in mvp:
            if fid not in story_ids: E(f"MVP {fid} has no story file in docs/features/")

    # ADRs
    adrs = sorted((docs / "decisions").glob("*.md"))
    nums = []
    for p in adrs:
        m = re.match(r"(\d{4})-", p.name)
        if not m: E(f"decisions/{p.name}: name must start with NNNN-"); continue
        nums.append(int(m.group(1)))
    if nums and sorted(nums) != list(range(1, len(nums) + 1)):
        W(f"ADR numbers not contiguous from 0001: {sorted(nums)}")
    if si >= 4:
        for f in ("api.md", "data-model.md", "nfr.md"):
            t = (docs / f).read_text(encoding="utf-8") if (docs / f).exists() else ""
            if len(t.strip().splitlines()) < 8: W(f"{f} looks mostly empty")

    print(f"product={cfg.get('product')} stage={stage} modules={len(codes)} "
          f"features={len(feats)} mvp={len(mvp)} stories={len(story_ids)} adrs={len(adrs)}")
    for w in warns: print("WARN ", w)
    for e in errors: print("ERROR", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
