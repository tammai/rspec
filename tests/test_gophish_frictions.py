"""Plugin frictions the gophish run surfaced (v0.9.9)."""
import json, unittest
from helpers import project, run, story

DOMAIN = """# Domain rules

## Roles and permissions
| Action | Operations | member | admin |
|---|---|---|---|
| Delete a campaign | _(tech fills)_ | no | yes |

## Enumerations
| Name | Values | Notes |
|---|---|---|
| campaignStatus | Draft, Sending, Completed | |
| permission (slug) | read, write | |
"""

SCHEMA = json.dumps({"x-features": ["F-ISS-01"], "required": ["id"],
                     "properties": {"id": {"type": "string", "readOnly": True},
                                    "campaignStatus": {"enum": ["Draft", "Sending", "Completed"]}}})
API = json.dumps({"openapi": "3.1.0", "paths": {}})


class Frictions(unittest.TestCase):
    def test_a_format_placeholder_email_is_not_flagged_as_pii(self):
        res = {"prof.md": "The from-address matches local@domain.tld. `[code]`"}
        r = run("check_spec.py", project(stage="discovered", research=res))
        self.assertNotIn("contains an email address", r.stdout)

    def test_a_real_email_is_still_flagged(self):
        res = {"prof.md": "Contact jane.doe@acme.co for access. `[docs]`"}
        r = run("check_spec.py", project(stage="discovered", research=res))
        self.assertIn("contains an email address", r.stdout)

    def test_a_placeholder_operations_cell_does_not_warn(self):
        r = run("check_spec.py", project(stage="tech", files={
            "domain.md": DOMAIN, "openapi.json": API, "schemas/campaign.schema.json": SCHEMA}))
        self.assertNotIn("names operation", r.stdout)

    def test_an_enum_name_matching_no_property_warns(self):
        r = run("check_spec.py", project(stage="tech", files={
            "domain.md": DOMAIN, "openapi.json": API, "schemas/campaign.schema.json": SCHEMA}))
        self.assertIn("'permission (slug)' matches no schema property", r.stdout)

    def test_h3_slice_headings_are_an_error(self):
        plan = "# Build plan\n\n## Release 1: MVP\n### Slice 1: s\n| 1 | F-ISS-01 | x |\n"
        r = run("check_spec.py", project(stage="handoff", config={"build": {"engine": "none"}},
                                         files={"build-plan.md": plan}))
        self.assertIn("must be '## Slice N'", r.stdout)


if __name__ == "__main__":
    unittest.main()
