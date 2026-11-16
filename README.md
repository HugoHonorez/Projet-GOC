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
| `05_simulated_annealing` | simulated annealing: acceptance rule, detailed trajectory, parameter studies, comparison with notebook 04 results, best solutions |
| `99_comparison` | comparison of all metaheuristics on all instances; add a new metaheuristic with one line in `CONTENDERS` (only the new one is computed) |

Analysis and plotting code lives in the notebooks next to the figures it produces. Measurements are cached in `results/`.

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
  local_search.py       descent on the distance cost
  experiment.py         run_algorithm, run_grid (optionally parallel), results and history frames, save/load
  result.py             Result record (best mapping, history, algorithm trace)
  solution_files.py     <Group>_Challenge_<n>.txt writer (write_*_if_better never overwrites a better existing solution)
  algorithms/           identity, random_search, surrogate_filtered, ant_colony, simulated_annealing
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
