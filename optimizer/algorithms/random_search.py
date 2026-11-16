"""Référence « recherche aléatoire » : évalue des placements tirés au hasard.

C'est la référence minimale : une métaheuristique qui ne la bat pas, à budget égal, n'apporte rien.
"""

from ..representation import random_permutation

name = "random_search"


def run(problem, rng):
    """Tire une permutation aléatoire et l'évalue, en boucle jusqu'à la fin du budget."""
    while True:
        problem.fitness_of(random_permutation(problem.m, rng))
