import json, unittest
from helpers import project, run

DOMAIN = """# Domain rules

## Roles and permissions
| Action | Operations | guest | member | admin |
|---|---|---|---|---|
| Create an API key | createApiKey | no | no | yes |

## Enumerations
| Name | Values | Notes |
|---|---|---|
| role | guest, member, admin | |
"""


def api(roles, body_props=("name",)):
    return json.dumps({"openapi": "3.1.0", "paths": {"/keys": {"post": {
        "operationId": "createApiKey", "x-roles": roles, "x-features": ["F-ISS-01"], "responses": {}}}},
        "components": {"schemas": {"ApiKeyCreate": {"x-entity": "api-key",
                                                    "properties": {p: {} for p in body_props}}}}})


SCHEMA = json.dumps({"x-features": ["F-ISS-01"], "required": ["id", "name"],
                     "properties": {"id": {"type": "string", "readOnly": True}, "name": {"type": "string"},
                                    "role": {"enum": ["guest", "member", "admin"]}}})


def check(openapi, schema=SCHEMA):
    return run("check_spec.py", project(stage="tech", files={
        "domain.md": DOMAIN, "openapi.json": openapi, "schemas/api-key.schema.json": schema}))


class DomainRules(unittest.TestCase):
    def test_contract_matching_the_domain_rules_passes(self):
        r = check(api(["admin"]))
        self.assertNotIn("domain.md", r.stdout)
        self.assertNotIn("not in schemas/", r.stdout)

    def test_operation_roles_differing_from_the_permission_table_are_an_error(self):
        r = check(api(["member", "admin"]))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("createApiKey x-roles ['admin', 'member'] differ from domain.md", r.stdout)

    def test_an_enum_differing_from_the_domain_is_an_error(self):
        owner = SCHEMA.replace('"admin"]', '"admin", "owner"]')
        self.assertIn("enum 'role'", check(api(["admin"]), owner).stdout)


class Contracts(unittest.TestCase):
    def test_a_body_field_missing_from_its_entity_schema_is_an_error(self):
        r = check(api(["admin"], body_props=("name", "scopes")))
        self.assertIn("ApiKeyCreate uses scopes, not in schemas/api-key.schema.json", r.stdout)

    def test_a_required_id_without_readonly_warns(self):
        loose = SCHEMA.replace('"readOnly": true', '"readOnly": false')
        self.assertIn("required server-set fields are not readOnly", check(api(["admin"]), loose).stdout)


if __name__ == "__main__":
    unittest.main()
