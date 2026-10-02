"""Small-corpus BM25 retriever with topic-aware boosting (stdlib only)."""
import json, math, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOP = set("the a an of is are what which who how do does for to in on at and or by with this that it its be as from my me please tell".split())
SYN = {"sip": ["systematic", "sip"], "ter": ["total", "expense", "ratio"], "benchmark": ["benchmark", "index"],
       "riskometer": ["riskometer", "risk"], "statement": ["statement", "account", "cas"], "lockin": ["lock-in", "lock", "elss"]}
# topic -> (query trigger regex, phrases that mark relevant chunks, preferred doc types)
TOPICS = {
    "expense ratio": (r"expense|\bter\b|charges|fees?", ["maximum total expense ratio", "recurring expenses (% p.a."], ["kim", "sid"]),
    "exit load": (r"exit\s*load", ["exit load"], ["factsheet", "kim"]),
    "minimum sip": (r"\bsip\b|minimum|min\.?\s|systematic", ["minimum application", "minimum additional"], ["kim", "sid"]),
    "lock-in": (r"lock[- ]?in|elss|80c", ["lock-in", "lock in"], ["sid", "kim"]),
    "riskometer": (r"risk(o)?meter|risk level|how risky", ["riskometer"], ["factsheet", "kim"]),
    "benchmark": (r"benchmark|index", ["benchmark"], ["factsheet", "kim"]),
    "statement": (r"statement|cas\b|capital[- ]gains?|download|tax", ["account statement", "consolidated account statement", "capital gain"], ["kim", "sid"]),
}


def tok(s):
    return [w for w in re.findall(r"[a-z0-9][a-z0-9\-/.%]*", s.lower()) if w not in STOP]


class Retriever:
    def __init__(self, path=None):
        path = path or ROOT / "data" / "processed" / "chunks.jsonl"
        self.docs = [json.loads(l) for l in open(path)]
        self.tf = [Counter(tok(d["text"] + " " + d["title"])) for d in self.docs]
        self.len = [sum(c.values()) for c in self.tf]
        self.avg = sum(self.len) / max(len(self.len), 1)
        df = Counter(t for c in self.tf for t in c)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + .5) / (f + .5)) for t, f in df.items()}

    @staticmethod
    def topic(query):
        for name, (rx, _, _) in TOPICS.items():
            if re.search(rx, query, re.I):
                return name
        return None

    def search(self, query, k=4):
        q = tok(query)
        topic = self.topic(query)
        phrases, prefer = (TOPICS[topic][1], TOPICS[topic][2]) if topic else ([], [])
        scored = []
        for i, d in enumerate(self.docs):
            tf, L = self.tf[i], self.len[i]
            s = sum(self.idf.get(t, 0) * tf[t] * 2.2 / (tf[t] + 1.2 * (.25 + .75 * L / self.avg)) for t in q if t in tf)
            if s <= 0:
                continue
            low = d["text"].lower()
            if any(p in low for p in phrases):
                s *= 3.0
            if d["doc_type"] in prefer:
                s *= 1.0 + .15 * (len(prefer) - prefer.index(d["doc_type"]))
            if d["doc_type"] in ("presentation", "leaflet") and topic:
                s *= .6
            scored.append((s, d))
        scored.sort(key=lambda x: -x[0])
        return [(s, d) for s, d in scored[:k]], topic
