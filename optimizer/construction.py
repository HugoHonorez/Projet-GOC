"""Briques communes aux métaheuristiques constructives (colonies de fourmis, GRASP).

Notations de docs/theory/01_ant_colony.md et 02_grasp.md :
- W = (w_ij) : nombre de portes à 2 qubits entre les qubits logiques i et j ;
- ordre de construction i_1, ..., i_n ;
- g_t(u) : coût de distance ajouté en plaçant le qubit i_t sur le qubit physique libre u.
"""

import numpy as np


def interaction_weights(instance):
    """Matrice n × n du nombre de portes à 2 qubits entre chaque paire de qubits logiques (symétrique)."""
    weights = np.zeros((instance.n, instance.n))
    for (a, b), weight in zip(instance.pairs, instance.weights):
        weights[a, b] = weights[b, a] = weight
    return weights


def construction_order(weights):
    """Ordre dans lequel les qubits logiques sont placés.

    i_1 = le qubit de plus grande force str(i) = somme des w_ij ; ensuite, toujours le qubit qui a le plus
    de portes avec les qubits déjà placés (égalités départagées par la force, puis par le plus petit numéro).
    Ainsi, chaque qubit placé a déjà des partenaires sur la puce pour guider son choix.
    """
    # Force d'un qubit : son nombre total de portes à 2 qubits.
    strength = weights.sum(axis=1)
    order = [int(np.argmax(strength))]
    remaining = set(range(len(weights))) - set(order)
    while remaining:
        # Nombre de portes de chaque qubit avec ceux déjà placés.
        link = weights[:, order].sum(axis=1)
        # Choix lexicographique : plus de liens, puis plus de force, puis plus petit numéro (d'où le -q).
        chosen = max(remaining, key=lambda q: (link[q], strength[q], -q))
        order.append(chosen)
        remaining.remove(chosen)
    return order


def hardware_degree(instance):
    """Nombre de voisins de chaque qubit physique sur la puce (deg_C)."""
    return np.bincount(np.asarray(instance.edges).ravel(), minlength=instance.m)


def placed_partners(weights, qubit, mapping):
    """Partenaires de `qubit` (au moins une porte en commun) qui ont déjà un qubit physique (mapping >= 0)."""
    return np.flatnonzero((weights[qubit] > 0) & (mapping >= 0))


def added_cost(instance, weights, qubit, mapping, free):
    """g_t(u) pour chaque qubit physique libre u : somme des w_(qubit, j) × (d(u, s(j)) − 1) sur les partenaires placés.

    Renvoie None si le qubit n'a encore aucun partenaire placé (g_t serait identiquement nul).
    """
    partners = placed_partners(weights, qubit, mapping)
    if partners.size == 0:
        return None
    # Distances de chaque qubit libre aux qubits physiques des partenaires, moins 1, pondérées par les portes.
    return (instance.distances[np.ix_(free, mapping[partners])] - 1) @ weights[qubit, partners]
