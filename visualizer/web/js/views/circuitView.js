import { html } from "../core/dom.js";
import { inverseMapping } from "../core/mapping.js";
import { distanceClass, operationDistance } from "../core/metrics.js";
import { store } from "../core/store.js";
import { drawCircuit } from "./circuitRenderer.js";

export function mountCircuitView(root) {
  const head = html("div", { class: "card-head" }, root);
  const tabs = html("div", { class: "tabs" }, head);
  const logicalTab = html("button", { type: "button", class: "active" }, tabs, "Logical circuit");
  const routedTab = html("button", { type: "button", disabled: true }, tabs, "Routed circuit");
  const options = html("div", { class: "row" }, head);
  const info = html("span", { class: "hint" }, options);
  const onlyTwoQubit = html("input", { type: "checkbox", id: "only-two-qubit" });
  const label = html("label", { class: "check", for: "only-two-qubit" }, options);
  label.append(onlyTwoQubit, "2-qubit gates only");
  const scroll = html("div", { class: "circuit-scroll" }, root);
  const canvas = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  scroll.appendChild(canvas);

  let view = "logical";

  logicalTab.addEventListener("click", () => setView("logical"));
  routedTab.addEventListener("click", () => setView("routed"));
  onlyTwoQubit.addEventListener("change", render);
  store.on("mapping", render);
  store.on("evaluation", (evaluation) => {
    routedTab.disabled = !evaluation;
    if (!evaluation && view === "routed") view = "logical";
    render();
  });

  function setView(next) {
    view = next;
    logicalTab.classList.toggle("active", view === "logical");
    routedTab.classList.toggle("active", view === "routed");
    render();
  }

  function filter(operations) {
    return onlyTwoQubit.checked ? operations.filter((op) => op.qubits.length > 1) : operations;
  }

  function render() {
    const { instance, mapping, distances, evaluation } = store.state;
    if (!instance || mapping.length !== instance.n) return;
    logicalTab.classList.toggle("active", view === "logical");
    routedTab.classList.toggle("active", view === "routed");
    if (view === "routed" && evaluation) renderRouted(instance, evaluation);
    else renderLogical(instance, mapping, distances);
  }

  function renderLogical(instance, mapping, distances) {
    const wires = mapping.map((physical, q) => ({ index: q, label: `q${q}`, sub: `P${physical}`, focus: String(q) }));
    const { columns } = drawCircuit(canvas, {
      wires,
      operations: filter(instance.circuit.operations),
      gateClass: (op) => distanceClass(operationDistance(distances, mapping, op.qubits)),
      operationFocus: (op) => op.qubits.join(" "),
    });
    info.textContent = `depth ${instance.circuit.depth} · ${instance.circuit.size} gates · ${instance.circuit.twoQubitGates} 2q · ${columns} columns drawn`;
  }

  function renderRouted(instance, evaluation) {
    const routed = evaluation.routed;
    const m = instance.m;
    const initial = inverseMapping(evaluation.mapping, m);
    const final = routed.finalLayout ? inverseMapping(routed.finalLayout, m) : null;
    const used = new Set(evaluation.mapping);
    routed.operations.forEach((op) => op.qubits.forEach((q) => used.add(q)));
    const wires = [...used].sort((a, b) => a - b).map((p) => ({
      index: p,
      label: `P${p}`,
      sub: initial[p] >= 0 ? `q${initial[p]}` : "",
      tail: final && final[p] >= 0 ? `q${final[p]}` : "",
    }));
    const { columns } = drawCircuit(canvas, { wires, operations: filter(routed.operations), routed: true });
    info.textContent = `sample · depth ${routed.depth} · ${routed.size} gates · ${routed.twoQubitGates} 2q · ${columns} columns drawn · left: initial, right: final layout`;
  }
}
