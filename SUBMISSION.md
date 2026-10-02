# Submission checklist
| Deliverable | Where | Status |
|---|---|---|
| Working prototype | Static build in `web/` (Netlify: `netlify.toml`); also `python3 src/server.py` locally | Runs locally; **hosting link still to be created** (or record DEMO.md as a <=3 min video) |
| Source list | `sources.csv` | 8 documents (target 15-25); **URLs unverified** (`url_verified=no`) |
| README | `README.md` | Done: setup, scope, known limits |
| Sample Q&A | `eval/sample_qa.md` | 11 queries incl. refusals |
| Disclaimer snippet | `DISCLAIMER.md` (UI shows "Facts-only. No investment advice.") | Done |

## Open items before submitting
1. Replace guessed hdfcfund.com URLs in `sources.csv` with the exact document links; set `url_verified=yes`.
2. Add more sources (HDFC TER/charges/FAQ/statement pages, SEBI riskometer circular, AMFI investor pages) to reach 15-25.
3. Verify the SEBI/AMFI educational links used in refusals (`src/guardrails.py`).
4. Deploy and paste the link here.
