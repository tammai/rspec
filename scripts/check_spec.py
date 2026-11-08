#!/usr/bin/env python3
"""Validate an rspec spec folder.

Usage: check_spec.py [project-root | spec-folder]
Exit code 1 if any ERROR is found. WARN lines do not fail.
"""
import json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from contract_checks import check_domain, check_bodies, server_set_not_readonly
from rspec_lib import (STAGES, PRIORITIES, STATUSES, ID_RE, FILE_ID_RE, TEMPLATES, open_layout, feature_rows,
                       stories, dependencies, find_cycles, feature_refs, contract_files, adr_statuses,
                       build_slices, GOALS, md_table, readiness_open, parked_decisions, in_scope,
                       slice_criteria, SDLC_MAX_CRITERIA, SLICE_BUDGET)

sys.path.insert(0, str(TEMPLATES.parent / "contracts" / "v1"))
import contracts

STORY_TPL = TEMPLATES / "feature-story.md"
PLACEHOLDERS = set(re.findall(r"<[^<>\n]+>", STORY_TPL.read_text(encoding="utf-8-sig"))) if STORY_TPL.exists() else set()
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# Format descriptors and example addresses, not personal data.
EMAIL_PLACEHOLDER = re.compile(
    r"\b(?:local|user|name|you|someone|me|operator|admin)@(?:domain|example|host|server)\.[\w.-]+",
    re.I)
