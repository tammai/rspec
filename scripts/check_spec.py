#!/usr/bin/env python3
"""Validate an rspec spec folder.

Usage: check_spec.py [project-root | spec-folder]
Exit code 1 if any ERROR is found. WARN lines do not fail.
"""
import json, re, sys
from pathlib import Path
from rspec_lib import (STAGES, PRIORITIES, STATUSES, ID_RE, FILE_ID_RE, TEMPLATES, open_layout, feature_rows,
                       stories, dependencies, find_cycles, feature_refs, contract_files, adr_statuses,
                       build_slices, GOALS, md_table, readiness_open, parked_decisions, in_scope,
                       slice_criteria, SDLC_MAX_CRITERIA)

STORY_TPL = TEMPLATES / "feature-story.md"
PLACEHOLDERS = set(re.findall(r"<[^<>\n]+>", STORY_TPL.read_text(encoding="utf-8-sig"))) if STORY_TPL.exists() else set()
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
GHERKIN = re.compile(r"\bgiven\b.*\bwhen\b.*\bthen\b", re.I)


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "."
    errors, warns = [], []
    E, W = errors.append, warns.append

    try:
        layout, cfg = open_layout(arg)
    except json.JSONDecodeError as e:
        print(f"ERROR rspec.json is not valid JSON: {e}"); sys.exit(1)
    if layout is None:
        print(f"ERROR no rspec.json under {arg}/docs or {arg}/docs/specs/*. Run /rspec:init first."); sys.exit(1)
    docs, contracts = layout.spec, layout.contracts

    stage = cfg.get("stage", "init")
    if stage not in STAGES: E(f"rspec.json: unknown stage '{stage}'")
    si = STAGES.index(stage) if stage in STAGES else 0
    if not cfg.get("product"): E("rspec.json: 'product' is empty")
    if cfg.get("goal") not in GOALS: E("rspec.json: goal must be 'learn', 'personal-use' or 'production'")
    production = cfg.get("goal") == "production"
    track = cfg.get("track", "rspec")
    if track not in ("rspec", "modernize"): E(f"rspec.json: track '{track}' must be 'rspec' or 'modernize'")
    modernize = track == "modernize"
    if not modernize and cfg.get("code"):
        src = cfg.get("sources") or {}
        if not src.get("repo"): E("rspec.json: code is true but sources.repo is empty")
        if not src.get("commit"): E("rspec.json: reading the product's code: pin the commit in sources.commit")
    if modernize and cfg.get("strategy") not in ("rewrite", "strangler", "refactor"):
        E("rspec.json: a modernize spec needs strategy 'rewrite', 'strangler' or 'refactor'")

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
                W(f"no research file for module {c} in research/")
    for p in research:
        if EMAIL.search(p.read_text(encoding="utf-8-sig")):
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
    scope = cfg.get("scope")
    if scope not in (None, "full", "mvp"): E(f"rspec.json: scope '{scope}' must be 'full' or 'mvp'")
    scoped = in_scope(feats, cfg)

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
    for cycle in find_cycles(dependencies(story_map)):
        E(f"dependency cycle: {' -> '.join(cycle)}")
    if si >= 3:
        for fid in scoped:
            if fid not in story_map: E(f"{feats[fid]} {fid} has no story file in features/")

    # contracts (OpenAPI, AsyncAPI, JSON Schema)
    referenced = set()
    if si >= 4:
        if not (contracts / "openapi.json").exists(): E("openapi.json missing; re-run /rspec:tech")
        if not list((contracts / "schemas").glob("*.json")): E("schemas/ has no JSON Schema files; re-run /rspec:tech")
        for f in ("api.md", "data-model.md", "nfr.md"):
            t = (docs / f).read_text(encoding="utf-8-sig") if (docs / f).exists() else ""
            if len(t.strip().splitlines()) < 8: W(f"{f} looks mostly empty")
    for f in contract_files(contracts):
        rel = f.relative_to(contracts).as_posix()
        try:
            doc = json.loads(f.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as e:
            E(f"{rel}: not valid JSON: {e}"); continue
        if f.name == "openapi.json" and not str(doc.get("openapi", "")).startswith("3.1"):
            E(f"{rel}: 'openapi' must be 3.1.x")
        if f.name == "asyncapi.json" and not str(doc.get("asyncapi", "")).startswith("3."):
            E(f"{rel}: 'asyncapi' must be 3.x")
        for ref in feature_refs(doc):
            if feats and ref not in feats: E(f"{rel}: x-features references unknown {ref}")
            referenced.add(ref)
    if si >= 4 and modernize:
        dm = docs / "data-migration.md"
        if not dm.exists():
            E("data-migration.md missing; a modernize spec needs one, re-run /rspec:tech")
        else:
            mapping = md_table(dm.read_text(encoding="utf-8-sig"), "M-")
            if not mapping: E("data-migration.md: no mapping rows (M-01, ...)")
            for row in mapping:
                if not row.get("Validation"):
                    E(f"data-migration.md: {row.get('ID')} has no Validation (how you prove the data moved intact)")
    if si >= 4 and production:
        nfr = (docs / "nfr.md").read_text(encoding="utf-8-sig") if (docs / "nfr.md").exists() else ""
        rows = md_table(nfr, "NFR-")
        if not rows: E("nfr.md: production needs NFR rows (NFR-01, ...)")
        for row in rows:
            if not row.get("Verification"):
                E(f"nfr.md: {row.get('ID')} has no Verification (the test, monitor or review that proves it)")
        tm = docs / "threat-model.md"
        if not tm.exists():
            E("threat-model.md missing; production needs one, re-run /rspec:tech (nfr area)")
        else:
            threats = md_table(tm.read_text(encoding="utf-8-sig"), "T-")
            if not threats: E("threat-model.md: no threats listed (T-01, ...)")
            for row in threats:
                if not row.get("Mitigation"):
                    E(f"threat-model.md: {row.get('ID')} has no Mitigation")
    if si >= 4:
        for fid in scoped:
            if fid not in referenced: W(f"{feats[fid]} {fid} is not served by any operation or schema (x-features)")
        if not (cfg.get("deploy") or "").strip():
            W("rspec.json 'deploy' is empty; the stack ADR needs the deployment target (e.g. Cloudflare Workers, Vercel, a VPS, local only)")

    # ADRs and handoff
    adrs = adr_statuses(layout.decisions)
    nums = []
    for name in adrs:
        m = re.match(r"(\d{4})-", name)
        if not m: E(f"decisions/{name}: name must start with NNNN-"); continue
        nums.append(int(m.group(1)))
    if nums and sorted(nums) != list(range(1, len(nums) + 1)):
        W(f"ADR numbers not contiguous from 0001: {sorted(nums)}")
    if si >= 5:
        plan = docs / "build-plan.md"
        text = plan.read_text(encoding="utf-8-sig") if plan.exists() else ""
        if not text: E("build-plan.md missing; run /rspec:handoff")
        if not (cfg.get("stack") or "").strip() or cfg.get("stack") == "undecided":
            W("rspec.json 'stack' is empty; record the stack the accepted stack ADR chose")
        for fid in scoped:
            if text and fid not in text: E(f"build-plan.md does not include {feats[fid]} {fid}")
        if (cfg.get("build") or {}).get("engine") == "sdlc":
            for num, name, ids in build_slices(docs):
                total = slice_criteria(story_map, ids)
                if total > SDLC_MAX_CRITERIA:
                    W(f"build-plan.md: Slice {num} has {total} acceptance criteria; sdlc takes about 10 per change, split it")
        if modernize:
            cp = docs / "cutover-plan.md"
            if not cp.exists():
                E("cutover-plan.md missing; run /rspec:handoff")
            elif not re.search(r"^##\s*Rollback", cp.read_text(encoding="utf-8-sig"), re.M | re.I):
                E("cutover-plan.md has no '## Rollback' section")
        if production:
            ready = docs / "production-readiness.md"
            if not ready.exists():
                E("production-readiness.md missing; run /rspec:handoff")
            else:
                left = sum(len(v) for v in readiness_open(ready).values())
                if left: W(f"production-readiness.md: {left} item(s) still open; the pipeline is not done until they are")
        for name, status in adrs.items():
            if status.lower() == "proposed": E(f"decisions/{name} is still Proposed; accept or reject it before building")

    parked = parked_decisions(docs)
    if parked:
        W(f"{len(parked)} autopilot decision(s) parked for you in autopilot-log.md")

    print(f"product={cfg.get('product')} stage={stage} modules={len(codes)} features={len(feats)} "
          f"mvp={len(mvp)} stories={len(story_map)} contracts={len(contract_files(contracts))} adrs={len(adrs)}")
    for w in warns: print("WARN ", w)
    for e in errors: print("ERROR", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
