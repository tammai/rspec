import subprocess, sys, unittest
from pathlib import Path

V1 = Path(__file__).resolve().parent.parent / "contracts" / "v1"


class ContractsVendor(unittest.TestCase):
    def test_vendored_copy_matches_manifest(self):
        r = subprocess.run([sys.executable, str(V1 / "contracts.py"), "vendor-check", str(V1)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
