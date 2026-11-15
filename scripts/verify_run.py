#!/usr/bin/env python3
"""Run one recorded acceptance test against the reference, three times, and log every run.

Usage: verify_run.py [project-root | spec-folder] <test path, relative to the spec> [--times 3]
The runner follows the bundle folder (contracts C4): http/ via contracts.run_http, e2e/ via `npx playwright test`,
mobile/ via `maestro test`; cli/ is not run (contracts v1 settles no cli format). Each run is appended to
<spec>/verify/runs.jsonl with the criterion's text hash, the test file's hash and the reference build, so
verify_report.py, not the recording agent, decides level 2 and flaky. A failing run's full output goes to
<spec>/verify/fail-output/ (git-ignored) for the judge. Exit 0 only when every run passed; exit 3 when the
reference stopped answering, which stops the run and, by the recorder's rules, the whole verify.
"""
import hashlib, http.client, json, os, shutil, ssl, subprocess, sys, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from rspec_lib import open_layout, criteria, contracts

RUNNERS = {"http": "http", "e2e": "playwright", "mobile": "maestro", "cli": "cli"}
TAIL = 300  # runs.jsonl keeps this much of a runner's output; judges read the rest from verify/fail-output/
UNREACHABLE = 3


def criterion_of(path):
    name = path.name
    for ext in (".spec.ts", ".yaml"):
        if name.endswith(ext):
            return name[:-len(ext)]
    return path.stem


def test_hash(path):
    """sha256 of a test file with CRLF read as LF, so a checkout's line endings never change it. Copied in
    verify_report.py: change both."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def answers(url):
    """None when url answers as itself (any status but a gateway's 502-504), else why not, naming only scheme,
    host and port: the base URL can carry a key or a password, and the reason is written to runs.jsonl."""
    try:
        u = urllib.parse.urlsplit(url)
        where = f"{u.scheme}://{u.hostname}" + (f":{u.port}" if u.port else "")
    except ValueError:
        where = "the base URL"
    try:
        # contracts.run_http's own request timeout, so a slow first page is not taken for a dead reference
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=30):
            return None
    except urllib.error.HTTPError as e:
        return f"{where} answers {e.code} from a gateway" if e.code in (502, 503, 504) else None
    except urllib.error.URLError as e:
        # run_http checks certificates too, so a rejected one would fail every HTTP test as if the criterion were
        # wrong: stop instead, with the reason.
        if isinstance(e.reason, ssl.SSLError):
            return f"{where} has a TLS certificate this client rejects ({e.reason.__class__.__name__})"
        return f"nothing answers at {where} ({e.reason.__class__.__name__})"
    except (OSError, ValueError, http.client.HTTPException) as e:
        return f"nothing answers at {where} ({e.__class__.__name__})"


def run_once(runner, path, env):
    """(result, detail, full output or ""): result is pass, fail or not run."""
    if runner == "http":
        xml, failed = contracts.run_http([str(path)], env)
        # The XML is run_http's own output with server text escaped, so no DTD from the reference reaches the parser.
        failure = ET.fromstring(xml).find("testcase/failure")
        if failure is None:
            return "pass", "", ""
        message = failure.get("message", "")
        # A json check's message quotes the response, which can be large and hold what the reference echoed.
        return ("not run" if "not run:" in message else "fail"), message[-TAIL:], message
    if runner == "cli":
        return "not run", "cli runner not in contracts v1", ""
    tool = "npx" if runner == "playwright" else "maestro"
    # The full path: on Windows npx is npx.cmd, which a bare name in an argument list never finds.
    exe = shutil.which(tool)
    if not exe:
        return "not run", f"{tool} is not installed", ""
    cmd = [exe, "playwright", "test", str(path)] if runner == "playwright" else [exe, "test", str(path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    out = (proc.stdout + proc.stderr).strip()
    return ("pass" if proc.returncode == 0 else "fail"), out[-TAIL:], out


def save_output(spec, name, text):
    """Write a failing run's full output and return its path relative to the spec. The folder ignores itself in
    git: the output can quote a token or cookie, and runs.jsonl is committed."""
    folder = spec / "verify" / "fail-output"
    folder.mkdir(parents=True, exist_ok=True)
    if not (folder / ".gitignore").exists():
        (folder / ".gitignore").write_text("*\n", encoding="utf-8")
    (folder / name).write_text(text, encoding="utf-8")
    return f"verify/fail-output/{name}"


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
    # verify_report.py judges level 2 and flaky on the runs of the test content as it is now.
    test_sha = test_hash(path)
    base = env.get("ACCEPT_BASE_URL")
    down = answers(base) if base else None
    results = []
    for n in range(1, times + 1):
        result, detail, full = ("not run", "", "") if down else run_once(runner, path, env)
        # Asked again after a failure: a reference that died mid-sweep answers nothing, in whatever words its runner
        # used, and those failures are not the criterion's.
        if result == "fail" and base:
            down = answers(base)
        if down:
            result, detail, full = "not run", f"reference unreachable: {down}", ""
        results.append(result)
        ts = datetime.now(timezone.utc)
        line = {"ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"), "criterion": cid, "test": rel, "runner": runner,
                "build": build, "text_sha256": sha, "test_sha256": test_sha, "result": result, "detail": detail}
        if result == "fail" and len(full) > TAIL:
            line["output"] = save_output(spec, f"{cid}-{ts.strftime('%Y%m%dT%H%M%S%fZ')}-{n}.txt", full)
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")
        print(f"{cid} run {n}: {result}" + (f" ({detail})" if detail and result != "pass" else "")
              + (f"\n  full output: {line['output']}" if "output" in line else ""))
        if down:
            print("stopped: the reference is unreachable. Start it, then run verify again.")
            sys.exit(UNREACHABLE)
    sys.exit(0 if results and all(r == "pass" for r in results) else 1)


if __name__ == "__main__":
    main()
