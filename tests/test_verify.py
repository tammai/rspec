import json, os, shutil, subprocess, sys, tempfile, unittest, urllib.request
from pathlib import Path
from helpers import run

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "reference-app"
sys.path.insert(0, str(ROOT / "contracts" / "v1"))
import contracts

SEED = """steps:
  - request: {method: POST, path: /api/reset}
    expect: {status: 204}
  - request: {method: POST, path: /api/tasks, account: MEMBER, json: {title: "Plan"}}
    expect: {status: 201}
  - request: {method: POST, path: /api/tasks, account: MEMBER, json: {title: "Ship"}}
    expect: {status: 201}
"""
LIST = """criterion: F-TSK-02.AC3
seed: [seed/two-tasks.yaml]
steps:
  - request: {method: GET, path: /api/tasks, account: MEMBER}
    expect: {status: 200, json: [{pointer: /count, equals: 2}]}
"""
STATS = """criterion: F-TSK-03.AC1
seed: [seed/two-tasks.yaml]
steps:
  - request: {method: GET, path: /api/stats, account: MEMBER}
    expect: {status: 200, json: [{pointer: /count, equals: 2}]}
"""


def copy_fixture():
    root = Path(tempfile.mkdtemp()) / "reference-app"
    shutil.copytree(FIXTURE, root, ignore=shutil.ignore_patterns("__pycache__"))
    return root


def config(root, **run_fields):
    path = root / "docs" / "rspec.json"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg["reference"]["run"].update(run_fields)
    path.write_text(json.dumps(cfg), encoding="utf-8")


