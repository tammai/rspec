import json, subprocess, sys, unittest
from helpers import SCRIPTS, project, run, story


class InputForms(unittest.TestCase):
    def test_run_from_inside_the_spec_folder_finds_the_contracts(self):
        paths = {"spec": "docs", "contracts": "docs", "decisions": "docs/decisions", "changelog": "CHANGELOG.md"}
        root = project(stage="init", config={"paths": paths}, files={"openapi.json": json.dumps({"openapi": "3.0.0"})})
        r = subprocess.run([sys.executable, str(SCRIPTS / "check_spec.py")], cwd=root / "docs",
                           capture_output=True, text=True)
        self.assertIn("'openapi' must be 3.1.x", r.stdout)

    def test_single_value_depends_on_counts_as_a_list(self):
        root = project(features=(("F-ISS-02", "MVP"), ("F-ISS-01", "MVP")), stories={
            "F-ISS-01-a.md": story("F-ISS-01"),
            "F-ISS-02-b.md": story("F-ISS-02").replace("depends_on: []", "depends_on: F-ISS-01")})
        p = json.loads(run("progress.py", root, "--build-order").stdout)
        self.assertEqual(p["order"], ["F-ISS-01", "F-ISS-02"])

    def test_story_saved_with_a_bom_is_read(self):
        root = project(stories={"F-ISS-01-x.md": "﻿" + story("F-ISS-01")})
        r = run("check_spec.py", root)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_escaped_pipe_in_a_feature_cell_keeps_the_columns(self):
        root = project()
        f = root / "docs" / "features.md"
        f.write_text(f.read_text(encoding="utf-8").replace("Does it", "match `a \\| b` queries"), encoding="utf-8")
        r = run("check_spec.py", root)
        self.assertIn("mvp=1", r.stdout)


if __name__ == "__main__":
    unittest.main()
