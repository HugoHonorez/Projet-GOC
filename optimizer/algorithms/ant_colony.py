"""Optimisation par colonies de fourmis (variante MAX-MIN Ant System) pour le placement de qubits.

Principe :
- une matrice de phéromones `pheromone[i, p]` (taille n × m) mémorise l'intérêt de placer le qubit logique i
  sur le qubit physique p ; c'est la mémoire collective de la colonie ;
- chaque fourmi construit un placement qubit par qubit, en choisissant un qubit physique libre p avec une
  probabilité proportionnelle à pheromone[i, p]^alpha × heuristique(p)^beta ;
- les fourmis sont classées par coût de distance (gratuit) et seules les meilleures sont vraiment évaluées ;
- les phéromones s'évaporent, puis la meilleure fourmi de l'itération et la meilleure solution globale en déposent ;
- les phéromones sont bornées entre tau_min et tau_max pour qu'aucun choix ne devienne impossible.
"""

import math

import numpy as np

# Ordre de construction et matrice W : partagés avec GRASP (optimizer/construction.py).
from ..construction import construction_order, hardware_degree, interaction_weights
from ..local_search import surrogate_descent
from ..representation import from_mapping, to_mapping

name = "ant_colony"


class Colony:
    """Les informations fixes de la colonie (ordre de placement, heuristique) et la construction d'une fourmi."""

    def __init__(self, instance, alpha=1.0, beta=2.0):
        self.instance = instance
        self.alpha = alpha  # poids des phéromones (la mémoire de la colonie)
        self.beta = beta  # poids de l'heuristique (l'information locale sur les distances)
        self.weights = interaction_weights(instance)
        self.order = construction_order(self.weights)
        # Nombre de voisins de chaque qubit physique, normalisé entre 0 et 1 : la « centralité ».
        degree = hardware_degree(instance)
        self.centrality = degree / degree.max()

    def heuristic(self, qubit, mapping, free):
        """Attractivité de chaque qubit physique libre pour placer `qubit`, d'après les partenaires déjà placés.

        heuristique(p) = 1 / (1 + somme sur les partenaires j déjà placés de : portes(qubit, j) × (distance(p, p_j) − 1))
        Elle vaut 1 si p est voisin de tous ses partenaires, et diminue quand p s'en éloigne.
        Sans partenaire déjà placé (premier qubit), on favorise les qubits physiques les plus connectés.
        """
        # Partenaires du qubit (au moins une porte en commun) qui ont déjà un qubit physique (mapping >= 0).
        partners = np.flatnonzero((self.weights[qubit] > 0) & (mapping >= 0))
        if partners.size == 0:
            return self.centrality[free]
        # Pour chaque qubit libre p : distances vers les qubits physiques des partenaires, moins 1, pondérées par les portes.
        extra = (self.instance.distances[np.ix_(free, mapping[partners])] - 1) @ self.weights[qubit, partners]
        return 1.0 / (1.0 + extra)

    def probabilities(self, pheromone, qubit, mapping, free):
        """Probabilité de choisir chaque qubit physique libre : proportionnelle à phéromone^alpha × heuristique^beta."""
        desirability = pheromone[qubit, free] ** self.alpha * self.heuristic(qubit, mapping, free) ** self.beta
        # Division par la somme pour que les probabilités totalisent 1.
        return desirability / desirability.sum()

    def construct(self, pheromone, rng, record=False):
        """Construit le placement d'une fourmi. Avec record=True, garde le détail de chaque étape (pour les graphiques)."""
        # -1 = qubit logique pas encore placé.
        mapping = np.full(self.instance.n, -1)
        # used[p] = True si le qubit physique p est déjà occupé.
        used = np.zeros(self.instance.m, dtype=bool)
        steps = []
        for qubit in self.order:
            # Qubits physiques encore libres.
            free = np.flatnonzero(~used)
            probabilities = self.probabilities(pheromone, qubit, mapping, free)
            # Tirage au sort d'un qubit libre selon ces probabilités.
            choice = int(free[rng.choice(free.size, p=probabilities)])
            if record:
                steps.append({"qubit": qubit, "free": free.copy(), "probabilities": probabilities, "choice": choice, "mapping": mapping.copy()})
            mapping[qubit] = choice
            used[choice] = True
        return [int(p) for p in mapping], steps


