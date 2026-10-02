// Retrieval + grounded generation for questions the curated facts don't cover.
// Port of src/retriever.py (BM25 + topic boosting) with an LLM step and a number-grounding check.
const STOP = new Set("the a an of is are what which who how do does for to in on at and or by with this that it its be as from my me please tell".split(" "));
const tok = (s) => (s.toLowerCase().match(/[a-z0-9][a-z0-9\-/.%]*/g) || []).filter((w) => !STOP.has(w));
const MIN_SCORE = 6.0;

export const SYSTEM =
  "You answer factual questions about a mutual fund scheme using ONLY the provided context from official documents. " +
  "Reply in at most 3 short sentences. State only facts present in the context; if the context does not contain the " +
  "answer, reply exactly: NOT_FOUND. Never give advice, opinions, or return calculations. " +
  "Do not include links; the citation is added separately.";

export function createRetriever(docs, topics) {
  const tf = docs.map((d) => {
    const m = new Map();
    for (const t of tok(d.text + " " + d.title)) m.set(t, (m.get(t) || 0) + 1);
    return m;
  });
  const len = tf.map((m) => [...m.values()].reduce((a, b) => a + b, 0));
  const avg = len.reduce((a, b) => a + b, 0) / Math.max(len.length, 1);
  const df = new Map();
  for (const m of tf) for (const t of m.keys()) df.set(t, (df.get(t) || 0) + 1);
  const n = docs.length;
  const idf = (t) => Math.log(1 + (n - df.get(t) + 0.5) / (df.get(t) + 0.5));
  const topicOf = (q) => Object.keys(topics).find((k) => new RegExp(topics[k][0], "i").test(q)) || null;

  function search(query, k, scheme) {
    const q = tok(query);
    const topic = topicOf(query);
    const [, phrases, prefer] = topic ? topics[topic] : [null, [], []];
    const scored = [];
    docs.forEach((d, i) => {
      if (scheme && d.scheme !== scheme) return;
      let s = 0;
      for (const t of q) {
        const f = tf[i].get(t);
        if (f) s += (idf(t) * f * 2.2) / (f + 1.2 * (0.25 + (0.75 * len[i]) / avg));
      }
      if (s <= 0) return;
      const low = d.text.toLowerCase();
      if (phrases.some((p) => low.includes(p))) s *= 3.0;
      if (prefer.includes(d.doc_type)) s *= 1.0 + 0.15 * (prefer.length - prefer.indexOf(d.doc_type));
      if ((d.doc_type === "presentation" || d.doc_type === "leaflet") && topic) s *= 0.6;
      scored.push([s, d]);
    });
    scored.sort((a, b) => b[0] - a[0]);
    return { hits: scored.slice(0, k), topic };
  }
  return { search };
}

const numbers = (s) => (s.match(/\d[\d,]*(?:\.\d+)?/g) || []).map((x) => x.replace(/,/g, "").replace(/\.$/, ""));
const sentences = (t) => t.replace(/\s*\|\s*/g, " ").replace(/\n/g, " ").split(/(?<=[.;:!?])\s+(?=[A-Z•\-(])/).map((s) => s.trim()).filter((s) => s.split(/\s+/).length >= 4);
export const capSentences = (t, k = 3) => t.replace(/\s+/g, " ").trim().split(/(?<=[.!?])\s+(?=[A-Z])/).slice(0, k).join(" ");

// No-LLM fallback: show the best-matching line(s) of the top chunk (table rows stay readable as "label: value").
export function extractive(query, doc, topic) {
  const name = new Set([...tok(doc.scheme || ""), "fund", "hdfc", "scheme"]); // scheme words appear in every title line
  const q = new Set([...tok(query), ...tok(topic || "")].filter((w) => !name.has(w)));
  const lines = doc.text.split("\n").map((l) => l.replace(/\s*\|\s*/g, ": ").replace(/^:\s*/, "").trim()).filter((l) => l.split(/\s+/).length >= 2);
  if (!lines.length) return doc.text.slice(0, 300);
  const score = (l) => new Set(tok(l).filter((w) => q.has(w))).size;
  let best = 0;
  lines.forEach((l, i) => { if (score(l) > score(lines[best])) best = i; });
  const pick = lines[best].split(/\s+/).length < 14 ? lines.slice(best, best + 2) : [lines[best]];
  const out = pick.join(" ").slice(0, 300);
  return /[.!?]$/.test(out) ? out : out + ".";
}

// Every number in the answer must appear in the chunk we cite; choose the first supporting chunk.
export function ground(answer, chunks) {
  const nums = numbers(answer);
  return chunks.find((c) => { const have = new Set(numbers(c.text)); return nums.every((x) => have.has(x)); }) || null;
}

export async function callLLM(query, chunks, { apiKey, model, fetchImpl = fetch }) {
  const ctx = chunks.map((d) => `[${d.title} p.${d.page}]\n${d.text}`).join("\n\n");
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 15000);
  try {
    const r = await fetchImpl("https://api.anthropic.com/v1/messages", {
      method: "POST", signal: ctl.signal,
      headers: { "x-api-key": apiKey, "anthropic-version": "2023-06-01", "content-type": "application/json" },
      body: JSON.stringify({ model, max_tokens: 200, system: SYSTEM, messages: [{ role: "user", content: `Context:\n${ctx}\n\nQuestion: ${query}` }] }),
    });
    if (!r.ok) return null;
    return (await r.json()).content?.[0]?.text?.trim() || null;
  } catch { return null; } finally { clearTimeout(timer); }
}

// Returns a formatted response, or null so the caller answers "couldn't find that".
export function makeFallback(retriever, env = {}, fetchImpl = fetch) {
  return async (query, scheme, fmt) => {
    const { hits, topic } = retriever.search(query + " " + scheme, 4, scheme);
    if (!hits.length || hits[0][0] < MIN_SCORE) return null;
    const chunks = hits.map((h) => h[1]);
    let text = null, path = "retrieved";
    if (env.ANTHROPIC_API_KEY) {
      const out = await callLLM(query, chunks, { apiKey: env.ANTHROPIC_API_KEY, model: env.RAG_MODEL || "claude-haiku-4-5-20251001", fetchImpl });
      if (out && !/NOT_FOUND/.test(out)) { text = capSentences(out); path = "retrieved+llm"; }
      else if (out) return null; // model says the context lacks the answer
    }
    if (!text) text = extractive(query, chunks[0], topic);
    const cite = ground(text, chunks);
    if (!cite) return null; // answer contains a number unsupported by any retrieved chunk
    return { ...fmt(text, cite, null, "answer"), path };
  };
}
