import unittest
from helpers import project, run, story

# Each row is one case; the trailing comment says what it proves.
DOMAIN = """# Domain rules

## Limits and defaults
| Rule | Value | Source |
|---|---|---|
| Quantity | 1 to 10,000, else "quantity out of range" | [code] `billing@abc1234 app/models/line_item.rb:5-10` |
| Currency | required | [code] `billing@abc1234 app/models/invoice.rb` |
| Retry | retried later per NFR-10; cap 25.00 | [code] `billing@abc1234 app/services/payment_recorder.rb:43` |
| Unit price | must be positive (F-BIL-01) | [code] `billing@abc1234 app/models/line_item.rb:11` |
| Late fee | 1.5% per 30 days, cap 25.00, ratio 1.5:1 | [code] `billing@abc1234 app/services/late_fee_calculator.rb:7, 30 days later` |
| PDF | stays pending | [code] `billing@abc1234 app/services/invoice_issuer.rb:41` — 12 more |
| Surcharge | none | [code] `billing@abc1234 app/services/invoice_issuer.rb:40, 12.5% surcharge` |
| Tax rates | SG 19%, EU 20% | [code] `billing@abc1234 config/billing.rb:5` |
| Description | a description is required | [code] `app\\models\\line_item.rb:4` |
| Outstanding | only succeeded payments count | [code] `billing@abc1234 app/models/invoice.rb:15–16` |
| Unknown region | no tax | [code] https://github.com/o/billing/blob/abc1234/config/billing.rb#L15-L17 |
| Days overdue | 0 when not yet due | [code] `billing@abc1234 app/models/invoice.rb:31-27` |
| Unit cap | cap 25,00 EUR | [code] `billing@abc1234 app/models/line_item.rb:11` |
| Give up | abandoned | [code] `billing@abc1234 app/services/payment_recorder.rb:38;3` |
"""
# Retry: G-19 found; "10" inside NFR-10 and "5" inside 25.00 are not its values. Unit price: G-26 found, "0" only
# in a feature ID. Late fee: G-03 strict (25.00 is 25); "30 days" after the comma and "1.5:1" are not citations.
# PDF: G-20 alone; the spaced dash is not a range 12-41. Surcharge: line 40 is a stray, "12.5%" no citation.
# Tax: G-02 found, 9% not read inside 19%. Backslashes, en dash, #L and a reversed range are not citations.
# Unit cap: "25,00" holds no 0 for G-26. Give up: G-25 found; the ";3" left of a citation is not its value 3.

CRITERIA = "\n".join([
    '- [ ] **F-BIL-01.AC1** Given a declined card, when the payment is attempted, then it is "failed" and the request answers 402. `[code]`',
    '- [ ] **F-BIL-01.AC2** Given an invoice with 10.00 outstanding, when 10.00 succeeds, then the invoice is "paid". `[code]`',
    '- [ ] **F-BIL-01.AC3** Given a line item of 3 at 1.005, when it is saved, then its amount is 3.02. `[code]`',
    '- [ ] **F-BIL-01.AC4** Given an issued invoice past its due date, when dunning runs, then it is "overdue". `[docs]`',
])

SOURCES = "\n".join([
    "- F-BIL-01.AC1: billing@abc1234 app/services/payment_recorder.rb:25-28",
    "- billing@abc1234 app/services/payment_recorder.rb:33",
    "- billing@abc1234 app/models/line_item.rb:2",
    "- F-BIL-01.AC3: billing@abc1234 app/models/line_item.rb:30",
    "- F-BIL-01.AC4: billing@abc1234 app/jobs/dunning_job.rb:5",
])


class RulesRecall(unittest.TestCase):
    def test_scores_a_spec_against_the_gold_rules(self):
        text = story("F-BIL-01", criteria=CRITERIA).replace("- research/iss-issues.md, Flows", SOURCES)
        root = project(modules=("BIL",), features=(("F-BIL-01", "MVP"),),
                       stories={"F-BIL-01-pay.md": text}, files={"domain.md": DOMAIN})
        r = run("rules_recall.py", root, "--model", "mid")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        first = r.stdout.splitlines()[0]
        # Found: G-04 G-18 G-11 G-19 G-26 G-03 G-20 G-02 G-25. Strict: G-04 G-18 G-03 G-20.
        self.assertIn("recall 27% (9/33)", first)
        self.assertIn("strict 12% (4/33)", first)
        self.assertIn("model mid", first)
        weak = r.stdout.split("Found, values missing")[1].split("\n\n")[0]
        self.assertRegex(weak, r"G-11 .*partially_paid")
        for rule in ("G-19", "G-26", "G-02", "G-25"):
            self.assertIn(rule, weak)
        # Off-line, file-level, [docs], dash-spread and non-token citations find nothing.
        missed = r.stdout.split("Missed")[1].split("\n\n")[0]
        for rule in ("G-01", "G-28", "G-12", "G-08", "G-09", "G-14", "G-27", "G-30", "G-16", "G-31"):
            self.assertIn(rule, missed)
        stray = r.stdout.split("matching no gold rule")[1]
        self.assertIn("(3)", stray.splitlines()[0])
        for cite in ("app/models/line_item.rb:30 ", "app/services/invoice_issuer.rb:40 "):
            self.assertIn(cite, stray)
        self.assertEqual(stray.count("app/models/line_item.rb:2 "), 1)

        for bad in (["--model=mid"], ["--model"]):
            b = run("rules_recall.py", root, *bad)
            self.assertEqual(b.returncode, 1, b.stdout)
            self.assertIn("ERROR", b.stdout)


if __name__ == "__main__":
    unittest.main()