class Verify(unittest.TestCase):
    def setUp(self):
        self.root = copy_fixture()
        self.app = subprocess.Popen([sys.executable, "-m", "app", "--port", "0"], cwd=self.root,
                                    stdout=subprocess.PIPE, text=True)
        port = self.app.stdout.readline().split()[-1]
        self.env = dict(os.environ, ACCEPT_BASE_URL=f"http://127.0.0.1:{port}",
                        ACCEPT_ACCOUNT_MEMBER="Authorization: Bearer member")
        bundle = self.root / "docs" / "acceptance"
        (bundle / "seed").mkdir(parents=True)
        (bundle / "http").mkdir()
        (bundle / "seed" / "two-tasks.yaml").write_text(SEED, encoding="utf-8")

    def tearDown(self):
        self.app.kill()
        self.app.wait()
        self.app.stdout.close()

    def script(self, name, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts" / name), str(self.root), *args],
                              capture_output=True, text=True, env=self.env)

    def record(self, name, text):
        (self.root / "docs" / "acceptance" / "http" / name).write_text(text, encoding="utf-8")
        return self.script("verify_run.py", f"acceptance/http/{name}")

    def lock(self):
        return {c["id"]: c for c in json.loads((self.root / "docs" / "criteria.lock.json").read_text(encoding="utf-8"))["criteria"]}

    def test_three_greens_reach_level_2(self):
        r = self.record("F-TSK-02.AC3.yaml", LIST)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.script("verify_report.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([m for s, m in contracts.check_bundle(str(self.root / "docs" / "acceptance")) if s == "error"], [])
        summary = (self.root / "docs" / "verify" / "summary.md").read_text(encoding="utf-8")
        self.assertIn("| MVP | 6 | 1 | 17% |", summary)
        self.assertIn("| TSK | 7 | 1 | 14% |", summary)
        self.assertEqual(run("check_spec.py", self.root).returncode, 0)
        entry = self.lock()["F-TSK-02.AC3"]
        self.assertEqual((entry["level"], entry["test"]), (2, "acceptance/http/F-TSK-02.AC3.yaml"))

    def test_hidden_entry_survives_a_rerun_and_counts_as_level_2(self):
        self.record("F-TSK-02.AC3.yaml", LIST)
        self.script("verify_report.py")
        bundle = self.root / "docs" / "acceptance"
        manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
        manifest["tests"][0]["visibility"] = "hidden"
        hidden = json.dumps(manifest["tests"][0], indent=2)
        (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (bundle / "http" / "F-TSK-02.AC3.yaml").unlink()
        r = self.script("verify_report.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        after = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))["tests"]
        self.assertEqual([json.dumps(t, indent=2) for t in after], [hidden])
        self.assertIn("| MVP | 6 | 1 | 17% |", (self.root / "docs" / "verify" / "summary.md").read_text(encoding="utf-8"))
        self.assertEqual(run("check_spec.py", self.root).returncode, 0)
        entry = self.lock()["F-TSK-02.AC3"]
        self.assertEqual((entry["level"], entry["test"]), (2, "acceptance/http/F-TSK-02.AC3.yaml"))

    def test_pass_and_fail_on_one_build_is_flaky(self):
        r = self.record("F-TSK-03.AC1.yaml", STATS)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.script("verify_report.py")
        summary = (self.root / "docs" / "verify" / "summary.md").read_text(encoding="utf-8")
        self.assertIn("F-TSK-03.AC1", summary.split("## Flaky")[1].split("##")[0])
        run("check_spec.py", self.root)
        self.assertNotEqual(self.lock()["F-TSK-03.AC1"]["level"], 2)

    def test_verify_step_sits_between_audit_and_handoff(self):
        def progress():
            p = json.loads(run("progress.py", self.root).stdout)
            return p["next"], p["pending"]
        self.assertEqual(progress(), ("verify", ["TSK"]))
        self.record("F-TSK-02.AC3.yaml", LIST)
        self.assertEqual(progress(), ("verify", ["TSK"]))  # other MVP criteria of the module are still unrecorded
        for ids in json.loads(self.script("verify_report.py", "--plan").stdout)["features"].values():
            for cid in ids:
                self.script("verify_report.py", "--note", cid, "unrecordable", "fixture")
        self.assertEqual(progress(), ("verify", ["report"]))
        self.script("verify_report.py")
        self.assertEqual(progress()[0], "handoff")
        config(self.root, kind="")
        shutil.rmtree(self.root / "docs" / "verify")
        self.assertEqual(progress(), ("verify", ["decide"]))
        config(self.root, kind="none")
        self.assertEqual(progress()[0], "handoff")

    def runs(self):
        return [json.loads(l) for l in (self.root / "docs" / "verify" / "runs.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_failing_ui_run_keeps_its_full_output(self):
        bin_dir = Path(tempfile.mkdtemp())
        code = "import sys; print('Expected: 2'); print('x' * 2000); print('Received: 3'); sys.exit(1)"
        (bin_dir / "npx").write_text(f'#!/bin/sh\n"{sys.executable}" -c "{code}"\n', encoding="utf-8")
        (bin_dir / "npx").chmod(0o755)
        (bin_dir / "npx.cmd").write_text(f'@"{sys.executable}" -c "{code}"\r\n', encoding="utf-8")
        self.env["PATH"] = str(bin_dir) + os.pathsep + self.env["PATH"]
        (self.root / "docs" / "acceptance" / "e2e").mkdir()
        (self.root / "docs" / "acceptance" / "e2e" / "F-TSK-02.AC3.spec.ts").write_text("// ui\n", encoding="utf-8")
        r = self.script("verify_run.py", "acceptance/e2e/F-TSK-02.AC3.spec.ts", "--times", "1")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        line = self.runs()[-1]
        self.assertEqual(line["result"], "fail", line)
        saved = self.root / "docs" / line["output"]
        self.assertEqual(saved.parent, self.root / "docs" / "verify" / "fail-output")
        self.assertIn("Expected: 2", saved.read_text(encoding="utf-8"))
        self.assertNotIn("Expected: 2", line["detail"])
        self.assertEqual((saved.parent / ".gitignore").read_text(encoding="utf-8").strip(), "*")

    def test_long_http_failure_keeps_runs_jsonl_short(self):
        long_list = LIST.replace("equals: 2", 'equals: "' + "x" * 400 + '"')
        r = self.record("F-TSK-02.AC3.yaml", long_list)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        line = self.runs()[-1]
        self.assertLessEqual(len(line["detail"]), 300)
        self.assertIn("x" * 400, (self.root / "docs" / line["output"]).read_text(encoding="utf-8"))
        self.assertIn(line["output"], r.stdout)
        self.assertEqual(len({l["output"] for l in self.runs()}), 3)  # one file per run, even within a second

    def test_unreachable_reference_stops_as_not_run(self):
        self.app.kill()
        self.app.wait()
        self.env["ACCEPT_BASE_URL"] = self.env["ACCEPT_BASE_URL"].replace("http://", "http://user:pw@") + "/?key=s3cret"
        r = self.record("F-TSK-02.AC3.yaml", LIST)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        lines = self.runs()
        self.assertEqual([l["result"] for l in lines], ["not run"], lines)
        self.assertIn("unreachable", lines[0]["detail"])
        self.assertNotIn("s3cret", lines[0]["detail"])
        self.assertNotIn("pw@", lines[0]["detail"])

    def test_an_older_test_version_does_not_pin_flaky(self):
        self.record("F-TSK-02.AC3.yaml", LIST)
        log = self.root / "docs" / "verify" / "runs.jsonl"
        lines = self.runs()
        old = dict(lines[0], result="fail", detail="written while the test was rewritten", test_sha256="0" * 64)

        def report(rows):
            log.write_text("".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
            self.script("verify_report.py")
            return json.loads((self.root / "docs" / "verify" / "levels.json").read_text(encoding="utf-8"))["criteria"]
        self.assertIn("F-TSK-02.AC3", report([old] + lines))
        bare = [{k: v for k, v in x.items() if k != "test_sha256"} for x in [old] + lines]
        self.assertNotIn("F-TSK-02.AC3", report(bare))
        test = self.root / "docs" / "acceptance" / "http" / "F-TSK-02.AC3.yaml"
        lf = test.read_bytes().replace(b"\r\n", b"\n")
        test.write_bytes(lf.replace(b"\n", b"\r\n") if test.read_bytes() == lf else lf)  # the other line endings
        self.assertIn("F-TSK-02.AC3", report(lines))
        test.write_text(LIST + "# edited, never run\n", encoding="utf-8")
        self.assertNotIn("F-TSK-02.AC3", report(lines))

    def test_plan_lists_mvp_criteria_still_to_record(self):
        self.record("F-TSK-02.AC3.yaml", LIST)

        def plan(*args):
            r = self.script("verify_report.py", "--plan", *args)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            return json.loads(r.stdout)["features"]
        default = plan()
        self.assertEqual(sorted(default), ["F-TSK-01", "F-TSK-02"])
        self.assertNotIn("F-TSK-02.AC3", default["F-TSK-02"])
        self.assertIn("F-TSK-03", plan("--scope", "full"))
        self.assertEqual(plan("--only", "F-TSK-03.AC1"), {"F-TSK-03": ["F-TSK-03.AC1"]})
        self.assertFalse((self.root / "docs" / "verify" / "levels.json").exists())
        here = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_report.py"), "--plan", "--scope", "full"],
                              capture_output=True, text=True, env=self.env, cwd=self.root)
        self.assertIn("F-TSK-03", json.loads(here.stdout)["features"], here.stdout + here.stderr)
        self.assertNotEqual(self.script("verify_report.py", "--plan", "--only").returncode, 0)
        self.assertNotEqual(self.script("verify_report.py", "--plan", "--only", "").returncode, 0)
        self.assertNotEqual(self.script("verify_report.py", "--plan", "--scope=full").returncode, 0)
        self.script("verify_report.py")
        bundle = self.root / "docs" / "acceptance"
        manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
        manifest["tests"][0]["visibility"] = "hidden"
        (bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        self.assertNotIn("F-TSK-02.AC3", plan("--only", "F-TSK-02")["F-TSK-02"])

    TASKS_ANY = ("criterion: F-TSK-02.AC3\nsteps:\n"
                 "  - request: {method: GET, path: /api/tasks, account: MEMBER}\n    expect: {status: 200}\n")
    ADAPTER = {"start": "python3 adapter.py", "base_url_env": "ACCEPT_ADAPTER_URL"}

    def second_app(self):
        """A second copy of the fixture app, standing in for the adapter: its own state, so a test can tell which
        one it reached."""
        app = subprocess.Popen([sys.executable, "-m", "app", "--port", "0"], cwd=self.root, stdout=subprocess.PIPE, text=True)
        self.addCleanup(lambda: (app.kill(), app.wait(), app.stdout.close()))
        return f"http://127.0.0.1:{app.stdout.readline().split()[-1]}"

    def task_count(self, url):
        req = urllib.request.Request(url + "/api/tasks", headers={"Authorization": "Bearer member"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())["count"]

    def test_adapter_runs_http_tests_through_it(self):
        config(self.root, adapter=self.ADAPTER)
        self.env["ACCEPT_ADAPTER_URL"] = adapter = self.second_app()
        # A path template ({id}) and a capture in a path both pass the contract check.
        r = self.record("F-TSK-02.AC3.yaml", "criterion: F-TSK-02.AC3\nsteps:\n"
                        "  - request: {method: POST, path: /api/tasks, account: MEMBER, json: {title: Plan}}\n"
                        "    expect: {status: 201, json: [{pointer: /id, rule: uuid, capture: task_id}]}\n"
                        "  - request: {method: GET, path: \"/api/tasks/{task_id}\", account: MEMBER}\n"
                        "    expect: {status: 200}\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([l["result"] for l in self.runs()], ["pass"] * 3)
        self.assertEqual((self.task_count(adapter), self.task_count(self.env["ACCEPT_BASE_URL"])), (3, 0))

    def test_adapter_refuses_a_path_outside_the_contract(self):
        config(self.root, adapter=self.ADAPTER)
        self.env["ACCEPT_ADAPTER_URL"] = self.second_app()
        r = self.record("F-TSK-02.AC3.yaml", LIST)  # its seed resets through /api/reset, which openapi.json lacks
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("/api/reset", r.stdout + r.stderr)
        self.assertIn("openapi.json", r.stdout + r.stderr)
        self.assertFalse((self.root / "docs" / "verify" / "runs.jsonl").exists())
        r = self.record("F-TSK-02.AC3.yaml", self.TASKS_ANY.replace("/api/tasks,", "\"/api/tasks?limit=1\","))
        self.assertNotIn("openapi.json", r.stdout + r.stderr)  # the query string is not part of the path

    def test_unreachable_adapter_or_reference_stops_as_not_run(self):
        config(self.root, adapter=self.ADAPTER)
        for adapter, reference, who in (("http://127.0.0.1:9", self.env["ACCEPT_BASE_URL"], "adapter"),
                                        (self.second_app(), "http://127.0.0.1:9", "reference")):
            with self.subTest(who):
                self.env.update(ACCEPT_ADAPTER_URL=adapter, ACCEPT_BASE_URL=reference)
                (self.root / "docs" / "verify" / "runs.jsonl").unlink(missing_ok=True)
                r = self.record("F-TSK-02.AC3.yaml", self.TASKS_ANY)
                self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
                self.assertEqual([l["result"] for l in self.runs()], ["not run"])
                self.assertIn(f"{who} unreachable", self.runs()[0]["detail"])

    def test_a_malformed_adapter_is_one_error_line(self):
        for adapter in ("python3 adapter.py", {"start": "x", "base_url_env": 5},
                        {"start": "x", "base_url_env": "ACCEPT_BASE_URL"}):
            with self.subTest(str(adapter)):
                config(self.root, adapter=adapter)
                self.env["ACCEPT_ADAPTER_URL"] = self.env["ACCEPT_BASE_URL"]
                r = self.record("F-TSK-02.AC3.yaml", self.TASKS_ANY)
                c = run("check_spec.py", self.root)
                self.assertEqual((r.returncode, c.returncode), (1, 1), r.stdout + r.stderr + c.stdout)
                self.assertIn("reference.run.adapter", r.stderr)
                self.assertNotIn("Traceback", r.stderr + c.stdout + c.stderr)
                self.assertFalse((self.root / "docs" / "verify" / "runs.jsonl").exists())

    def test_reference_run_rules(self):
        for fields, needle in (({"kind": "url", "writes": True}, "writes"),
                               ({"base_url_env": "BASE_URL"}, "ACCEPT_"),
                               ({"adapter": {"base_url_env": "ACCEPT_ADAPTER_URL"}}, "adapter.start"),
                               ({"adapter": {"start": "x", "base_url_env": "ACCEPT_BASE_URL"}}, "adapter.base_url_env"),
                               ({"base_url_env": "ACCEPT_REF_URL", "adapter": {"start": "x", "base_url_env": "ACCEPT_BASE_URL"}},
                                "adapter.base_url_env")):
            with self.subTest(needle):
                root = copy_fixture()
                config(root, **fields)
                r = run("check_spec.py", root)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("reference.run", r.stdout)
                self.assertIn(needle, r.stdout)


if __name__ == "__main__":
    unittest.main()
