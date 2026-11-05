#!/usr/bin/env python3
"""Validate an rspec docs/ folder.

Usage: check_spec.py [project-root]
Exit code 1 if any ERROR is found. WARN lines do not fail.
"""
import json, re, sys
from pathlib import Path
from rspec_lib import (STAGES, PRIORITIES, STATUSES, ID_RE, FILE_ID_RE, TEMPLATES, load_config, feature_rows,
                       stories, dependencies, find_cycle, feature_refs, contract_files, adr_statuses)

STORY_TPL = TEMPLATES / "feature-story.md"
PLACEHOLDERS = set(re.findall(r"<[^<>\n]+>", STORY_TPL.read_text(encoding="utf-8"))) if STORY_TPL.exists() else set()
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
GHERKIN = re.compile(r"\bgiven\b.*\bwhen\b.*\bthen\b", re.I)


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    docs = root / "docs"
    errors, warns = [], []
    E, W = errors.append, warns.append

    if not (docs / "rspec.json").exists():
        print(f"ERROR {docs / 'rspec.json'} not found. Run /rspec:init first."); sys.exit(1)
    try:
        cfg = load_config(docs)
    except json.JSONDecodeError as e:
        print(f"ERROR rspec.json is not valid JSON: {e}"); sys.exit(1)

    stage = cfg.get("stage", "init")
    if stage not in STAGES: E(f"rspec.json: unknown stage '{stage}'")
    si = STAGES.index(stage) if stage in STAGES else 0
    if not cfg.get("product"): E("rspec.json: 'product' is empty")
    if cfg.get("goal") not in ("learn", "personal-use"): E("rspec.json: goal must be 'learn' or 'personal-use'")

    # modules and research
    codes = {}
    for m in cfg.get("modules", []):
        c = m.get("code", "")
        if not re.fullmatch(r"[A-Z]{2,4}", c): E(f"module '{m.get('name')}': code '{c}' must be 2-4 uppercase letters")
        if c in codes: E(f"duplicate module code {c}")
        codes[c] = m.get("name", "")
    if si >= 1 and not codes: E("stage >= discovered but no modules defined")
    research = sorted((docs / "research").glob("*.md"))
    if si >= 1:
        for c in codes:
            if not any(p.name.lower().startswith(c.lower() + "-") for p in research):
                W(f"no research file for module {c} in docs/research/")
    for p in research:
        if EMAIL.search(p.read_text(encoding="utf-8")):
            W(f"research/{p.name}: contains an email address; remove personal data before committing")

    # features.md
    feats = {}
    for n, cells in feature_rows(docs):
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
    mvp = [k for k, v in feats.items() if v == "MVP"]
    if len(mvp) > 25: W(f"{len(mvp)} MVP features; consider trimming (guideline ~25)")

    # stories
    story_map = stories(docs)
    for p in sorted((docs / "features").glob("F-*.md")):
        if not FILE_ID_RE.match(p.name):
            E(f"{p.name}: file name must start with feature ID")
    for fid, (p, text, fm) in story_map.items():
        if feats and fid not in feats: E(f"{p.name}: {fid} not listed in features.md")
        if fm is None:
            E(f"{p.name}: missing frontmatter (id, module, priority, depends_on, status); re-run /rspec:stories to upgrade")
        else:
            if fm.get("id") != fid: E(f"{p.name}: frontmatter id '{fm.get('id')}' does not match file name")
            if fm.get("status", "") not in STATUSES: E(f"{p.name}: status '{fm.get('status', '')}' must be todo/in-progress/done")
            for d in fm.get("depends_on") or []:
                if feats and d not in feats: E(f"{p.name}: depends on unknown {d}")
                elif feats.get(fid) == "MVP" and feats.get(d) and feats[d] != "MVP":
                    E(f"{p.name}: MVP {fid} depends on {d} which is {feats[d]}")
        sec = re.search(r"^##\s*(Acceptance criteria|Tiêu chí[^\n]*)\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
        if not sec:
            E(f"{p.name}: missing '## Acceptance criteria' section")
        else:
            items = re.findall(r"^\s*-\s*\[[ xX]\]\s+(\S.*)$", sec.group(2), re.M)
            if not items: E(f"{p.name}: acceptance criteria has no '- [ ]' items")
            loose = [i for i in items if not GHERKIN.search(i)]
            if loose: W(f"{p.name}: {len(loose)} criteria not in 'Given …, when …, then …' form")
        left = sorted(ph for ph in PLACEHOLDERS if ph in text)
        if left: E(f"{p.name}: template placeholders left in file: {', '.join(left)}")
    cycle = find_cycle(dependencies(story_map))
    if cycle: E(f"dependency cycle: {' -> '.join(cycle)}")
    if si >= 3:
        for fid in mvp:
            if fid not in story_map: E(f"MVP {fid} has no story file in docs/features/")

    # contracts (OpenAPI, AsyncAPI, JSON Schema)
    referenced = set()
    if si >= 4:
        if not (docs / "openapi.json").exists(): E("openapi.json missing; re-run /rspec:tech")
        if not list((docs / "schemas").glob("*.json")): E("schemas/ has no JSON Schema files; re-run /rspec:tech")
        for f in ("api.md", "data-model.md", "nfr.md"):
            t = (docs / f).read_text(encoding="utf-8") if (docs / f).exists() else ""
            if len(t.strip().splitlines()) < 8: W(f"{f} looks mostly empty")
    for f in contract_files(docs):
        rel = f.relative_to(docs).as_posix()
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            E(f"{rel}: not valid JSON: {e}"); continue
        if f.name == "openapi.json" and not str(doc.get("openapi", "")).startswith("3.1"):
            E(f"{rel}: 'openapi' must be 3.1.x")
        if f.name == "asyncapi.json" and not str(doc.get("asyncapi", "")).startswith("3."):
            E(f"{rel}: 'asyncapi' must be 3.x")
        for ref in feature_refs(doc):
            if feats and ref not in feats: E(f"{rel}: x-features references unknown {ref}")
            referenced.add(ref)
    if si >= 4:
        for fid in mvp:
            if fid not in referenced: W(f"MVP {fid} is not served by any operation or schema (x-features)")

    # ADRs and handoff
    adrs = adr_statuses(docs)
    nums = []
    for name in adrs:
        m = re.match(r"(\d{4})-", name)
        if not m: E(f"decisions/{name}: name must start with NNNN-"); continue
        nums.append(int(m.group(1)))
    if nums and sorted(nums) != list(range(1, len(nums) + 1)):
        W(f"ADR numbers not contiguous from 0001: {sorted(nums)}")
    if si >= 5:
        plan = docs / "build-plan.md"
        text = plan.read_text(encoding="utf-8") if plan.exists() else ""
        if not text: E("build-plan.md missing; run /rspec:handoff")
        for fid in mvp:
            if text and fid not in text: E(f"build-plan.md does not include MVP {fid}")
        for name, status in adrs.items():
            if status.lower() == "proposed": E(f"decisions/{name} is still Proposed; accept or reject it before building")

    print(f"product={cfg.get('product')} stage={stage} modules={len(codes)} features={len(feats)} "
          f"mvp={len(mvp)} stories={len(story_map)} contracts={len(contract_files(docs))} adrs={len(adrs)}")
    for w in warns: print("WARN ", w)
    for e in errors: print("ERROR", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
