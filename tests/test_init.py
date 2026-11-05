import json, unittest, tempfile
from pathlib import Path
from helpers import run

class InitSpec(unittest.TestCase):
    def test_monorepo_is_detected_and_spec_goes_to_docs_specs(self):
        root = Path(tempfile.mkdtemp())
        (root / ".sdlc").mkdir()
        (root / ".sdlc" / "config.json").write_text(json.dumps({"packages": [{"name": "web", "path": "apps/web"}]}))
        r = run("init_spec.py", root, "--name", "Acme Tracker")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cfg = json.loads((root / "docs/specs/acme-tracker/rspec.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["paths"]["contracts"], "packages/api-contract/v1")
        self.assertTrue((root / "packages/api-contract/v1/schemas").is_dir())
        self.assertTrue((root / "docs/specs/acme-tracker/CHANGELOG.md").exists())

    def test_single_repo_keeps_docs(self):
        root = Path(tempfile.mkdtemp())
        r = run("init_spec.py", root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cfg = json.loads((root / "docs/rspec.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["paths"]["spec"], "docs")
        self.assertTrue((root / "CHANGELOG.md").exists())

if __name__ == "__main__":
    unittest.main()
