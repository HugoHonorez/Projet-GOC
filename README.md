Run des "résultats" faites sur 200 évaluations, en dessus du coup d'une descente pour les algos de descente locale et surtout en dessous du truc de 300 seconde par instance donc ca a pas vraiment de valeur pour tester les algos

# GOC · Qubit Allocation

Tools around the course base code (`source.py`, `StudentCode.py`, `Instances/`), which is never modified.

## Setup

Python 3.12 is required: `qiskit==1.2.4` depends on `symengine<0.14`, which has no wheels for Python 3.13+.

```
uv venv --python 3.12 .venv
uv pip install --link-mode=copy --python .venv\Scripts\python.exe -r requirements.txt
uv pip install --link-mode=copy --python .venv\Scripts\python.exe -e .
```

`--link-mode=copy` is needed when the project lives in a OneDrive-synced folder. The editable install makes `goc`, `optimizer` and `visualizer` importable from the notebooks.

## Notebooks

Open them in VS Code with the `.venv` kernel.

| Notebook | Content |
|---|---|
| `00_instance_explorer` | choose an instance and a mapping: interaction graph, hardware with mapping overlay, matrices, degrees, circuit, real fitness, routed circuit |
| `01_fitness_explained` | what `fitness_inner` computes, depth before vs after routing, effect of the mapping, first look at the noise |
| `02_noise_and_surrogate` | noise of the fitness per instance, re-evaluations needed, correlation between distance cost and fitness |
| `03_metaheuristic_template` | how to write, run and compare algorithms with `optimizer`, comparison table, convergence plots, solution files |
| `04_ant_colony` | ant colony optimisation: principle, step-by-step construction, pheromone evolution, parameter studies, comparison with baselines on all instances, best solutions |
| `05_grasp` | GRASP: randomized greedy construction, RCL, exact local search on the distance cost, parameter studies (α, RCL type, local search), comparison with the ant colony and baselines, best solutions |
| `06_genetic` | genetic algorithm: permutation crossovers (OX, uniform, PMX, CX) checked on the course examples, what each crossover preserves, parameter studies (crossover, selection, mutation, population, free use of the distance cost), comparison, best solutions |
| `07_hybridization` | hybridization system (course taxonomy): low-level hooks inside a metaheuristic, high-level relay of stages, improvers; how to declare a hybrid, add it to the comparison, make a new metaheuristic hook-ready; demonstration |
| `99_comparison` | comparison of all metaheuristics (including the team's simulated annealing, PSO-DE, bee colony, tabu search, multi-start, ILS and VNS) on all instances; add a new metaheuristic with one line in `CONTENDERS` (only the new one is computed) |

Analysis and plotting code lives in the notebooks next to the figures it produces. Measurements are cached in `results/`.

Mathematical background (in French, LaTeX formulas): `docs/theory/` covers the problem and graphs, the ant colony, GRASP and the genetic algorithm, each in the general case and applied to qubit allocation.

## Python packages

```
goc/                    shared bridge to the base code
  source_bridge.py      imports source.py, loads instances, calls fitness_inner, routed circuit
  circuit_data.py       circuit operations, interactions, statistics
  hardware.py           coupling edges, drawing coordinates of the chips
  paths.py              project paths
optimizer/              framework for metaheuristics
  instance.py           InstanceData: pairs, weights, distance matrix (cached per instance)
  problem.py            Problem: fitness with evaluation budget and history, free surrogate
  representation.py     permutation encoding and swap neighbourhood
  surrogate.py          distance cost
  construction.py       shared construction pieces (interaction matrix, construction order, added cost g_t)
  randomness.py         seeded random.Random for code written with the standard random module
  fitness_local_search.py  team local search on f (descent, VND, perturbation), used by multi_start / ILS / VNS
  local_search.py       descents on the distance cost (random tries, exact best-improvement local optimum)
  experiment.py         run_algorithm, run_grid (optionally parallel), results and history frames, save/load
  result.py             Result record (best mapping, history, algorithm trace)
  solution_files.py     <Group>_Challenge_<n>.txt writer (write_*_if_better never overwrites a better existing solution)
  algorithms/           identity, random_search, surrogate_filtered, ant_colony, grasp, genetic, hybrid (relay of stages)
                        team codes, same logic as the originals: simulated_annealing, pso_de, bee_colony, tabu_search,
                        multi_start, iterated_local_search, variable_neighbourhood_search
  hybrid/               hybridization: improvers (local searches), hooks (low level), Hybrid builder
visualizer/             local web app
```

An algorithm is a function `run(problem, rng, **params)` that calls `problem.fitness(mapping)` until the budget raises `BudgetExhausted`. It can store internal diagnostics in `problem.trace`, which ends up in `Result.trace`.
`run_grid(..., workers=N)` runs in parallel processes; this requires algorithms defined in `optimizer/algorithms/`, not in a notebook.

## Visualizer

```
.venv\Scripts\python -m visualizer
```

Options: `--port 8000`, `--instances DIR`, `--solutions DIR` (repeatable), `--no-browser`.
Solution files named `<Group>_Challenge_<n>.txt` or `<Group>_Instance_<n>.txt` are read from the project root and `solutions/`; content is the mapping optionally followed by the claimed cost (`1 0 2 53`).
