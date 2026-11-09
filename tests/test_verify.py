import json, os, shutil, subprocess, sys, tempfile, unittest
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
        self.assertEqual(progress(), ("verify", ["report"]))
        self.script("verify_report.py")
        self.assertEqual(progress()[0], "handoff")
        config(self.root, kind="")
        shutil.rmtree(self.root / "docs" / "verify")
        self.assertEqual(progress(), ("verify", ["decide"]))
        config(self.root, kind="none")
        self.assertEqual(progress()[0], "handoff")

    def test_reference_run_rules(self):
        for fields, needle in (({"kind": "url", "writes": True}, "writes"),
                               ({"base_url_env": "BASE_URL"}, "ACCEPT_")):
            with self.subTest(needle):
                root = copy_fixture()
                config(root, **fields)
                r = run("check_spec.py", root)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("reference.run", r.stdout)
                self.assertIn(needle, r.stdout)


if __name__ == "__main__":
    unittest.main()
