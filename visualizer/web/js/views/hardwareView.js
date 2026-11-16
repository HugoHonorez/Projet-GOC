import { clear, svg, tooltip } from "../core/dom.js";
import { bindFocus } from "../core/focus.js";
import { inverseMapping, swapPhysical } from "../core/mapping.js";
import { distanceClass } from "../core/metrics.js";
import { store } from "../core/store.js";

const UNIT = 64;
const MARGIN = 32;

export function mountHardwareView(root, title, overlayToggle) {
  let showOverlay = overlayToggle.checked;

  overlayToggle.addEventListener("change", () => {
    showOverlay = overlayToggle.checked;
    draw();
  });
  store.on("mapping", draw);
  store.on("selection", draw);
  store.on("instance", (instance) => {
    title.textContent = `Hardware · ${instance.hardware.name} · ${instance.m} qubits`;
  });

  function draw() {
    const { instance, mapping, distances, selectedPhysical } = store.state;
    if (!instance || mapping.length !== instance.n) return;
    const { coordinates, edges, numQubits } = instance.hardware;
    const x = (p) => MARGIN + coordinates[p][0] * UNIT;
    const y = (p) => MARGIN + coordinates[p][1] * UNIT;
    const width = 2 * MARGIN + Math.max(...coordinates.map((c) => c[0])) * UNIT;
    const height = 2 * MARGIN + Math.max(...coordinates.map((c) => c[1])) * UNIT;
    clear(root);
    root.setAttribute("viewBox", `0 0 ${width} ${height}`);
    root.style.minWidth = `${Math.min(width, 520)}px`;
    root.style.maxWidth = `${width * 1.3}px`;

    const couplingLayer = svg("g", {}, root);
    const overlayLayer = svg("g", {}, root);
    const nodeLayer = svg("g", {}, root);

    for (const [a, b] of edges) {
      svg("line", { class: "coupling", x1: x(a), y1: y(a), x2: x(b), y2: y(b) }, couplingLayer);
    }

    if (showOverlay) {
      const interactions = instance.circuit.interactions;
      const maxCount = Math.max(1, ...interactions.map((e) => e.count));
      interactions.forEach(({ a, b, count }, index) => {
        const pa = mapping[a];
        const pb = mapping[b];
        const distance = distances[pa][pb];
        const [x1, y1, x2, y2] = [x(pa), y(pa), x(pb), y(pb)];
        let d = `M${x1},${y1}L${x2},${y2}`;
        if (distance > 1) {
          const length = Math.hypot(x2 - x1, y2 - y1) || 1;
          const bend = (index % 2 ? 1 : -1) * Math.min(0.28 * length, 60);
          const cx = (x1 + x2) / 2 - ((y2 - y1) / length) * bend;
          const cy = (y1 + y2) / 2 + ((x2 - x1) / length) * bend;
          d = `M${x1},${y1}Q${cx},${cy} ${x2},${y2}`;
        }
        const path = svg("path", {
          d,
          class: `overlay ${distanceClass(distance)}`,
          "stroke-width": (1.2 + 3 * Math.sqrt(count / maxCount)).toFixed(2),
          "data-q": `${a} ${b}`,
        }, overlayLayer);
        tooltip(path, `q${a} (P${pa}) – q${b} (P${pb}) · distance ${distance} · ${count} gate(s)`);
      });
    }

    const inverse = inverseMapping(mapping, numQubits);
    for (let p = 0; p < numQubits; p++) {
      const q = inverse[p];
      const used = q >= 0;
      const group = svg("g", {
        class: `pnode ${used ? "used" : "free"}${selectedPhysical === p ? " selected" : ""}`,
        transform: `translate(${x(p)},${y(p)})`,
        tabindex: 0,
        role: "button",
        "aria-label": used ? `Physical qubit ${p} holds q${q}` : `Physical qubit ${p} is free`,
        "data-q": used ? String(q) : "-",
      }, nodeLayer);
      svg("circle", { class: "ring", r: used ? 21 : 16 }, group);
      svg("circle", { class: "body", r: used ? 17 : 12 }, group);
      svg("text", { class: "name" }, group, used ? `q${q}` : String(p));
      if (used) svg("text", { class: "index", y: -22 }, group, `P${p}`);
      tooltip(group, used ? `P${p} ← q${q}` : `P${p} (free)`);
      group.addEventListener("click", () => select(p));
      group.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          select(p);
        }
      });
      if (used) bindFocus(group, [q]);
    }
  }

  function select(physical) {
    const current = store.state.selectedPhysical;
    if (current < 0) return store.selectPhysical(physical);
    if (current === physical) return store.selectPhysical(-1);
    store.setMapping(swapPhysical(store.state.mapping, current, physical), "swap");
  }
}
