import json, unittest
from helpers import project, run, story

OPENAPI = {"openapi": "3.1.0", "info": {"title": "X", "version": "0.1"},
           "paths": {"/issues": {"post": {"operationId": "createIssue", "x-features": ["F-ISS-01"]}}}}
SCHEMA = {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "Issue", "type": "object", "x-features": ["F-ISS-01"]}

def tech_files(openapi=OPENAPI):
    return {"openapi.json": json.dumps(openapi), "schemas/issue.schema.json": json.dumps(SCHEMA),
            "api.md": "x\n" * 9, "data-model.md": "x\n" * 9, "nfr.md": "x\n" * 9}

class CheckSpec(unittest.TestCase):
    def test_complete_spec_passes(self):
        r = run("check_spec.py", project(stage="tech", files=tech_files()))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_leftover_template_placeholder_fails(self):
        r = run("check_spec.py", project(stories={"F-ISS-01-x.md": story("F-ISS-01", edge="- <case>: <expected behaviour>")}))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("template placeholders", r.stdout)

    def test_email_in_research_warns(self):
        r = run("check_spec.py", project(research={"iss-issues.md": "Assignee seen: jane.doe@example.com"}))
        self.assertIn("contains an email address", r.stdout)

    def test_dependency_cycle_fails(self):
        r = run("check_spec.py", project(features=(("F-ISS-01", "MVP"), ("F-ISS-02", "MVP")), stories={
            "F-ISS-01-a.md": story("F-ISS-01", depends=["F-ISS-02"]),
            "F-ISS-02-b.md": story("F-ISS-02", depends=["F-ISS-01"])}))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("dependency cycle", r.stdout)

    def test_mvp_depending_on_later_fails(self):
        r = run("check_spec.py", project(features=(("F-ISS-01", "MVP"), ("F-ISS-02", "Later")), stories={
            "F-ISS-01-a.md": story("F-ISS-01", depends=["F-ISS-02"])}))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("depends on F-ISS-02 which is Later", r.stdout)

    def test_contract_with_unknown_feature_fails(self):
        bad = json.loads(json.dumps(OPENAPI))
        bad["paths"]["/issues"]["post"]["x-features"] = ["F-ISS-09"]
        r = run("check_spec.py", project(stage="tech", files=tech_files(bad)))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("openapi.json: x-features references unknown F-ISS-09", r.stdout)

    def test_handoff_requires_every_mvp_in_build_plan_and_no_proposed_adr(self):
        files = tech_files()
        files["build-plan.md"] = "# Build plan\n"
        files["decisions/0001-store.md"] = "# 0001. Store\n\n- Status: Proposed\n"
        r = run("check_spec.py", project(stage="handoff", files=files))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("build-plan.md does not include MVP F-ISS-01", r.stdout)
        self.assertIn("still Proposed", r.stdout)

    def test_sdlc_slice_over_ten_criteria_warns(self):
        many = "\n".join(f"- [ ] Given state {i}, when I act, then I see {i}." for i in range(11))
        files = tech_files()
        files["build-plan.md"] = "# Build plan\n\n## Slice 1: Issues\n| 1 | F-ISS-01 |\n"
        r = run("check_spec.py", project(stage="handoff", files=files, config={"build": {"engine": "sdlc"}},
                                         stories={"F-ISS-01-x.md": story("F-ISS-01", criteria=many)}))
        self.assertIn("Slice 1 has 11 acceptance criteria", r.stdout)

if __name__ == "__main__":
    unittest.main()
