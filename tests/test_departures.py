import json, unittest
from helpers import project, run, story
from test_check_spec import tech_files

ACCEPTED = """- id: D-004
  kind: simplification
  criteria: [F-ISS-01.AC1]
  features: [F-ISS-01]
  summary: Issue keys use 2-4 letters; the reference allows 1-5.
  decided_by: "Tam Mai, features approval 2026-11-08"
"""
PROPOSED = """- id: D-004
  kind: simplification
  features: [F-ISS-01]
  summary: Issue keys use 2-4 letters; the reference allows 1-5.
  status: proposed
"""


def differing(line):
    return {"F-ISS-01-x.md": story("F-ISS-01").replace("## Differences from the original\n- none",
                                                       f"## Differences from the original\n{line}")}


class Departures(unittest.TestCase):
    def test_differences_link_to_departures_registry(self):
        ok = project(stories=differing("- Keys use 2-4 letters → D-004"), files={"departures.yaml": ACCEPTED})
        r = run("check_spec.py", ok)
        self.assertEqual(r.returncode, 0, r.stdout)
        lock = json.loads((ok / "docs" / "criteria.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["criteria"][0]["departures"], ["D-004"])
        cases = {
            "no link": (differing("- Keys use 2-4 letters"), {"departures.yaml": ACCEPTED}, "the next /rspec:stories pass asks"),
            "dangling": (differing("- Keys use 2-4 letters → D-009"), {"departures.yaml": ACCEPTED},
                         "D-009 is not in departures.yaml"),
            "undecided": (differing("- Keys use 2-4 letters → D-004"),
                          {"departures.yaml": ACCEPTED.replace('  decided_by: "Tam Mai, features approval 2026-11-08"\n', "")},
                          "decided_by is required"),
        }
        for name, (stories, files, needle) in cases.items():
            with self.subTest(name):
                r = run("check_spec.py", project(stories=stories, files=files))
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(needle, r.stdout)

    def test_proposed_departure_warns_until_handoff(self):
        stories = differing("- Keys use 2-4 letters → D-004")
        r = run("check_spec.py", project(stories=stories, files={"departures.yaml": PROPOSED}))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARN  departures.yaml: D-004 is proposed", r.stdout)
        files = dict(tech_files(), **{"departures.yaml": PROPOSED,
                                      "build-plan.md": "# Build plan\n\n## Slice 1: Issues\n| 1 | F-ISS-01 F-ISS-01.AC1 |\n"})
        r = run("check_spec.py", project(stage="handoff", stories=stories, files=files, config={"stack": "x"}))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR departures.yaml: D-004 is proposed", r.stdout)


if __name__ == "__main__":
    unittest.main()
