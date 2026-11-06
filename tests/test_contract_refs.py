import json, unittest
from helpers import project, run, story

API = {"openapi": "3.1.0", "paths": {"/issues": {"get": {"operationId": "listIssues", "x-features": ["F-ISS-01"],
       "responses": {"200": {"content": {"application/json": {"schema": {"$ref": "REF"}}}}}}}}}
SCHEMA = json.dumps({"$defs": {"filter": {"type": "object"}}, "x-features": ["F-ISS-01"]})


def api(ref):
    return json.dumps(API).replace("REF", ref)


class ContractRefs(unittest.TestCase):
    def test_a_ref_to_a_missing_schema_is_an_error(self):
        r = run("check_spec.py", project(stage="tech", files={"openapi.json": api("issue.schema.json#/$defs/filter"),
                                                              "schemas/issue.schema.json": SCHEMA}))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("$ref 'issue.schema.json#/$defs/filter' does not resolve", r.stdout)

    def test_a_ref_into_an_existing_schema_passes(self):
        r = run("check_spec.py", project(stage="tech", files={"openapi.json": api("schemas/issue.schema.json#/$defs/filter"),
                                                              "schemas/issue.schema.json": SCHEMA}))
        self.assertNotIn("does not resolve", r.stdout)

    def test_a_ui_only_feature_needs_no_contract(self):
        ui = story("F-ISS-02").replace("status: todo", "status: todo\nui_only: true")
        r = run("check_spec.py", project(stage="tech", config={"deploy": "x"},
                                         features=(("F-ISS-01", "MVP"), ("F-ISS-02", "MVP")),
                                         stories={"F-ISS-01-a.md": story("F-ISS-01"), "F-ISS-02-b.md": ui},
                                         files={"openapi.json": api("schemas/issue.schema.json"),
                                                "schemas/issue.schema.json": SCHEMA}))
        self.assertNotIn("F-ISS-02 is not served", r.stdout)


if __name__ == "__main__":
    unittest.main()
