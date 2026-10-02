"""Retrieval hit-rate: is the expected text inside the top-k retrieved chunks (scheme-filtered)?
Run: python3 eval/retrieval_eval.py [k]   (exit code 1 if hit rate < MIN_HIT_RATE)"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from retriever import Retriever

MIN_HIT_RATE = 0.8
def run(k=3):
    r = Retriever()
    rows = json.loads((ROOT / "eval" / "retrieval_eval.json").read_text())
    misses, hits = [], 0
    for c in rows:
        top = [d for _, d in r.search(c["q"] + " " + c["scheme"], k=k, scheme=c["scheme"])[0]]
        ok = any(c["expect"].lower() in d["text"].lower() for d in top)
        hits += ok
        if not ok:
            misses.append(c)
    return hits / len(rows), misses

if __name__ == "__main__":
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    rate, misses = run(k)
    print(f"hit@{k}: {rate:.0%}")
    for m in misses:
        print("MISS:", m["scheme"], "|", m["q"], "->", m["expect"])
    sys.exit(0 if rate >= MIN_HIT_RATE else 1)
