#!/usr/bin/env python3
"""Turn the verify run log into levels, the acceptance manifest and the report. Every figure comes from here.

Usage: verify_report.py [project-root | spec-folder]
       verify_report.py [project-root | spec-folder] --note <criterion ID> <outcome> "<reason>"
Reads <spec>/verify/runs.jsonl (verify_run.py) and <spec>/verify/outcomes.jsonl (--note: the judge's and the
seeder's calls). On the latest build of a criterion's latest test, with its current text: three passes in a row and
no failure → level 2; a pass and a failure → flaky. Writes <spec>/verify/levels.json (check_spec.py puts level 2
into the lock), <spec>/acceptance/manifest.json (contracts C4, level 2 tests only;
an entry marked `visibility: hidden` is kept as is and counts as level 2) and <spec>/verify/summary.md.
"""
import hashlib, json, sys
from datetime import datetime, timezone
from rspec_lib import open_layout, criteria, priorities, in_scope, contracts

OUTCOMES = ("spec-wrong", "test-wrong", "unrecordable", "unseedable", "read-only reference")
RUNNERS = {"http": "integration", "playwright": "e2e", "maestro": "e2e", "cli": "integration"}


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def status(cid, sha, runs, spec):
    """(status, last run or None): level-2, flaky, red, not-run or unrecorded."""
    # a test /rspec:amend --test removed no longer counts, whatever its old runs said
    mine = [r for r in runs if r["criterion"] == cid and r["text_sha256"] == sha and (spec / r["test"]).exists()]
    if not mine:
        return "unrecorded", None
    last = mine[-1]
    same = [r for r in mine if r["test"] == last["test"] and r["build"] == last["build"]]
    results = [r["result"] for r in same if r["result"] != "not run"]
    if not results:
        return "not-run", last
    if "pass" in results and "fail" in results:
        return "flaky", last
    if len(results) >= 3 and all(r == "pass" for r in results[-3:]):
        return "level-2", last
    return ("red" if "fail" in results else "not-run"), last


def share(n, total):
    return f"{round(100 * n / total)}%" if total else "—"


def note(spec, args):
    if len(args) != 3 or args[1] not in OUTCOMES:
        sys.exit("usage: --note <criterion ID> <" + "|".join(OUTCOMES) + "> \"<reason>\"")
    log = spec / "verify" / "outcomes.jsonl"
    log.parent.mkdir(exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "criterion": args[0], "outcome": args[1], "reason": args[2]}) + "\n")
    print(f"noted {args[0]}: {args[1]}")


