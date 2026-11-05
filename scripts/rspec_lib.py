"""Shared parsing for the rspec scripts (standard library only)."""
import json, re
from pathlib import Path

STAGES = ["init", "discovered", "features-approved", "stories", "tech", "handoff"]
PRIORITIES = {"MVP", "Later", "Drop"}
STATUSES = {"todo", "in-progress", "done"}
ID_RE = re.compile(r"^F-([A-Z]{2,4})-(\d{2,3})$")
FILE_ID_RE = re.compile(r"^(F-[A-Z]{2,4}-\d{2,3})")
TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def load_config(docs):
    return json.loads((docs / "rspec.json").read_text(encoding="utf-8"))


def feature_rows(docs):
    """Yield (line number, cells) for every feature row in features.md."""
    f = docs / "features.md"
    if not f.exists():
        return
    for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0].startswith("F-"):
            yield n, cells


def priorities(docs):
    """{feature ID: priority} in features.md order."""
    return {cells[0]: (cells[4] if len(cells) > 4 else "") for _, cells in feature_rows(docs)}


def frontmatter(text):
    """Parse a flat YAML frontmatter block: `key: value` and `key: [a, b]`. None if absent."""
    m = re.match(r"\A---\s*\n(.*?)\n---\s*(\n|\Z)", text, re.S)
    if not m:
        return None
    out = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = (s.strip() for s in line.split(":", 1))
        if value.startswith("[") and value.endswith("]"):
            out[key] = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        else:
            out[key] = value.strip("'\"")
    return out


def stories(docs):
    """{feature ID: (path, text, frontmatter or None)} for docs/features/F-*.md."""
    out = {}
    for p in sorted((docs / "features").glob("F-*.md")):
        m = FILE_ID_RE.match(p.name)
        if m:
            text = p.read_text(encoding="utf-8")
            out[m.group(1)] = (p, text, frontmatter(text))
    return out


def dependencies(story_map):
    return {fid: list((fm or {}).get("depends_on") or []) for fid, (_, _, fm) in story_map.items()}


def find_cycle(deps):
    """Return one dependency cycle as a list of IDs, or None."""
    state, stack = {}, []

    def visit(n):
        state[n] = 1
        stack.append(n)
        for d in deps.get(n, []):
            if state.get(d) == 1:
                return stack[stack.index(d):] + [d]
            if d in deps and not state.get(d):
                found = visit(d)
                if found:
                    return found
        stack.pop()
        state[n] = 2
        return None

    for n in deps:
        if not state.get(n):
            found = visit(n)
            if found:
                return found
    return None


def build_order(ids, deps):
    """Order ids so every dependency comes first; ties keep the given order."""
    done, order = set(), []

    def place(n, seen=()):
        if n in done or n in seen:
            return
        for d in deps.get(n, []):
            if d in ids:
                place(d, seen + (n,))
        done.add(n)
        order.append(n)

    for n in ids:
        place(n)
    return order


def feature_refs(obj):
    """All feature IDs listed under any `x-features` key in a JSON document."""
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "x-features" and isinstance(v, list):
                found += [x for x in v if isinstance(x, str)]
            else:
                found += feature_refs(v)
    elif isinstance(obj, list):
        for v in obj:
            found += feature_refs(v)
    return found


def contract_files(docs):
    files = [docs / "openapi.json", docs / "asyncapi.json"] + sorted((docs / "schemas").glob("*.json"))
    return [f for f in files if f.exists()]


def adr_statuses(docs):
    out = {}
    for p in sorted((docs / "decisions").glob("*.md")):
        m = re.search(r"^-?\s*Status:\s*(\w+)", p.read_text(encoding="utf-8"), re.M | re.I)
        out[p.name] = m.group(1) if m else ""
    return out


SLICE_RE = re.compile(r"^##\s*Slice\s+(\d+)\s*:?\s*(.*)$", re.M)
CRITERION_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s+\S", re.M)


def build_slices(docs):
    """[(number as str, name, [feature IDs])] from the `## Slice N: name` sections of build-plan.md."""
    plan = docs / "build-plan.md"
    if not plan.exists():
        return []
    text = plan.read_text(encoding="utf-8")
    heads = list(SLICE_RE.finditer(text))
    out = []
    for i, h in enumerate(heads):
        body = text[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        ids = list(dict.fromkeys(re.findall(r"\bF-[A-Z]{2,4}-\d{2,3}\b", body)))
        out.append((h.group(1), h.group(2).strip(), ids))
    return out


def criteria_count(text):
    m = re.search(r"^##\s*(Acceptance criteria|Tiêu chí[^\n]*)\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    return len(CRITERION_RE.findall(m.group(2))) if m else 0


def sdlc_status(root, feature):
    """The `Status:` of an sdlc feature's state file (.sdlc/state/<feature>.md), or '' if absent."""
    p = Path(root) / ".sdlc" / "state" / f"{feature}.md"
    if not p.exists():
        return ""
    m = re.search(r"^\**Status:?\**\s*:?\s*([\w-]+)", p.read_text(encoding="utf-8"), re.M)
    return m.group(1).lower() if m else ""
