import json, sys, unittest
from pathlib import Path
from helpers import project, run, story

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "contracts" / "v1"))
import contracts

LEGACY = """---
id: F-ISS-01
module: ISS
priority: MVP
depends_on: []
status: todo
---
# F-ISS-01: Create issue

## Story
As a member, I want to create issues so that work is tracked.

## Acceptance criteria
- [ ] Given team ENG with 11 issues, when a member creates "Fix login", then it is shown as ENG-12. `[docs]`
- [ ] **F-ISS-01.AC2** Given an issue ENG-3, when a member opens it, then the title "Fix login" is shown. `[observed]`
- [ ] Given team ENG, when a guest creates an issue, then 403 is returned. `[api]`

## Edge cases
- Empty title: the issue is not created.

## Differences from the original
- none

## Sources
- research/iss-issues.md, Flows
"""


class CriteriaIds(unittest.TestCase):
    def test_story_breaking_c1_or_c2_fails(self):
        self.assertEqual(run("check_spec.py", project()).returncode, 0)
        cases = {
            "legacy": (LEGACY, "Edge cases"),
            "no example data": (story("F-ISS-01", criteria="- [ ] **F-ISS-01.AC1** Given a team, when a member "
                                                            "creates an issue, then it is shown. `[docs]`"),
                                "example data"),
            "no source tag": (story("F-ISS-01", criteria="- [ ] **F-ISS-01.AC1** Given team ENG, when a member "
                                                          "creates an issue, then it is ENG-1."), "no source tag"),
            "no ID": (story("F-ISS-01", criteria="- [ ] Given team ENG, when a member creates an issue, then it is "
                                                 "ENG-1. `[docs]`"), "migrate_criteria.py"),
        }
        for name, (text, needle) in cases.items():
            with self.subTest(name):
                r = run("check_spec.py", project(stories={"F-ISS-01-x.md": text}))
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("ERROR F-ISS-01-x.md", r.stdout)
                self.assertIn(needle, r.stdout)

    def test_template_is_c2_and_placeholders_fail(self):
        tpl = (ROOT / "templates" / "feature-story.md").read_text(encoding="utf-8")
        body = tpl.split("\n---\n", 1)[1]
        structural = [m for _, m in contracts.check_story(body) if "section" in m or "Edge cases" in m]
        self.assertEqual(structural, [])
        self.assertIn("**F-<CODE>-<NN>.AC1**", tpl)
        self.assertIn("## Open questions", tpl)
        left = story("F-ISS-01", criteria="- [ ] **F-ISS-01.AC1** Given <state with example data>, when a member "
                                          "acts, then 1 is shown. `[docs]`")
        r = run("check_spec.py", project(stories={"F-ISS-01-x.md": left}))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("template placeholders", r.stdout)

    def test_migration_assigns_ids_and_is_idempotent(self):
        root = project(stories={"F-ISS-01-x.md": LEGACY})
        path = root / "docs" / "features" / "F-ISS-01-x.md"
        r = run("migrate_criteria.py", root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = path.read_text(encoding="utf-8")
        self.assertIn('- [ ] **F-ISS-01.AC3** Given team ENG with 11 issues', text)
        self.assertIn('- [ ] **F-ISS-01.AC2** Given an issue ENG-3', text)
        self.assertIn('- [ ] **F-ISS-01.AC4** Given team ENG, when a guest', text)
        self.assertNotIn("## Edge cases", text)
        self.assertIn("## Failure modes\n- Empty title: the issue is not created. → TODO", text)
        self.assertIn("## Must never break\n- none", text)
        first = path.read_bytes()
        run("migrate_criteria.py", root)
        self.assertEqual(path.read_bytes(), first)
        check = run("check_spec.py", root)
        self.assertEqual(check.returncode, 0, check.stdout)
        self.assertIn("needs /rspec:stories ISS", check.stdout)

    def test_migration_moves_text_after_the_tag_to_sources(self):
        cited = LEGACY.replace("then 403 is returned. `[api]`",
                               "then 403 is returned. `[code]` repo@95618469 controllers/route.go:395-403")
        root = project(stories={"F-ISS-01-x.md": cited})
        path = root / "docs" / "features" / "F-ISS-01-x.md"
        run("migrate_criteria.py", root)
        text = path.read_text(encoding="utf-8")
        self.assertIn("then 403 is returned. `[code]`\n", text)
        self.assertIn("## Sources\n- research/iss-issues.md, Flows\n"
                      "- F-ISS-01.AC4: repo@95618469 controllers/route.go:395-403\n", text)
        first = path.read_bytes()
        run("migrate_criteria.py", root)
        self.assertEqual(path.read_bytes(), first)
        self.assertEqual(run("check_spec.py", root).returncode, 0)

    def test_lock_written_and_changed_text_drops_to_level_0(self):
        two = (story("F-ISS-01").split("## Acceptance criteria\n")[1].split("\n")[0] + "\n"
               '- [ ] **F-ISS-01.AC2** Given an issue ENG-3, when a member opens it, then "Fix login" is shown. `[observed]`')
        root = project(stories={"F-ISS-01-x.md": story("F-ISS-01", criteria=two)})
        self.assertEqual(run("check_spec.py", root).returncode, 0)
        lock_path = root / "docs" / "criteria.lock.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        self.assertEqual(contracts.check_lock(lock, str(root)), [])
        self.assertEqual([(c["id"], c["tag"], c["priority"], c["level"]) for c in lock["criteria"]],
                         [("F-ISS-01.AC1", "docs", "MVP", 0), ("F-ISS-01.AC2", "observed", "MVP", 0)])
        for c in lock["criteria"]:
            c["level"], c["test"] = 2, f"acceptance/http/{c['id']}.yaml"
        lock_path.write_text(json.dumps(lock), encoding="utf-8")
        story_path = root / "docs" / "features" / "F-ISS-01-x.md"
        story_path.write_text(story_path.read_text(encoding="utf-8").replace("ENG-12", "ENG-13"), encoding="utf-8")
        r = run("check_spec.py", root)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("F-ISS-01.AC1", r.stdout)
        self.assertIn("needs re-verify", r.stdout)
        levels = {c["id"]: c["level"] for c in json.loads(lock_path.read_text(encoding="utf-8"))["criteria"]}
        self.assertEqual(levels, {"F-ISS-01.AC1": 0, "F-ISS-01.AC2": 2})

    def test_failing_check_writes_no_lock(self):
        root = project(stories={"F-ISS-01-x.md": LEGACY})
        self.assertEqual(run("check_spec.py", root).returncode, 1)
        self.assertFalse((root / "docs" / "criteria.lock.json").exists())


if __name__ == "__main__":
    unittest.main()
