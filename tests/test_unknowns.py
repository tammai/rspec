import json, unittest
from helpers import project, run, story

CRITERIA = ('- [ ] **F-ISS-01.AC1** Given team ENG with 11 issues, when a member creates "Fix login", '
            'then it is shown as ENG-12. `[docs]`\n'
            '- [ ] **F-ISS-01.AC2** Given team ENG archived, when a member opens ENG-3, then it reads "Archived". '
            '`[inferred]`')


def entry(**kw):
    e = {"id": "U-001", "question": "Does archiving a team archive its issues?", "criteria": ["F-ISS-01.AC1"],
         "probe": "Archive a seeded team on the reference and read its issues", "status": "open",
         "raised": "stories 2026-11-11"}
    e.update(kw)
    return {k: v for k, v in e.items() if v is not None}


def to_yaml(entries):
    lines = []
    for e in entries:
        first = True
        for k, v in e.items():
            val = "[" + ", ".join(v) + "]" if isinstance(v, list) else json.dumps(v)
            lines.append(("- " if first else "  ") + f"{k}: {val}")
            first = False
    return "\n".join(lines) + "\n"


def spec(entries=None, stage="stories", story_text=None, features=(("F-ISS-01", "MVP"),), extra_stories=None):
    files = {} if entries is None else {"unknowns.yaml": to_yaml(entries)}
    stories = {"F-ISS-01-a.md": story_text or story("F-ISS-01", criteria=CRITERIA)}
    stories.update(extra_stories or {})
    return project(stage=stage, features=features, stories=stories, files=files)


def lock(root):
    return {c["id"]: c for c in json.loads((root / "docs" / "criteria.lock.json").read_text(encoding="utf-8"))["criteria"]}


def set_status(root, entries):
    (root / "docs" / "unknowns.yaml").write_text(to_yaml(entries), encoding="utf-8")


