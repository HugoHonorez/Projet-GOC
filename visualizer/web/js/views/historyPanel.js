import { clear, html } from "../core/dom.js";
import { formatMapping, sameMapping } from "../core/mapping.js";
import { mappingMetrics } from "../core/metrics.js";
import { store } from "../core/store.js";

const COLUMNS = [["source", ""], ["min", "r"], ["mean", "r"], ["max", "r"], ["runs", "r"], ["dist.", "r"]];

export function mountHistoryPanel(root) {
  const head = html("div", { class: "card-head" }, root);
  html("h2", {}, head, "History");
  const clearButton = html("button", { type: "button" }, head, "Clear");
  const box = html("div", { class: "scroll-y" }, root);

  clearButton.addEventListener("click", () => store.clearHistory());
  store.on("history", render);
  store.on("mapping", () => render(store.history()));

  function render(list) {
    clear(box);
    clearButton.disabled = !list.length;
    if (!list.length) {
      html("div", { class: "muted" }, box, "No evaluation yet.");
      return;
    }
    const { instance, distances } = store.state;
    const best = Math.min(...list.map((e) => e.min));
    const table = html("table", {}, box);
    const header = html("tr", {}, html("thead", {}, table));
    for (const [label, cls] of COLUMNS) html("th", { class: cls }, header, label);
    const body = html("tbody", {}, table);
    for (const entry of list) {
      const row = html("tr", {
        class: ["clickable", entry.min === best ? "best" : "", sameMapping(entry.mapping, store.state.mapping) ? "current" : ""].join(" "),
        title: formatMapping(entry.mapping),
      }, body);
      const distance = mappingMetrics(instance.circuit.interactions, entry.mapping, distances).distanceCost;
      html("td", { class: "truncate", title: entry.label }, row, entry.label);
      html("td", { class: "r" }, row, String(entry.min));
      html("td", { class: "r" }, row, entry.mean.toFixed(1));
      html("td", { class: "r" }, row, String(entry.max));
      html("td", { class: "r" }, row, String(entry.costs.length));
      html("td", { class: "r" }, row, String(distance));
      row.addEventListener("click", () => store.setMapping(entry.mapping, entry.label));
    }
  }

  render([]);
}
