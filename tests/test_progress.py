import json, unittest
from helpers import project, run, story

def progress(root, *args):
    return json.loads(run("progress.py", root, *args).stdout)

class Progress(unittest.TestCase):
    def test_discover_resumes_only_unfinished_modules(self):
        root = project(stage="init", modules=("IS", "ISS"), features=(), stories={})
        p = progress(root)
        self.assertEqual((p["next"], p["pending"]), ("discover", ["IS"]))

    def test_stories_resume_only_missing_mvp_ids(self):
        root = project(stage="features-approved", features=(("F-ISS-01", "MVP"), ("F-ISS-02", "MVP"), ("F-ISS-03", "Later")),
                       stories={"F-ISS-01-a.md": story("F-ISS-01")})
        p = progress(root)
        self.assertEqual((p["next"], p["pending"]), ("stories", ["F-ISS-02"]))

    def test_build_order_puts_dependencies_first_and_reports_status(self):
        root = project(stage="handoff", features=(("F-ISS-01", "MVP"), ("F-ISS-02", "MVP")), stories={
            "F-ISS-01-a.md": story("F-ISS-01", depends=["F-ISS-02"]),
            "F-ISS-02-b.md": story("F-ISS-02", status="done")})
        p = progress(root, "--build-order")
        self.assertEqual(p["order"], ["F-ISS-02", "F-ISS-01"])
        self.assertEqual(p["build"], {"todo": 1, "in-progress": 0, "done": 1})

    def test_finished_pipeline_reports_done_not_check_again(self):
        root = project(stage="handoff", config={"build": {"engine": "none"}, "pipeline": {"status": "done"}})
        p = progress(root)
        self.assertEqual((p["next"], p["pending"]), ("done", []))

    def test_sdlc_build_resumes_at_first_slice_sdlc_has_not_finished(self):
        plan = "# Build plan\n\n## Slice 1: Issues\n| 1 | F-ISS-01 |\n\n## Slice 2: Lists\n| 2 | F-ISS-02 |\n"
        root = project(stage="handoff", features=(("F-ISS-01", "MVP"), ("F-ISS-02", "MVP")),
                       config={"build": {"engine": "sdlc", "slices": {"1": "2026-11-05-m-issues"}}},
                       files={"build-plan.md": plan},
                       root_files={".sdlc/state/2026-11-05-m-issues.md": "Status: done\n"})
        p = progress(root)
        self.assertEqual((p["next"], p["pending"]), ("build", ["2"]))

if __name__ == "__main__":
    unittest.main()
