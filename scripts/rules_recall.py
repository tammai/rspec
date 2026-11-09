#!/usr/bin/env python3
"""Score how many of the rules-recall fixture's known rules a spec records.

Usage: rules_recall.py <project-or-spec> [--model <tier>]
A gold rule (tests/fixtures/rules-recall/gold.yaml) is found when a domain.md line, or a criterion tagged
[code], cites `path:line` inside one of its locations; strict also needs every `values` group in that line's
own text. Prints recall, strict recall, the missed rules and the citations matching no gold rule.
Exit 0 whatever the score: the number is a reading, not a gate. Exit 1 on bad arguments or no spec to score.
"""
import json, re, sys
from decimal import Decimal
from pathlib import Path
from rspec_lib import contracts, criteria, open_layout, stories

ROOT = Path(__file__).resolve().parent.parent
GOLD = ROOT / "tests" / "fixtures" / "rules-recall" / "gold.yaml"
# Only an exact token `path:N` or `path:N-M` cites: no spaces, no other dash, nothing glued on either side. Any
# looser reading guesses, and a guess (a dash or a comma before prose) credits lines nobody cited.
CITE = re.compile(r"(?<![\w./\\-])(?P<path>[\w.-]+(?:/[\w.-]+)*\.[A-Za-z]\w*):(?P<a>\d+)(?:-(?P<b>\d+))?"
                  r"(?![\w:\-\u2013\u2014]|\.\d)")
REPO_AT = re.compile(r"\S+@[0-9a-f]{6,40}\b")
CRIT_ID = re.compile(r"\bF-[A-Z]{2,4}-\d{2,3}\.AC\d+\b")
ANY_ID = re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*-\d+(?:\.[A-Za-z]+\d+)?\b")  # F-BIL-01.AC2, NFR-10
NUMBER = re.compile(r"(?<![\w.,])(\d+(?:[,_]\d{3})*(?:\.\d+)?)(%?)(?![\w%]|[.,]\d)")
NUMERIC_VALUE = re.compile(r"\d+(?:[,_]\d{3})*(?:\.\d+)?%?")
# Anything shaped like a path with a line or anchor after it, cited or not: its digits are locations, not values.
PATH_REF = re.compile(r"[\w./\\-]*\.[A-Za-z]\w*[:#]\S*")
SOURCES = re.compile(r"^##\s*Sources\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)


def citations(line):
    """[(path, first, last)] for each citation token in a line; a reversed range is not one."""
    out = []
    for m in CITE.finditer(line):
        a, b = int(m.group("a")), int(m.group("b") or m.group("a"))
        if a <= b:
            out.append((m.group("path"), a, b))
    return out


def own_text(line):
    return PATH_REF.sub("", REPO_AT.sub("", line)).lower()


def claims(spec):
    """[(label, text, citations)] for every domain.md line and [code] criterion that cites a source line."""
    out = []
    domain = spec / "domain.md"
    if domain.exists():
        for n, line in enumerate(domain.read_text(encoding="utf-8-sig").splitlines(), 1):
            cites = citations(line)
            if cites:
                out.append((f"domain.md:{n}", own_text(line), cites))
    by_file = {}
    for cid, tag, _, name, line in criteria(spec):
        if tag == "code":
            by_file.setdefault(name, []).append((cid, line))
    for path, text, _ in stories(spec).values():
        crits = by_file.get(path.name, [])
        src = SOURCES.search(text)
        linked, unlinked = {}, []
        for line in (src.group(1).splitlines() if src else []):
            ids = CRIT_ID.findall(line)
            for i in ids:
                linked.setdefault(i, []).extend(citations(line))
            if not ids:
                unlinked += citations(line)
        for cid, line in crits:
            cites = citations(line) + linked.get(cid, []) + unlinked
            if cites:
                out.append((cid, own_text(line), cites))
    return out


def located(rule, cite):
    path, a, b = cite
    return any((path == loc["path"] or path.endswith("/" + loc["path"])) and a <= loc["lines"][1] and b >= loc["lines"][0]
               for loc in rule["locations"])


def number(digits):
    return Decimal(digits.replace(",", "").replace("_", ""))


def has_value(text, value):
    value = str(value).lower()
    if NUMERIC_VALUE.fullmatch(value):
        # Whole number tokens compared by value, so "25.00" is 25 and "19%" is not 9%; IDs such as NFR-10 are
        # names, not numbers.
        want = (number(value.rstrip("%")), value.endswith("%"))
        return any((number(d), bool(p)) == want for d, p in NUMBER.findall(ANY_ID.sub(" ", text)))
    return value in text


def missing_values(rule, text):
    return [g for g in rule.get("values") or [] if not any(has_value(text, alt) for alt in g)]


def pct(n, d):
    return f"{int(n * 100 / d + 0.5)}%"


def main():
    args, model, target = sys.argv[1:], "not given", []
    while args:
        a = args.pop(0)
        if a == "--model":
            if not args or args[0].startswith("-"):
                print("ERROR --model needs a tier, such as --model mid")
                sys.exit(1)
            model = args.pop(0)
        elif a.startswith("-") or target:
            print(f"ERROR unknown argument {a}; usage: rules_recall.py <project-or-spec> [--model <tier>]")
            sys.exit(1)
        else:
            target.append(a)
    target = target[0] if target else "."
    layout, _ = open_layout(target)
    if layout is None:
        print(f"ERROR no rspec.json under {target}: nothing to score")
        sys.exit(1)
    rules = contracts.parse_yaml(GOLD.read_text(encoding="utf-8-sig"))["rules"]
    version = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]

    found, strict, stray = {}, set(), {}
    for label, text, cites in claims(layout.spec):
        for cite in cites:
            hits = [r for r in rules if located(r, cite)]
            if not hits:
                stray.setdefault(f"{cite[0]}:{cite[1]}" + (f"-{cite[2]}" if cite[2] != cite[1] else ""), label)
            for r in hits:
                found.setdefault(r["id"], []).append(text)
                if not missing_values(r, text):
                    strict.add(r["id"])

    sys.stdout.reconfigure(errors="replace")  # gold text has × and −, which a Windows console may not encode
    total = len(rules)
    print(f"Rules recall: recall {pct(len(found), total)} ({len(found)}/{total}), "
          f"strict {pct(len(strict), total)} ({len(strict)}/{total}) · rspec {version} · model {model}")
    missed = [r for r in rules if r["id"] not in found]
    if missed:
        print(f"\nMissed ({len(missed)}):")
        for r in missed:
            print(f"  {r['id']} — {r['rule']}" + (f"\n         hard: {r['hard']}" if r.get("hard") else ""))
    weak = [r for r in rules if r["id"] in found and r["id"] not in strict]
    if weak:
        print(f"\nFound, values missing ({len(weak)}):")
        for r in weak:
            lacking = min((missing_values(r, t) for t in found[r["id"]]), key=len)
            print(f"  {r['id']} — missing: {', '.join(g[0] for g in lacking)}")
    if stray:
        print(f"\nCitations matching no gold rule ({len(stray)}); if the claim is true of the line, the gold set is short:")
        for cite, label in stray.items():
            print(f"  {cite} — {label}")


if __name__ == "__main__":
    main()
