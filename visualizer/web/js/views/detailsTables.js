import { clear, html } from "../core/dom.js";
import { bindFocus } from "../core/focus.js";
import { distanceClass, pairDistance, qubitStats } from "../core/metrics.js";
import { store } from "../core/store.js";

export function mountDetailsTables(root) {
  const split = html("div", { class: "split" }, root);
  const interactionsPanel = html("div", { class: "sub-panel" }, split);
  const qubitsPanel = html("div", { class: "sub-panel" }, split);
  html("h2", {}, interactionsPanel, "Interactions (sorted by distance)");
  const interactionsBox = html("div", { class: "scroll-y tall scroll-x" }, interactionsPanel);
  html("h2", {}, qubitsPanel, "Logical qubits");
  const qubitsBox = html("div", { class: "scroll-y tall scroll-x" }, qubitsPanel);

  store.on("mapping", render);

  function render() {
    const { instance, mapping, distances } = store.state;
    if (!instance) return;
    renderInteractions(instance, mapping, distances);
    renderQubits(instance, mapping, distances);
  }

  function renderInteractions(instance, mapping, distances) {
    const rows = instance.circuit.interactions
      .map((e) => ({ ...e, distance: pairDistance(distances, mapping, e.a, e.b) }))
      .sort((x, y) => y.distance - x.distance || y.count - x.count || x.a - y.a);
    const table = table_(interactionsBox, [["pair", ""], ["gates", "r"], ["physical", ""], ["distance", "r"], ["cost", "r"]]);
    for (const row of rows) {
      const tr = html("tr", { "data-q": `${row.a} ${row.b}` }, table);
      html("td", {}, tr, `q${row.a} – q${row.b}`);
      html("td", { class: "r" }, tr, String(row.count));
      html("td", {}, tr, `P${mapping[row.a]} – P${mapping[row.b]}`);
      html("td", { class: `r ${distanceClass(row.distance)}` }, tr, String(row.distance));
      html("td", { class: "r" }, tr, String(row.count * (row.distance - 1)));
      bindFocus(tr, [row.a, row.b]);
    }
  }

  function renderQubits(instance, mapping, distances) {
    const stats = qubitStats(instance, mapping, distances);
    const table = table_(qubitsBox, [["q", ""], ["P", "r"], ["degree", "r"], ["2q", "r"], ["1q", "r"], ["cost", "r"], ["neighbours", ""]]);
    for (const s of stats) {
      const tr = html("tr", { "data-q": String(s.q) }, table);
      html("td", {}, tr, `q${s.q}`);
      html("td", { class: "r" }, tr, `P${s.physical}`);
      html("td", { class: "r" }, tr, String(s.degree));
      html("td", { class: "r" }, tr, String(s.twoQubit));
      html("td", { class: "r" }, tr, String(s.oneQubit));
      html("td", { class: `r ${s.distanceCost ? "d3" : "d1"}` }, tr, String(s.distanceCost));
      html("td", {}, tr, s.neighbours.sort((a, b) => a - b).map((q) => `q${q}`).join(" "));
      bindFocus(tr, [s.q]);
    }
  }
}

function table_(container, columns) {
  clear(container);
  const table = html("table", {}, container);
  const header = html("tr", {}, html("thead", {}, table));
  for (const [label, cls] of columns) html("th", { class: cls }, header, label);
  return html("tbody", {}, table);
}
