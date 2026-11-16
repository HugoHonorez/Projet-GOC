async function request(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

export const api = {
  overview: () => request("/api/instances"),
  instance: (id) => request(`/api/instances/${id}`),
  solutions: (id) => request(`/api/instances/${id}/solutions`),
  evaluate: (id, mapping, runs) =>
    request(`/api/instances/${id}/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mapping, runs }),
    }),
};