AC_SECTION = re.compile(r"^##\s*Acceptance criteria\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)


SNAKE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$")
CAMEL = re.compile(r"^[a-z][a-z0-9]*([A-Z][a-z0-9]*)+$")


def property_names(obj):
    """Every key of every `properties` object in a JSON Schema or OpenAPI document."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "properties" and isinstance(v, dict):
                yield from v.keys()
            yield from property_names(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from property_names(v)


def _refs(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "$ref" and isinstance(v, str):
                yield v
            else:
                yield from _refs(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _refs(v)


def _pointer(doc, frag):
    for part in [p for p in frag.split("/") if p]:
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(doc, dict) and part in doc:
            doc = doc[part]
        elif isinstance(doc, list) and part.isdigit() and int(part) < len(doc):
            doc = doc[int(part)]
        else:
            return False
    return True


def broken_refs(path, doc):
    """Local and relative-file `$ref`s in a contract file that point nowhere (http refs are skipped)."""
    out = []
    for ref in dict.fromkeys(_refs(doc)):
        if re.match(r"^[a-z]+://", ref):
            continue
        target, _, frag = ref.partition("#")
        if target:
            p = (path.parent / target)
            try:
                tdoc = json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else None
            except json.JSONDecodeError:
                tdoc = None
            if tdoc is None or not _pointer(tdoc, frag):
                out.append(ref)
        elif not _pointer(doc, frag):
            out.append(ref)
    return out


def story_issues(text, module, domain):
    """Contracts C1/C2 for one story, with rspec's severities and hints."""
    lines = text.split("\n")
    issues = []
    for sev, msg in contracts.check_story(text):
        if msg.startswith("Acceptance criteria: "):
            continue  # re-checked below with domain.md, which check_story does not take
        m = re.match(r"line (\d+): ", msg)
        line = lines[int(m.group(1)) - 1].rstrip() if m else ""
        if "failure mode must end" in msg and line.endswith("→ TODO"):
            sev, msg = "warning", f"{m.group(0)}failure mode → TODO from migration; needs /rspec:stories {module}"
        elif "difference must end with" in msg:
            sev = "warning"  # an error once departures.yaml exists (R8)
        elif "Edge cases" in msg:
            msg += "; run scripts/migrate_criteria.py"
        issues.append((sev, msg))
    sec = AC_SECTION.search(text)
    if sec:
        loose = [i for i in re.findall(r"^\s*[-*] (?:\[[ xX]\] )?(\S.*)$", sec.group(1), re.M)
                 if not re.match(r"(~~)?\*\*", i)]
        if loose:
            issues.append(("error", f"{len(loose)} acceptance criteria have no ID (**F-…-NN.AC<n>**); "
                                    "run scripts/migrate_criteria.py"))
        for sev, msg in contracts.check_criteria(text, "rspec", domain):
            if not (loose and msg.startswith("no criterion line")):
                issues.append((sev, msg))
    return issues


def write_lock(layout, story_map, feats, E, W):
    """Write <spec>/criteria.lock.json (contracts C3); a criterion whose text changed drops to level 0."""
    path = layout.spec / "criteria.lock.json"
    prev = {}
    if path.exists():
        try:
            prev = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as e:
            E(f"criteria.lock.json is not valid JSON ({e}); restore it from git, or delete it to reset every level to 0")
            return
    old = {c.get("id"): c for c in prev.get("criteria") or []}
    criteria = []
    for fid, (p, text, fm) in story_map.items():
        sec = AC_SECTION.search(text)
        for line in (sec.group(1).split("\n") if sec else []):
            line = line.rstrip("\r")
            m = contracts.CRIT_LINE.match(line)
            a = contracts.ACTIVE.match(m.group("body")) if m else None
            if not a:
                continue
            cid, sha = a.group("id"), contracts.criterion_text_sha256(line)
            tag = next(t for t in contracts.TAG.findall(a.group("rest")) if t in contracts.REVERSE_TAGS)
            entry = {"id": cid, "feature": fid, "file": p.relative_to(layout.spec).as_posix(), "text_sha256": sha,
                     "tag": tag, "priority": feats.get(fid) or (fm or {}).get("priority") or None,
                     "level": 0, "test": None, "departures": []}
            was = old.get(cid)
            if was:
                entry.update(test=was.get("test"), departures=was.get("departures") or [])
                if was.get("text_sha256") == sha:
                    entry["level"] = was.get("level", 0)
                else:
                    W(f"{cid}: text changed since the last lock (level {was.get('level', 0)} → 0); needs re-verify")
            criteria.append(entry)
    unchanged = prev.get("criteria") == criteria and prev.get("generated")
    lock = {"contracts": contracts.VERSION, "spec": layout.spec.relative_to(layout.root).as_posix(),
            "generated": prev["generated"] if unchanged else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "criteria": criteria}
    issues = [m for s, m in contracts.check_lock(lock, str(layout.root)) if s == "error"]
    for m in issues:
        E(f"criteria.lock.json: {m}")
    if not issues and lock != prev:
        path.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


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
    for m in cfg.get("modules") or []:
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
        hits = [m.group(0) for m in EMAIL.finditer(p.read_text(encoding="utf-8-sig"))
                if not EMAIL_PLACEHOLDER.fullmatch(m.group(0))]
        if hits:
            W(f"research/{p.name}: contains an email address ({hits[0]}); remove personal data before committing")

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
    domain_text = (docs / "domain.md").read_text(encoding="utf-8-sig") if (docs / "domain.md").exists() else None
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
            if "also_needs" in fm:
                W(f"{p.name}: also_needs not merged yet; run scripts/merge_deps.py")
            for d in fm.get("depends_on") or []:
                if feats and d not in feats: E(f"{p.name}: depends on unknown {d}")
                elif feats.get(fid) == "MVP" and feats.get(d) and feats[d] != "MVP":
                    E(f"{p.name}: MVP {fid} depends on {d} which is {feats[d]}")
        for sev, msg in story_issues(text, (fm or {}).get("module") or fid.split("-")[1], domain_text):
            (E if sev == "error" else W)(f"{p.name}: {msg}")
        left = sorted(ph for ph in PLACEHOLDERS if ph in text)
        if left: E(f"{p.name}: template placeholders left in file: {', '.join(left)}")
    for cycle in find_cycles(dependencies(story_map)):
        E(f"dependency cycle: {' -> '.join(cycle)}")
    if si >= 3:
        for fid in scoped:
            if fid not in story_map: E(f"{feats[fid]} {fid} has no story file in features/")

    # contracts (OpenAPI, AsyncAPI, JSON Schema)
    referenced = set()
    casing = {"snake_case": set(), "camelCase": set()}
    parsed = {}
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
        if not isinstance(doc, dict):
            E(f"{rel}: top level must be a JSON object"); continue
        parsed[rel] = doc
        if f.name == "openapi.json" and not str(doc.get("openapi", "")).startswith("3.1"):
            E(f"{rel}: 'openapi' must be 3.1.x")
        if f.name == "asyncapi.json" and not str(doc.get("asyncapi", "")).startswith("3."):
            E(f"{rel}: 'asyncapi' must be 3.x")
        for ref in broken_refs(f, doc):
            E(f"{rel}: $ref '{ref}' does not resolve")
        for ref in feature_refs(doc):
            if feats and ref not in feats: E(f"{rel}: x-features references unknown {ref}")
            referenced.add(ref)
        for name in property_names(doc):
            if SNAKE.match(name): casing["snake_case"].add(name)
            elif CAMEL.match(name): casing["camelCase"].add(name)
    if casing["snake_case"] and casing["camelCase"]:
        W("contracts mix field-name casings: " + ", ".join(
            f"{len(v)} {k} (e.g. {', '.join(sorted(v)[:3])})" for k, v in casing.items()) + "; use one")
    loose_ids = [f"{rel} {p}" for rel, d in parsed.items() if rel.startswith("schemas/") for p in server_set_not_readonly(d)]
    if loose_ids:
        W(f"{len(loose_ids)} required server-set fields are not readOnly, so create bodies cannot validate "
          f"(e.g. {', '.join(loose_ids[:3])})")
    for e in check_bodies(parsed.get("openapi.json"), contracts / "schemas"): E(e)
    domain = docs / "domain.md"
    if domain.exists():
        de, dw = check_domain(domain.read_text(encoding="utf-8-sig"), parsed.get("openapi.json"), parsed)
        errors.extend(de); warns.extend(dw)
    elif si >= 3:
        W("domain.md missing: roles, permissions, enumerations and limits are restated per story; run /rspec:features to write it")
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
            ui_only = str(((story_map.get(fid) or (None, None, None))[2] or {}).get("ui_only", "")).lower() == "true"
            if fid not in referenced and not ui_only: W(f"{feats[fid]} {fid} is not served by any operation or schema (x-features)")
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
        if text and not build_slices(docs) and re.search(r"^#{3,}\s*Slice\s+\d", text, re.M):
            E("build-plan.md: slice headings must be '## Slice N', not '### Slice N'; none were parsed")
        if not (cfg.get("stack") or "").strip() or cfg.get("stack") == "undecided":
            W("rspec.json 'stack' is empty; record the stack the accepted stack ADR chose")
        plan_ids = set(re.findall(r"\bF-[A-Z]{2,4}-\d{2,3}\b", text))  # whole IDs: F-X-10 is not F-X-100
        for fid in scoped:
            if text and fid not in plan_ids: E(f"build-plan.md does not include {feats[fid]} {fid}")
        sliced = {i for _, _, ids in build_slices(docs) for i in ids}
        for fid in sorted(i for i, p in feats.items() if p == "Drop" and i in sliced):
            E(f"build-plan.md still includes Drop {fid}; run /rspec:features triage")
        sdlc = (cfg.get("build") or {}).get("engine") == "sdlc"
        for num, name, ids in build_slices(docs):
            total = slice_criteria(story_map, ids)
            if sdlc and total > SDLC_MAX_CRITERIA:
                W(f"build-plan.md: Slice {num} has {total} acceptance criteria; sdlc takes about 10 per change, split it")
            elif not sdlc and total > SLICE_BUDGET and len(ids) > 1:
                W(f"build-plan.md: Slice {num} has {total} acceptance criteria; keep a slice to about {SLICE_BUDGET}, split it")
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

    if not errors:
        write_lock(layout, story_map, feats, E, W)

    print(f"product={cfg.get('product')} stage={stage} modules={len(codes)} features={len(feats)} "
          f"mvp={len(mvp)} stories={len(story_map)} contracts={len(contract_files(contracts))} adrs={len(adrs)}")
    for w in warns: print("WARN ", w)
    for e in errors: print("ERROR", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
