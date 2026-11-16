import { copyText, html } from "../core/dom.js";
import { formatMapping, identityMapping, parseMapping, randomMapping } from "../core/mapping.js";
import { mappingMetrics } from "../core/metrics.js";
import { store } from "../core/store.js";

export function mountMappingPanel(root) {
  const head = html("div", { class: "card-head" }, root);
  html("h2", {}, head, "Mapping");
  const origin = html("span", { class: "hint" }, head);
  html("label", { for: "mapping-input", class: "muted" }, root, "mapping[i] = physical qubit of logical qubit i");
  const input = html("textarea", { id: "mapping-input", spellcheck: "false", rows: 2 }, root);
  const message = html("div", { class: "status" }, root);
  const actions = html("div", { class: "row" }, root);
  const identity = html("button", { type: "button" }, actions, "Identity");
  const random = html("button", { type: "button" }, actions, "Random");
  const copy = html("button", { type: "button" }, actions, "Copy list");
  const metrics = html("dl", { class: "kv" }, root);
  let editing = false;

  input.addEventListener("input", () => {
    const { instance } = store.state;
    const parsed = parseMapping(input.value, instance.n, instance.m);
    input.classList.toggle("invalid", !!parsed.error);
    setMessage(parsed.error || "", !!parsed.error);
    if (parsed.mapping) {
      editing = true;
      store.setMapping(parsed.mapping, "manual");
      editing = false;
    }
  });
  identity.addEventListener("click", () => store.setMapping(identityMapping(store.state.instance.n), "identity"));
  random.addEventListener("click", () => store.setMapping(randomMapping(store.state.instance.n, store.state.instance.m), "random"));
  copy.addEventListener("click", async () => {
    const text = formatMapping(store.state.mapping);
    if (await copyText(text)) setMessage(`Copied ${text}`);
    else {
      input.select();
      setMessage("Clipboard unavailable: text selected.");
    }
  });

  store.on("mapping", ({ mapping, origin: source }) => {
    if (!editing) {
      input.value = formatMapping(mapping);
      input.classList.remove("invalid");
      setMessage("");
    }
    origin.textContent = source;
    renderMetrics();
  });
  store.on("selection", (physical) => {
    setMessage(physical >= 0 ? `P${physical} selected: click another physical qubit to swap.` : "");
  });

  function setMessage(text, isError = false) {
    message.textContent = text;
    message.className = `status${isError ? " error" : ""}`;
  }

  function renderMetrics() {
    const { instance, mapping, distances } = store.state;
    const m = mappingMetrics(instance.circuit.interactions, mapping, distances);
    const rows = [
      ["distance cost", m.distanceCost, "Σ gates × (distance − 1)"],
      ["max distance", m.maxDistance, "largest physical distance between interacting qubits"],
      ["direct 2q gates", `${m.directGates}/${m.totalGates}`, "2-qubit gates already on coupled qubits"],
      ["adjacent pairs", `${m.adjacentPairs}/${m.totalPairs}`, "interacting pairs placed on coupled qubits"],
    ];
    metrics.replaceChildren();
    for (const [label, value, title] of rows) {
      const item = html("div", { title }, metrics);
      html("dt", {}, item, label);
      html("dd", {}, item, String(value));
    }
  }
}
