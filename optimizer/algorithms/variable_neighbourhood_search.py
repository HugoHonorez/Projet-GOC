"""Recherche à voisinage variable, VNS (code de l'équipe : `VNS`, StudentCode (2).py), intégrée sans changer l'algorithme.

Algorithme d'origine :
- VND (`VND`) depuis un placement aléatoire ; k = 2 ;
- tant qu'il reste du temps : perturbation de la meilleure solution avec k mouvements (`perturbation`), VND,
  puis : si c'est mieux (strictement, ou ≤ avec accept_equal), on garde et k revient à 2 ;
  sinon k ← k + 1, et retour à 2 après k_max.
Fonctions de recherche locale : optimizer/fitness_local_search.py.

VND : descente sur les déplacements et les échanges, du plus petit voisinage au plus grand. Les deux conditions
erronées de la boucle de `VND` ont été corrigées (voir optimizer/fitness_local_search.py) ; sans cette correction,
VND n'évaluait que son départ et la VNS ne faisait aucune descente.

Adaptations au framework : fitness → problem.fitness ; TEMPS_MAX devient optionnel (max_seconds) : l'arrêt normal
est l'épuisement du budget d'évaluations ; hasard initialisé par la graine.

Hybridation (optimizer/hybrid) : hooks « solution » sur chaque point de départ de VND (départ aléatoire ou solution
perturbée), hooks « itération » sur le résultat de chaque VND ; initial_mapping remplace le départ aléatoire.
"""

import math
import time

from ..fitness_local_search import FitnessLocalSearch
from ..hybrid.hooks import improve_iteration, improve_solution, normalized

name = "variable_neighbourhood_search"


def run(problem, rng, k_max=5, accept_equal=False, max_seconds=None, hooks=None, initial_mapping=None):
    """Exécute `VNS`. k_max : nombre maximal de mouvements de la perturbation (5) ; accept_equal : accepte les égalités.
    Renvoie (meilleur coût, meilleur placement, nombre de tours) comme le code d'origine."""
    tools = FitnessLocalSearch(rng)
    hooks = normalized(hooks)
    n, m, fitness = problem.n, problem.m, problem.fitness
    TEMPS_MAX = math.inf if max_seconds is None else max_seconds
    trace = problem.trace
    trace.update({"rounds": []})

    def improved_start(solution):
        """Hooks « solution » appliqués au point de départ de VND."""
        return improve_solution(problem, solution, hooks, rng) if hooks["solution"] else solution

    def improved_result(solution, cost):
        """Hooks « itération » appliqués au résultat de VND."""
        return improve_iteration(problem, solution, cost, hooks, rng) if hooks["iteration"] else (solution, cost)

    start = time.time()
    end = start + TEMPS_MAX
    first = tools.random_solution(n, m)
    if initial_mapping is not None:
        first = [int(u) for u in initial_mapping]
    best, best_cost = improved_result(*tools.vnd(improved_start(first), fitness, m, end))

    k = 2
    rounds = 0
    while time.time() < end:
        rounds += 1
        candidate = tools.perturbation(best, k, n, m)
        candidate, cost = improved_result(*tools.vnd(improved_start(candidate), fitness, m, end))

        better = (cost <= best_cost) if accept_equal else (cost < best_cost)
        trace["rounds"].append({"evaluations": problem.evaluations, "k": k, "cost": int(cost), "accepted": bool(better), "best": int(min(cost, best_cost))})
        if better:
            best, best_cost = candidate, cost
            k = 2  # succès : on reste près
        else:
            k = k + 1 if k < k_max else 2  # échec : on s'éloigne

    return best_cost, best, rounds
