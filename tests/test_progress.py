import json, subprocess, sys, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "progress.py"

def project(stage, modules, research=(), features="", stories=()):
    root = Path(tempfile.mkdtemp())
    docs = root / "docs"
    for d in ("research", "features", "decisions"):
        (docs / d).mkdir(parents=True)
    (docs / "rspec.json").write_text(json.dumps({"product": "X", "stage": stage,
        "modules": [{"code": c, "name": c} for c in modules]}), encoding="utf-8")
    for name in research:
        (docs / "research" / name).write_text("# r", encoding="utf-8")
    (docs / "features.md").write_text(features, encoding="utf-8")
    for name in stories:
        (docs / "features" / name).write_text("# s", encoding="utf-8")
    return root

def progress(root):
    r = subprocess.run([sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True)
    return json.loads(r.stdout)

class Progress(unittest.TestCase):
    def test_discover_resumes_only_unfinished_modules(self):
        root = project("init", ["IS", "ISS"], research=["iss-issues.md"])
        p = progress(root)
        self.assertEqual(p["next"], "discover")
        self.assertEqual(p["pending"], ["IS"])

    def test_stories_resume_only_missing_mvp_ids(self):
        rows = ("| F-ISS-01 | ISS | A | a | MVP | |\n| F-ISS-02 | ISS | B | b | MVP | |\n"
                "| F-ISS-03 | ISS | C | c | Later | |\n")
        root = project("features-approved", ["ISS"], features=rows, stories=["F-ISS-01-a.md"])
        p = progress(root)
        self.assertEqual(p["next"], "stories")
        self.assertEqual(p["pending"], ["F-ISS-02"])

if __name__ == "__main__":
    unittest.main()
