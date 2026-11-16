"""Chargement d'une instance sous une forme pratique pour les calculs (tableaux NumPy).

`load_instance(numéro)` renvoie un objet `InstanceData` qui contient tout ce dont une métaheuristique a besoin :
le circuit, la puce, les paires de qubits qui interagissent et la matrice des distances entre qubits physiques.
"""

from collections import deque
from dataclasses import dataclass
from functools import cache

import numpy as np

from goc import circuit_data, hardware, source_bridge
from goc.paths import find_instances_dir


# frozen=True : l'objet ne peut plus être modifié après création (évite les modifications accidentelles).
# eq=False : deux instances sont comparées par identité (comparer des tableaux NumPy champ par champ n'aurait pas de sens).
@dataclass(frozen=True, eq=False)
class InstanceData:
    """Toutes les données d'une instance, prêtes pour les calculs."""

    instance_id: int  # numéro de l'instance (1 à 9)
    n: int  # nombre de qubits logiques (dans le circuit)
    m: int  # nombre de qubits physiques (sur la puce)
    circuit: object  # circuit Qiskit, utilisé par la fitness
    backend: object  # puce Qiskit, utilisée par la fitness
    edges: tuple  # connexions physiques de la puce : paires (a, b)
    pairs: np.ndarray  # tableau (k, 2) : les k paires de qubits logiques qui interagissent
    weights: np.ndarray  # tableau (k,) : nombre de portes à 2 qubits de chaque paire
    distances: np.ndarray  # tableau (m, m) : distance (en nombre de connexions) entre deux qubits physiques
    logical_depth: int  # profondeur du circuit avant routage

    @property
    def two_qubit_gates(self):
        """Nombre total de portes à 2 qubits du circuit."""
        return int(self.weights.sum())

    @property
    def hardware_name(self):
        """Nom de la puce (par ex. « fake_20q_v1 »)."""
        return self.backend.name

    def degrees(self):
        """Degré de chaque qubit logique : nombre de partenaires différents avec lesquels il interagit."""
        degree = np.zeros(self.n, dtype=int)
        # pairs.ravel() aplatit les paires en une seule liste de qubits ; chaque apparition ajoute 1 au degré.
        np.add.at(degree, self.pairs.ravel(), 1)
        return degree


def distance_matrix(m, edges):
    """Distance entre chaque paire de qubits physiques = plus petit nombre de connexions à traverser.

    Calculée par un parcours en largeur (BFS) depuis chaque qubit. La distance 1 signifie « voisins ».
    """
    # Liste des voisins de chaque qubit physique.
    neighbours = [[] for _ in range(m)]
    for a, b in edges:
        neighbours[a].append(b)
        neighbours[b].append(a)
    # m + 1 sert de valeur « pas encore atteint » (aucune distance réelle ne peut dépasser m - 1).
    distances = np.full((m, m), m + 1, dtype=int)
    for source in range(m):
        distances[source, source] = 0
        # File d'attente du parcours en largeur : on visite les qubits par distance croissante.
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for v in neighbours[u]:
                # Si v n'a pas encore été atteint, sa distance est celle de u plus une connexion.
                if distances[source, v] > m:
                    distances[source, v] = distances[source, u] + 1
                    queue.append(v)
    return distances


# @cache : le résultat est gardé en mémoire ; charger deux fois la même instance ne coûte rien la deuxième fois.
@cache
def load_instance(instance_id):
    """Charge l'instance avec le code du cours et prépare toutes ses données de calcul."""
    # Chargement officiel via source.py (la puce, le circuit, n et m).
    backend, circuit, n, m = source_bridge.load_instance(instance_id)
    # Connexions physiques de la puce.
    edges = tuple(hardware.coupling_edges(backend))
    # Paires de qubits logiques qui interagissent, avec leur nombre de portes.
    interactions = circuit_data.interactions(circuit)
    # Conversion en tableaux NumPy (reshape(-1, 2) garde la bonne forme même s'il n'y a aucune paire).
    pairs = np.array([[i["a"], i["b"]] for i in interactions], dtype=int).reshape(-1, 2)
    weights = np.array([i["count"] for i in interactions], dtype=int)
    return InstanceData(
        instance_id=instance_id,
        n=n,
        m=m,
        circuit=circuit,
        backend=backend,
        edges=edges,
        pairs=pairs,
        weights=weights,
        distances=distance_matrix(m, edges),
        logical_depth=circuit.depth(),
    )


def available_instances():
    """Numéros des instances dont le fichier QASM existe et que source.py sait charger."""
    directory = find_instances_dir()
    return [i for i in source_bridge.SUPPORTED_INSTANCES if (directory / f"Instance_{i}.qasm").exists()]
