import json, unittest
from helpers import project, run, story

FULL = {"scope": "full", "deploy": "x", "build": {"engine": "none"}}


def plan(*slices):
    return "# Build plan\n\n## Release 1: MVP\n" + "".join(
        f"\n## Slice {n}: s{n}\n" + "".join(f"| 1 | {i} | x |\n" for i in ids) for n, ids in enumerate(slices, 1))


class Triage(unittest.TestCase):
    def test_a_drop_feature_promoted_after_handoff_routes_to_triage(self):
        root = project(stage="handoff", config=FULL, features=(("F-ISS-01", "MVP"), ("F-ISS-02", "Later")),
                       files={"build-plan.md": plan(["F-ISS-01"])})
        p = json.loads(run("progress.py", root).stdout)
        self.assertEqual((p["next"], p["pending"]), ("triage", ["F-ISS-02"]))

    def test_a_feature_demoted_to_drop_but_still_planned_is_an_error(self):
        root = project(stage="handoff", config=FULL, features=(("F-ISS-01", "MVP"), ("F-ISS-02", "Drop")),
                       files={"build-plan.md": plan(["F-ISS-01", "F-ISS-02"])})
        self.assertEqual(json.loads(run("progress.py", root).stdout)["next"], "triage")
        self.assertIn("still includes Drop F-ISS-02", run("check_spec.py", root).stdout)

    def test_a_slice_over_the_criteria_budget_without_sdlc_warns(self):
        eight = chr(10).join(f"- [ ] Given state {n}, when I act, then I see it." for n in range(8))
        feats = tuple((f"F-ISS-{n:02d}", "MVP") for n in range(1, 5))
        root = project(stage="handoff", config=FULL, features=feats,
                       stories={f"{i}-x.md": story(i, criteria=eight) for i, _ in feats},
                       files={"build-plan.md": plan([i for i, _ in feats])})
        self.assertIn("Slice 1 has 32 acceptance criteria; keep a slice to about 30", run("check_spec.py", root).stdout)


class MergeDeps(unittest.TestCase):
    def test_merges_a_later_module_dependency_and_skips_one_that_closes_a_cycle(self):
        iss = story("F-ISS-01").replace("depends_on: []", "depends_on: []\nalso_needs: [F-VIEW-01, F-VIEW-02]")
        root = project(modules=("ISS", "VIEW"), features=(("F-ISS-01", "MVP"), ("F-VIEW-01", "MVP"), ("F-VIEW-02", "MVP")),
                       stories={"F-ISS-01-a.md": iss, "F-VIEW-01-b.md": story("F-VIEW-01"),
                                "F-VIEW-02-c.md": story("F-VIEW-02", depends=["F-ISS-01"])})
        out = json.loads(run("merge_deps.py", root).stdout)
        self.assertEqual(out["added"], [["F-ISS-01", "F-VIEW-01"]])
        self.assertEqual(out["skipped"], [["F-ISS-01", "F-VIEW-02", "would close a cycle"]])
        text = (root / "docs" / "features" / "F-ISS-01-a.md").read_text(encoding="utf-8")
        self.assertIn("depends_on: [F-VIEW-01]", text)
        self.assertNotIn("also_needs", text)


if __name__ == "__main__":
    unittest.main()