class Unknowns(unittest.TestCase):
    def test_open_unknown_caps_level_until_resolved(self):
        root = spec([])
        self.assertEqual(run("check_spec.py", root).returncode, 0)
        sha = {i: c["text_sha256"] for i, c in lock(root).items()}
        audit = root / "docs" / "audit"
        audit.mkdir()
        (audit / "levels.json").write_text(json.dumps({"criteria": {"F-ISS-01.AC1": sha["F-ISS-01.AC1"]}}),
                                           encoding="utf-8")
        self.assertEqual(lock(root)["F-ISS-01.AC1"]["level"], 0)
        run("check_spec.py", root)
        self.assertEqual(lock(root)["F-ISS-01.AC1"]["level"], 1)

        set_status(root, [entry()])
        r = run("check_spec.py", root)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(lock(root)["F-ISS-01.AC1"]["level"], 0)
        self.assertIn("U-001", r.stdout)
        self.assertRegex(r.stdout, r"WARN .*F-ISS-01\.AC1.*U-001")

        set_status(root, [entry(criteria=[], features=["F-ISS-01"])])  # through its feature: every criterion
        run("check_spec.py", root)
        self.assertEqual(lock(root)["F-ISS-01.AC1"]["level"], 0)

        set_status(root, [entry(status="resolved", resolution="Yes, they become read-only.",
                                evidence=["https://docs.example/teams#archive"])])
        self.assertEqual(run("check_spec.py", root).returncode, 0)
        self.assertEqual(lock(root)["F-ISS-01.AC1"]["level"], 1)

        set_status(root, [entry()])
        run("check_spec.py", root)
        set_status(root, [entry(status="accepted", decided_by="Tam, handoff 2026-11-11")])
        self.assertEqual(run("check_spec.py", root).returncode, 0)
        self.assertEqual(lock(root)["F-ISS-01.AC1"]["level"], 1)

    def test_malformed_entries_are_errors(self):
        root = spec([entry(), entry(),  # duplicate U-001
                     entry(id="U-002", status="maybe"),
                     entry(id="U-003", probe=None),
                     entry(id="U-004", criteria=["F-ISS-01.AC9"]),
                     entry(id="U-005", status="resolved", resolution="It does."),
                     entry(id="U-006", status="accepted"),
                     entry(id="U-007", status="resolved", resolution="Done.", evidence=["https://x.example"],
                           criteria=["F-ISS-01.AC8"])])
        r = run("check_spec.py", root)
        self.assertNotEqual(r.returncode, 0)
        errors = [l for l in r.stdout.splitlines() if l.startswith("ERROR")]
        for needle in ("U-001", "U-002", "U-003", "U-004", "U-005", "U-006"):
            self.assertTrue(any(needle in l for l in errors), f"{needle} not in errors:\n{r.stdout}")
        self.assertFalse(any("U-007" in l for l in errors), r.stdout)
        self.assertRegex(r.stdout, r"WARN .*U-007")

        bad = spec(None)
        (bad / "docs" / "unknowns.yaml").write_text("- id: U-001\n  question: [unclosed\n", encoding="utf-8")
        r = run("check_spec.py", bad)
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stdout + r.stderr)
        self.assertRegex(r.stdout, r"ERROR unknowns\.yaml")

    def test_open_unknown_blocks_from_handoff(self):
        before = run("check_spec.py", spec([entry()]))
        self.assertRegex(before.stdout, r"WARN .*U-001")
        self.assertFalse(any("U-001" in l for l in before.stdout.splitlines() if l.startswith("ERROR")))

        at = run("check_spec.py", spec([entry()], stage="handoff"))
        self.assertTrue(any("U-001" in l and "handoff" in l for l in at.stdout.splitlines() if l.startswith("ERROR")),
                        at.stdout)

        later = story("F-ISS-02", criteria='- [ ] **F-ISS-02.AC1** Given team ENG, when a member opens it, '
                                           'then it reads "ENG". `[docs]`')
        out = run("check_spec.py", spec([entry(criteria=["F-ISS-02.AC1"])], stage="handoff",
                                        features=(("F-ISS-01", "MVP"), ("F-ISS-02", "Later")),
                                        extra_stories={"F-ISS-02-b.md": later.replace("priority: MVP", "priority: Later")}))
        self.assertFalse(any("U-001" in l for l in out.stdout.splitlines() if l.startswith("ERROR")), out.stdout)

    def test_unknown_link_must_exist(self):
        text = story("F-ISS-01", criteria=CRITERIA).replace("## Sources", "## Open questions\n- U-007: Who may archive?\n\n## Sources")
        r = run("check_spec.py", spec([entry()], story_text=text))
        self.assertTrue(any("F-ISS-01-a.md" in l and "U-007" in l for l in r.stdout.splitlines()
                            if l.startswith("ERROR")), r.stdout)
        ok = run("check_spec.py", spec([entry()], story_text=text.replace("U-007", "U-001")))
        self.assertEqual(ok.returncode, 0, ok.stdout)

    def test_no_registry_changes_nothing(self):
        r = run("check_spec.py", spec(None))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("unknowns", r.stdout)
        self.assertNotIn("U-", r.stdout)

    def errors(self, r):
        return [l for l in r.stdout.splitlines() if l.startswith("ERROR")]

    def test_open_unknown_caps_verified_level_2_and_keeps_level_files(self):
        root = spec([])
        run("check_spec.py", root)
        sha = lock(root)["F-ISS-01.AC1"]["text_sha256"]
        verify = root / "docs" / "verify"
        verify.mkdir()
        levels = json.dumps({"criteria": {"F-ISS-01.AC1": {"text_sha256": sha, "test": "acceptance/http/F-ISS-01.AC1.yaml"}}})
        (verify / "levels.json").write_text(levels, encoding="utf-8")
        run("check_spec.py", root)
        self.assertEqual(lock(root)["F-ISS-01.AC1"]["level"], 2)
        set_status(root, [entry()])
        r = run("check_spec.py", root)
        self.assertEqual(lock(root)["F-ISS-01.AC1"]["level"], 0, r.stdout)
        self.assertRegex(r.stdout, r"WARN .*F-ISS-01\.AC1: level 2 capped to 0 by open U-001")
        self.assertEqual((verify / "levels.json").read_text(encoding="utf-8"), levels)
        set_status(root, [entry(status="accepted", decided_by="Tam, handoff 2026-11-11")])
        run("check_spec.py", root)
        self.assertEqual(lock(root)["F-ISS-01.AC1"]["level"], 2)

    def test_named_features_are_checked_against_features_md_and_scope(self):
        feats = (("F-ISS-01", "MVP"), ("F-ISS-02", "Drop"), ("F-ISS-03", "Later"))
        for stage in ("stories", "handoff"):
            root = spec([entry(criteria=[], features=["F-ISS-02"]), entry(id="U-002", criteria=[], features=["F-ISS-03"])],
                        stage=stage, features=feats)
            r = run("check_spec.py", root)
            self.assertFalse(any("U-001" in l or "U-002" in l for l in self.errors(r)), r.stdout)
        r = run("check_spec.py", spec([entry(criteria=[], features=["F-ISS-01"])], stage="handoff"))
        self.assertTrue(any("U-001" in l and "F-ISS-01" in l for l in self.errors(r)), r.stdout)
        r = run("check_spec.py", spec([entry(criteria=[], features=["F-ISS-09"])]))
        self.assertTrue(any("U-001" in l and "F-ISS-09" in l for l in self.errors(r)), r.stdout)

    def test_struck_criterion_errors_only_while_open(self):
        struck = CRITERIA.replace("- [ ] **F-ISS-01.AC2** Given", "- [ ] ~~**F-ISS-01.AC2** Given").replace(
            "`[inferred]`", "`[inferred]`~~ merged into AC1")
        text = story("F-ISS-01", criteria=struck)
        r = run("check_spec.py", spec([entry(criteria=["F-ISS-01.AC2"])], story_text=text))
        self.assertTrue(any("U-001" in l and "F-ISS-01.AC2" in l for l in self.errors(r)), r.stdout)
        r = run("check_spec.py", spec([entry(criteria=["F-ISS-01.AC2"], status="resolved", resolution="Merged.",
                                             evidence=["https://docs.example/a"])], story_text=text))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertRegex(r.stdout, r"WARN .*U-001.*F-ISS-01\.AC2")

    def test_registry_shape_errors_never_trace(self):
        cases = {"- id: [U-001]\n  question: q\n  probe: p\n  status: open\n  criteria: [F-ISS-01.AC1]\n": "id",
                 "id: U-001\n": "list",
                 "- id: U1\n  question: q\n  probe: p\n  status: open\n  criteria: [F-ISS-01.AC1]\n": "U-<nnn>",
                 "- id: U-001\n  question: q\n  probe: p\n  criteria: [F-ISS-01.AC1]\n": "status is required",
                 "- id: U-001\n  question: q\n  probe: p\n  status: open\n  criteria: [F-ISS-01.AC1]\n  owner: me\n": "owner",
                 "- just a string\n": "not a mapping",
                 "- id: U-001\n  question: q\n  probe: p\n  status: open\n": "names no criterion",
                 "- id: U-001\n  question: q\n  probe: p\n  status: open\n  criteria: F-ISS-01.AC1\n": "lists of IDs",
                 "- id: U-001\n  probe: p\n  status: open\n  criteria: [F-ISS-01.AC1]\n": "question is required"}
        for text, needle in cases.items():
            root = spec(None)
            (root / "docs" / "unknowns.yaml").write_text(text, encoding="utf-8")
            r = run("check_spec.py", root)
            self.assertNotIn("Traceback", r.stdout + r.stderr, text)
            self.assertTrue(any(l.startswith("ERROR unknowns.yaml") and needle in l for l in self.errors(r)),
                            f"{needle!r} not reported for {text!r}:\n{r.stdout}")
        root = spec(None)
        (root / "docs" / "unknowns.yaml").write_bytes(b"- id: U-001\n  question: \xff\xfe\n")
        r = run("check_spec.py", root)
        self.assertNotIn("Traceback", r.stdout + r.stderr)
        self.assertTrue(any(l.startswith("ERROR unknowns.yaml") for l in self.errors(r)), r.stdout + r.stderr)

    def test_only_open_question_lines_are_links(self):
        data = CRITERIA.replace("ENG-3", "U-123")
        r = run("check_spec.py", spec(None, story_text=story("F-ISS-01", criteria=data)))
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
