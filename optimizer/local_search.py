"""Recherche locale sur le coût de distance : une brique réutilisable par les métaheuristiques.

Ce n'est pas un algorithme complet (pas de budget, pas de vraie fitness) : c'est un outil qui
améliore un placement gratuitement avant de le donner à évaluer.
"""

from .representation import random_swap_indices, swap
from .surrogate import distance_cost


def surrogate_descent(instance, permutation, steps, rng):
    """Améliore une permutation par `steps` essais d'échanges aléatoires sur le coût de distance.

    À chaque essai, on échange deux positions ; on garde l'échange s'il ne dégrade pas le coût de distance
    (« <= » plutôt que « < » pour pouvoir traverser les plateaux de coût égal). Aucune vraie évaluation.
    """
    # On travaille sur une copie pour ne pas modifier la permutation reçue.
    current = permutation.copy()
    # Coût de distance du placement de départ (seuls les n premiers éléments forment le placement).
    current_cost = distance_cost(instance, current[: instance.n])
    for _ in range(steps):
        # Voisin : la permutation après un échange utile tiré au hasard.
        candidate = swap(current, *random_swap_indices(instance.n, instance.m, rng))
        cost = distance_cost(instance, candidate[: instance.n])
        # Accepté s'il n'est pas pire.
        if cost <= current_cost:
            current, current_cost = candidate, cost
    return current
