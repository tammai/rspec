import json, unittest
from pathlib import Path
from helpers import project, run

OPENAPI = {"openapi": "3.1.0", "info": {"title": "X", "version": "0.1"},
           "paths": {"/issues": {"post": {"operationId": "createIssue", "x-features": ["F-ISS-01"]}}}}
SCHEMA = {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "Issue", "type": "object", "x-features": ["F-ISS-01"]}
NFR_HEAD = "| ID | Quality characteristic (ISO/IEC 25010) | Requirement (measurable) | Features | Verification | Why | Tag |\n|---|---|---|---|---|---|---|\n"
THREATS = ("| ID | STRIDE | Entry point | Threat | Mitigation | Tag |\n|---|---|---|---|---|---|\n"
           "| T-01 | Spoofing | POST /sessions | Credential stuffing | NFR-02 | [inferred] |\n")


def tech_files(nfr_rows, threat_model=THREATS):
    files = {"openapi.json": json.dumps(OPENAPI), "schemas/issue.schema.json": json.dumps(SCHEMA),
             "api.md": "x\n" * 9, "data-model.md": "x\n" * 9, "nfr.md": NFR_HEAD + nfr_rows + "x\n" * 6}
    if threat_model is not None:
        files["threat-model.md"] = threat_model
    return files


class ProductionGoal(unittest.TestCase):
    def test_production_spec_with_verified_nfrs_and_threat_model_passes(self):
        rows = ("| NFR-01 | Performance efficiency | p95 create < 300 ms at 50 rps | all | k6 load test in CI | | [inferred] |\n"
                "| NFR-02 | Security | 10 failed logins lock the account for 15 min | F-ISS-01 | integration test | | [docs] |\n")
        r = run("check_spec.py", project(stage="tech", config={"goal": "production"}, files=tech_files(rows)))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_production_nfr_without_verification_fails(self):
        rows = "| NFR-01 | Performance efficiency | p95 create < 300 ms | all |  | | [inferred] |\n"
        r = run("check_spec.py", project(stage="tech", config={"goal": "production"}, files=tech_files(rows)))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("NFR-01 has no Verification", r.stdout)

    def test_production_without_threat_model_fails(self):
        rows = "| NFR-01 | Security | lockout after 10 failures | all | integration test | | [docs] |\n"
        r = run("check_spec.py", project(stage="tech", config={"goal": "production"}, files=tech_files(rows, threat_model=None)))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("threat-model.md missing", r.stdout)

    def test_pipeline_is_not_done_until_readiness_items_are_done(self):
        readiness = ("# Production readiness\n\n## Security\n- [x] Dependency scan in CI: .github/workflows/ci.yml\n\n"
                     "## Operations\n- [ ] Restore drill from backup\n- [x] Status page (n/a: internal tool)\n")
        plan = "# Build plan\n\n## Slice 1: Issues\n| 1 | F-ISS-01 |\n"
        root = project(stage="handoff", config={"goal": "production", "build": {"engine": "sdlc", "slices": {"1": "f1"}}},
                       files={"build-plan.md": plan, "production-readiness.md": readiness},
                       root_files={".sdlc/state/f1.md": "Status: done\n"})
        p = json.loads(run("progress.py", root).stdout)
        self.assertEqual((p["next"], p["pending"]), ("readiness", ["Operations"]))

    def test_handoff_accepts_the_readiness_template_and_its_categories_stay_pending(self):
        template = (Path(__file__).resolve().parents[1] / "templates" / "production-readiness.md").read_text(encoding="utf-8")
        rows = "| NFR-01 | Security | lockout after 10 failures | all | integration test | | [docs] |\n"
        files = dict(tech_files(rows), **{"production-readiness.md": template,
                                          "build-plan.md": "# Build plan\n\n## Slice 1: Issues\n| 1 | F-ISS-01 F-ISS-01.AC1 |\n"})
        root = project(stage="handoff", config={"goal": "production", "stack": "x",
                                                "build": {"engine": "sdlc", "slices": {"1": "f1"}}},
                       files=files, root_files={".sdlc/state/f1.md": "Status: done\n"})
        r = run("check_spec.py", root)
        self.assertEqual(r.returncode, 0, r.stdout)
        p = json.loads(run("progress.py", root).stdout)
        self.assertEqual(p["next"], "readiness")
        for category in ("Requirements (NFRs)", "Documentation",
                         "Client app (anything shipped to a device or an app store; delete this section otherwise)"):
            self.assertIn(category, p["pending"])


if __name__ == "__main__":
    unittest.main()
