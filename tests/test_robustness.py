"""Edge-input robustness, from bugs the bug-hunter surfaced (v0.9.8)."""
import json, sys, unittest
from pathlib import Path
from helpers import project, run, story

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import scorecard  # noqa: E402


class Scorecard(unittest.TestCase):
    def test_an_empty_feature_name_does_not_crash(self):
        self.assertFalse(scorecard.similar("Issue list", ""))
        self.assertFalse(scorecard.similar("", ""))

    def test_non_ascii_names_tokenize_to_real_words_not_fragments(self):
        # Vietnamese "Đăng ký" (sign up): the ASCII tokenizer gave the fragment {k, ng};
        # it must give the real words so unrelated names do not collide on a fragment.
        self.assertEqual(scorecard.words("Đăng ký"), {"đăng", "ký"})
        self.assertFalse(scorecard.similar("Chiến dịch", "Mẫu thư"))  # campaign vs template: no shared word


class MalformedInput(unittest.TestCase):
    def test_build_plan_matches_whole_ids_not_substrings(self):
        feats = (("F-ISS-10", "MVP"), ("F-ISS-100", "MVP"))
        plan = "# Build plan\n\n## Release 1: MVP\n## Slice 1: s\n| 1 | F-ISS-100 | x |\n"
        r = run("check_spec.py", project(stage="handoff", config={"build": {"engine": "none"}}, features=feats,
                                         stories={f"{i}-x.md": story(i) for i, _ in feats},
                                         files={"build-plan.md": plan}))
        self.assertIn("does not include MVP F-ISS-10", r.stdout)  # not hidden by F-ISS-100

    def test_a_contract_file_that_is_not_an_object_errors_cleanly(self):
        r = run("check_spec.py", project(stage="tech", files={"openapi.json": "[]", "schemas/x.schema.json": "{}"}))
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("must be a JSON object", r.stdout)

    def test_modules_set_to_null_does_not_crash(self):
        r = run("check_spec.py", project(stage="discovered", config={"modules": None}))
        self.assertNotIn("Traceback", r.stderr)

    def test_a_body_whose_entity_schema_is_invalid_json_does_not_crash(self):
        api = json.dumps({"openapi": "3.1.0", "paths": {}, "components": {"schemas": {
            "IssueCreate": {"x-entity": "issue", "properties": {"a": {}}}}}})
        r = run("check_spec.py", project(stage="tech", files={"openapi.json": api,
                                                              "schemas/issue.schema.json": "{not json"}))
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("not valid JSON", r.stdout)


if __name__ == "__main__":
    unittest.main()
