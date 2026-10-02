"""The static (JS) assistant must give the same kind/answer as the Python one for curated questions."""
import json, subprocess, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from answer import Assistant

QS = ["What is the exit load of HDFC Flexi Cap Fund?", "minimum sip for mid cap fund", "expense ratio of HDFC Mid Cap Fund",
      "benchmark of flexi cap fund", "riskometer of mid cap", "lock-in for flexi cap", "statement for mid cap fund",
      "Should I buy HDFC Mid Cap Fund now?", "3 year returns of flexi cap", "my PAN ABCDE1234F exit load", "what is the exit load?",
      "compare flexi cap and mid cap exit load", "ELSS lock-in period?", "exit load of tax saver", "is flexi cap an ELSS?", "tax saver minimum sip"]
JS = """const {makeAssistant}=require('./web/assistant.js');const D=require('./web/data.json');
const a=makeAssistant(D);console.log(JSON.stringify(JSON.parse(process.argv[1]).map(q=>a.ask(q))));"""


class Parity(unittest.TestCase):
    def test_same_as_python(self):
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_static.py")], check=True, capture_output=True)
        out = json.loads(subprocess.run(["node", "-e", JS, json.dumps(QS)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        py = Assistant()
        for q, js in zip(QS, out):
            p = py.ask(q)
            self.assertEqual((p["kind"], p["answer"]), (js["kind"], js["answer"]), q)


if __name__ == "__main__":
    unittest.main()
