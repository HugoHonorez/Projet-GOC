const ITERATIONS = 600;
const SPRING_LENGTH = 62;
const REPULSION = 3000;

export function forceLayout(n, interactions) {
  const points = Array.from({ length: n }, (_, i) => {
    const angle = i * 2.39996;
    const radius = 14 * Math.sqrt(i + 0.5);
    return { x: radius * Math.cos(angle), y: radius * Math.sin(angle) };
  });
  for (let iteration = 0; iteration < ITERATIONS; iteration++) {
    const temperature = 1 - iteration / ITERATIONS;
    const forces = points.map(() => ({ x: 0, y: 0 }));
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const dx = points[i].x - points[j].x;
        const dy = points[i].y - points[j].y;
        const squared = Math.max(dx * dx + dy * dy, 1);
        const length = Math.sqrt(squared);
        const force = REPULSION / squared;
        forces[i].x += (dx / length) * force;
        forces[i].y += (dy / length) * force;
        forces[j].x -= (dx / length) * force;
        forces[j].y -= (dy / length) * force;
      }
    }
    for (const { a, b } of interactions) {
      const dx = points[b].x - points[a].x;
      const dy = points[b].y - points[a].y;
      const length = Math.max(Math.hypot(dx, dy), 0.01);
      const force = (length - SPRING_LENGTH) * 0.12;
      forces[a].x += (dx / length) * force;
      forces[a].y += (dy / length) * force;
      forces[b].x -= (dx / length) * force;
      forces[b].y -= (dy / length) * force;
    }
    const cap = 10 * temperature + 0.4;
    for (let i = 0; i < n; i++) {
      forces[i].x -= points[i].x * 0.012;
      forces[i].y -= points[i].y * 0.012;
      const magnitude = Math.hypot(forces[i].x, forces[i].y);
      const scale = magnitude > cap ? cap / magnitude : 1;
      points[i].x += forces[i].x * scale;
      points[i].y += forces[i].y * scale;
    }
  }
  return points;
}
