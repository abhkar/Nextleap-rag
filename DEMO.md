# Demo script (<= 3 min)
Run `python3 src/server.py`, open http://localhost:8000.
1. Show the welcome line, the 3 example questions and the "Facts-only. No investment advice." note.
2. Ask "What is the exit load of HDFC Flexi Cap Fund?" -> 1.00% within 1 year, one source link, last-updated date.
3. Ask "What is the benchmark of HDFC Mid Cap Fund?" and "What is the riskometer level of HDFC Mid Cap Fund?".
4. Ask "What is the exit load?" (no scheme) -> assistant asks which scheme.
5. Ask "Should I buy HDFC Mid Cap Fund now?" -> polite refusal + educational link.
6. Ask "What were the 3-year returns of HDFC Flexi Cap Fund?" -> refuses to compute, links the official document.
7. Ask "My PAN is ABCDE1234F, what is the exit load?" -> PII refusal; nothing is stored.
8. Mention: answers <= 3 sentences, citations attached from document metadata, tests verify every curated fact against the source PDF page.
