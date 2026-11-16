"""Référence « identité » : évalue toujours le placement [0, 1, ..., n-1].

Comme la fitness est bruitée, son meilleur coût est le minimum de plusieurs tirages du même placement.
C'est le point zéro : une métaheuristique utile doit faire mieux.
"""

from ..representation import identity_permutation

name = "identity"


def run(problem, rng):
    """Évalue le placement identité en boucle jusqu'à la fin du budget (rng n'est pas utilisé)."""
    while True:
        problem.fitness_of(identity_permutation(problem.m))
