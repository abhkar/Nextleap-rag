"""Build data/processed/chunks.jsonl from the PDFs listed in sources.csv (needs `pdftotext`)."""
import csv, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNK_WORDS, OVERLAP = 90, 20


def pdf_pages(path):
    out = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=True).stdout
    return out.split("\f")


def clean(line):
    line = re.sub(r"\s{3,}", " | ", line.strip())
    return re.sub(r"\s+", " ", line)


def chunk_page(lines):
    """Yield word-windowed chunks over a page's non-empty lines (keeps table rows together)."""
    buf, n = [], 0
    for ln in lines:
        w = len(ln.split())
        if buf and n + w > CHUNK_WORDS:
            yield "\n".join(buf)
            keep, kn = [], 0
            for prev in reversed(buf):
                kn += len(prev.split())
                if kn > OVERLAP:
                    break
                keep.insert(0, prev)
            buf, n = keep, sum(len(x.split()) for x in keep)
        buf.append(ln)
        n += w
    if buf:
        yield "\n".join(buf)


def main():
    rows = list(csv.DictReader(open(ROOT / "sources.csv")))
    out = ROOT / "data" / "processed" / "chunks.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(out, "w") as f:
        for r in rows:
            for pno, page in enumerate(pdf_pages(ROOT / r["local_file"]), 1):
                lines = [c for c in (clean(l) for l in page.splitlines()) if c]
                for text in chunk_page(lines):
                    if len(text.split()) < 8:
                        continue
                    f.write(json.dumps({"id": f"{r['id']}-p{pno}-{count}", "source_id": r["id"], "title": r["title"],
                                        "doc_type": r["doc_type"], "scheme": r["scheme"], "as_of": r["as_of"],
                                        "page": pno, "url": r["url"], "text": text}) + "\n")
                    count += 1
        # chunks transcribed by hand from image-only content (e.g. riskometer graphic)
        meta = {r["id"]: r for r in rows}
        manual = ROOT / "data" / "manual_chunks.json"
        for m in json.loads(manual.read_text()) if manual.exists() else []:
            r = meta[m["source_id"]]
            f.write(json.dumps({"id": f"{r['id']}-manual-{count}", "source_id": r["id"], "title": r["title"],
                                "doc_type": r["doc_type"], "scheme": r["scheme"], "as_of": r["as_of"],
                                "page": m["page"], "url": r["url"], "text": m["text"]}) + "\n")
            count += 1
    print(f"wrote {count} chunks from {len(rows)} sources -> {out}")


if __name__ == "__main__":
    sys.exit(main())
