"""La classe `Problem` : ce qu'une métaheuristique manipule pendant une exécution.

Elle donne accès à la vraie fitness (coûteuse, comptée dans un budget) et au coût de distance (gratuit),
et enregistre automatiquement l'historique et la meilleure solution trouvée.
"""

import math
import time

import pandas as pd

from goc import source_bridge

from .representation import to_mapping, validate_mapping
from .surrogate import distance_cost


class BudgetExhausted(Exception):
    """Exception levée quand on demande une évaluation alors que le budget est épuisé.

    Elle interrompt l'algorithme ; `run_algorithm` l'attrape. Un algorithme n'a donc pas besoin de la gérer.
    """


class Problem:
    """Une instance + un budget d'évaluations + le suivi de la recherche."""

    def __init__(self, instance, budget=None):
        # Données de l'instance (circuit, puce, paires, distances).
        self.instance = instance
        # Nombre maximal de vraies évaluations (None = illimité).
        self.budget = budget
        # Remise à zéro des compteurs et de l'historique.
        self.reset()

    @property
    def n(self):
        """Nombre de qubits logiques."""
        return self.instance.n

    @property
    def m(self):
        """Nombre de qubits physiques."""
        return self.instance.m

    @property
    def remaining(self):
        """Nombre d'évaluations encore disponibles (infini si pas de budget)."""
        return math.inf if self.budget is None else self.budget - self.evaluations

    @property
    def exhausted(self):
        """Vrai quand le budget est entièrement consommé."""
        return self.remaining <= 0

    @property
    def elapsed(self):
        """Temps écoulé (en secondes) depuis le début de l'exécution."""
        return time.perf_counter() - self.started

    def reset(self):
        """Remet le problème dans son état de départ."""
        self.evaluations = 0  # nombre de vraies évaluations déjà faites
        self.best_cost = math.inf  # meilleure fitness vue jusqu'ici
        self.best_mapping = None  # placement correspondant
        self.history = []  # une entrée par évaluation : (numéro, coût, meilleur coût, temps)
        self.trace = {}  # informations libres que l'algorithme veut garder (phéromones, diversité...)
        self.started = time.perf_counter()  # instant de départ, pour mesurer le temps

    def fitness(self, mapping):
        """Vraie fitness d'un placement (appel à source.fitness_inner). Coûte 1 évaluation du budget."""
        # Plus de budget : on arrête l'algorithme.
        if self.exhausted:
            raise BudgetExhausted
        # Conversion en liste d'entiers Python (le placement peut arriver sous forme de tableau NumPy).
        mapping = [int(p) for p in mapping]
        # Vérifie que le placement est valide : n valeurs, toutes différentes, entre 0 et m - 1.
        validate_mapping(mapping, self.n, self.m)
        # Appel au code du cours : profondeur du circuit après routage.
        cost = source_bridge.fitness(mapping, self.instance.circuit, self.instance.backend)
        self.evaluations += 1
        # Mise à jour de la meilleure solution si ce placement fait mieux.
        if cost < self.best_cost:
            self.best_cost = cost
            self.best_mapping = mapping
        # Enregistrement dans l'historique (sert aux courbes de convergence).
        self.history.append((self.evaluations, cost, self.best_cost, self.elapsed))
        return cost

    def fitness_of(self, permutation):
        """Comme `fitness`, mais à partir d'une permutation de range(m) : ses n premiers éléments forment le placement."""
        return self.fitness(to_mapping(permutation, self.n))

    def fitness_samples(self, mapping, runs):
        """Évalue le même placement plusieurs fois (utile pour mesurer le bruit). Coûte `runs` évaluations."""
        return [self.fitness(mapping) for _ in range(runs)]

    def surrogate(self, mapping):
        """Coût de distance d'un placement : estimation instantanée, gratuite (ne consomme pas de budget)."""
        return distance_cost(self.instance, mapping)

    def surrogate_of(self, permutation):
        """Coût de distance à partir d'une permutation (seuls les n premiers éléments comptent)."""
        return distance_cost(self.instance, permutation[: self.n])

    def history_frame(self):
        """Historique sous forme de tableau pandas : une ligne par évaluation."""
        return pd.DataFrame(self.history, columns=["evaluation", "cost", "best", "seconds"])
