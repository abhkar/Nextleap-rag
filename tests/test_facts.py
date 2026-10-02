"""Every curated fact must be backed by verbatim quotes in the cited source PDF page."""
import csv, json, re, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from ingest import pdf_pages
from guardrails import route
from answer import Assistant

norm = lambda s: re.sub(r"\s+", " ", re.sub(r"\s*\|\s*", " ", s)).strip()
SRC = {r["id"]: r for r in csv.DictReader(open(ROOT / "sources.csv"))}


class FactQuotes(unittest.TestCase):
    def test_quotes_present_in_source_pages(self):
        cache = {}
        for f in json.loads((ROOT / "data" / "facts.json").read_text()):
            path = ROOT / SRC[f["source_id"]]["local_file"]
            pages = cache.setdefault(path, [norm(p) for p in pdf_pages(path)])
            page = pages[f["page"] - 1]
            for q in f["quotes"]:
                self.assertIn(norm(q), page, f"{f['id']}: quote not on p.{f['page']}: {q}")


class RetrievalQuality(unittest.TestCase):
    def test_hit_rate_gate(self):
        sys.path.insert(0, str(ROOT / "eval"))
        from retrieval_eval import run, MIN_HIT_RATE
        rate, misses = run(3)
        self.assertGreaterEqual(rate, MIN_HIT_RATE, misses)


class Behaviour(unittest.TestCase):
    a = Assistant()

    def test_routes(self):
        self.assertEqual(route("Should I buy HDFC Flexi Cap?")[0], "advice")
        self.assertEqual(route("my pan ABCDE1234F")[0], "pii")
        self.assertEqual(route("call me on 9876543210")[0], "pii")
        self.assertEqual(route("mail me a@b.com")[0], "pii")
        self.assertEqual(route("3 year returns?")[0], "performance")
        self.assertEqual(route("What is the exit load?")[0], "factual")

    def test_scheme_specific_answers(self):
        a = self.a
        self.assertIn("NIFTY 500", a.ask("benchmark of HDFC Flexi Cap Fund")["answer"])
        self.assertIn("NIFTY MIDCAP 150", a.ask("benchmark of HDFC Mid Cap Fund")["answer"])
        self.assertIn("May 31, 2026", a.ask("riskometer of mid cap fund")["answer"])
        self.assertIn("statutory lock-in of 3 years", a.ask("What is the lock-in for ELSS?")["answer"])
        self.assertIn("Nil", a.ask("exit load of HDFC ELSS Tax Saver")["answer"])
        self.assertIn("Rs.500", a.ask("minimum investment in tax saver fund")["answer"])
        self.assertIn("HDFC Flexi Cap Fund is categorised", a.ask("Is HDFC Flexi Cap Fund an ELSS with lock-in?")["answer"])
        self.assertIn("0.0070%", a.ask("exit load of HDFC Liquid Fund")["answer"])
        self.assertIn("CRISIL Liquid Debt A-I", a.ask("benchmark of liquid fund")["answer"])
        self.assertIn("low to moderate", a.ask("riskometer of liquid fund")["answer"])
        self.assertIn("0.80%", a.ask("expense ratio of liquid fund")["answer"])
        self.assertEqual(a.ask("what is the exit load?")["kind"], "clarify")
        self.assertEqual(a.ask("compare exit load of flexi cap and mid cap")["kind"], "clarify")
        self.assertEqual(a.ask("benchmark returns of mid cap fund")["kind"], "refusal")

    def test_every_answer_has_one_link(self):
        for q in ["Exit load of flexi cap?", "Expense ratio of mid cap?", "Should I sell?", "3 year return of mid cap?", "random unknown thing xyz", "unknown xyz mid cap fund"]:
            ans = self.a.ask(q)["answer"]
            self.assertEqual(len(re.findall(r"https?://", ans)), 1, q)

    def test_answer_sentence_limit(self):
        for q in ["exit load", "minimum sip", "expense ratio", "benchmark", "riskometer", "lock-in", "statement", "category"]:
          for sc in ("flexi cap fund", "mid cap fund", "elss tax saver fund", "liquid fund"):
            body = self.a.ask(f"{q} of {sc}")["answer"].split("\n\nSource:")[0]
            self.assertLessEqual(len(re.findall(r"[.!?](?:\s+[A-Z'(]|$)", body)), 3, q)


if __name__ == "__main__":
    unittest.main()
