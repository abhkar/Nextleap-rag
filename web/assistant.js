// Browser/Node port of src/answer.py's routing + curated-fact answers. Nothing is sent to a server or stored.
(function (root) {
  function makeAssistant(D) {
    const rx = (p) => new RegExp(p, "i");
    const fmt = (text, doc, link, kind) => {
      link = link || (doc && doc.url);
      const out = doc
        ? `${text}\n\nSource: ${doc.title}${doc.page ? ` (p.${doc.page})` : ""} - ${link}\nLast updated from sources: ${doc.as_of}`
        : `${text}\n\nLearn more: ${link}`;
      return { kind, answer: out, link };
    };
    function ask(query) {
      query = query.trim();
      const pii = Object.keys(D.pii).filter((k) => rx(D.pii[k]).test(query));
      if (pii.length)
        return fmt(`Please don't share personal or account details such as ${pii.join(", ")}. I can't accept or store them. Ask a general question about the scheme instead.`, null, D.amfi_link, "refusal");
      if (rx(D.advice).test(query))
        return fmt("I can only share facts from official documents, so I can't advise on whether to buy, sell or hold, or which fund is better. For investing basics, see the investor education resources below.", null, D.edu_link, "refusal");
      let found = Object.keys(D.schemes).filter((n) => rx(D.schemes[n]).test(query));
      if (!found.length) found = Object.keys(D.weak).filter((n) => rx(D.weak[n]).test(query));
      if (found.length !== 1) {
        const msg = found.length ? "Please ask about one scheme at a time, and I will answer from its official documents." : `Which scheme do you mean: ${Object.keys(D.schemes).join(" or ")}?`;
        return fmt(msg + " I can answer one scheme per question.", null, D.amc_link, "clarify");
      }
      const scheme = found[0];
      if (rx(D.performance).test(query)) {
        const doc = D.perf_docs[scheme];
        return fmt("I don't calculate or compare returns. Please see the scheme's official factsheet or leaflet for performance data.", doc, doc ? null : D.amc_link, "refusal");
      }
      const fact = D.facts.find((f) => f.scheme === scheme && rx(f.pattern).test(query));
      if (fact) return fmt(fact.answer, fact, null, "answer");
      return fmt(`I couldn't find that in the official documents I have for ${scheme}.`, null, D.amc_link, "no_answer");
    }
    return { ask };
  }
  if (typeof module !== "undefined") module.exports = { makeAssistant };
  else root.makeAssistant = makeAssistant;
})(this);
