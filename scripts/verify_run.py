#!/usr/bin/env python3
"""Run one recorded acceptance test against the reference, three times, and log every run.

Usage: verify_run.py [project-root | spec-folder] <test path, relative to the spec> [--times 3]
The runner follows the bundle folder (contracts C4): http/ via contracts.run_http, e2e/ via `npx playwright test`,
mobile/ via `maestro test`; cli/ is not run (contracts v1 settles no cli format). Each run is appended to
<spec>/verify/runs.jsonl with the criterion's text hash and the reference build, so verify_report.py, not the
recording agent, decides level 2 and flaky. Exit 0 only when every run passed.
"""
import json, os, shutil, subprocess, sys, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from rspec_lib import open_layout, criteria, contracts

RUNNERS = {"http": "http", "e2e": "playwright", "mobile": "maestro", "cli": "cli"}


def criterion_of(path):
    name = path.name
    for ext in (".spec.ts", ".yaml"):
        if name.endswith(ext):
            return name[:-len(ext)]
    return path.stem


def run_once(runner, path, env):
    """(result, detail): result is pass, fail or not run."""
    if runner == "http":
        xml, failed = contracts.run_http([str(path)], env)
        # The XML is run_http's own output with server text escaped, so no DTD from the reference reaches the parser.
        failure = ET.fromstring(xml).find("testcase/failure")
        if failure is None:
            return "pass", ""
        message = failure.get("message", "")
        return ("not run" if "not run:" in message else "fail"), message
    if runner == "cli":
        return "not run", "cli runner not in contracts v1"
    tool = "npx" if runner == "playwright" else "maestro"
    if not shutil.which(tool):
        return "not run", f"{tool} is not installed"
    cmd = ["npx", "playwright", "test", str(path)] if runner == "playwright" else ["maestro", "test", str(path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return ("pass" if proc.returncode == 0 else "fail"), (proc.stdout + proc.stderr).strip()[-300:]


def main():
    args = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] != "--times"]
    if len(args) != 2:
        sys.exit("usage: verify_run.py <project-root | spec-folder> <test path relative to the spec> [--times 3]")
    times = int(sys.argv[sys.argv.index("--times") + 1]) if "--times" in sys.argv else 3
    layout, cfg = open_layout(args[0])
    if layout is None:
        sys.exit("ERROR no rspec.json found")
    spec = layout.spec
    rel = Path(args[1]).as_posix()
    path = spec / rel
    folder = Path(rel).parts[1] if rel.startswith("acceptance/") and len(Path(rel).parts) > 2 else ""
    if folder not in RUNNERS or not path.is_file():
        sys.exit(f"ERROR {rel}: not a test under acceptance/http, e2e, mobile or cli")
    runner = RUNNERS[folder]
    cid = criterion_of(path)
    sha = {c[0]: c[2] for c in criteria(spec)}.get(cid)
    if sha is None:
        sys.exit(f"ERROR {cid}: no such criterion in the stories")
    run_cfg = (cfg.get("reference") or {}).get("run") or {}
    env = dict(os.environ)
    base_var = run_cfg.get("base_url_env") or "ACCEPT_BASE_URL"
    if env.get(base_var):
        env["ACCEPT_BASE_URL"] = env[base_var]
    build = ((cfg.get("sources") or {}).get("commit") or "unversioned")
    log = spec / "verify" / "runs.jsonl"
    log.parent.mkdir(exist_ok=True)
    results = []
    for n in range(1, times + 1):
        result, detail = run_once(runner, path, env)
        results.append(result)
        line = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "criterion": cid, "test": rel,
                "runner": runner, "build": build, "text_sha256": sha, "result": result, "detail": detail}
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")
        print(f"{cid} run {n}: {result}" + (f" ({detail})" if detail and result != "pass" else ""))
    sys.exit(0 if results and all(r == "pass" for r in results) else 1)


if __name__ == "__main__":
    main()
