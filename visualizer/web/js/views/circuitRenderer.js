import { clear, svg, tooltip } from "../core/dom.js";
import { bindFocus } from "../core/focus.js";

const COLUMN = 26;
const ROW = 24;
const LEFT = 84;
const TOP = 20;

const LABELS = {
  h: "H", x: "X", y: "Y", z: "Z", s: "S", sdg: "S†", t: "T", tdg: "T†", sx: "√X", sxdg: "√X†",
  rz: "Rz", rx: "Rx", ry: "Ry", u1: "U1", u2: "U2", u3: "U3", u: "U", p: "P", id: "I", reset: "|0⟩",
};

function layoutColumns(operations, rowOf) {
  const busy = new Array(rowOf.size).fill(0);
  const placed = [];
  for (const operation of operations) {
    const rows = operation.qubits.map((q) => rowOf.get(q));
    if (rows.some((r) => r === undefined)) continue;
    const low = Math.min(...rows);
    const high = Math.max(...rows);
    let column = 0;
    for (let r = low; r <= high; r++) column = Math.max(column, busy[r]);
    for (let r = low; r <= high; r++) busy[r] = column + 1;
    placed.push({ operation, rows, column });
  }
  return { placed, columns: Math.max(1, ...busy) };
}

function describe(operation) {
  const params = operation.params.length ? `(${operation.params.join(", ")})` : "";
  return `${operation.name}${params} ${operation.qubits.map((q) => `[${q}]`).join(" ")}`;
}

function drawTwoQubit(group, operation, x, ys) {
  svg("line", { x1: x, x2: x, y1: Math.min(...ys), y2: Math.max(...ys) }, group);
  const dot = (y) => svg("circle", { class: "dot", cx: x, cy: y, r: 3.5 }, group);
  const target = (y) => {
    svg("circle", { class: "target", cx: x, cy: y, r: 7 }, group);
    svg("line", { x1: x - 7, x2: x + 7, y1: y, y2: y }, group);
    svg("line", { x1: x, x2: x, y1: y - 7, y2: y + 7 }, group);
  };
  const cross = (y) => {
    svg("line", { class: "cross", x1: x - 5, x2: x + 5, y1: y - 5, y2: y + 5 }, group);
    svg("line", { class: "cross", x1: x - 5, x2: x + 5, y1: y + 5, y2: y - 5 }, group);
  };
  const box = (y, text) => {
    svg("rect", { x: x - 10, y: y - 8, width: 20, height: 16, rx: 2 }, group);
    svg("text", { x, y }, group, text);
  };
  const name = operation.name;
  if (name === "cx") { dot(ys[0]); target(ys[1]); }
  else if (name === "ccx") { dot(ys[0]); dot(ys[1]); target(ys[2]); }
  else if (name === "cz" || name === "cp" || name === "cu1") ys.forEach(dot);
  else if (name === "swap") ys.forEach(cross);
  else if (/^r(xx|yy|zz)$/.test(name)) ys.forEach((y) => box(y, name.slice(1).toUpperCase()));
  else ys.forEach((y) => box(y, name.slice(0, 3)));
}

export function drawCircuit(root, { wires, operations, gateClass = () => "", operationFocus = () => null, routed = false }) {
  clear(root);
  root.classList.toggle("routed", routed);
  const rowOf = new Map(wires.map((wire, row) => [wire.index, row]));
  const { placed, columns } = layoutColumns(operations, rowOf);
  const hasTail = wires.some((wire) => wire.tail);
  const width = LEFT + columns * COLUMN + (hasTail ? 44 : 12);
  const height = TOP + wires.length * ROW + 6;
  root.setAttribute("viewBox", `0 0 ${width} ${height}`);
  root.setAttribute("width", width);
  root.setAttribute("height", height);

  const yOf = (row) => TOP + row * ROW + ROW / 2;
  const xOf = (column) => LEFT + column * COLUMN + COLUMN / 2;

  for (let c = 0; c < columns; c += 10) svg("text", { class: "tick", x: xOf(c), y: 10 }, root, String(c));

  wires.forEach((wire, row) => {
    const group = svg("g", { "data-q": wire.focus ?? undefined }, root);
    svg("line", { class: "wire", x1: LEFT - 4, x2: LEFT + columns * COLUMN + 4, y1: yOf(row), y2: yOf(row) }, group);
    svg("text", { class: "wire-label", x: 4, y: yOf(row) }, group, wire.label);
    if (wire.sub) svg("text", { class: "wire-sub", x: 40, y: yOf(row) }, group, wire.sub);
    if (wire.tail) svg("text", { class: "wire-tail", x: LEFT + columns * COLUMN + 10, y: yOf(row) }, group, wire.tail);
    if (wire.focus !== undefined && wire.focus !== null) bindFocus(group, [Number(wire.focus)]);
  });

  for (const { operation, rows, column } of placed) {
    const x = xOf(column);
    const ys = rows.map(yOf);
    const focus = operationFocus(operation);
    if (operation.qubits.length === 1) {
      const group = svg("g", { class: "gate1", "data-q": focus ?? undefined }, root);
      svg("rect", { x: x - 10, y: ys[0] - 8.5, width: 20, height: 17, rx: 2 }, group);
      svg("text", { x, y: ys[0] }, group, LABELS[operation.name] || operation.name.slice(0, 3));
      tooltip(group, describe(operation));
      continue;
    }
    const group = svg("g", { class: `gate2 ${gateClass(operation)}`, "data-q": focus ?? undefined }, root);
    drawTwoQubit(group, operation, x, ys);
    tooltip(group, describe(operation));
  }
  return { columns };
}
