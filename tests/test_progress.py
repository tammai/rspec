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

if __name__ == "__main__":
    unittest.main()
