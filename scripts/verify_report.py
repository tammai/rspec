#!/usr/bin/env python3
"""Turn the verify run log into levels, the acceptance manifest and the report. Every figure comes from here.

Usage: verify_report.py [project-root | spec-folder]
       verify_report.py [project-root | spec-folder] --note <criterion ID> <outcome> "<reason>"
       verify_report.py [project-root | spec-folder] --plan [--scope mvp|full] [--only <feature or criterion IDs>]
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
    # Runs of another version of the test file say nothing about this one, and content no run carries was never run.
    # Runs with no test hash are judged all together, as they always were.
    # CRLF read as LF, as verify_run.test_hash does (copied: change both).
    cur = hashlib.sha256((spec / last["test"]).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if any(r.get("test_sha256") for r in same):
        same = [r for r in same if r.get("test_sha256") == cur]
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


def hidden_criteria(bundle):
    """Criteria whose test product-rebuild's holdout split moved out of the bundle: level 2, recorded elsewhere."""
    p = bundle / "manifest.json"
    try:
        tests = (json.loads(p.read_text(encoding="utf-8")).get("tests") or []) if p.exists() else []
        return {t["criterion"] for t in tests if t.get("visibility") == "hidden"}
    except (ValueError, AttributeError, KeyError, TypeError) as e:
        sys.exit(f"ERROR acceptance/manifest.json is not a readable manifest ({e!r}); restore it from git")


def opt(name):
    """The value after option `name`, None when absent; exits when the option is given with no value."""
    if any(a.startswith(name + "=") for a in sys.argv):
        sys.exit(f"ERROR write {name} <value>, not {name}=<value>")
    if name not in sys.argv:
        return None
    i = sys.argv.index(name) + 1
    if i >= len(sys.argv) or sys.argv[i].startswith("--") or not sys.argv[i].strip(" ,"):
        sys.exit(f"ERROR {name} needs a value")
    return sys.argv[i]


def plan(spec, cfg):
    """Print, without writing anything, the criteria /rspec:verify should record, grouped by feature (one recorder
    each). Verify scope is --scope, else rspec.json verify_scope, else mvp: Later criteria are recorded when a slice
    builds them. --only names features or criteria of any priority but Drop and lists them all; otherwise criteria
    already at level 2 or whose latest outcome is a level 1 reason are skipped. A criterion whose test the holdout
    hid is never listed: an open test for it would put the hidden test where builders read."""
    scope = opt("--scope") or cfg.get("verify_scope") or "mvp"
    if scope not in ("mvp", "full"):
        sys.exit(f"ERROR verify scope '{scope}' must be mvp or full")
    only = [i.strip() for i in (opt("--only") or "").split(",") if i.strip()]
    prio = priorities(spec)
    crits = criteria(spec)
    known = {c[0] for c in crits} | set(prio)
    unknown = [i for i in only if i not in known]
    if unknown:
        sys.exit(f"ERROR --only: no such feature or criterion: {', '.join(unknown)}")
    runs = read_jsonl(spec / "verify" / "runs.jsonl")
    latest = {o["criterion"]: o for o in read_jsonl(spec / "verify" / "outcomes.jsonl")}  # as main() reads them
    reasons = {c for c, o in latest.items() if o.get("outcome") in ("unrecordable", "unseedable", "read-only reference")}
    hidden = hidden_criteria(spec / "acceptance")
    wanted = {"MVP", "Later"} if scope == "full" else {"MVP"}
    features, skipped = {}, {"level-2": 0, "hidden": 0, "reason": 0}
    for cid, _, sha, _, _ in crits:
        fid = cid.split(".AC")[0]
        if only:
            if (fid not in only and cid not in only) or prio.get(fid) == "Drop":
                continue
        elif prio.get(fid) not in wanted:
            continue
        if cid in hidden:
            skipped["hidden"] += 1
            continue
        if not only and status(cid, sha, runs, spec)[0] == "level-2":
            skipped["level-2"] += 1
            continue
        if not only and cid in reasons:
            skipped["reason"] += 1
            continue
        features.setdefault(fid, []).append(cid)
    print(json.dumps({"scope": scope, "only": only, "features": features, "skipped": skipped}, indent=2))


def main():
    pos = [a for i, a in enumerate(sys.argv[1:], 1)
           if not a.startswith("--") and sys.argv[i - 1] not in ("--scope", "--only")]
    layout, cfg = open_layout(pos[0] if pos else ".")
    if layout is None:
        sys.exit("ERROR no rspec.json found")
    spec = layout.spec
    if "--note" in sys.argv:
        return note(spec, sys.argv[sys.argv.index("--note") + 1:])
    if "--plan" in sys.argv:
        return plan(spec, cfg)
    run_cfg = (cfg.get("reference") or {}).get("run") or {}
    prio = priorities(spec)
    scoped = set(in_scope(prio, cfg))
    runs = read_jsonl(spec / "verify" / "runs.jsonl")
    outcomes = {o["criterion"]: o for o in read_jsonl(spec / "verify" / "outcomes.jsonl")}
    bundle = spec / "acceptance"
    # product-rebuild's holdout split moves these files out of the bundle; their entries are its record, kept as is
    try:
        prior = json.loads((bundle / "manifest.json").read_text(encoding="utf-8")) if (bundle / "manifest.json").exists() else {}
        hidden = [t for t in prior.get("tests") or [] if t.get("visibility") == "hidden"]
        hidden_test = {}
        for t in hidden:
            hidden_test.setdefault(t["criterion"], {"test": "acceptance/" + t["path"]})
    except (ValueError, AttributeError, KeyError, TypeError) as e:
        sys.exit(f"ERROR acceptance/manifest.json is not a readable manifest ({e!r}); restore it from git")
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
