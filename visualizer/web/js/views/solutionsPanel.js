import { evaluateMapping, refreshSolutions } from "../core/actions.js";
import { clear, html } from "../core/dom.js";
import { formatMapping, sameMapping } from "../core/mapping.js";
import { store } from "../core/store.js";

export function mountSolutionsPanel(root) {
  const head = html("div", { class: "card-head" }, root);
  html("h2", {}, head, "Solution files");
  const actions = html("div", { class: "row" }, head);
  const refresh = html("button", { type: "button" }, actions, "Refresh");
  const evaluateAll = html("button", { type: "button" }, actions, "Evaluate all");
  const status = html("div", { class: "status muted" }, root);
  const box = html("div", { class: "scroll-y" }, root);

  refresh.addEventListener("click", () => refreshSolutions().catch((error) => setStatus(error.message, true)));
  evaluateAll.addEventListener("click", async () => {
    const valid = store.state.solutions.filter((s) => s.mapping);
    for (const [index, solution] of valid.entries()) {
      setStatus(`Evaluating ${index + 1}/${valid.length}: ${solution.file}`);
      try {
        await evaluateMapping(solution.mapping, solution.file);
      } catch (error) {
        setStatus(`${solution.file}: ${error.message}`, true);
        return;
      }
    }
    setStatus(valid.length ? `Evaluated ${valid.length} file(s).` : "No valid solution file.");
  });

  store.on("solutions", render);
  store.on("history", () => render(store.state.solutions));
  store.on("mapping", () => render(store.state.solutions));
  store.on("evaluating", (flag) => { evaluateAll.disabled = flag; });
  store.on("overview", (overview) => {
    root.title = `Scanned: ${overview.solutionDirs.join(" ; ")}\nPattern: <Group>_Challenge_<n>.txt or <Group>_Instance_<n>.txt`;
  });

  function setStatus(text, isError = false) {
    status.textContent = text;
    status.className = `status ${isError ? "error" : "muted"}`;
  }

  function render(solutions) {
    clear(box);
    if (!solutions.length) {
      html("div", { class: "muted" }, box, `No file named <Group>_Challenge_${store.state.instance?.id}.txt or <Group>_Instance_${store.state.instance?.id}.txt found.`);
      return;
    }
    const history = store.history();
    const table = html("table", {}, box);
    const header = html("tr", {}, html("thead", {}, table));
    for (const [label, cls] of [["file", ""], ["claimed", "r"], ["min", "r"], ["status", ""]]) html("th", { class: cls }, header, label);
    const body = html("tbody", {}, table);
    for (const solution of solutions) {
      const evaluated = solution.mapping && history.find((e) => sameMapping(e.mapping, solution.mapping));
      const row = html("tr", {
        class: `${solution.mapping ? "clickable" : ""} ${solution.mapping && sameMapping(solution.mapping, store.state.mapping) ? "current" : ""}`,
        title: solution.error || formatMapping(solution.mapping),
      }, body);
      html("td", { class: "truncate", title: solution.file }, row, solution.file);
      html("td", { class: "r" }, row, solution.claimedCost ?? "–");
      html("td", { class: "r" }, row, evaluated ? String(evaluated.min) : "–");
      html("td", { class: solution.error ? "error" : "" }, row, check(solution, evaluated));
      if (solution.mapping) {
        row.addEventListener("click", async () => {
          store.setMapping(solution.mapping, solution.file);
          if (!evaluated) {
            try {
              await evaluateMapping(solution.mapping, solution.file);
            } catch (error) {
              setStatus(error.message, true);
            }
          }
        });
      }
    }
  }
}

function check(solution, evaluated) {
  if (solution.error) return "invalid";
  if (!evaluated) return "pending";
  if (solution.claimedCost === null) return "no cost";
  if (evaluated.min === solution.claimedCost) return "matches";
  const gap = evaluated.min - solution.claimedCost;
  return gap > 0 ? `+${gap}` : `−${-gap}`;
}
