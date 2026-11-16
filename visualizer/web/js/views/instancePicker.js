import { clear, html } from "../core/dom.js";
import { store } from "../core/store.js";

export function mountInstancePicker(root) {
  store.on("overview", ({ instances }) => {
    clear(root);
    const groups = new Map();
    for (const instance of instances) {
      if (!groups.has(instance.m)) groups.set(instance.m, []);
      groups.get(instance.m).push(instance);
    }
    for (const [m, list] of [...groups].sort((a, b) => a[0] - b[0])) {
      const group = html("div", { class: "picker-group" }, root);
      html("span", { class: "picker-label" }, group, `${m}q`);
      for (const instance of list) {
        const button = html("button", {
          type: "button",
          "data-id": instance.id,
          title: `Instance ${instance.id} · n=${instance.n} · m=${instance.m} · ${instance.hardware} · depth ${instance.depth}`,
        }, group, String(instance.id));
        button.addEventListener("click", () => { location.hash = `instance-${instance.id}`; });
      }
    }
  });

  store.on("instance", (instance) => {
    for (const button of root.querySelectorAll("button")) {
      button.classList.toggle("active", Number(button.dataset.id) === instance.id);
    }
  });
}
