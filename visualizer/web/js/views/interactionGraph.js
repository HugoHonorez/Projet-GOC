import { clear, svg, tooltip } from "../core/dom.js";
import { bindFocus } from "../core/focus.js";
import { forceLayout } from "../core/forceLayout.js";
import { distanceClass, pairDistance } from "../core/metrics.js";
import { store } from "../core/store.js";

const PADDING = 36;

export function mountInteractionGraph(root) {
  let points = [];
  let edges = [];
  let vertices = [];

  store.on("instance", (instance) => {
    points = forceLayout(instance.n, instance.circuit.interactions);
    draw(instance);
  });
  store.on("mapping", () => update());

  function fitView() {
    const xs = points.map((p) => p.x);
    const ys = points.map((p) => p.y);
    const minX = Math.min(...xs) - PADDING;
    const minY = Math.min(...ys) - PADDING;
    root.setAttribute("viewBox", `${minX} ${minY} ${Math.max(...xs) - minX + PADDING} ${Math.max(...ys) - minY + PADDING}`);
  }

  function draw(instance) {
    clear(root);
    const interactions = instance.circuit.interactions;
    const maxCount = Math.max(1, ...interactions.map((e) => e.count));
    const edgeLayer = svg("g", {}, root);
    const vertexLayer = svg("g", {}, root);
    edges = interactions.map((interaction) => {
      const group = svg("g", { "data-q": `${interaction.a} ${interaction.b}` }, edgeLayer);
      const line = svg("line", { class: "edge", "stroke-width": (1.4 + 4 * Math.sqrt(interaction.count / maxCount)).toFixed(2) }, group);
      const title = tooltip(line, "");
      const label = interaction.count > 1 ? svg("text", { class: "edge-count" }, group, String(interaction.count)) : null;
      bindFocus(group, [interaction.a, interaction.b]);
      return { interaction, line, label, title };
    });
    vertices = points.map((_, q) => {
      const group = svg("g", { class: "vertex", "data-q": String(q) }, vertexLayer);
      svg("circle", { r: 14 }, group);
      svg("text", { class: "name" }, group, `q${q}`);
      const physical = svg("text", { class: "phys", y: 25 }, group);
      bindFocus(group, [q]);
      enableDrag(group, q);
      return { group, physical };
    });
    fitView();
    place();
    update();
  }

  function place() {
    vertices.forEach(({ group }, q) => group.setAttribute("transform", `translate(${points[q].x.toFixed(1)},${points[q].y.toFixed(1)})`));
    for (const { interaction, line, label } of edges) {
      const a = points[interaction.a];
      const b = points[interaction.b];
      line.setAttribute("x1", a.x);
      line.setAttribute("y1", a.y);
      line.setAttribute("x2", b.x);
      line.setAttribute("y2", b.y);
      if (label) {
        label.setAttribute("x", (a.x + b.x) / 2);
        label.setAttribute("y", (a.y + b.y) / 2 - 7);
      }
    }
  }

  function update() {
    const { mapping, distances } = store.state;
    if (!distances || mapping.length !== vertices.length) return;
    for (const { interaction, line, title } of edges) {
      const distance = pairDistance(distances, mapping, interaction.a, interaction.b);
      line.setAttribute("class", `edge ${distanceClass(distance)}`);
      title.textContent = `q${interaction.a}–q${interaction.b} · ${interaction.count} gate(s) · P${mapping[interaction.a]}–P${mapping[interaction.b]} · distance ${distance}`;
    }
    vertices.forEach(({ physical }, q) => { physical.textContent = `P${mapping[q]}`; });
  }

  function enableDrag(group, q) {
    group.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      group.setPointerCapture(event.pointerId);
      const move = (e) => {
        const point = root.createSVGPoint();
        point.x = e.clientX;
        point.y = e.clientY;
        const local = point.matrixTransform(root.getScreenCTM().inverse());
        points[q] = { x: local.x, y: local.y };
        place();
      };
      const stop = () => {
        group.removeEventListener("pointermove", move);
        group.removeEventListener("pointerup", stop);
        group.removeEventListener("pointercancel", stop);
        fitView();
      };
      group.addEventListener("pointermove", move);
      group.addEventListener("pointerup", stop);
      group.addEventListener("pointercancel", stop);
    });
  }
}
