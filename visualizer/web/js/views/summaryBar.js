import { clear, html } from "../core/dom.js";
import { store } from "../core/store.js";

export function mountSummaryBar(root) {
  store.on("instance", (instance) => {
    const { circuit, hardware } = instance;
    const degree = new Array(instance.n).fill(0);
    for (const { a, b } of circuit.interactions) {
      degree[a] += 1;
      degree[b] += 1;
    }
    const gates = Object.entries(circuit.gateCounts)
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => `${name} ${count}`)
      .join(" · ");
    const items = [
      ["file", instance.file],
      ["n", instance.n],
      ["m", instance.m],
      ["hardware", `${hardware.name} (${hardware.edges.length} couplings)`],
      ["gates", circuit.size],
      ["2q gates", circuit.twoQubitGates],
      ["pairs", circuit.interactions.length],
      ["max degree", Math.max(0, ...degree)],
      ["logical depth", circuit.depth],
      ["ops", gates],
    ];
    clear(root);
    for (const [label, value] of items) {
      const item = html("div", {}, root);
      html("dt", {}, item, label);
      html("dd", {}, item, String(value));
    }
  });
}
