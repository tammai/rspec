import json, unittest
from helpers import project, run, story


class QualityBar(unittest.TestCase):
    def test_criteria_without_a_source_tag_fail(self):
        bare = story("F-ISS-01", criteria="- [ ] **F-ISS-01.AC1** Given ENG-1 exists, when I create an issue, then it is ENG-2.")
        r = run("check_spec.py", project(stories={"F-ISS-01-a.md": bare}))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("F-ISS-01.AC1: no source tag", r.stdout)

    def test_tagged_criteria_pass(self):
        tagged = story("F-ISS-01", criteria="- [ ] **F-ISS-01.AC1** Given ENG-1 exists, when I create an issue, then it is ENG-2. `[docs]`")
        r = run("check_spec.py", project(stories={"F-ISS-01-a.md": tagged}))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_contracts_mixing_snake_and_camel_case_warn(self):
        schema = {"x-features": ["F-ISS-01"], "properties": {"teamId": {}, "created_at": {}}}
        r = run("check_spec.py", project(stage="tech", files={"schemas/issue.schema.json": json.dumps(schema)}))
        self.assertIn("contracts mix field-name casings", r.stdout)


if __name__ == "__main__":
    unittest.main()
