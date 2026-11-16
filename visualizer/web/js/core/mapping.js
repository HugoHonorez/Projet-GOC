export function identityMapping(n) {
  return Array.from({ length: n }, (_, i) => i);
}

export function randomMapping(n, m) {
  const pool = identityMapping(m);
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  return pool.slice(0, n);
}

export function swapPhysical(mapping, first, second) {
  return mapping.map((p) => (p === first ? second : p === second ? first : p));
}

export function sameMapping(a, b) {
  return !!a && !!b && a.length === b.length && a.every((value, i) => value === b[i]);
}

export function formatMapping(mapping) {
  return `[${mapping.join(", ")}]`;
}

export function submissionLine(mapping, cost) {
  return [...mapping, cost].join(" ");
}

export function inverseMapping(mapping, m) {
  const inverse = new Array(m).fill(-1);
  mapping.forEach((p, i) => { inverse[p] = i; });
  return inverse;
}

export function parseMapping(text, n, m) {
  const values = (text.match(/-?\d+/g) || []).map(Number);
  if (values.length !== n) return { error: `Expected ${n} values, got ${values.length}.` };
  const outside = values.find((v) => v < 0 || v >= m);
  if (outside !== undefined) return { error: `Value ${outside} is outside 0..${m - 1}.` };
  const seen = new Set();
  const duplicate = values.find((v) => seen.has(v) || !seen.add(v));
  if (duplicate !== undefined) return { error: `Physical qubit ${duplicate} is used more than once.` };
  return { mapping: values };
}
