"""Recuit simulé pour le placement de qubits.

Principe :
- on part d'un placement (par défaut déjà bon : descente gratuite sur le coût de distance) ;
- à chaque pas, on propose un voisin (échange de deux qubits) et on l'évalue avec la vraie fitness ;
- un voisin meilleur (ou égal) est toujours accepté ; un voisin pire de delta est accepté avec la
  probabilité exp(-delta / T), où T est la « température » ;
- T diminue au fil du budget : au début on explore (on accepte souvent des dégradations), à la fin
  on n'accepte presque plus que des améliorations.

La température est exprimée en proportion du coût de départ (t_start = 0.05 signifie T = 5 % du coût
de départ) pour que les mêmes réglages conviennent à des instances de coûts très différents.
"""

import math

from ..local_search import surrogate_descent
from ..representation import from_mapping, identity_permutation, random_permutation, random_swap, to_mapping

name = "simulated_annealing"


def initial_permutation(problem, rng, start, start_descent_steps, initial_mapping):
    """Permutation de départ : un placement imposé, l'identité, un placement aléatoire, ou (par défaut) un placement optimisé pour le coût de distance."""
    # Placement imposé (par exemple la meilleure solution d'un autre algorithme, dans un hybride).
    if initial_mapping is not None:
        return from_mapping(initial_mapping, problem.m)
    if start == "identity":
        return identity_permutation(problem.m)
    if start == "random":
        return random_permutation(problem.m, rng)
    # Départ « surrogate » : permutation aléatoire améliorée gratuitement par une descente sur le coût de distance.
    return surrogate_descent(problem.instance, random_permutation(problem.m, rng), start_descent_steps, rng)


def temperature(progress, t_start, t_end):
    """Température relative à un avancement entre 0 et 1 : décroissance géométrique de t_start à t_end."""
    return t_start * (t_end / t_start) ** progress


def propose(problem, current, rng, candidates):
    """Voisin proposé : un échange aléatoire, ou le meilleur de `candidates` échanges selon le coût de distance (gratuit)."""
    neighbours = [random_swap(current, problem.n, rng) for _ in range(candidates)]
    if candidates == 1:
        return neighbours[0]
    return min(neighbours, key=problem.surrogate_of)


def run(problem, rng, t_start=0.05, t_end=0.002, start="surrogate", start_descent_steps=2000, candidates=1, initial_mapping=None, schedule_length=None):
    """Exécute le recuit simulé jusqu'à épuisement du budget.

    Paramètres :
    - t_start, t_end : températures de début et de fin, en proportion du coût de départ ;
    - start : point de départ, « surrogate » (défaut), « identity » ou « random » ;
    - start_descent_steps : nombre d'échanges de la descente gratuite pour le départ « surrogate » ;
    - candidates : nombre de voisins générés par pas ; seul le meilleur selon le coût de distance est évalué (1 = recuit classique) ;
    - initial_mapping : placement de départ imposé (prioritaire sur `start`) ;
    - schedule_length : nombre de pas sur lequel la température descend (par défaut : le budget restant).
    """
    # Point de départ et son évaluation (coûte 1 évaluation).
    current = initial_permutation(problem, rng, start, start_descent_steps, initial_mapping)
    current_cost = problem.fitness_of(current)
    # Échelle des températures : le coût de départ (au moins 1 pour éviter une température nulle).
    scale = max(float(current_cost), 1.0)
    # Nombre de pas sur lequel la température descend : le budget restant, ou 1000 si le budget est illimité.
    length = schedule_length or (problem.remaining if math.isfinite(problem.remaining) else 1000)
    # Trace interne pour les graphiques du notebook.
    trace = problem.trace
    trace.update({
        "sa_start_mapping": to_mapping(current, problem.n),
        "sa_start_cost": int(current_cost),
        "sa_start_surrogate": problem.surrogate_of(current),
        "sa_start_evaluation": problem.evaluations,
        "sa_scale": scale,
        "sa_steps": [],
    })
    step = 0
    # Boucle infinie : elle s'arrête quand problem.fitness lève BudgetExhausted.
    while True:
        # Avancement dans le programme de refroidissement (borné à 1).
        progress = min(step / max(length, 1), 1.0)
        # Température absolue : température relative × coût de départ.
        current_temperature = temperature(progress, t_start, t_end) * scale
        candidate = propose(problem, current, rng, candidates)
        cost = problem.fitness_of(candidate)
        # delta > 0 : le voisin est pire.
        delta = cost - current_cost
        # Règle d'acceptation de Metropolis.
        accepted = delta <= 0 or rng.random() < math.exp(-delta / current_temperature)
        if accepted:
            current, current_cost = candidate, cost
        step += 1
        trace["sa_steps"].append({
            "step": step,
            "evaluations": problem.evaluations,
            "temperature": current_temperature,
            "candidate_cost": int(cost),
            "candidate_surrogate": problem.surrogate_of(candidate),
            "current_cost": int(current_cost),
            "delta": int(delta),
            "accepted": bool(accepted),
            "best": int(problem.best_cost),
        })
        # Dernier placement courant connu (le budget peut s'arrêter au pas suivant).
        trace["sa_current_mapping"] = to_mapping(current, problem.n)
