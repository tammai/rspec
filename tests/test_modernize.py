import json, unittest
from helpers import project, run

OPENAPI = {"openapi": "3.1.0", "info": {"title": "X", "version": "0.1"},
           "paths": {"/issues": {"post": {"operationId": "createIssue", "x-features": ["F-ISS-01"]}}}}
SCHEMA = {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "Issue", "type": "object", "x-features": ["F-ISS-01"]}
MIGRATION = ("# Data migration\n\n## Mapping\n| ID | Old (store.table) | New (entity) | Transform | Validation |\n|---|---|---|---|---|\n"
             "| M-01 | mysql.tickets | issue | status codes 1-4 to enum | row count and checksum of ids |\n")
CUTOVER = "# Cutover plan\n\n## Steps\n1. Freeze writes\n\n## Rollback\n1. Point DNS back to the old system\n"
MODERNIZE = {"track": "modernize", "strategy": "rewrite", "goal": "personal-use"}


def tech_files(**extra):
    files = {"openapi.json": json.dumps(OPENAPI), "schemas/issue.schema.json": json.dumps(SCHEMA),
             "api.md": "x\n" * 9, "data-model.md": "x\n" * 9, "nfr.md": "x\n" * 9, "data-migration.md": MIGRATION}
    files.update(extra)
    return {k: v for k, v in files.items() if v is not None}


class ModernizeTrack(unittest.TestCase):
    def test_modernize_spec_with_migration_and_cutover_passes(self):
        files = tech_files(**{"build-plan.md": "# Build plan\n\n## Slice 1: Issues\n| 1 | F-ISS-01 |\n", "cutover-plan.md": CUTOVER})
        r = run("check_spec.py", project(stage="handoff", config=MODERNIZE, files=files))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_modernize_without_data_migration_fails(self):
        r = run("check_spec.py", project(stage="tech", config=MODERNIZE, files=tech_files(**{"data-migration.md": None})))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("data-migration.md missing", r.stdout)

    def test_mapping_without_validation_fails(self):
        bad = MIGRATION.replace("row count and checksum of ids", "")
        r = run("check_spec.py", project(stage="tech", config=MODERNIZE, files=tech_files(**{"data-migration.md": bad})))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("M-01 has no Validation", r.stdout)

    def test_cutover_plan_without_rollback_fails(self):
        files = tech_files(**{"build-plan.md": "# Build plan\n\n## Slice 1: Issues\n| 1 | F-ISS-01 |\n",
                              "cutover-plan.md": "# Cutover plan\n\n## Steps\n1. Switch\n"})
        r = run("check_spec.py", project(stage="handoff", config=MODERNIZE, files=files))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("cutover-plan.md has no '## Rollback' section", r.stdout)

    def test_tech_resume_includes_data_migration(self):
        root = project(stage="stories", config=MODERNIZE, files={"nfr.md": "x\n" * 9})
        p = json.loads(run("progress.py", root).stdout)
        self.assertEqual(p["next"], "tech")
        self.assertIn("data-migration", p["pending"])


if __name__ == "__main__":
    unittest.main()
