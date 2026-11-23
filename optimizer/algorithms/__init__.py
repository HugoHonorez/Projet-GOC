"""Les algorithmes disponibles. Chacun est un module avec une variable `name` et une fonction `run(problem, rng, **params)`.

Pour ajouter une métaheuristique : créer un module dans ce dossier, l'ajouter au dictionnaire ci-dessous,
puis l'ajouter au dictionnaire CONTENDERS du notebook 99_comparison.
Pour l'hybridation (hooks et relais d'étapes) : voir optimizer/hybrid/ et le notebook 07_hybridization.
"""

from . import ant_colony, genetic, grasp, hybrid, identity, random_search, surrogate_filtered
# Algorithmes de l'équipe, intégrés sans changer leur logique (voir l'en-tête de chaque module).
from . import bee_colony, iterated_local_search, multi_start, pso_de, simulated_annealing, tabu_search, variable_neighbourhood_search

# Correspondance nom -> fonction run, pratique pour choisir un algorithme par son nom.
ALGORITHMS = {
    identity.name: identity.run,
    random_search.name: random_search.run,
    surrogate_filtered.name: surrogate_filtered.run,
    ant_colony.name: ant_colony.run,
    grasp.name: grasp.run,
    genetic.name: genetic.run,
    simulated_annealing.name: simulated_annealing.run,
    pso_de.name: pso_de.run,
    bee_colony.name: bee_colony.run,
    tabu_search.name: tabu_search.run,
    multi_start.name: multi_start.run,
    iterated_local_search.name: iterated_local_search.run,
    variable_neighbourhood_search.name: variable_neighbourhood_search.run,
    # Relais d'étapes (hybridation de haut niveau) ; voir optimizer/hybrid/.
    hybrid.name: hybrid.run,
}
