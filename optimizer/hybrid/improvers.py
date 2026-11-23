"""Briques d'amélioration réutilisables pour l'hybridation (recherches locales).

Une brique est une fonction `improver(problem, mapping, cost, rng, **params) -> (mapping, cost)` :
- `mapping` : le placement à améliorer ; `cost` : sa fitness si elle est connue, sinon None ;
- elle renvoie le placement amélioré et sa fitness (None si elle n'a pas été évaluée).
Les briques sur C sont gratuites ; les briques sur f consomment des évaluations (et peuvent déclencher BudgetExhausted).
Elles sont désignées par leur nom dans IMPROVERS, ce qui rend les hybrides décrits par de simples dictionnaires
(sérialisables en JSON, utilisables par run_grid en parallèle et par le cache des notebooks).
"""

from ..construction import interaction_weights
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


# Nom -> brique. Pour ajouter une brique : écrire la fonction ci-dessus et l'enregistrer ici.
IMPROVERS = {
    "surrogate_local_optimum": surrogate_local_optimum,
    "surrogate_descent": surrogate_descent,
    "fitness_descent": fitness_descent,
}
