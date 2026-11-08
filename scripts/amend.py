#!/usr/bin/env python3
"""Change one acceptance criterion after handoff: the only path for a spec question to change the spec.

Usage: amend.py [project-root | spec-folder] <criterion ID> --text "<Given …, when …, then …. `[tag]`>" --reason "<why>"
       amend.py [project-root | spec-folder] <feature ID> --new --text "<…>" --reason "<why>"
       amend.py [project-root | spec-folder] <criterion ID> --test --reason "<why the recorded test is wrong>"
       add --finding <finding-v1 file> to answer a finding (sdlc spec question, bug-hunter spec gap)
Checks the new text against contracts C1 before writing anything, keeps the ID (a new criterion gets the next unused
number), drops the criterion to level 0 (audit and verify levels and, with --test, the recorded test), adds a
changelog line, and regenerates the lock with check_spec.py. Names `/rspec:verify --only <feature>` when a reference
is configured.
"""
import json, re, subprocess, sys
from datetime import date
from pathlib import Path
from rspec_lib import open_layout, stories, contracts

SCRIPTS = Path(__file__).resolve().parent
ID_PREFIX = re.compile(r"^(\s*[-*] (?:\[[ xX]\] )?\*\*[^*]+\*\*)")


def flag(name):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv and sys.argv.index(name) + 1 < len(sys.argv) else None


def fail(msg):
    print(f"ERROR {msg}")
    sys.exit(1)


def read_finding(path):
    f = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    errors = [m for s, m in contracts.check_finding(f) if s == "error"]
    if errors:
        fail(f"{path}: not a valid finding-v1: {'; '.join(errors)}")
    route = contracts.finding_route(f)
    if route is None:
        fail(f"{f['id']}: not routed: verified_by is not reproduced (contracts C6)")
    if route != "rspec":
        fail(f"{f['id']}: route is {route}, not rspec: only a spec-gap finding changes the spec")
    return f


def main():
    values = {"--text", "--reason", "--finding"}
    pos = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] not in values]
    reason, text, new, test = flag("--reason"), flag("--text"), "--new" in sys.argv, "--test" in sys.argv
    finding = read_finding(flag("--finding")) if flag("--finding") else None
    if not pos or not reason or (not test and not text):
        fail("usage: amend.py <root> <criterion ID> --text \"…\" --reason \"…\" (or --new, --test, --finding <file>)")
    layout, cfg = open_layout(pos[0])
    if layout is None:
        fail("no rspec.json found")
    target = pos[1] if len(pos) > 1 else (finding or {}).get("criterion")
    if not target:
        fail("name the criterion (the finding has none)")
    fid = target if new else target.split(".AC")[0]
    story_map = stories(layout.spec)
    if fid not in story_map:
        fail(f"{fid}: no story in features/")
    path, _, _ = story_map[fid]
    raw = path.read_bytes().decode("utf-8")
    bom = "﻿" if raw.startswith("﻿") else ""
    crlf = "\r\n" in raw
    lines = raw[len(bom):].replace("\r\n", "\n").split("\n")

    head = next((i for i, l in enumerate(lines) if re.match(r"^##\s*Acceptance criteria\s*$", l)), None)
    if head is None:
        fail(f"{path.name}: no ## Acceptance criteria section")
    end = next((i for i in range(head + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    ids = [(i, contracts.ACTIVE.match(m.group("body"))) for i in range(head + 1, end)
           for m in [contracts.CRIT_LINE.match(lines[i])] if m]
    if new:
        used = [int(n) for n in re.findall(re.escape(fid) + r"\.AC(\d+)\b", raw)]
        lock = layout.spec / "criteria.lock.json"
        if lock.exists():
            used += [int(c["id"].split(".AC")[1]) for c in json.loads(lock.read_text(encoding="utf-8")).get("criteria", [])
                     if c["id"].startswith(fid + ".AC")]
        cid = f"{fid}.AC{max(used, default=0) + 1}"
        at = (ids[-1][0] + 1) if ids else head + 1
        lines.insert(at, f"- [ ] **{cid}** {text}")
    else:
        cid = target
        hit = [i for i, a in ids if a and a.group("id") == cid]
        if not hit:
            fail(f"{cid}: no active criterion with that ID in {path.name}")
        at = hit[0]
        if text:
            lines[at] = f"{ID_PREFIX.match(lines[at]).group(1)} {text}"
    if text:
        domain = layout.spec / "domain.md"
        domain_text = domain.read_text(encoding="utf-8-sig") if domain.exists() else None
        problems = [m for s, m in contracts.check_criteria("## Acceptance criteria\n" + lines[at], "rspec", domain_text)
                    if s == "error"]
        if problems:
            fail(f"{cid}: the new text breaks contracts C1, nothing written: {'; '.join(problems)}")

    if text:
        out = "\n".join(lines)
        path.write_bytes((bom + (out.replace("\n", "\r\n") if crlf else out)).encode("utf-8"))
    if test:
        for folder, ext in (("http", ".yaml"), ("e2e", ".spec.ts"), ("mobile", ".yaml"), ("cli", ".yaml")):
            recorded = layout.spec / "acceptance" / folder / f"{cid}{ext}"
            if recorded.exists():
                recorded.unlink()
                print(f"removed {recorded.relative_to(layout.spec).as_posix()}")
    for rel in ("audit/levels.json", "verify/levels.json"):
        levels = layout.spec / rel
        if levels.exists():
            data = json.loads(levels.read_text(encoding="utf-8"))
            if cid in (data.get("criteria") or {}):
                del data["criteria"][cid]
                levels.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    note = f"- {date.today().isoformat()} Amend {cid}: {reason}" + (" (new criterion)" if new else "") + \
        (" (recorded test removed for re-record)" if test else "") + (f" (finding {finding['id']})" if finding else "")
    log = layout.changelog
    body = log.read_text(encoding="utf-8-sig") if log.exists() else "# Changelog\n\n## [Unreleased]\n"
    m = re.search(r"^## \[Unreleased\][^\n]*\n", body, re.M)
    body = body[:m.end()] + note + "\n" + body[m.end():] if m else body.rstrip("\n") + "\n" + note + "\n"
    log.write_text(body, encoding="utf-8", newline="\n")
    print(f"amended {cid} in {path.name}; changelog: {note[2:]}")

    check = subprocess.run([sys.executable, str(SCRIPTS / "check_spec.py"), pos[0]], capture_output=True, text=True)
    print(check.stdout.rstrip())
    if ((cfg.get("reference") or {}).get("run") or {}).get("kind") in ("local", "url"):
        print(f"next: /rspec:verify --only {fid}")
    sys.exit(check.returncode)


if __name__ == "__main__":
    main()
