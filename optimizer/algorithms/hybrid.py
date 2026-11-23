"""Hybridation de haut niveau, mode relais : des étapes exécutées l'une après l'autre, chacune avec une part du budget.

Paramètre `stages` : liste de dictionnaires (JSON), dans l'ordre d'exécution :
- {"algorithm": nom, "params": {...}, "share": part} : une métaheuristique de ALGORITHMS
  (ses `params` peuvent contenir des `hooks`, l'hybridation de bas niveau) ;
- {"improver": nom, "params": {...}, "share": part} : une brique de optimizer.hybrid.IMPROVERS appliquée à la
  meilleure solution trouvée jusque-là (relais : la sortie d'une étape est l'entrée de la suivante).
`share` est la part du budget total B donnée à l'étape ; None = tout ce que les autres étapes ne prennent pas.
Une étape qui finit avant d'avoir utilisé sa part laisse le reste aux étapes suivantes.
Si une métaheuristique accepte un paramètre `initial_mapping` et que l'étape a "start_from_best": true,
elle démarre de la meilleure solution trouvée jusque-là.
"""

import inspect
import math

from ..hybrid.improvers import IMPROVERS
from ..problem import BudgetExhausted

name = "hybrid"


def stage_budgets(stages, total):
    """Nombre d'évaluations de chaque étape : share × B, l'étape sans share recevant le reste."""
    fixed = [stage.get("share") for stage in stages]
    free = [k for k, share in enumerate(fixed) if share is None]
    if len(free) > 1:
        raise ValueError("At most one stage may omit its share")
    budgets = [0 if share is None else int(round(share * total)) for share in fixed]
    if free:
        budgets[free[0]] = max(0, total - sum(budgets))
    return budgets


def run(problem, rng, stages):
    """Exécute les étapes en relais. La trace contient, pour chaque étape, sa trace propre et ses évaluations."""
    # Import local : le dictionnaire ALGORITHMS importe ce module (import circulaire sinon).
    from . import ALGORITHMS

    total = problem.budget if problem.budget is not None else math.inf
    if math.isinf(total):
        raise ValueError("The hybrid relay needs a finite budget to share between stages")
    budgets = stage_budgets(stages, total)
    traces = []
    # Trace commune remplacée, le temps d'une étape, par la trace propre à l'étape.
    shared_trace = problem.trace
    planned = 0
    try:
        for stage, budget in zip(stages, budgets):
            planned += budget
            start = problem.evaluations
            # Budget de l'étape : jusqu'à la fin de sa part (les parts non utilisées passent à la suite).
            problem.budget = min(total, planned)
            stage_trace = {}
            problem.trace = stage_trace
            label = stage.get("algorithm") or stage.get("improver")
            try:
                if "algorithm" in stage:
                    algorithm = ALGORITHMS[stage["algorithm"]]
                    params = dict(stage.get("params", {}))
                    if stage.get("start_from_best") and problem.best_mapping is not None and "initial_mapping" in inspect.signature(algorithm).parameters:
                        params["initial_mapping"] = list(problem.best_mapping)
                    algorithm(problem, rng, **params)
                elif problem.best_mapping is not None:
                    IMPROVERS[stage["improver"]](problem, list(problem.best_mapping), problem.best_cost, rng, **stage.get("params", {}))
            except BudgetExhausted:
                pass
            traces.append({"stage": label, "evaluations": problem.evaluations - start, "best_after": problem.best_cost, "trace": stage_trace})
    finally:
        problem.budget = total
        problem.trace = shared_trace
        problem.trace["stages"] = traces
