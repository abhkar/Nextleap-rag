# MF FAQ Assistant (RAG, facts-only)

A small, citation-first FAQ assistant for **HDFC Flexi Cap Fund** (HDFC Mutual Fund). Product context: Groww (answers use only AMC documents, never Groww pages).
It answers factual questions (exit load, minimum investment, expense ratio, benchmark, riskometer, statements) in <=3 sentences with **one source link** and a *"Last updated from sources"* date. It refuses advice/opinion questions, performance/returns questions, and anything containing PII.

## Scope
- AMC: HDFC Mutual Fund. Scheme: **HDFC Flexi Cap Fund only** (the milestone allows 3-5; this build is deliberately narrowed to one).
- Corpus: 5 official documents listed in [`sources.csv`](sources.csv) (factsheet Sep 2026, KIM and SID dated 21 Nov 2025, leaflet May 2026, presentation Jul 2026). **Below the 15-25 source target; see Known limits.**

## How it works
1. `src/ingest.py` - `pdftotext` -> ~90-word page-aware chunks -> `data/processed/chunks.jsonl`.
2. `src/guardrails.py` - routes each query: **pii** / **advice** / **performance** / **factual**.
3. `data/facts.json` - curated facts, each pinned to a source page. `tests/test_facts.py` verifies that every fact's quotes appear verbatim in that page of the PDF.
4. `src/retriever.py` - stdlib BM25 with topic boosting over chunks (fallback when no curated fact matches). Below a score threshold -> "couldn't find it".
5. `src/answer.py` - builds the reply; the citation is attached in code from chunk metadata (never LLM-generated). If `ANTHROPIC_API_KEY` is set, fallback answers are phrased by Claude from retrieved context only; otherwise extractive.
6. `src/server.py` - tiny web UI (welcome line, 3 example questions, disclaimer). Queries are not logged or stored.

## Setup
Requires Python 3.9+ and `pdftotext` (poppler-utils). No pip packages.
```
python3 src/ingest.py          # rebuild chunks from sources.csv
python3 -m unittest discover -s tests
python3 src/server.py          # http://localhost:8000
python3 src/answer.py "What is the exit load?"   # CLI
python3 eval/run_samples.py    # regenerate eval/sample_qa.md
```

## Known limits
- **Citation URLs are not yet verified.** Documents were supplied as PDFs; `sources.csv` points to the scheme page on hdfcfund.com (`url_verified=no`). Replace with the exact document download links before submission.
- Only 5 documents / 1 scheme; no SEBI/AMFI pages ingested (the build environment could not reach those hosts). The advice-refusal link points to SEBI investor education and is likewise unverified.
- Riskometer is an image in the factsheet; its value was transcribed by hand (`data/manual_chunks.json`) and stated as of 31 Aug 2026.
- No separate minimum-SIP amount or capital-gains-statement download steps appear in these documents; the assistant says so rather than guessing. ELSS lock-in is out of scope (no ELSS scheme in corpus).
- Figures (TER, exit load, riskometer) change; answers show the document date.
- Rule-based routing can misclassify unusual phrasing.
