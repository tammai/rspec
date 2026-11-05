import json, unittest
from helpers import project, run

LOG = """# Autopilot log

## Decisions
- [x] 2026-11-05 features: approved 18 MVP features as proposed (rule: approve-as-proposed)

## Parked
- [ ] F-ISS-07 Archive issues: still used by 30% of teams; kept as MVP instead of retiring
- [ ] NFR-04 accepted risk needs an owner
- [x] F-ISS-02 resolved by the user
"""
AUTOPILOT = {"autopilot": {"enabled": True, "rules": {"features": "approve-as-proposed"}}}


class Autopilot(unittest.TestCase):
    def test_progress_reports_autopilot_and_parked_decisions(self):
        root = project(stage="stories", config=AUTOPILOT, files={"autopilot-log.md": LOG})
        p = json.loads(run("progress.py", root).stdout)
        self.assertTrue(p["autopilot"])
        self.assertEqual(p["parked"], 2)

    def test_check_warns_about_parked_decisions(self):
        r = run("check_spec.py", project(stage="stories", config=AUTOPILOT, files={"autopilot-log.md": LOG}))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("2 autopilot decision(s) parked for you", r.stdout)


if __name__ == "__main__":
    unittest.main()