def main():
    pos = [a for a in sys.argv[1:] if not a.startswith("--")]
    layout, cfg = open_layout(pos[0] if pos else ".")
    if layout is None:
        sys.exit("ERROR no rspec.json found")
    spec = layout.spec
    if "--note" in sys.argv:
        return note(spec, sys.argv[sys.argv.index("--note") + 1:])
    run_cfg = (cfg.get("reference") or {}).get("run") or {}
    prio = priorities(spec)
    scoped = set(in_scope(prio, cfg))
    runs = read_jsonl(spec / "verify" / "runs.jsonl")
    outcomes = {o["criterion"]: o for o in read_jsonl(spec / "verify" / "outcomes.jsonl")}
    bundle = spec / "acceptance"
    # product-rebuild's holdout split moves these files out of the bundle; their entries are its record, kept as is
    prior = json.loads((bundle / "manifest.json").read_text(encoding="utf-8")) if (bundle / "manifest.json").exists() else {}
    hidden = [t for t in prior.get("tests") or [] if t.get("visibility") == "hidden"]
    hidden_test = {}
    for t in hidden:
        hidden_test.setdefault(t["criterion"], {"test": "acceptance/" + t["path"]})
    rows = []
    for cid, _, sha, _, _ in criteria(spec):
        fid = cid.split(".AC")[0]
        if fid in scoped:
            st, last = ("level-2", hidden_test[cid]) if cid in hidden_test else status(cid, sha, runs, spec)
            rows.append({"id": cid, "feature": fid, "module": fid.split("-")[1], "mvp": prio.get(fid) == "MVP",
                         "sha": sha, "status": st, "last": last})

    level2 = [r for r in rows if r["status"] == "level-2"]
    levels = {r["id"]: {"text_sha256": r["sha"], "test": r["last"]["test"]} for r in level2}
    (spec / "verify").mkdir(exist_ok=True)
    (spec / "verify" / "levels.json").write_text(json.dumps({"criteria": levels}, indent=2) + "\n", encoding="utf-8")

    tests = []
    for r in (r for r in level2 if r["id"] not in hidden_test):
        rel = r["last"]["test"][len("acceptance/"):]
        green = [x for x in runs if x["criterion"] == r["id"] and x["result"] == "pass"][-1]
        tests.append({"criterion": r["id"], "runner": r["last"]["runner"], "path": rel,
                      "sha256": hashlib.sha256((bundle / rel).read_bytes()).hexdigest(),
                      "level": RUNNERS[r["last"]["runner"]], "visibility": "open",
                      "recorded_against": {"kind": run_cfg.get("kind") or "none", "version_or_commit": r["last"]["build"],
                                           "base_url_env": run_cfg.get("base_url_env") or "ACCEPT_BASE_URL"},
                      "last_green": {"timestamp": green["ts"], "target": "reference"}, "normalize": []})
    errors = []
    if bundle.is_dir():
        (bundle / "manifest.json").write_text(json.dumps({"contracts": contracts.VERSION, "tests": tests + hidden},
                                                         indent=2) + "\n", encoding="utf-8")
        away = {f"{t['criterion']}: {t['path']} not found" for t in hidden}
        errors = [m for s, m in contracts.check_bundle(str(bundle)) if s == "error" and m not in away]

    def line(label, subset):
        n = sum(1 for r in subset if r["status"] == "level-2")
        return f"| {label} | {len(subset)} | {n} | {share(n, len(subset))} |"

    mvp = [r for r in rows if r["mvp"]]
    mvp_share = sum(1 for r in mvp if r["status"] == "level-2") / len(mvp) if mvp else 0
    kind = run_cfg.get("kind") or "none"
    target = (f"MVP level 2 ≥ 90%: {'met' if mvp_share >= 0.9 else 'not met'}" if kind == "local"
              else "report only (reference kind " + kind + ")")
    out = ["# Verify summary", "", f"Generated by verify_report.py from verify/runs.jsonl on "
           f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}. Target: {target}.", "",
           "| Scope | Criteria | Level 2 | Share |", "|---|---|---|---|", line("MVP", mvp), line("All in scope", rows),
           "", "## Per module", "", "| Module | Criteria | Level 2 | Share |", "|---|---|---|---|"]
    out += [line(m, [r for r in rows if r["module"] == m]) for m in dict.fromkeys(r["module"] for r in rows)]
    sections = {"Flaky": [r for r in rows if r["status"] == "flaky"],
                "Red (not level 2)": [r for r in rows if r["status"] == "red" and r["id"] not in outcomes],
                "Not run": [r for r in rows if r["status"] == "not-run"]}
    for title, items in sections.items():
        out += ["", f"## {title}", ""] + ([f"- {r['id']}: {r['last']['test']} ({r['last']['detail'] or r['status']})"
                                           for r in items] or ["- none"])
    disputes = [o for o in outcomes.values() if o["outcome"] in ("spec-wrong", "test-wrong", "unrecordable")]
    out += ["", "## Disputes", ""] + ([f"- {o['criterion']}: {o['outcome']}, {o['reason']}" for o in disputes] or ["- none"])
    level1 = [o for o in outcomes.values() if o["outcome"] in ("unrecordable", "unseedable", "read-only reference")]
    out += ["", "## Unrecordable (level 1)", ""] + ([f"- {o['criterion']}: {o['outcome']}, {o['reason']}" for o in level1]
                                                    or ["- none"])
    (spec / "verify" / "summary.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{spec / 'verify' / 'summary.md'} level 2: {len(level2)} of {len(rows)} in scope, "
          f"MVP {share(sum(1 for r in mvp if r['status'] == 'level-2'), len(mvp))}")
    for e in errors:
        print("ERROR acceptance/" + e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
