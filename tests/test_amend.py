import json, unittest
from helpers import project, run, story

LOCAL = {"reference": {"run": {"kind": "local", "base_url_env": "ACCEPT_BASE_URL", "accounts": [], "writes": True,
                               "start": "python3 -m app", "stop": ""}}}
NEW_TEXT = 'Given team ENG with 11 issues, when a member creates "Fix login", then it is shown as ENG-12 at the top. `[observed]`'


def finding(cls, route, result="reproduced"):
    return {"id": "Q-0001", "source": "sdlc", "class": cls, "severity": "medium", "criterion": "F-ISS-01.AC1",
            "rule": None, "repro": {"runner": "http", "steps": [{"request": {"method": "GET", "path": "/api/issues"},
                                                                 "expect": {"status": 200}}]},
            "observed": {"rebuild": "list unsorted", "reference": "not run: question"}, "route": route,
            "verified_by": {"agent": "qa-tester", "result": result}}


class Amend(unittest.TestCase):
    def setUp(self):
        self.root = project(config=LOCAL)
        self.docs = self.root / "docs"
        self.story = self.docs / "features" / "F-ISS-01-x.md"
        self.assertEqual(run("check_spec.py", self.root).returncode, 0)

    def level(self, cid="F-ISS-01.AC1"):
        lock = json.loads((self.docs / "criteria.lock.json").read_text(encoding="utf-8"))
        return {c["id"]: c for c in lock["criteria"]}[cid]

    def make_level_2(self):
        sha = self.level()["text_sha256"]
        (self.docs / "acceptance" / "http").mkdir(parents=True)
        (self.docs / "acceptance" / "http" / "F-ISS-01.AC1.yaml").write_text("criterion: F-ISS-01.AC1\nsteps: []\n", encoding="utf-8")
        (self.docs / "verify").mkdir()
        (self.docs / "verify" / "levels.json").write_text(json.dumps({"criteria": {"F-ISS-01.AC1": {
            "text_sha256": sha, "test": "acceptance/http/F-ISS-01.AC1.yaml"}}}), encoding="utf-8")
        run("check_spec.py", self.root)
        self.assertEqual(self.level()["level"], 2)

    def changelog(self):
        return (self.root / "CHANGELOG.md").read_text(encoding="utf-8")

    def test_amend_edits_logs_and_drops_to_level_0(self):
        self.make_level_2()
        r = run("amend.py", self.root, "F-ISS-01.AC1", "--text", NEW_TEXT, "--reason", "builder: order unclear")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f"- [ ] **F-ISS-01.AC1** {NEW_TEXT}", self.story.read_text(encoding="utf-8"))
        self.assertIn("F-ISS-01.AC1: builder: order unclear", self.changelog())
        self.assertEqual(self.level()["level"], 0)
        self.assertIn("/rspec:verify --only F-ISS-01", r.stdout)
        before = self.story.read_bytes()
        bad = run("amend.py", self.root, "F-ISS-01.AC1", "--text", "The list is sorted.", "--reason", "x")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertEqual(self.story.read_bytes(), before)

    def test_new_criterion_takes_the_next_unused_number(self):
        struck = story("F-ISS-01").replace("`[docs]`", "`[docs]`\n- [ ] ~~**F-ISS-01.AC2** Given x, when y, then 1.~~ merged into AC1")
        self.story.write_text(struck, encoding="utf-8")
        r = run("amend.py", self.root, "F-ISS-01", "--new", "--text", NEW_TEXT, "--reason", "missing case")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f"- [ ] **F-ISS-01.AC3** {NEW_TEXT}", self.story.read_text(encoding="utf-8"))
        self.assertEqual(self.level("F-ISS-01.AC3")["level"], 0)

    def test_finding_input_is_routed_by_class(self):
        path = self.root / "q.json"
        path.write_text(json.dumps(finding("spec-gap", "rspec")), encoding="utf-8")
        r = run("amend.py", self.root, "--finding", str(path), "--text", NEW_TEXT, "--reason", "sort order")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("finding Q-0001", self.changelog())
        for f, needle in ((finding("build-defect", "sdlc"), "route"), (finding("spec-gap", "rspec", "not-reproduced"), "reproduced")):
            with self.subTest(needle):
                path.write_text(json.dumps(f), encoding="utf-8")
                r = run("amend.py", self.root, "--finding", str(path), "--text", NEW_TEXT, "--reason", "again")
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(needle, r.stdout + r.stderr)

    def test_amend_test_removes_the_recorded_test(self):
        self.make_level_2()
        green = {"ts": "2026-11-08T10:00:00Z", "criterion": "F-ISS-01.AC1", "test": "acceptance/http/F-ISS-01.AC1.yaml",
                 "runner": "http", "build": "unversioned", "text_sha256": self.level()["text_sha256"], "result": "pass", "detail": ""}
        (self.docs / "verify" / "runs.jsonl").write_text((json.dumps(green) + "\n") * 3, encoding="utf-8")
        r = run("amend.py", self.root, "F-ISS-01.AC1", "--test", "--reason", "test asserted the wrong field")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((self.docs / "acceptance" / "http" / "F-ISS-01.AC1.yaml").exists())
        self.assertEqual(self.level()["level"], 0)
        self.assertIn("/rspec:verify --only F-ISS-01", r.stdout)
        run("verify_report.py", self.root)
        levels = json.loads((self.docs / "verify" / "levels.json").read_text(encoding="utf-8"))
        self.assertNotIn("F-ISS-01.AC1", levels["criteria"])


if __name__ == "__main__":
    unittest.main()
