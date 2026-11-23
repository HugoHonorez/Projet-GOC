"""Recherche locale à départs multiples (code de l'équipe : `multi_depart`, StudentCode (2).py), intégrée sans changer
l'algorithme.

Algorithme d'origine : tant qu'il reste du temps, un départ aléatoire (`solution_aleatoire`) suivi d'une descente
« première amélioration » sur f (`descente`, optimizer/fitness_local_search.py) ; on garde le meilleur optimum local.

Adaptations au framework : fitness → problem.fitness ; TEMPS_MAX devient optionnel (max_seconds) : l'arrêt normal
est l'épuisement du budget d'évaluations ; hasard initialisé par la graine.

Hybridation (optimizer/hybrid) : hooks « solution » sur chaque départ avant sa descente, hooks « itération » sur
l'optimum local de chaque descente ; initial_mapping remplace le premier départ aléatoire.
"""

import math
import time

import numpy as np

from ..fitness_local_search import FitnessLocalSearch
from ..hybrid.hooks import improve_iteration, improve_solution, normalized

name = "multi_start"


def run(problem, rng, max_seconds=None, hooks=None, initial_mapping=None):
    """Exécute `multi_depart`. Renvoie (meilleur coût, meilleur placement) comme le code d'origine."""
    tools = FitnessLocalSearch(rng)
    hooks = normalized(hooks)
    n, m, fitness = problem.n, problem.m, problem.fitness
    TEMPS_MAX = math.inf if max_seconds is None else max_seconds
    trace = problem.trace
    trace.update({"descents": []})

    start = time.time()

    best_start = []
    best_cost = np.inf

    while time.time() - start < TEMPS_MAX:
        temp = tools.random_solution(n, m)
        if initial_mapping is not None and not trace["descents"]:
            temp = [int(u) for u in initial_mapping]
        if hooks["solution"]:
            temp = improve_solution(problem, temp, hooks, rng)
        opti_temp, cost_temp = tools.descent(temp, fitness, m, start + TEMPS_MAX)
        if hooks["iteration"]:
            opti_temp, cost_temp = improve_iteration(problem, opti_temp, cost_temp, hooks, rng)
        if cost_temp < best_cost:
            best_cost = cost_temp
            best_start = opti_temp
        trace["descents"].append({"evaluations": problem.evaluations, "local_optimum": int(cost_temp), "best": int(best_cost)})
    return best_cost, best_start
