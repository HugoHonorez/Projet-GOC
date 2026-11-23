"""Recherche locale itérée, ILS (code de l'équipe : `ILS`, StudentCode (2).py), intégrée sans changer l'algorithme.

Algorithme d'origine :
- descente « première amélioration » sur f (`descente`) depuis un placement aléatoire ;
- puis, tant qu'il reste du temps : perturbation de la meilleure solution (k mouvements aléatoires, `perturbation`),
  descente, et acceptation si le nouvel optimum local n'est pas pire (≤) que le meilleur.
Fonctions de recherche locale : optimizer/fitness_local_search.py.

Adaptations au framework : fitness → problem.fitness ; TEMPS_MAX devient optionnel (max_seconds) : l'arrêt normal
est l'épuisement du budget d'évaluations ; hasard initialisé par la graine.

Hybridation (optimizer/hybrid) : hooks « solution » sur chaque point de départ d'une descente (départ aléatoire ou
solution perturbée), hooks « itération » sur l'optimum local de chaque descente ; initial_mapping remplace le départ aléatoire.
"""

import math
import time

import numpy as np

from ..fitness_local_search import FitnessLocalSearch
from ..hybrid.hooks import improve_iteration, improve_solution, normalized

name = "iterated_local_search"


def run(problem, rng, k=3, max_seconds=None, hooks=None, initial_mapping=None):
    """Exécute `ILS`. k : nombre de mouvements de la perturbation (3 dans le script d'origine).
    Renvoie (meilleur coût, meilleur placement) comme le code d'origine."""
    tools = FitnessLocalSearch(rng)
    hooks = normalized(hooks)
    n, m, fitness = problem.n, problem.m, problem.fitness
    TEMPS_MAX = math.inf if max_seconds is None else max_seconds
    trace = problem.trace
    trace.update({"descents": []})

    def improved_start(solution):
        """Hooks « solution » appliqués au point de départ d'une descente."""
        return improve_solution(problem, solution, hooks, rng) if hooks["solution"] else solution

    def improved_optimum(solution, cost):
        """Hooks « itération » appliqués à l'optimum local d'une descente."""
        return improve_iteration(problem, solution, cost, hooks, rng) if hooks["iteration"] else (solution, cost)

    start = time.time()
    best_start = []
    best_cost = np.inf
    temp = tools.random_solution(n, m)
    if initial_mapping is not None:
        temp = [int(u) for u in initial_mapping]
    opti_temp, cost_temp = improved_optimum(*tools.descent(improved_start(temp), fitness, m, start + TEMPS_MAX))
    best_start = opti_temp
    best_cost = cost_temp
    trace["descents"].append({"evaluations": problem.evaluations, "local_optimum": int(cost_temp), "accepted": True, "best": int(best_cost)})

    while time.time() - start < TEMPS_MAX:
        new_list = tools.perturbation(best_start, k, n, m)
        new_opt, new_cost = improved_optimum(*tools.descent(improved_start(new_list), fitness, m, start + TEMPS_MAX))
        accepted = new_cost <= best_cost
        if new_cost <= best_cost:
            best_cost = new_cost
            best_start = new_opt
        trace["descents"].append({"evaluations": problem.evaluations, "local_optimum": int(new_cost), "accepted": bool(accepted), "best": int(best_cost)})
    return best_cost, best_start
