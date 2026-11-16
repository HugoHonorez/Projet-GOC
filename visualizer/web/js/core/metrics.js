export function distanceMatrix(m, edges) {
  const neighbours = Array.from({ length: m }, () => []);
  for (const [a, b] of edges) {
    neighbours[a].push(b);
    neighbours[b].push(a);
  }
  return neighbours.map((_, source) => {
    const distance = new Array(m).fill(Infinity);
    distance[source] = 0;
    const queue = [source];
    for (let head = 0; head < queue.length; head++) {
      const u = queue[head];
      for (const v of neighbours[u]) {
        if (distance[v] === Infinity) {
          distance[v] = distance[u] + 1;
          queue.push(v);
        }
      }
    }
    return distance;
  });
}

export function distanceClass(distance) {
  if (distance <= 1) return "d1";
  return distance === 2 ? "d2" : "d3";
}

export function pairDistance(distances, mapping, a, b) {
  return distances[mapping[a]][mapping[b]];
}

export function operationDistance(distances, mapping, qubits) {
  let worst = 0;
  for (let i = 0; i < qubits.length; i++) {
    for (let j = i + 1; j < qubits.length; j++) {
      worst = Math.max(worst, pairDistance(distances, mapping, qubits[i], qubits[j]));
    }
  }
  return worst;
}

export function mappingMetrics(interactions, mapping, distances) {
  const result = { distanceCost: 0, directGates: 0, totalGates: 0, adjacentPairs: 0, totalPairs: interactions.length, maxDistance: 0 };
  for (const { a, b, count } of interactions) {
    const distance = pairDistance(distances, mapping, a, b);
    result.totalGates += count;
    result.distanceCost += count * (distance - 1);
    result.maxDistance = Math.max(result.maxDistance, distance);
    if (distance === 1) {
      result.directGates += count;
      result.adjacentPairs += 1;
    }
  }
  return result;
}

export function qubitStats(instance, mapping, distances) {
  const n = instance.n;
  const stats = Array.from({ length: n }, (_, q) => ({ q, physical: mapping[q], degree: 0, twoQubit: 0, oneQubit: 0, distanceCost: 0, neighbours: [] }));
  for (const { a, b, count } of instance.circuit.interactions) {
    const cost = count * (pairDistance(distances, mapping, a, b) - 1);
    for (const [self, other] of [[a, b], [b, a]]) {
      stats[self].degree += 1;
      stats[self].twoQubit += count;
      stats[self].distanceCost += cost;
      stats[self].neighbours.push(other);
    }
  }
  for (const operation of instance.circuit.operations) {
    if (operation.qubits.length === 1) stats[operation.qubits[0]].oneQubit += 1;
  }
  return stats;
}

export function summarizeCosts(costs) {
  const mean = costs.reduce((sum, c) => sum + c, 0) / costs.length;
  const variance = costs.reduce((sum, c) => sum + (c - mean) ** 2, 0) / costs.length;
  return { min: Math.min(...costs), max: Math.max(...costs), mean, stdev: Math.sqrt(variance) };
}
