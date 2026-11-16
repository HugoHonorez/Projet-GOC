import { distanceMatrix, summarizeCosts } from "./metrics.js";
import { identityMapping, sameMapping } from "./mapping.js";

const listeners = new Map();

const state = {
  overview: null,
  instance: null,
  distances: null,
  mapping: [],
  mappingOrigin: "identity",
  selectedPhysical: -1,
  evaluation: null,
  evaluating: false,
  runs: 5,
  solutions: [],
  histories: new Map(),
};

function on(event, handler) {
  if (!listeners.has(event)) listeners.set(event, []);
  listeners.get(event).push(handler);
}

function emit(event, payload) {
  for (const handler of listeners.get(event) || []) handler(payload);
}

function history() {
  const id = state.instance?.id;
  if (!state.histories.has(id)) state.histories.set(id, []);
  return state.histories.get(id);
}

function mergeEvaluation(previous, result, label) {
  const costs = previous ? [...previous.costs, ...result.costs] : result.costs;
  return { ...result, ...summarizeCosts(costs), costs, label: previous?.label ?? label, time: Date.now() };
}

export const store = {
  state,
  on,
  emit,
  history,

  setOverview(overview) {
    state.overview = overview;
    emit("overview", overview);
  },

  setInstance(instance) {
    state.instance = instance;
    state.distances = distanceMatrix(instance.hardware.numQubits, instance.hardware.edges);
    state.mapping = identityMapping(instance.n);
    state.evaluation = null;
    state.solutions = [];
    emit("instance", instance);
    emit("history", history());
    this.setMapping(identityMapping(instance.n), "identity");
  },

  setMapping(mapping, origin = "manual") {
    state.mapping = mapping;
    state.mappingOrigin = origin;
    state.selectedPhysical = -1;
    state.evaluation = history().find((entry) => sameMapping(entry.mapping, mapping)) || null;
    emit("mapping", { mapping, origin });
    emit("evaluation", state.evaluation);
  },

  selectPhysical(physical) {
    state.selectedPhysical = physical;
    emit("selection", physical);
  },

  setRuns(runs) {
    state.runs = runs;
  },

  setEvaluating(flag) {
    state.evaluating = flag;
    emit("evaluating", flag);
  },

  addEvaluation(result, label) {
    const list = history();
    const index = list.findIndex((entry) => sameMapping(entry.mapping, result.mapping));
    const entry = mergeEvaluation(index >= 0 ? list[index] : null, result, label);
    if (index >= 0) list.splice(index, 1);
    list.unshift(entry);
    if (sameMapping(result.mapping, state.mapping)) {
      state.evaluation = entry;
      emit("evaluation", entry);
    }
    emit("history", list);
    return entry;
  },

  clearHistory() {
    history().length = 0;
    state.evaluation = null;
    emit("history", history());
    emit("evaluation", null);
  },

  setSolutions(solutions) {
    state.solutions = solutions;
    emit("solutions", solutions);
  },

  setFocus(qubits) {
    emit("focus", qubits);
  },
};
