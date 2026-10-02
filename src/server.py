"""Tiny dependency-free web UI: python3 src/server.py  ->  http://localhost:8000"""
import html, json, os, re, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from answer import Assistant, DISCLAIMER, SCHEME

EXAMPLES = ["What is the exit load of HDFC Flexi Cap Fund?", "What is the benchmark of HDFC Mid Cap Fund?", "What is the riskometer level of HDFC Mid Cap Fund?"]
PAGE = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MF FAQ Assistant</title><style>
:root{--bg:#fff;--fg:#1b1f24;--mute:#59636e;--card:#f4f6f8;--acc:#0b5cab;--bd:#d8dee4}
@media(prefers-color-scheme:dark){:root{--bg:#0f1318;--fg:#e6edf3;--mute:#9aa4af;--card:#1a2028;--acc:#6cb2ff;--bd:#2d333b}}
body{background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;margin:0}main{max-width:720px;margin:0 auto;padding:24px 16px}
h1{font-size:1.4rem;margin:0 0 4px}.mute{color:var(--mute);font-size:.9rem}.chips button{margin:6px 6px 0 0;padding:6px 12px;border:1px solid var(--bd);
border-radius:16px;background:var(--card);color:var(--fg);cursor:pointer}#log{margin:20px 0}.q{font-weight:600;margin-top:16px}
.a{background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:10px 14px;white-space:pre-wrap;word-break:break-word}a{color:var(--acc)}
form{display:flex;gap:8px}input{flex:1;padding:10px;border:1px solid var(--bd);border-radius:8px;background:var(--bg);color:var(--fg)}
form button{padding:10px 16px;border:0;border-radius:8px;background:var(--acc);color:var(--bg);cursor:pointer}.note{margin-top:16px;font-weight:600}</style>
<main><h1>Mutual Fund FAQ Assistant</h1>
<p>Hi! Ask me factual questions about <b>%(scheme)s</b> (name the scheme in your question), answered only from official HDFC Mutual Fund documents.</p>
<div class="chips">%(chips)s</div><div id="log"></div>
<form id="f"><input id="q" maxlength="300" placeholder="Ask a factual question..." autocomplete="off"><button>Ask</button></form>
<p class="note">%(disc)s</p><p class="mute">Please don't enter PAN, Aadhaar, account numbers, OTPs, emails or phone numbers.</p></main>
<script>
const log=document.getElementById('log'),q=document.getElementById('q');
function linkify(t){return t.replace(/(https?:\\/\\/[^\\s]+)/g,'<a href="$1" target="_blank" rel="noopener">$1</a>')}
async function ask(text){if(!text.trim())return;const d=document.createElement('div');
d.innerHTML='<div class="q"></div><div class="a">...</div>';d.firstChild.textContent=text;log.appendChild(d);q.value='';
const r=await fetch('/ask',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({q:text})});
const j=await r.json();const esc=j.answer.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));d.lastChild.innerHTML=linkify(esc)}
document.getElementById('f').onsubmit=e=>{e.preventDefault();ask(q.value)};
document.querySelectorAll('.chips button').forEach(b=>b.onclick=()=>ask(b.textContent));
</script></html>"""

assistant = Assistant()


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code); self.send_header("content-type", ctype); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        chips = "".join(f"<button type='button'>{html.escape(e)}</button>" for e in EXAMPLES)
        self._send(200, (PAGE % {"scheme": SCHEME, "chips": chips, "disc": DISCLAIMER}).encode(), "text/html; charset=utf-8")

    def do_POST(self):
        n = min(int(self.headers.get("content-length", 0)), 2000)
        q = json.loads(self.rfile.read(n) or b"{}").get("q", "")[:300]
        self._send(200, json.dumps(assistant.ask(q)).encode(), "application/json")  # queries are never logged or stored

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", 8000))
    print(f"Serving on http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
