// Run: node --test tests/test_rag_function.mjs
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { createRetriever, makeFallback, ground, capSentences } from "../netlify/functions/rag.mjs";

const D = JSON.parse(readFileSync("web/data.json", "utf8"));
const docs = readFileSync("data/processed/chunks.jsonl", "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));
const { makeAssistant } = createRequire(import.meta.url)("../web/assistant.js");
const retriever = createRetriever(docs, D.topics);
const build = (env, fetchImpl) => makeAssistant(D, { fallback: makeFallback(retriever, env, fetchImpl) });
const llm = (text) => async () => ({ ok: true, json: async () => ({ content: [{ text }] }) });
const links = (a) => (a.answer.match(/https?:\/\//g) || []).length;

test("curated questions skip retrieval", async () => {
  const r = await build({}).askAsync("exit load of flexi cap fund");
  assert.equal(r.path, "curated");
});
test("uncovered question is retrieved with one citation, no LLM key", async () => {
  const r = await build({}).askAsync("What is the stamp duty on HDFC Flexi Cap Fund purchases?");
  assert.ok(["answer", "no_answer"].includes(r.kind));
  assert.equal(links(r), 1);
});
test("LLM answer is grounded: unsupported number is rejected", async () => {
  const bad = await build({ ANTHROPIC_API_KEY: "k" }, llm("The fund charges a stamp duty of 7.77%.")).askAsync("What is the stamp duty on flexi cap fund?");
  assert.equal(bad.kind, "no_answer");
});
test("LLM answer with supported numbers is cited and capped at 3 sentences", async () => {
  const r = await build({ ANTHROPIC_API_KEY: "k" }, llm("A. One. B. Two. C. Three. D. Four.")).askAsync("What is the stamp duty on flexi cap fund?");
  assert.ok(!/Four/.test(r.answer));
  assert.equal(links(r), 1);
});
test("NOT_FOUND from the model becomes no_answer", async () => {
  const r = await build({ ANTHROPIC_API_KEY: "k" }, llm("NOT_FOUND")).askAsync("What is the stamp duty on flexi cap fund?");
  assert.equal(r.kind, "no_answer");
});
test("LLM failure falls back to extractive, not an error", async () => {
  const r = await build({ ANTHROPIC_API_KEY: "k" }, async () => { throw new Error("down"); }).askAsync("What is the stamp duty on flexi cap fund?");
  assert.equal(links(r), 1);
});
test("refusals still happen before retrieval", async () => {
  const a = build({ ANTHROPIC_API_KEY: "k" }, async () => { throw new Error("must not call LLM"); });
  assert.equal((await a.askAsync("Should I buy flexi cap fund?")).kind, "refusal");
  assert.equal((await a.askAsync("my PAN ABCDE1234F flexi cap")).kind, "refusal");
  assert.equal((await a.askAsync("3 year returns of flexi cap")).kind, "refusal");
});
test("helpers", () => {
  assert.equal(capSentences("A b c. D e f. G h i. J k l."), "A b c. D e f. G h i.");
  assert.equal(ground("is 99.99", [{ text: "no such" }]), null);
});
