"""Représentation des solutions et mouvements de base (voisinage par échange).

Un placement (« mapping ») est une liste de n entiers distincts : `mapping[i]` = qubit physique du qubit logique i.

Pour simplifier les métaheuristiques, on travaille souvent avec une **permutation** de range(m) :
ses n premiers éléments forment le placement, les m - n suivants sont les qubits physiques libres.
Ainsi toute permutation donne un placement valide, et échanger deux positions reste toujours valide.
"""

import numpy as np


class InvalidMapping(ValueError):
    """Erreur levée quand un placement ne respecte pas les règles (taille, doublons, valeurs hors puce)."""


def identity_permutation(m):
    """Permutation identité [0, 1, ..., m-1] : le qubit logique i va sur le qubit physique i."""
    return np.arange(m)


def random_permutation(m, rng):
    """Permutation aléatoire de range(m), tirée avec le générateur `rng`."""
    return rng.permutation(m)


def to_mapping(permutation, n):
    """Placement correspondant à une permutation : ses n premiers éléments, en entiers Python."""
    return [int(p) for p in permutation[:n]]


def from_mapping(mapping, m):
    """Permutation complète à partir d'un placement : le placement, puis les qubits physiques libres dans l'ordre."""
    used = set(mapping)
    return np.array(list(mapping) + [p for p in range(m) if p not in used])


def validate_mapping(mapping, n, m):
    """Vérifie les règles du sujet : exactement n valeurs, entre 0 et m - 1, toutes différentes."""
    if len(mapping) != n:
        raise InvalidMapping(f"Mapping must contain {n} values, got {len(mapping)}")
    if any(not 0 <= p < m for p in mapping):
        raise InvalidMapping(f"Mapping values must be in 0..{m - 1}")
    # Un ensemble (set) supprime les doublons : s'il est plus petit que n, une valeur est répétée.
    if len(set(mapping)) != n:
        raise InvalidMapping("Mapping values must be distinct")


def swap(permutation, i, j):
    """Copie de la permutation où les positions i et j sont échangées (l'original n'est pas modifié)."""
    result = permutation.copy()
    result[i], result[j] = result[j], result[i]
    return result


def random_swap_indices(n, m, rng):
    """Tire un échange utile (i, j) : i parmi les n positions du placement, j n'importe où ailleurs (j != i).

    - si j < n : on échange les qubits physiques de deux qubits logiques ;
    - si j >= n : on déplace un qubit logique vers un qubit physique libre.
    """
    i = int(rng.integers(n))
    # On tire j parmi m - 1 valeurs, puis on saute i (si j >= i, on décale de 1) pour garantir j != i.
    j = int(rng.integers(m - 1))
    return i, j + (j >= i)


def random_swap(permutation, n, rng):
    """Voisin aléatoire : la permutation après un échange utile tiré au hasard."""
    return swap(permutation, *random_swap_indices(n, len(permutation), rng))


def swap_moves(n, m):
    """Tous les échanges utiles (i, j) avec i < n et i < j : le voisinage complet d'une permutation."""
    for i in range(n):
        for j in range(i + 1, m):
            yield i, j
