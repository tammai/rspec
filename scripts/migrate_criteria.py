#!/usr/bin/env python3
"""Bring stories written before rspec 0.11 to contracts C1/C2. Safe to run again: a migrated story is left as is.

Usage: migrate_criteria.py [project-root | spec-folder]
Gives each criterion without an ID the next free `<feature>.AC<n>` in file order, turns `## Edge cases` into
`## Failure modes` lines ending `→ TODO` (the next /rspec:stories pass links each to a criterion), moves any text
after a criterion's last tag (a `repo@commit path:line` citation) unchanged into `## Sources`, and adds the
`Failure modes` and `Must never break` sections a story lacks.
"""
import re, sys
from rspec_lib import open_layout, stories

HEADING = re.compile(r"^##\s+(.+?)\s*$")
LOOSE = re.compile(r"^(\s*[-*] (?:\[[ xX]\] )?)(?!~~|\*\*|\[[ xX]\] )(\S.*)$")
ITEM = re.compile(r"^\s*[-*] (.*)$")
TAG = re.compile(r"`\[[^\]`]*\]`")
CITED = re.compile(r"^\s*[-*] (?:\[[ xX]\] )?\*\*(?P<id>[^*]+)\*\*")


def sections(lines):
    """[(title or None, start, end)] for the `## ` sections of a story, the preamble first."""
    heads = [(i, HEADING.match(l).group(1)) for i, l in enumerate(lines) if HEADING.match(l)]
    out = [(None, 0, heads[0][0] if heads else len(lines))]
    for k, (i, title) in enumerate(heads):
        out.append((title, i, heads[k + 1][0] if k + 1 < len(heads) else len(lines)))
    return out


def find(lines, title):
    return next(((s, e) for t, s, e in sections(lines) if t and t.lower() == title.lower()), None)


def body_end(lines, start, end):
    """Index after the section's last non-blank line, so inserted lines sit before the blank line that follows it."""
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    return end


def migrate(text, fid):
    lines = text.split("\n")
    ac = find(lines, "Acceptance criteria")
    if ac:
        used = [int(n) for n in re.findall(re.escape(fid) + r"\.AC(\d+)\b", text)]
        n = max(used, default=0)
        for i in range(ac[0] + 1, ac[1]):
            m = LOOSE.match(lines[i])
            if m:
                n += 1
                lines[i] = f"{m.group(1)}**{fid}.AC{n}** {m.group(2)}"
    moved = []
    for i in range(ac[0] + 1, ac[1]) if ac else ():
        c, tags = CITED.match(lines[i]), list(TAG.finditer(lines[i]))
        if c and tags and lines[i][tags[-1].end():].strip():
            moved.append(f"- {c.group('id')}: {lines[i][tags[-1].end():].strip()}")
            lines[i] = lines[i][:tags[-1].end()]
    edge = find(lines, "Edge cases")
    if edge:
        todo = []
        for line in lines[edge[0] + 1:edge[1]]:
            m = ITEM.match(line)
            if m and m.group(1).strip().lower() != "none":
                todo.append(line if "→" in m.group(1) else f"{line.rstrip()} → TODO")
        fm = find(lines, "Failure modes")
        if fm:
            del lines[edge[0]:edge[1]]
            fm = find(lines, "Failure modes")
            at = body_end(lines, *fm)
            lines[at:at] = todo
        else:
            lines[edge[0]:edge[1]] = ["## Failure modes"] + (todo or ["- none"]) + [""]
    if moved:
        src = find(lines, "Sources")
        if src:
            at = body_end(lines, *src)
            lines[at:at] = moved
        else:
            lines += ["", "## Sources"] + moved
    anchor = find(lines, "Differences from the original") or find(lines, "Sources")
    for title in ("Failure modes", "Must never break"):
        if not find(lines, title):
            at = anchor[0] if anchor else len(lines)
            lines[at:at] = [f"## {title}", "- none", ""]
            anchor = find(lines, "Differences from the original") or find(lines, "Sources")
    return "\n".join(lines)


def main():
    layout, _ = open_layout(sys.argv[1] if len(sys.argv) > 1 else ".")
    if layout is None:
        print("ERROR no rspec.json found. Run /rspec:init first."); sys.exit(1)
    changed = 0
    for fid, (p, _, _) in stories(layout.spec).items():
        raw = p.read_bytes().decode("utf-8")
        bom = "﻿" if raw.startswith("﻿") else ""
        crlf = "\r\n" in raw
        text = raw[len(bom):].replace("\r\n", "\n")
        new = migrate(text, fid)
        if new != text:
            out = bom + (new.replace("\n", "\r\n") if crlf else new)
            p.write_bytes(out.encode("utf-8"))
            changed += 1
            print(f"migrated {p.name}")
    print(f"{changed} stor{'y' if changed == 1 else 'ies'} migrated; run check_spec.py next")


if __name__ == "__main__":
    main()
