"""Cross-file contract checks: domain.md rules, API bodies vs entity schemas, server-set fields."""
import json, re
from pathlib import Path

SERVER_SET = {"id", "createdAt", "updatedAt", "created_at", "updated_at"}


def _section_table(text, heading):
    """Header and rows of the first Markdown table under `## heading`, placeholder rows (<...>) left out."""
    m = re.search(rf"^##\s*{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    if not m:
        return [], []
    lines = [l for l in m.group(1).splitlines() if l.strip().startswith("|")]
    if len(lines) < 2:
        return [], []
    cells = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]
    header = cells(lines[0])
    rows = [cells(l) for l in lines[2:] if "<" not in l]
    return header, rows


def _split(cell):
    return [v.strip().strip("`") for v in re.split(r"[,;]", cell) if v.strip()]


def operations(openapi):
    """{operationId: operation object} from an OpenAPI document."""
    out = {}
    for item in (openapi.get("paths") or {}).values():
        for op in (item or {}).values():
            if isinstance(op, dict) and op.get("operationId"):
                out[op["operationId"]] = op
    return out


def enum_properties(obj):
    """Yield (property name, enum values) for every property with an `enum`, anywhere in a JSON document."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "properties" and isinstance(v, dict):
                for name, prop in v.items():
                    if isinstance(prop, dict):
                        vals = prop.get("enum") or (prop.get("items") or {}).get("enum")
                        if isinstance(vals, list):
                            yield name, vals
            yield from enum_properties(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from enum_properties(v)


def check_domain(domain_text, openapi, docs):
    """docs: {relative name: parsed JSON} of every contract file. Returns (errors, warnings)."""
    errors, warns = [], []
    header, rows = _section_table(domain_text, "Roles and permissions")
    if header and "Operations" in header:
        roles = header[header.index("Operations") + 1:]
        ops = operations(openapi or {})
        for row in rows:
            row = row + [""] * (len(header) - len(row))
            action, allowed = row[0], {r for r, v in zip(roles, row[header.index("Operations") + 1:])
                                       if v.lower().startswith(("yes", "y", "✓"))}
            for op_id in _split(row[header.index("Operations")]):
                if not op_id or not re.fullmatch(r"[A-Za-z][\w.-]*", op_id):
                    continue  # blank or a placeholder like "(tech fills)"; tech fills it later
                op = ops.get(op_id)
                if op is None:
                    warns.append(f"domain.md: '{action}' names operation {op_id}, which openapi.json does not have")
                elif "x-roles" not in op:
                    warns.append(f"openapi.json: {op_id} has no x-roles; domain.md '{action}' allows {', '.join(sorted(allowed)) or 'nobody'}")
                elif set(op["x-roles"]) != allowed:
                    errors.append(f"openapi.json: {op_id} x-roles {sorted(op['x-roles'])} differ from domain.md "
                                  f"'{action}' {sorted(allowed)}")
    _, enums = _section_table(domain_text, "Enumerations")
    for row in enums:
        if len(row) < 2:
            continue
        name, values = row[0].strip("`"), set(_split(row[1]))
        seen = False
        for rel, doc in docs.items():
            for prop, vals in enum_properties(doc):
                if prop == name:
                    seen = True
                    if set(map(str, vals)) != values:
                        errors.append(f"{rel}: enum '{name}' {sorted(map(str, vals))} differs from domain.md {sorted(values)}")
        if not seen:
            warns.append(f"domain.md: enumeration '{name}' matches no schema property of that name; "
                         "the Name cell must be the exact property name so the check is meaningful")
    return errors, warns


def check_bodies(openapi, schemas_dir):
    """Component schemas with `x-entity` may only use properties of that entity's schema."""
    errors = []
    for name, comp in ((openapi or {}).get("components", {}).get("schemas") or {}).items():
        entity = isinstance(comp, dict) and comp.get("x-entity")
        if not entity:
            continue
        f = Path(schemas_dir) / f"{entity}.schema.json"
        if not f.exists():
            errors.append(f"openapi.json: {name} has x-entity '{entity}' but schemas/{entity}.schema.json is missing")
            continue
        try:
            schema = json.loads(f.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            continue  # the main check already reports an unreadable or invalid schema file
        known = set((schema.get("properties") or {}) if isinstance(schema, dict) else ())
        unknown = sorted(set(comp.get("properties") or {}) - known)
        if unknown:
            errors.append(f"openapi.json: {name} uses {', '.join(unknown)}, not in schemas/{entity}.schema.json")
    return errors


def server_set_not_readonly(schema):
    """Required server-set properties (id, createdAt, updatedAt) without readOnly: true."""
    props = schema.get("properties") or {}
    return [p for p in schema.get("required") or [] if p in SERVER_SET and not (props.get(p) or {}).get("readOnly")]