def pheromone_bounds(rho, tau_min_ratio):
    """Bornes des phéromones : tau_max = 1 / rho (niveau d'équilibre d'un dépôt de 1 par itération), tau_min = une fraction de tau_max."""
    tau_max = 1.0 / rho
    return tau_max * tau_min_ratio, tau_max


def deposit(pheromone, mapping, amount):
    """Ajoute `amount` de phéromone sur chaque case (i, mapping[i]) utilisée par le placement."""
    pheromone[np.arange(len(mapping)), mapping] += amount


def normalized_entropy(pheromone):
    """Mesure de convergence des phéromones : 1 = aucune préférence (uniforme), 0 = un seul choix par qubit.

    Pour chaque ligne (qubit logique), on transforme les phéromones en probabilités, on calcule leur entropie,
    on fait la moyenne et on divise par l'entropie maximale log(m).
    """
    probabilities = pheromone / pheromone.sum(axis=1, keepdims=True)
    entropy = -(probabilities * np.log(probabilities)).sum(axis=1)
    return float(entropy.mean() / math.log(pheromone.shape[1]))


def diversity(mappings):
    """Diversité des fourmis : part moyenne des qubits placés différemment entre deux fourmis (0 = toutes identiques)."""
    array = np.asarray(mappings)
    count = len(array)
    if count < 2:
        return 0.0
    # Compare toutes les paires de fourmis position par position (diffusion NumPy), puis moyenne par paire.
    differences = (array[:, None, :] != array[None, :, :]).mean(axis=2)
    # Moyenne sur les count × (count − 1) paires distinctes (la diagonale vaut 0).
    return float(differences.sum() / (count * (count - 1)))


def pheromone_mapping(pheromone):
    """Placement « consensus » lu dans la matrice des phéromones.

    On parcourt les cases de la plus forte à la plus faible phéromone et on attribue chaque qubit logique
    au premier qubit physique disponible (sans doublon).
    """
    pheromone = np.asarray(pheromone)
    n, m = pheromone.shape
    mapping = [-1] * n
    used = set()
    # argsort sur le tableau aplati, inversé : indices des cases par phéromone décroissante.
    for flat in np.argsort(pheromone, axis=None, kind="stable")[::-1]:
        # Conversion de l'indice aplati en (ligne, colonne) = (qubit logique, qubit physique).
        qubit, physical = divmod(int(flat), m)
        if mapping[qubit] < 0 and physical not in used:
            mapping[qubit] = physical
            used.add(physical)
            if len(used) == n:
                break
    return mapping


def build_ant(colony, pheromone, rng, local_search_steps):
    """Construit une fourmi, puis l'améliore éventuellement par une recherche locale sur le coût de distance."""
    mapping, _ = colony.construct(pheromone, rng)
    if local_search_steps:
        permutation = surrogate_descent(colony.instance, from_mapping(mapping, colony.instance.m), local_search_steps, rng)
        mapping = to_mapping(permutation, colony.instance.n)
    return mapping


