"""Recherche locale sur le coût de distance : une brique réutilisable par les métaheuristiques.

Ce n'est pas un algorithme complet (pas de budget, pas de vraie fitness) : c'est un outil qui
améliore un placement gratuitement avant de le donner à évaluer.
"""

import numpy as np

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


def surrogate_move_deltas(instance, weights, permutation):
    """ΔC de tous les mouvements du voisinage par transposition, calculés d'un coup (docs/theory/00, section 0.8).

    Avec s = permutation[:n] et A = W · D[s, :] (A[i, v] = somme des w_ik × d(v, s(k)), coût de i s'il était sur v) :
    - déplacement de i vers un qubit physique libre v : ΔC = A[i, v] − A[i, s(i)] ;
    - échange des qubits logiques a et b : ΔC = A[a, s(b)] − A[a, s(a)] + A[b, s(a)] − A[b, s(b)] + 2 w_ab d(s(a), s(b))
      (le dernier terme corrige l'arête {a, b}, dont la distance ne change pas).
    Renvoie (swaps, moves) : matrice n × n des échanges et matrice n × (m − n) des déplacements vers les libres.
    """
    n = instance.n
    mapping = np.asarray(permutation[:n])
    free = np.asarray(permutation[n:])
    # A[i, v] : coût de distance des arêtes de i si i était placé sur v (les autres qubits restant en place).
    cost_at = weights @ instance.distances[mapping, :]
    current = cost_at[np.arange(n), mapping]
    # B[a, b] = A[a, s(b)].
    cost_at_partner = cost_at[:, mapping]
    swaps = cost_at_partner + cost_at_partner.T - current[:, None] - current[None, :] + 2 * weights * instance.distances[np.ix_(mapping, mapping)]
    # Échanger un qubit avec lui-même n'est pas un mouvement.
    np.fill_diagonal(swaps, np.inf)
    moves = cost_at[:, free] - current[:, None] if free.size else np.zeros((n, 0))
    return swaps, moves


def surrogate_local_optimum(instance, weights, permutation, max_steps=10_000):
    """Descente « meilleure amélioration » sur C jusqu'à un optimum local du voisinage par transposition.

    À chaque pas, on applique le mouvement de plus petit ΔC s'il est strictement négatif ; sinon, la permutation
    est un minimum local de C (aucun voisin ne fait mieux). Renvoie (permutation, nombre de pas effectués).
    """
    current = np.array(permutation)
    n = instance.n
    for step in range(max_steps):
        swaps, moves = surrogate_move_deltas(instance, weights, current)
        best_swap = np.unravel_index(np.argmin(swaps), swaps.shape)
        best_move = np.unravel_index(np.argmin(moves), moves.shape) if moves.size else None
        swap_delta = swaps[best_swap]
        move_delta = moves[best_move] if best_move is not None else np.inf
        # Optimum local : aucun mouvement n'améliore strictement C.
        if min(swap_delta, move_delta) >= -1e-9:
            return current, step
        if swap_delta <= move_delta:
            a, b = best_swap
        else:
            # Position dans la permutation du qubit physique libre visé : n + indice parmi les libres.
            a, b = best_move[0], n + best_move[1]
        current[a], current[b] = current[b], current[a]
    return current, max_steps
