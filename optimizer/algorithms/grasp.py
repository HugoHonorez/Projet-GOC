"""GRASP (Greedy Randomized Adaptive Search Procedure) pour le placement de qubits.

Théorie et notations : docs/theory/02_grasp.md. Une itération :
1. construction gloutonne randomisée : les qubits logiques sont placés dans l'ordre i_1, ..., i_n ; à l'étape t,
   le coût incrémental de chaque qubit physique libre u est g_t(u) (coût de distance ajouté) et on tire u
   uniformément dans la liste restreinte de candidats (RCL) ;
2. recherche locale : descente « meilleure amélioration » sur C jusqu'à un optimum local (gratuite) ;
3. évaluation de f (1 évaluation), sauf si ce placement a déjà été évalué ;
4. optionnel : descente échantillonnée sur f autour du placement (consomme des évaluations).
Aucune mémoire d'une itération à l'autre (multi-départ indépendant).
"""

import numpy as np

from ..construction import added_cost, construction_order, hardware_degree, interaction_weights
from ..local_search import surrogate_local_optimum
from ..representation import from_mapping, random_swap_indices, swap, to_mapping

name = "grasp"


class Constructor:
    """Données fixes de la construction (W, ordre, degrés de la puce) et construction d'une solution."""

    def __init__(self, instance):
        self.instance = instance
        self.weights = interaction_weights(instance)
        self.order = construction_order(self.weights)
        self.degree = hardware_degree(instance)

    def incremental_costs(self, qubit, mapping, free):
        """c_t(u) pour chaque u libre : g_t(u), ou max deg_C − deg_C(u) si le qubit n'a aucun partenaire placé."""
        cost = added_cost(self.instance, self.weights, qubit, mapping, free)
        if cost is None:
            # Pas de partenaire placé : on favorise les qubits physiques les plus connectés (centralité).
            return (self.degree.max() - self.degree[free]).astype(float)
        return cost

    @staticmethod
    def restricted_list(costs, alpha, rcl, cardinality, rng):
        """Indices (dans `costs`) des candidats de la RCL.

        - rcl="value" : c ≤ c_min + alpha × (c_max − c_min) (cours) ;
        - rcl="cardinality" : les `cardinality` plus petits coûts (égalités départagées au hasard).
        """
        if rcl == "value":
            threshold = costs.min() + alpha * (costs.max() - costs.min())
            # Petite tolérance numérique pour ne pas exclure un coût égal au seuil.
            return np.flatnonzero(costs <= threshold + 1e-9)
        # Mélange aléatoire puis tri stable : à coût égal, l'ordre est aléatoire.
        shuffled = rng.permutation(len(costs))
        ranked = shuffled[np.argsort(costs[shuffled], kind="stable")]
        return ranked[: max(1, min(cardinality, len(costs)))]

    def construct(self, rng, alpha, rcl="value", cardinality=3, record=False):
        """Construit un placement ; avec record=True, renvoie aussi le détail de chaque étape."""
        n, m = self.instance.n, self.instance.m
        # -1 = qubit logique pas encore placé ; used[u] = qubit physique u déjà occupé.
        mapping = np.full(n, -1)
        used = np.zeros(m, dtype=bool)
        steps = []
        for qubit in self.order:
            free = np.flatnonzero(~used)
            costs = self.incremental_costs(qubit, mapping, free)
            candidates = self.restricted_list(costs, alpha, rcl, cardinality, rng)
            # Tirage uniforme dans la RCL.
            choice = int(free[candidates[rng.integers(len(candidates))]])
            if record:
                steps.append({"qubit": int(qubit), "free": free.copy(), "costs": costs.copy(), "rcl": free[candidates].copy(), "choice": choice})
            mapping[qubit] = choice
            used[choice] = True
        return [int(u) for u in mapping], steps


def fitness_descent(problem, start_mapping, start_cost, rng, patience, neighbours):
    """Descente échantillonnée sur f : à chaque pas, on tire `neighbours` voisins, on évalue le meilleur selon C,
    on s'y déplace s'il améliore f ; arrêt après `patience` échecs consécutifs (ou budget épuisé).
    Renvoie (placement final, coût, nombre d'évaluations utilisées)."""
    current = from_mapping(start_mapping, problem.m)
    current_cost = start_cost
    failures = used = 0
    while failures < patience:
        pool = [swap(current, *random_swap_indices(problem.n, problem.m, rng)) for _ in range(neighbours)]
        candidate = min(pool, key=problem.surrogate_of)
        cost = problem.fitness_of(candidate)
        used += 1
        if cost < current_cost:
            current, current_cost, failures = candidate, cost, 0
        else:
            failures += 1
    return to_mapping(current, problem.n), current_cost, used


def run(problem, rng, alpha=0.2, rcl="value", cardinality=3, local_search=True, fitness_patience=0, fitness_neighbours=20, max_skips=50):
    """Exécute GRASP jusqu'à épuisement du budget.

    Paramètres :
    - alpha : taux d'acceptation de la RCL par valeur (0 = glouton, 1 = aléatoire) ;
    - rcl : "value" (seuil alpha) ou "cardinality" (les `cardinality` meilleurs) ;
    - local_search : descente sur C jusqu'à l'optimum local après chaque construction ;
    - fitness_patience : > 0 active la descente échantillonnée sur f (arrêt après ce nombre d'échecs consécutifs) ;
    - fitness_neighbours : voisins tirés à chaque pas de cette descente (le meilleur selon C est évalué) ;
    - max_skips : nombre maximal d'itérations consécutives sautées parce que le placement était déjà évalué
      (au-delà, on le réévalue : utile quand alpha est petit et que les constructions se répètent).
    """
    instance = problem.instance
    constructor = Constructor(instance)
    evaluated = set()
    trace = problem.trace
    trace.update({"order": constructor.order, "iterations": []})
    skips = 0
    iteration = 0
    # Boucle infinie : elle s'arrête quand problem.fitness lève BudgetExhausted.
    while True:
        iteration += 1
        # 1. Construction gloutonne randomisée (gratuite).
        mapping, steps = constructor.construct(rng, alpha, rcl, cardinality, record=True)
        constructed_cost = problem.surrogate(mapping)
        # 2. Recherche locale sur C (gratuite).
        descent_steps = 0
        if local_search:
            permutation, descent_steps = surrogate_local_optimum(instance, constructor.weights, from_mapping(mapping, instance.m))
            mapping = to_mapping(permutation, instance.n)
        key = tuple(mapping)
        record = {
            "iteration": iteration,
            "constructed_surrogate": int(constructed_cost),
            "local_optimum_surrogate": int(problem.surrogate(mapping)),
            "descent_steps": int(descent_steps),
            "mean_rcl_size": float(np.mean([len(s["rcl"]) for s in steps])),
            "duplicate": key in evaluated,
        }
        # Placement déjà évalué : on passe à l'itération suivante sans consommer de budget (dans la limite de max_skips).
        if key in evaluated and skips < max_skips:
            skips += 1
            trace["iterations"].append({**record, "evaluations": problem.evaluations, "cost": None, "final_cost": None})
            continue
        skips = 0
        evaluated.add(key)
        # 3. Vraie évaluation.
        cost = problem.fitness(mapping)
        final_cost, extra = cost, 0
        # 4. Descente optionnelle sur f.
        if fitness_patience > 0:
            mapping, final_cost, extra = fitness_descent(problem, mapping, cost, rng, fitness_patience, fitness_neighbours)
        trace["iterations"].append({**record, "evaluations": problem.evaluations, "cost": int(cost), "final_cost": int(final_cost), "fitness_descent_evaluations": int(extra)})
