import unittest
from helpers import project, run, story

FEATS = (("F-ISS-01", "MVP"), ("F-ISS-02", "Later"))


class Scorecard(unittest.TestCase):
    def test_two_runs_with_the_same_mvp_agree(self):
        tagged = {"F-ISS-01-a.md": story("F-ISS-01", criteria="- [ ] Given ENG-1, when I create one, then it is ENG-2. `[docs]`")}
        a, b = project(features=FEATS, stories=tagged), project(features=FEATS, stories=tagged)
        r = run("scorecard.py", a, str(b))
        self.assertIn("MVP overlap 100%", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_run_mostly_inferred_misses_its_target(self):
        guessed = story("F-ISS-01", edge="- Limit [inferred], order [inferred], size [docs].")
        r = run("scorecard.py", project(stories={"F-ISS-01-a.md": guessed}))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("inferred share 67%", r.stdout)


if __name__ == "__main__":
    unittest.main()
