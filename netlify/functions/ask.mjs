import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { createRetriever, makeFallback } from "./rag.mjs";

const here = (f) => new URL(`./data/${f}`, import.meta.url);
const D = JSON.parse(readFileSync(here("data.json"), "utf8"));
const docs = readFileSync(here("chunks.jsonl"), "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));
const { makeAssistant } = createRequire(import.meta.url)("./data/assistant.cjs");
const assistant = makeAssistant(D, { fallback: makeFallback(createRetriever(docs, D.topics), process.env) });

const json = (code, body) => new Response(JSON.stringify(body), { status: code, headers: { "content-type": "application/json", "cache-control": "no-store" } });

export default async (req) => {
  if (req.method !== "POST") return json(405, { error: "POST only" });
  let q = "";
  try { q = String((await req.json()).q ?? "").slice(0, 300); } catch { return json(400, { error: "bad request" }); }
  if (!q.trim()) return json(400, { error: "empty question" });
  return json(200, await assistant.askAsync(q)); // queries are never logged or stored
};

export const config = { path: "/api/ask" };
