import { evaluateMapping } from "../core/actions.js";
import { clear, copyText, html } from "../core/dom.js";
import { submissionLine } from "../core/mapping.js";
import { store } from "../core/store.js";

const MAX_RUNS = 50;

export function mountEvaluationPanel(root) {
  const head = html("div", { class: "card-head" }, root);
  html("h2", {}, head, "Fitness");
  html("span", { class: "hint" }, head, "source.py · depth after routing");

  const controls = html("div", { class: "row" }, root);
  html("label", { for: "runs-input", class: "muted" }, controls, "runs");
  const runs = html("input", { id: "runs-input", type: "number", min: 1, max: MAX_RUNS, value: store.state.runs, style: "width:60px" }, controls);
  const evaluate = html("button", { type: "button", class: "primary" }, controls, "Evaluate");
  const status = html("div", { class: "status" }, root);
  const result = html("div", { class: "sub-panel" }, root);

  runs.addEventListener("change", () => {
    const value = Math.max(1, Math.min(MAX_RUNS, Number(runs.value) || 1));
    runs.value = value;
    store.setRuns(value);
  });
  evaluate.addEventListener("click", async () => {
    try {
      const entry = await evaluateMapping(store.state.mapping, store.state.mappingOrigin);
      setStatus(`Done in ${entry.seconds.toFixed(2)} s.`);
    } catch (error) {
      setStatus(error.message, true);
    }
  });

  store.on("evaluating", (flag) => {
    evaluate.disabled = flag;
    setStatus(flag ? `Evaluating ${store.state.runs} run(s)…` : "");
  });
  store.on("evaluation", render);

  function setStatus(text, isError = false) {
    status.textContent = text;
    status.className = `status${isError ? " error" : ""}`;
  }

  function render(entry) {
    clear(result);
    if (!entry) {
      html("div", { class: "muted" }, result, "Not evaluated for this mapping.");
      return;
    }
    const kv = html("dl", { class: "kv" }, result);
    const rows = [
      ["min", entry.min, true],
      ["mean", entry.mean.toFixed(2), true],
      ["max", entry.max],
      ["std dev", entry.stdev.toFixed(2)],
      ["runs", entry.costs.length],
      ["sample depth", entry.routed.depth],
      ["sample 2q", entry.routed.twoQubitGates],
      ["sample gates", entry.routed.size],
    ];
    for (const [label, value, big] of rows) {
      const item = html("div", {}, kv);
      html("dt", {}, item, label);
      html("dd", { class: big ? "big" : "" }, item, String(value));
    }
    html("div", { class: "costs", title: "all measured costs" }, result, entry.costs.join(" "));
    const line = submissionLine(entry.mapping, entry.min);
    const submission = html("div", { class: "submission" }, result);
    html("code", { title: "mapping followed by the best measured cost" }, submission, line);
    const copy = html("button", { type: "button" }, submission, "Copy");
    copy.addEventListener("click", async () => setStatus((await copyText(line)) ? "Submission line copied." : "Clipboard unavailable."));
  }

  render(null);
}
