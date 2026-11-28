"""Briques d'amélioration réutilisables pour l'hybridation (recherches locales).

Une brique est une fonction `improver(problem, mapping, cost, rng, **params) -> (mapping, cost)` :
- `mapping` : le placement à améliorer ; `cost` : sa fitness si elle est connue, sinon None ;
- elle renvoie le placement amélioré et sa fitness (None si elle n'a pas été évaluée).
Les briques sur C sont gratuites ; les briques sur f consomment des évaluations (et peuvent déclencher BudgetExhausted).
Elles sont désignées par leur nom dans IMPROVERS, ce qui rend les hybrides décrits par de simples dictionnaires
(sérialisables en JSON, utilisables par run_grid en parallèle et par le cache des notebooks).
"""

import math

from ..construction import interaction_weights
from ..fitness_local_search import FitnessLocalSearch
from ..local_search import surrogate_descent as random_surrogate_descent
from ..local_search import surrogate_local_optimum as exact_surrogate_local_optimum
from ..representation import from_mapping, random_swap_indices, swap, to_mapping


def surrogate_local_optimum(problem, mapping, cost, rng, max_steps=10_000):
    """Descente « meilleure amélioration » sur C jusqu'à un optimum local exact (gratuite)."""
    instance = problem.instance
    permutation, _ = exact_surrogate_local_optimum(instance, interaction_weights(instance), from_mapping(mapping, instance.m), max_steps)
    improved = to_mapping(permutation, instance.n)
    # Le coût connu reste valable seulement si le placement n'a pas changé.
    return improved, cost if improved == list(mapping) else None


def surrogate_descent(problem, mapping, cost, rng, steps=200):
    """`steps` essais de transpositions aléatoires, acceptés si C ne augmente pas (gratuite)."""
    instance = problem.instance
    permutation = random_surrogate_descent(instance, from_mapping(mapping, instance.m), steps, rng)
    improved = to_mapping(permutation, instance.n)
    return improved, cost if improved == list(mapping) else None


def fitness_descent(problem, mapping, cost, rng, patience=3, neighbours=20):
    """Descente échantillonnée sur f : à chaque pas, `neighbours` voisins tirés, le meilleur selon C est évalué,
    et on s'y déplace s'il améliore f ; arrêt après `patience` échecs consécutifs. Coûte des évaluations."""
    if cost is None:
        cost = problem.fitness(mapping)
    current = from_mapping(mapping, problem.m)
    failures = 0
    while failures < patience:
        pool = [swap(current, *random_swap_indices(problem.n, problem.m, rng)) for _ in range(neighbours)]
        candidate = min(pool, key=problem.surrogate_of)
        candidate_cost = problem.fitness_of(candidate)
        if candidate_cost < cost:
            current, cost, failures = candidate, candidate_cost, 0
        else:
            failures += 1
    return to_mapping(current, problem.n), cost


##-------------------------------------------------------
##  Recherche locale sur f, en briques d'hybridation
##  Partie << recherche locale >> du projet (ccl04).
##  (Recherche_locale.py : `descente` et `VND`, via optimizer/fitness_local_search.py)
##-------------------------------------------------------


class _EvaluationLimit(Exception):
    """Levée en interne quand une brique a consommé la part d'évaluations qui lui était allouée."""


def _bounded_fitness(problem, max_evaluations):
    """`problem.fitness` borné à `max_evaluations` appels, avec mémoire du meilleur placement vu.

    Renvoie (fonction, état). La fonction lève `_EvaluationLimit` au-delà de la part allouée ;
    `état` garde le meilleur placement rencontré pendant la brique, pour pouvoir le rendre
    si la part est épuisée en cours de descente. `BudgetExhausted` (fin du budget global)
    n'est pas interceptée : elle remonte et arrête l'algorithme, comme partout ailleurs.
    """
    state = {"remaining": math.inf if max_evaluations is None else int(max_evaluations), "mapping": None, "cost": math.inf}

    def fitness(mapping):
        if state["remaining"] <= 0:
            raise _EvaluationLimit
        state["remaining"] -= 1
        cost = problem.fitness(mapping)
        if cost < state["cost"]:
            state["mapping"], state["cost"] = list(mapping), cost
        return cost

    return fitness, state


def _recherche_locale(problem, mapping, rng, method, max_evaluations):
    """Applique `descent` ou `vnd` à un placement. Consomme des évaluations.

    Les deux fonctions d'origine réévaluent toujours leur point de départ (comportement conservé),
    donc la brique coûte au moins une évaluation même si le placement est déjà un optimum local.
    """
    search = getattr(FitnessLocalSearch(rng), method)
    fitness, state = _bounded_fitness(problem, max_evaluations)
    try:
        # end = +inf : c'est la part d'évaluations, et non le temps, qui borne la brique.
        return search(list(mapping), fitness, problem.m, math.inf)
    except _EvaluationLimit:
        # Part épuisée en cours de descente : on rend le meilleur placement vu pendant la brique.
        if state["mapping"] is None:
            return list(mapping), None
        return state["mapping"], state["cost"]


def ccl04_descente(problem, mapping, cost, rng, max_evaluations=200):
    """`descente` de Recherche_locale.py : première amélioration sur le voisinage complet mélangé (échanges + déplacements).

    `max_evaluations` borne la descente : sans borne, une seule descente consomme 250 à 400 évaluations
    et dévore le budget d'une construction quand la brique est branchée sur chaque solution candidate.
    """
    return _recherche_locale(problem, mapping, rng, "descent", max_evaluations)


def ccl04_vnd(problem, mapping, cost, rng, max_evaluations=200):
    """`VND` de Recherche_locale.py : voisinages alternés, du plus petit au plus grand, retour au premier après amélioration.

    Même borne que `ccl04_descente` (voir son commentaire).
    """
    return _recherche_locale(problem, mapping, rng, "vnd", max_evaluations)


# Nom -> brique. Pour ajouter une brique : écrire la fonction ci-dessus et l'enregistrer ici.
IMPROVERS = {
    "surrogate_local_optimum": surrogate_local_optimum,
    "surrogate_descent": surrogate_descent,
    "fitness_descent": fitness_descent,
    "ccl04_descente": ccl04_descente,
    "ccl04_vnd": ccl04_vnd,
}
