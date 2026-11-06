"""Shared parsing for the rspec scripts (standard library only)."""
import json, re
from pathlib import Path

STAGES = ["init", "discovered", "features-approved", "stories", "tech", "handoff"]
PRIORITIES = {"MVP", "Later", "Drop"}
STATUSES = {"todo", "in-progress", "done"}
TAG_RE = re.compile(r"\[(docs|api|observed|inferred|3p|code)\]")  # confidence tags
ID_RE = re.compile(r"^F-([A-Z]{2,4})-(\d{2,3})$")
FILE_ID_RE = re.compile(r"^(F-[A-Z]{2,4}-\d{2,3})")
TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def load_config(docs):
    return json.loads((docs / "rspec.json").read_text(encoding="utf-8-sig"))


SINGLE_PATHS = {"spec": "docs", "contracts": "docs", "decisions": "docs/decisions", "changelog": "CHANGELOG.md"}


def monorepo_paths(slug):
    """sdlc's monorepo layout: the SRS in docs/specs/<slug>/, the contract in packages/api-contract/v1/."""
    return {"spec": f"docs/specs/{slug}", "contracts": "packages/api-contract/v1",
            "decisions": "docs/adr", "changelog": f"docs/specs/{slug}/CHANGELOG.md"}


def find_spec(root):
    """The spec folder holding rspec.json: docs/, else the one docs/specs/<name>/. None if absent.
    Raises ValueError when several specs exist under docs/specs/."""
    root = Path(root)
    if (root / "docs" / "rspec.json").exists():
        return root / "docs"
    hits = sorted((root / "docs" / "specs").glob("*/rspec.json"))
    if len(hits) > 1:
        raise ValueError("several specs found: " + ", ".join(h.parent.relative_to(root).as_posix() for h in hits)
                         + "; pass the spec folder instead of the project root")
    return hits[0].parent if hits else None


class Layout:
    """Where each part of a spec lives. `paths` in rspec.json is relative to the project root."""

    def __init__(self, root, spec, cfg):
        self.root = Path(root)
        self.spec = Path(spec)
        default = dict(SINGLE_PATHS, spec=self.spec.relative_to(self.root).as_posix())
        if default["spec"] != "docs":
            default.update(contracts=default["spec"], decisions=default["spec"] + "/decisions")
        self.paths = {k: (cfg.get("paths") or {}).get(k) or v for k, v in default.items()}
        self.contracts = self.root / self.paths["contracts"]
        self.decisions = self.root / self.paths["decisions"]
        self.changelog = self.root / self.paths["changelog"]


def open_layout(arg):
    """Resolve a command-line path (project root or spec folder) to (Layout, cfg). Exits with a message on failure."""
    import sys
    p = Path(arg).resolve()  # so "." inside the spec folder still has a real parent
    try:
        spec = p if (p / "rspec.json").exists() else find_spec(p)
    except ValueError as e:
        print(f"ERROR {e}"); sys.exit(1)
    if spec is None:
        return None, None
    root = spec.parents[2] if spec.parent.name == "specs" and spec.parent.parent.name == "docs" else spec.parent
    cfg = load_config(spec)
    return Layout(root, spec, cfg), cfg


