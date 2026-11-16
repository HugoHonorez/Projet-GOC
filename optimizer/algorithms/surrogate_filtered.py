"""Référence « filtrage par coût de distance » : le meilleur de plusieurs placements aléatoires selon le coût gratuit.

À chaque tour : on tire `candidates` placements au hasard, on garde celui dont le coût de distance est
le plus faible (gratuit), et on ne paie qu'une vraie évaluation pour lui.
"""

from ..representation import random_permutation

name = "surrogate_filtered"


def run(problem, rng, candidates=200):
    """Boucle : tirer `candidates` permutations, évaluer seulement la meilleure selon le coût de distance."""
    while True:
        # Lot de permutations aléatoires.
        pool = [random_permutation(problem.m, rng) for _ in range(candidates)]
        # min(..., key=...) choisit celle de plus petit coût de distance ; seule elle est vraiment évaluée.
        problem.fitness_of(min(pool, key=problem.surrogate_of))
