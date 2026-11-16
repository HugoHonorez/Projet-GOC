"""Coût de distance : une estimation instantanée de la qualité d'un placement (« surrogate » = substitut).

Idée : une porte à 2 qubits est directe si ses deux qubits sont voisins sur la puce (distance 1) ;
sinon le routage doit ajouter des SWAP, d'autant plus que la distance est grande.

    coût de distance = somme sur les paires (i, j) qui interagissent de : nombre de portes(i, j) × (distance(i, j) − 1)

Il vaut 0 quand toutes les portes à 2 qubits sont directes. Il se calcule en quelques microsecondes,
contre environ 0,1 s pour la vraie fitness, mais ce n'est qu'une approximation (voir le notebook 02).
"""

import numpy as np


def pair_distances(instance, mapping):
    """Distance sur la puce entre les qubits physiques de chaque paire qui interagit, avec ce placement."""
    mapping = np.asarray(mapping)
    # mapping[pairs[:, 0]] : qubit physique du premier qubit de chaque paire ; idem pour le second.
    # On lit ensuite leur distance dans la matrice des distances (indexation NumPy vectorisée, sans boucle).
    return instance.distances[mapping[instance.pairs[:, 0]], mapping[instance.pairs[:, 1]]]


def distance_cost(instance, mapping):
    """Coût de distance du placement : somme des (portes × (distance − 1))."""
    # np.dot fait la somme des produits poids × (distance − 1) sur toutes les paires.
    return int(np.dot(instance.weights, pair_distances(instance, mapping) - 1))


def direct_gate_ratio(instance, mapping):
    """Part des portes à 2 qubits déjà directes (qubits voisins) avec ce placement, entre 0 et 1."""
    total = instance.weights.sum()
    # Circuit sans porte à 2 qubits : tout est direct.
    if total == 0:
        return 1.0
    # Somme des poids des paires dont la distance vaut 1, divisée par le total.
    return float(instance.weights[pair_distances(instance, mapping) == 1].sum() / total)
