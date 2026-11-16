import { api } from "./api.js";
import { store } from "./store.js";

export async function loadOverview() {
  store.setOverview(await api.overview());
}

export async function loadInstance(id) {
  const instance = await api.instance(id);
  store.setInstance(instance);
  await refreshSolutions();
}

export async function refreshSolutions() {
  const id = store.state.instance?.id;
  if (id === undefined) return;
  const solutions = await api.solutions(id);
  if (store.state.instance?.id === id) store.setSolutions(solutions);
}

export async function evaluateMapping(mapping, label) {
  const id = store.state.instance.id;
  store.setEvaluating(true);
  try {
    const result = await api.evaluate(id, mapping, store.state.runs);
    return store.state.instance?.id === id ? store.addEvaluation(result, label) : result;
  } finally {
    store.setEvaluating(false);
  }
}
