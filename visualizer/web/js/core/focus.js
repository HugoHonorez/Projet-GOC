import { store } from "./store.js";

export function installFocus() {
  store.on("focus", (qubits) => {
    const focus = qubits.map(String);
    for (const node of document.querySelectorAll("[data-q]")) {
      if (!focus.length) {
        node.classList.remove("dim");
        continue;
      }
      const own = node.dataset.q.split(" ");
      const visible = own.every((q) => focus.includes(q)) || focus.every((q) => own.includes(q));
      node.classList.toggle("dim", !visible);
    }
  });
}

export function bindFocus(node, qubits) {
  node.addEventListener("mouseenter", () => store.setFocus(qubits));
  node.addEventListener("mouseleave", () => store.setFocus([]));
}
