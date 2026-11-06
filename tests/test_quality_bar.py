import json, unittest
from helpers import project, run, story


class QualityBar(unittest.TestCase):
    def test_criteria_without_an_evidence_tag_warn(self):
        r = run("check_spec.py", project())
        self.assertIn("1 acceptance criteria in 1 stories have no evidence tag", r.stdout)

    def test_tagged_criteria_pass(self):
        tagged = story("F-ISS-01", criteria="- [ ] Given ENG-1 exists, when I create an issue, then it is ENG-2. `[docs]`")
        r = run("check_spec.py", project(stories={"F-ISS-01-a.md": tagged}))
        self.assertNotIn("evidence tag", r.stdout)

    def test_contracts_mixing_snake_and_camel_case_warn(self):
        schema = {"x-features": ["F-ISS-01"], "properties": {"teamId": {}, "created_at": {}}}
        r = run("check_spec.py", project(stage="tech", files={"schemas/issue.schema.json": json.dumps(schema)}))
        self.assertIn("contracts mix field-name casings", r.stdout)


if __name__ == "__main__":
    unittest.main()
