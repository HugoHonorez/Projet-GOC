"""Les algorithmes disponibles. Chacun est un module avec une variable `name` et une fonction `run(problem, rng, **params)`.

Pour ajouter une métaheuristique : créer un module dans ce dossier, l'ajouter au dictionnaire ci-dessous,
puis l'ajouter au dictionnaire CONTENDERS du notebook 99_comparison.
"""

from . import ant_colony, identity, random_search, simulated_annealing, surrogate_filtered

# Correspondance nom -> fonction run, pratique pour choisir un algorithme par son nom.
ALGORITHMS = {
    identity.name: identity.run,
    random_search.name: random_search.run,
    surrogate_filtered.name: surrogate_filtered.run,
    ant_colony.name: ant_colony.run,
    simulated_annealing.name: simulated_annealing.run,
}
