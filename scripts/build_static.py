"""Generate web/data.json (facts + routing rules + source metadata) for the static Netlify build."""
import csv, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import guardrails as g
import retriever as rt
from answer import SCHEMES, WEAK, AMC_LINK, DISCLAIMER

src = {r["id"]: r for r in csv.DictReader(open(ROOT / "sources.csv"))}
facts = []
for f in json.loads((ROOT / "data" / "facts.json").read_text()):
    s = src[f["source_id"]]
    facts.append({"scheme": f["scheme"], "pattern": f["pattern"], "answer": f["answer"], "title": s["title"],
                  "page": f["page"], "url": s["url"], "as_of": s["as_of"]})
perf = {}
for r in src.values():
    if r["doc_type"] in ("factsheet", "leaflet"):
        perf.setdefault(r["scheme"], r)
data = {"disclaimer": DISCLAIMER, "schemes": SCHEMES, "weak": WEAK, "amc_link": AMC_LINK, "edu_link": g.EDU_LINK, "amfi_link": g.AMFI_LINK,
        "pii": {k: rx.pattern for k, rx in g.PII.items()}, "advice": g.ADVICE.pattern, "performance": g.PERFORMANCE.pattern,
        "perf_docs": {k: {"title": v["title"], "url": v["url"], "as_of": v["as_of"]} for k, v in perf.items()},
        "topics": {k: [v[0], v[1], v[2]] for k, v in rt.TOPICS.items()}, "sources": [{k: r[k] for k in ("title", "doc_type", "scheme", "as_of", "url")} for r in src.values()], "facts": facts}
(ROOT / "web" / "data.json").write_text(json.dumps(data, indent=1))
print(f"web/data.json: {len(facts)} facts")

# files bundled into the Netlify Function
import shutil
fn = ROOT / "netlify" / "functions"
(fn / "data").mkdir(parents=True, exist_ok=True)
shutil.copy(ROOT / "web" / "data.json", fn / "data" / "data.json")
shutil.copy(ROOT / "data" / "processed" / "chunks.jsonl", fn / "data" / "chunks.jsonl")
shutil.copy(ROOT / "web" / "assistant.js", fn / "data" / "assistant.cjs")
print("copied function data")