def table_cells(line):
    """Cells of a Markdown table row; an escaped `\\|` stays inside its cell."""
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def feature_rows(docs):
    """Yield (line number, cells) for every feature row in features.md."""
    f = docs / "features.md"
    if not f.exists():
        return
    for n, line in enumerate(f.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.startswith("|"):
            continue
        cells = table_cells(line)
        if cells and cells[0].startswith("F-"):
            yield n, cells


def priorities(docs):
    """{feature ID: priority} in features.md order."""
    return {cells[0]: (cells[4] if len(cells) > 4 else "") for _, cells in feature_rows(docs)}


def in_scope(prio, cfg):
    """Feature IDs the spec covers, MVP first: every non-Drop feature when scope is "full",
    MVP only when it is "mvp" (and for specs made before 0.9.0, which have no scope)."""
    mvp = [i for i, p in prio.items() if p == "MVP"]
    if cfg.get("scope") != "full":
        return mvp
    return mvp + [i for i, p in prio.items() if p == "Later"]


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
    if isinstance(out.get("depends_on"), str):  # `depends_on: F-X-01` is a one-item list
        out["depends_on"] = [out["depends_on"]] if out["depends_on"] else []
    return out


def stories(docs):
    """{feature ID: (path, text, frontmatter or None)} for docs/features/F-*.md."""
    out = {}
    for p in sorted((docs / "features").glob("F-*.md")):
        m = FILE_ID_RE.match(p.name)
        if m:
            text = p.read_text(encoding="utf-8-sig")
            out[m.group(1)] = (p, text, frontmatter(text))
    return out


def dependencies(story_map):
    return {fid: list((fm or {}).get("depends_on") or []) for fid, (_, _, fm) in story_map.items()}


def find_cycles(deps):
    """Return every distinct dependency cycle found, each as a list of IDs ending where it starts."""
    state, stack, cycles, seen = {}, [], [], set()

    def visit(n):
        state[n] = 1
        stack.append(n)
        for d in deps.get(n, []):
            if state.get(d) == 1:
                cycle = stack[stack.index(d):]
                if frozenset(cycle) not in seen:
                    seen.add(frozenset(cycle))
                    cycles.append(cycle + [d])
            elif d in deps and not state.get(d):
                visit(d)
        stack.pop()
        state[n] = 2

    for n in deps:
        if not state.get(n):
            visit(n)
    return cycles


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


def contract_files(contracts):
    files = [contracts / "openapi.json", contracts / "asyncapi.json"] + sorted((contracts / "schemas").glob("*.json"))
    return [f for f in files if f.exists()]


def adr_statuses(decisions):
    out = {}
    for p in sorted(Path(decisions).glob("*.md")):
        if p.name.lower() == "readme.md":
            continue
        m = re.search(r"^-?\s*Status:\s*(\w+)", p.read_text(encoding="utf-8-sig"), re.M | re.I)
        out[p.name] = m.group(1) if m else ""
    return out


SLICE_RE = re.compile(r"^##\s*Slice\s+(\d+)\s*:?\s*(.*)$", re.M)
CRITERION_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s+\S", re.M)


def build_slices(docs):
    """[(number as str, name, [feature IDs])] from the `## Slice N: name` sections of build-plan.md."""
    plan = docs / "build-plan.md"
    if not plan.exists():
        return []
    text = plan.read_text(encoding="utf-8-sig")
    heads = list(SLICE_RE.finditer(text))
    out = []
    for i, h in enumerate(heads):
        body = text[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        ids = list(dict.fromkeys(re.findall(r"\bF-[A-Z]{2,4}-\d{2,3}\b", body)))
        out.append((h.group(1), h.group(2).strip(), ids))
    return out


def criteria_items(text):
    """The text of each `- [ ]` item under a story's `## Acceptance criteria`."""
    m = re.search(r"^##\s*(Acceptance criteria|Tiêu chí[^\n]*)\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    return re.findall(r"^\s*-\s*\[[ xX]\]\s+(\S.*)$", m.group(2), re.M) if m else []


def criteria_count(text):
    return len(criteria_items(text))


SDLC_MAX_CRITERIA = 10  # sdlc takes about 10 acceptance criteria per change
SLICE_BUDGET = 30  # without sdlc: about the acceptance criteria one build session can finish and test


def slice_criteria(story_map, ids):
    """Total acceptance criteria of the given features' stories."""
    return sum(criteria_count(story_map[i][1]) for i in ids if i in story_map)


def sdlc_status(root, feature):
    """The `Status:` of an sdlc feature's state file (.sdlc/state/<feature>.md), or '' if absent."""
    p = Path(root) / ".sdlc" / "state" / f"{feature}.md"
    if not p.exists():
        return ""
    m = re.search(r"^\**Status:?\**\s*:?\s*([\w-]+)", p.read_text(encoding="utf-8-sig"), re.M)
    return m.group(1).lower() if m else ""


GOALS = ("learn", "personal-use", "production")


def md_table(text, first_col_prefix):
    """Rows of the first Markdown table whose rows start with `first_col_prefix`, as dicts keyed by header."""
    header, rows = None, []
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            header = None if not rows else header
            continue
        cells = table_cells(line)
        if header is None:
            header = cells
        elif cells and cells[0].startswith(first_col_prefix):
            rows.append(dict(zip(header, cells + [""] * (len(header) - len(cells)))))
    return rows


def readiness_open(path):
    """{category: [unchecked items]} from production-readiness.md (`## Category` + `- [ ] item`)."""
    out = {}
    if not Path(path).exists():
        return out
    category = None
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            category = h.group(1)
            continue
        m = re.match(r"^\s*-\s*\[ \]\s+(\S.*)$", line)
        if m and category:
            out.setdefault(category, []).append(m.group(1))
    return out


def parked_decisions(spec):
    """Unchecked items under `## Parked` in autopilot-log.md: decisions autopilot left for the user."""
    p = Path(spec) / "autopilot-log.md"
    if not p.exists():
        return []
    m = re.search(r"^##\s*Parked\s*$(.*?)(?=^##\s|\Z)", p.read_text(encoding="utf-8-sig"), re.M | re.S)
    return re.findall(r"^\s*-\s*\[ \]\s+(\S.*)$", m.group(1), re.M) if m else []
