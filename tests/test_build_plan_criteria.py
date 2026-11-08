import unittest
from pathlib import Path
from helpers import project, run
from test_check_spec import tech_files

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


class BuildPlanCriteria(unittest.TestCase):
    def test_slice_lists_its_criterion_ids(self):
        files = tech_files()
        files["build-plan.md"] = "# Build plan\n\n## Slice 1: Issues\n| 1 | F-ISS-01 | features/F-ISS-01-x.md |\n"
        r = run("check_spec.py", project(stage="handoff", files=files, config={"stack": "x"}))
        self.assertIn("build-plan.md: Slice 1 does not list 1 criterion ID", r.stdout)
        files["build-plan.md"] = files["build-plan.md"].replace("x.md |", "x.md | F-ISS-01.AC1 |")
        r = run("check_spec.py", project(stage="handoff", files=files, config={"stack": "x"}))
        self.assertNotIn("does not list", r.stdout)
        plan = (TEMPLATES / "build-plan.md").read_text(encoding="utf-8")
        self.assertIn("acceptance/", plan)
        self.assertIn("level 2 test", plan)
        for name in ("claude-md.md", "claude-md-sdlc.md"):
            self.assertIn("read-only", (TEMPLATES / name).read_text(encoding="utf-8"), name)


if __name__ == "__main__":
    unittest.main()
