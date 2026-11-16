import { loadInstance, loadOverview } from "./core/actions.js";
import { installFocus } from "./core/focus.js";
import { store } from "./core/store.js";
import { mountCircuitView } from "./views/circuitView.js";
import { mountDetailsTables } from "./views/detailsTables.js";
import { mountEvaluationPanel } from "./views/evaluationPanel.js";
import { mountHardwareView } from "./views/hardwareView.js";
import { mountHistoryPanel } from "./views/historyPanel.js";
import { mountInstancePicker } from "./views/instancePicker.js";
import { mountInteractionGraph } from "./views/interactionGraph.js";
import { mountMappingPanel } from "./views/mappingPanel.js";
import { mountSolutionsPanel } from "./views/solutionsPanel.js";
import { mountSummaryBar } from "./views/summaryBar.js";

const byId = (id) => document.getElementById(id);

function mountViews() {
  installFocus();
  mountInstancePicker(byId("instance-picker"));
  mountSummaryBar(byId("summary-bar"));
  mountInteractionGraph(byId("interaction-graph"));
  mountHardwareView(byId("hardware-view"), byId("hardware-title"), byId("overlay-toggle"));
  mountMappingPanel(byId("mapping-panel"));
  mountEvaluationPanel(byId("evaluation-panel"));
  mountHistoryPanel(byId("history-panel"));
  mountSolutionsPanel(byId("solutions-panel"));
  mountDetailsTables(byId("details-tables"));
  mountCircuitView(byId("circuit-view"));
}

function requestedInstance() {
  const match = location.hash.match(/^#instance-(\d+)$/);
  const ids = store.state.overview.instances.map((i) => i.id);
  const id = match ? Number(match[1]) : NaN;
  return ids.includes(id) ? id : ids[0];
}

async function route() {
  const id = requestedInstance();
  if (id === undefined || store.state.instance?.id === id) return;
  try {
    await loadInstance(id);
  } catch (error) {
    showFatal(error);
  }
}

function showFatal(error) {
  byId("instance-picker").textContent = `Error: ${error.message}`;
  byId("instance-picker").classList.add("error");
}

async function start() {
  mountViews();
  try {
    await loadOverview();
  } catch (error) {
    showFatal(error);
    return;
  }
  window.addEventListener("hashchange", route);
  await route();
}

start();
