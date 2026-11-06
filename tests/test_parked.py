import json, unittest
from helpers import project, run

LOG = "# Autopilot log\n\n## Decisions\n\n## Parked\n- [ ] Owner or admin deletes a workspace?\n"


class Parked(unittest.TestCase):
    def test_a_finished_run_with_parked_decisions_is_not_done(self):
        root = project(stage="handoff", config={"pipeline": {"status": "done"}}, files={"autopilot-log.md": LOG})
        p = json.loads(run("progress.py", root).stdout)
        self.assertEqual((p["next"], p["pending"]), ("parked", ["Owner or admin deletes a workspace?"]))


if __name__ == "__main__":
    unittest.main()
