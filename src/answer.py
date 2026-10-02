"""Facts-only answer pipeline: route -> retrieve -> answer (<=3 sentences, one citation, last-updated)."""
import json, os, re, sys, urllib.request
from guardrails import route, EDU_LINK, AMFI_LINK
from retriever import Retriever, tok, ROOT

SCHEME = "HDFC Flexi Cap Fund"
MIN_SCORE = 6.0
DISCLAIMER = "Facts-only. No investment advice."

SYSTEM = (
    "You answer factual questions about a mutual fund scheme using ONLY the provided context from official documents. "
    "Reply in at most 3 short sentences. State only facts present in the context; if the context does not contain the "
    "answer, say you could not find it in the official documents. Never give advice, opinions, or return calculations. "
    "Do not include links; the citation is added separately."
)


def _fmt(answer, doc=None, link=None, kind="answer"):
    link = link or (doc and doc["url"])
    as_of = doc["as_of"] if doc else None
    text = answer.strip()
    if doc:
        text += f"\n\nSource: {doc['title']} (p.{doc['page']}) - {link}\nLast updated from sources: {as_of}"
    else:
        text += f"\n\nLearn more: {link}"
    return {"kind": kind, "answer": text, "link": link, "last_updated": as_of}


def _sentences(text):
    flat = re.sub(r"\s*\|\s*", " ", text.replace("\n", " "))
    return [s.strip() for s in re.split(r"(?<=[.;:])\s+(?=[A-Z•\-\(])", flat) if len(s.split()) >= 4]


def extractive(query, doc, topic):
    q = set(tok(query)) | set(tok(topic or ""))
    sents = _sentences(doc["text"])
    if not sents:
        return doc["text"][:300]
    scored = sorted(range(len(sents)), key=lambda i: -len(q & set(tok(sents[i]))))
    best = scored[0]
    pick = sents[best:best + 2] if len(sents[best].split()) < 25 else sents[best:best + 1]
    return " ".join(pick)[:420]


def llm_answer(query, docs):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    ctx = "\n\n".join(f"[{d['title']} p.{d['page']}]\n{d['text']}" for d in docs)
    body = {"model": os.environ.get("RAG_MODEL", "claude-haiku-4-5-20251001"), "max_tokens": 200, "system": SYSTEM,
            "messages": [{"role": "user", "content": f"Context:\n{ctx}\n\nQuestion: {query}"}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", json.dumps(body).encode(),
                                 {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)["content"][0]["text"]
    except Exception:
        return None


FACTS = json.loads((ROOT / "data" / "facts.json").read_text())


class Assistant:
    def __init__(self):
        self.ret = Retriever()
        self.meta = {}
        for d in self.ret.docs:
            self.meta.setdefault(d["source_id"], d)

    def fact_answer(self, query):
        """Curated, quote-verified facts (see tests/test_facts.py) take priority over free-form retrieval."""
        for f in FACTS:
            if re.search(f["pattern"], query, re.I):
                doc = dict(self.meta[f["source_id"]], page=f["page"])
                return _fmt(f["answer"], doc=doc)

    def ask(self, query):
        query = query.strip()
        r, detail = route(query)
        if r == "pii":
            return _fmt("Please don't share personal or account details such as " + ", ".join(detail) +
                        ". I can't accept or store them. Ask a general question about the scheme instead.", link=AMFI_LINK, kind="refusal")
        if r == "advice":
            return _fmt("I can only share facts from official documents, so I can't advise on whether to buy, sell or hold, "
                        "or which fund is better. For investing basics, see the investor education resources below.", link=EDU_LINK, kind="refusal")
        fact = self.fact_answer(query)
        if fact:
            return fact
        hits, topic = self.ret.search(query + " " + SCHEME, k=3)
        top = hits[0][1] if hits else None
        if r == "performance":
            doc = next((d for _, d in self.ret.search("factsheet performance", 5)[0] if d["doc_type"] == "factsheet"), top)
            return _fmt("I don't calculate or compare returns. Please see the scheme's official factsheet for performance data.",
                        doc=doc, kind="refusal")
        if not hits or hits[0][0] < MIN_SCORE:
            return _fmt("I couldn't find that in the official documents I have for HDFC Flexi Cap Fund.",
                        link="https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund/regular", kind="no_answer")
        text = llm_answer(query, [d for _, d in hits]) or extractive(query, top, topic)
        return _fmt(text, doc=top)


if __name__ == "__main__":
    a = Assistant()
    for q in sys.argv[1:] or ["What is the exit load?"]:
        print(f"Q: {q}\n{a.ask(q)['answer']}\n")
