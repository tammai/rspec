import json, subprocess, sys, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_spec.py"

STORY = """# F-ISS-01: Create issue

- Module: ISS
- Priority: MVP
- Depends on: none

## Story
As a member, I want to create an issue so that work is tracked.

## Acceptance criteria
- [ ] A new issue appears in the list with the next team number.

## Edge cases
{edge}

## Differences from the original
- none

## Sources
- research/iss-issues.md, Flows
"""

def run(edge):
    root = Path(tempfile.mkdtemp())
    docs = root / "docs"
    for d in ("research", "features", "decisions"):
        (docs / d).mkdir(parents=True)
    (docs / "rspec.json").write_text(json.dumps({"product": "X", "goal": "learn", "stage": "stories",
        "modules": [{"code": "ISS", "name": "Issues"}]}), encoding="utf-8")
    (docs / "research" / "iss-issues.md").write_text("# ISS", encoding="utf-8")
    (docs / "features.md").write_text("| ID | Module | Feature | Behaviour | Priority | Reason |\n"
        "| F-ISS-01 | ISS | Create | Create an issue | MVP | |\n", encoding="utf-8")
    (docs / "features" / "F-ISS-01-create.md").write_text(STORY.format(edge=edge), encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True)

class CheckSpec(unittest.TestCase):
    def test_complete_story_passes(self):
        r = run("- Empty title: the issue is not created and an error is shown.")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_leftover_template_placeholder_fails(self):
        r = run("- <case>: <expected behaviour>")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("template placeholders", r.stdout)

if __name__ == "__main__":
    unittest.main()
