import json, unittest
from helpers import project, run, story

FULL = {"scope": "full"}
FEATURES = (("F-ISS-01", "MVP"), ("F-ISS-02", "Later"), ("F-ISS-03", "Drop"))


class FullScope(unittest.TestCase):
    def test_full_scope_writes_stories_for_later_features_after_mvp(self):
        root = project(stage="features-approved", config=FULL, features=FEATURES, stories={})
        p = json.loads(run("progress.py", root).stdout)
        self.assertEqual((p["next"], p["pending"]), ("stories", ["F-ISS-01", "F-ISS-02"]))

    def test_full_scope_requires_a_story_for_every_later_feature(self):
        r = run("check_spec.py", project(stage="stories", config=FULL, features=FEATURES,
                                         stories={"F-ISS-01-a.md": story("F-ISS-01")}))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("Later F-ISS-02 has no story file", r.stdout)

    def test_full_scope_build_order_puts_mvp_first(self):
        root = project(stage="handoff", config=FULL, features=(("F-ISS-02", "Later"), ("F-ISS-01", "MVP")), stories={
            "F-ISS-01-a.md": story("F-ISS-01"),
            "F-ISS-02-b.md": story("F-ISS-02", depends=["F-ISS-01"])})
        p = json.loads(run("progress.py", root, "--build-order").stdout)
        self.assertEqual(p["order"], ["F-ISS-01", "F-ISS-02"])

    def test_tech_stage_without_a_deployment_target_warns(self):
        r = run("check_spec.py", project(stage="tech", config={"deploy": ""}))
        self.assertIn("'deploy' is empty", r.stdout)


if __name__ == "__main__":
    unittest.main()
