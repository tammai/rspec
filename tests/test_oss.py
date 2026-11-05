import unittest
from helpers import project, run


class OpenSourceProduct(unittest.TestCase):
    def test_reading_oss_code_requires_a_pinned_commit(self):
        cfg = {"code": True, "sources": {"repo": "https://github.com/example/tracker", "commit": ""}}
        r = run("check_spec.py", project(config=cfg))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("pin the commit", r.stdout)

    def test_oss_spec_with_repo_and_commit_passes(self):
        cfg = {"code": True, "sources": {"repo": "https://github.com/example/tracker", "commit": "abc1234"}}
        r = run("check_spec.py", project(config=cfg))
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
