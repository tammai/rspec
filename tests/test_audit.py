import json, unittest
from helpers import project, run, story

TECH_DONE = {"openapi.json": json.dumps({"openapi": "3.1.0", "paths": {}}), "schemas/issue.schema.json": "{}",
             "api.md": "x\n" * 10, "data-model.md": "x\n" * 10, "nfr.md": "x\n" * 10,
             "decisions/0001-stack.md": "# Stack\n- Status: Accepted\n"}


def criteria(counts):
    """Story criteria: counts is [(tag, n)], numbered AC1.. in that order."""
    lines, k = [], 0
    for tag, n in counts:
        for _ in range(n):
            k += 1
            lines.append(f"- [ ] **F-ISS-01.AC{k}** Given ENG-{k}, when I open it, then I see ENG-{k}. `[{tag}]`")
    return "\n".join(lines)


class Audit(unittest.TestCase):
    def test_after_tech_the_pipeline_audits_before_handoff(self):
        root = project(stage="tech", files=TECH_DONE)
        p = json.loads(run("progress.py", root).stdout)
        self.assertEqual((p["next"], p["pending"]), ("audit", ["facts", "coverage", "consistency"]))
        (root / "docs" / "audit").mkdir()
        (root / "docs" / "audit" / "summary.md").write_text("done", encoding="utf-8")
        self.assertEqual(json.loads(run("progress.py", root).stdout)["next"], "verify")

    def test_sample_size_per_tag(self):
        counts = [("docs", 40), ("api", 3), ("observed", 200), ("code", 26), ("inferred", 12), ("3p", 4)]
        root = project(stories={"F-ISS-01-a.md": story("F-ISS-01", criteria=criteria(counts))})
        r = run("audit_sample.py", root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sample = json.loads((root / "docs" / "audit" / "sample.json").read_text(encoding="utf-8"))
        self.assertEqual({t: (len(v["population"]), len(v["sample"])) for t, v in sample["tags"].items()},
                         {"docs": (40, 8), "api": (3, 3), "observed": (200, 25), "code": (26, 6), "inferred": (12, 5)})
        first = (root / "docs" / "audit" / "sample.md").read_text(encoding="utf-8")
        self.assertIn("F-ISS-01.AC", first)
        run("audit_sample.py", root)
        self.assertEqual(first, (root / "docs" / "audit" / "sample.md").read_text(encoding="utf-8"))

    def test_audit_verdicts_raise_criteria_to_level_1(self):
        counts = [("docs", 10), ("api", 2), ("observed", 10)]
        root = project(stories={"F-ISS-01-a.md": story("F-ISS-01", criteria=criteria(counts))})
        run("audit_sample.py", root)
        audit = root / "docs" / "audit"
        tags = json.loads((audit / "sample.json").read_text(encoding="utf-8"))["tags"]
        verdict = {i: "SUPPORTED" for v in tags.values() for i in v["sample"]}
        unsupported, contradicted = tags["api"]["sample"][0], tags["observed"]["sample"][0]
        verdict[unsupported], verdict[contradicted] = "UNSUPPORTED", "CONTRADICTED"
        rows = "".join(f"| {i} | x | {v} | https://docs.example | n |\n" for i, v in verdict.items())
        (audit / "facts.md").write_text("accuracy: 90%, contradicted: 1\n\n| ID | Tag | Verdict | Source | Note |\n"
                                        "|---|---|---|---|---|\n" + rows, encoding="utf-8")
        path = root / "docs" / "features" / "F-ISS-01-a.md"
        edited = next(i for i in tags["docs"]["population"] if i not in tags["docs"]["sample"])
        k = edited.split("AC")[1]
        path.write_text(path.read_text(encoding="utf-8").replace(f"then I see ENG-{k}.", f"then I see ENG-{k}9."),
                        encoding="utf-8")
        r = run("audit_sample.py", root, "--levels")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(run("check_spec.py", root).returncode, 0)
        lock = json.loads((root / "docs" / "criteria.lock.json").read_text(encoding="utf-8"))
        level = {c["id"]: c["level"] for c in lock["criteria"]}
        observed_unsampled = set(tags["observed"]["population"]) - set(tags["observed"]["sample"])
        self.assertTrue(all(level[i] == 1 for i in tags["docs"]["population"] if i != edited))
        self.assertEqual(level[edited], 0)
        self.assertEqual(level[unsupported], 0)
        self.assertEqual(level[contradicted], 0)
        self.assertTrue(all(level[i] == 0 for i in observed_unsampled))
        docs_one = next(i for i in tags["docs"]["population"] if i != edited)
        n = docs_one.split("AC")[1]
        path.write_text(path.read_text(encoding="utf-8").replace(f"then I see ENG-{n}.", f"then I see ENG-{n}0."),
                        encoding="utf-8")
        run("check_spec.py", root)
        lock = json.loads((root / "docs" / "criteria.lock.json").read_text(encoding="utf-8"))
        self.assertEqual({c["id"]: c["level"] for c in lock["criteria"]}[docs_one], 0)

    def levels_after(self, counts, verdict_for):
        """Draw, write facts.md with verdict_for(tag) for every sampled criterion, run --levels; (tags, lock levels)."""
        root = project(stories={"F-ISS-01-a.md": story("F-ISS-01", criteria=criteria(counts))})
        run("audit_sample.py", root)
        audit = root / "docs" / "audit"
        tags = json.loads((audit / "sample.json").read_text(encoding="utf-8"))["tags"]
        rows = "".join(f"| {i} | {t} | {verdict_for(t)} | https://docs.example | n |\n"
                       for t, v in tags.items() for i in v["sample"])
        (audit / "facts.md").write_text("| ID | Tag | Verdict | Source | Note |\n|---|---|---|---|---|\n" + rows,
                                        encoding="utf-8")
        r = run("audit_sample.py", root, "--levels")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(run("check_spec.py", root).returncode, 0)
        lock = json.loads((root / "docs" / "criteria.lock.json").read_text(encoding="utf-8"))
        return tags, {c["id"]: c["level"] for c in lock["criteria"]}

    def test_inferred_criteria_never_reach_level_1(self):
        tags, level = self.levels_after([("docs", 6), ("inferred", 12)],
                                        lambda t: "NOT-CONTRADICTED" if t == "inferred" else "SUPPORTED")
        self.assertLess(len(tags["inferred"]["sample"]), len(tags["inferred"]["population"]))
        self.assertTrue(all(level[i] == 0 for i in tags["inferred"]["population"]))
        self.assertTrue(all(level[i] == 1 for i in tags["docs"]["population"]))

    def test_not_contradicted_on_a_sourced_tag_stays_level_0(self):
        tags, level = self.levels_after([("docs", 6)], lambda t: "NOT-CONTRADICTED")
        self.assertTrue(all(level[i] == 0 for i in tags["docs"]["sample"]))


if __name__ == "__main__":
    unittest.main()
