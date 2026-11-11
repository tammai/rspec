import json, subprocess, sys, unittest
from pathlib import Path
from helpers import project, run, story

V1 = Path(__file__).resolve().parent.parent / "contracts" / "v1"


class ContractsVendor(unittest.TestCase):
    def test_vendored_copy_matches_manifest(self):
        r = subprocess.run([sys.executable, str(V1 / "contracts.py"), "vendor-check", str(V1)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_lock_records_contracts_1_2_0(self):
        root = project(stories={"F-ISS-01-a.md": story("F-ISS-01")})
        self.assertEqual(run("check_spec.py", root).returncode, 0)
        lock = json.loads((root / "docs" / "criteria.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["contracts"], "1.2.0")


if __name__ == "__main__":
    unittest.main()
