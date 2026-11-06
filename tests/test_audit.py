import json, unittest
from helpers import project, run, story

TECH_DONE = {"openapi.json": json.dumps({"openapi": "3.1.0", "paths": {}}), "schemas/issue.schema.json": "{}",
             "api.md": "x\n" * 10, "data-model.md": "x\n" * 10, "nfr.md": "x\n" * 10,
             "decisions/0001-stack.md": "# Stack\n- Status: Accepted\n"}


class Audit(unittest.TestCase):
    def test_after_tech_the_pipeline_audits_before_handoff(self):
        root = project(stage="tech", files=TECH_DONE)
        p = json.loads(run("progress.py", root).stdout)
        self.assertEqual((p["next"], p["pending"]), ("audit", ["facts", "coverage", "consistency"]))
        (root / "docs" / "audit").mkdir()
        (root / "docs" / "audit" / "summary.md").write_text("done", encoding="utf-8")
        self.assertEqual(json.loads(run("progress.py", root).stdout)["next"], "handoff")

    def test_the_sample_is_the_same_on_a_rerun(self):
        crit = chr(10).join(f"- [ ] Given ENG-{n}, when I open it, then I see it. `[docs]`" for n in range(40))
        root = project(stories={"F-ISS-01-a.md": story("F-ISS-01", criteria=crit)})
        run("audit_sample.py", root)
        first = (root / "docs" / "audit" / "sample.md").read_text(encoding="utf-8")
        run("audit_sample.py", root)
        self.assertEqual(first, (root / "docs" / "audit" / "sample.md").read_text(encoding="utf-8"))
        self.assertEqual(first.count("[docs]:"), 25)


if __name__ == "__main__":
    unittest.main()