def run(problem, rng, ants=10, evaluated=None, alpha=1.0, beta=2.0, rho=0.2, tau_min_ratio=0.05, elite_weight=1.0, local_search_steps=0, snapshot_every=5):
    """Exécute la colonie jusqu'à épuisement du budget.

    Paramètres :
    - ants : nombre de fourmis construites par itération ;
    - evaluated : nombre de fourmis vraiment évaluées par itération (les meilleures selon le coût de distance) ;
      None = toutes ;
    - alpha, beta : poids des phéromones et de l'heuristique ;
    - rho : taux d'évaporation (part des phéromones perdue à chaque itération) ;
    - tau_min_ratio : tau_min = tau_min_ratio × tau_max ;
    - elite_weight : quantité déposée chaque itération par la meilleure solution globale ;
    - local_search_steps : nombre d'essais de recherche locale sur le coût de distance pour chaque fourmi (0 = aucune) ;
    - snapshot_every : une copie de la matrice des phéromones est gardée toutes les `snapshot_every` itérations.
    """
    instance = problem.instance
    colony = Colony(instance, alpha, beta)
    # On ne peut pas évaluer plus de fourmis qu'on en construit, ni moins d'une.
    evaluated = ants if evaluated is None else max(1, min(evaluated, ants))
    tau_min, tau_max = pheromone_bounds(rho, tau_min_ratio)
    # Au départ, toutes les cases sont au maximum : aucune préférence, exploration maximale.
    pheromone = np.full((instance.n, instance.m), tau_max)
    # Trace interne enregistrée dans le Result (pour les graphiques du notebook).
    trace = problem.trace
    trace.update({"order": colony.order, "tau_min": tau_min, "tau_max": tau_max, "iterations": [], "snapshots": [], "pheromone": pheromone.tolist(), "best_mapping": None})
    best_mapping, best_cost = None, math.inf
    iteration = 0
    # Boucle infinie : elle s'arrête quand problem.fitness lève BudgetExhausted.
    while True:
        iteration += 1
        # 1. Construction des fourmis.
        mappings = [build_ant(colony, pheromone, rng, local_search_steps) for _ in range(ants)]
        # On supprime les doublons (inutile de payer deux fois le même placement dans une itération).
        unique = list({tuple(m): m for m in mappings}.values())
        # 2. Classement gratuit par coût de distance ; on garde les `evaluated` meilleures.
        surrogates = [problem.surrogate(m) for m in unique]
        candidates = [unique[k] for k in np.argsort(surrogates, kind="stable")[:evaluated]]
        # 3. Vraies évaluations (consomment le budget).
        costs = [problem.fitness(m) for m in candidates]
        # Meilleure fourmi de l'itération.
        winner = int(np.argmin(costs))
        if costs[winner] < best_cost:
            best_mapping, best_cost = candidates[winner], costs[winner]
        # 4. Évaporation : toutes les phéromones perdent une part rho.
        pheromone *= 1 - rho
        # 5. Dépôt par la meilleure fourmi de l'itération : de 1 (si elle égale le meilleur global) à moins de 1.
        deposit(pheromone, candidates[winner], best_cost / costs[winner])
        # Dépôt par la meilleure solution globale (élitisme).
        deposit(pheromone, best_mapping, elite_weight)
        # 6. Bornes MAX-MIN : on ramène chaque case dans [tau_min, tau_max].
        np.clip(pheromone, tau_min, tau_max, out=pheromone)
        # Enregistrement des indicateurs de l'itération.
        trace["iterations"].append({
            "iteration": iteration,
            "evaluations": problem.evaluations,
            "costs": [int(c) for c in costs],
            "iteration_best": int(costs[winner]),
            "iteration_mean": float(np.mean(costs)),
            "global_best": int(best_cost),
            "surrogate_mean": float(np.mean(surrogates)),
            "surrogate_min": int(min(surrogates)),
            "unique_ants": len(unique),
            "diversity": diversity(mappings),
            "entropy": normalized_entropy(pheromone),
        })
        # Dernier état connu (mis à jour à chaque itération car le budget peut s'arrêter en plein milieu de la suivante).
        trace["pheromone"] = pheromone.round(4).tolist()
        trace["best_mapping"] = list(best_mapping)
        # Copie périodique de la matrice des phéromones.
        if iteration == 1 or iteration % snapshot_every == 0:
            trace["snapshots"].append({"iteration": iteration, "evaluations": problem.evaluations, "pheromone": pheromone.round(4).tolist()})
