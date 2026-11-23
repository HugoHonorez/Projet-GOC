"""Algorithme génétique pour le placement de qubits.

Théorie et notations : docs/theory/03_genetic_algorithm.md.
- génotype : permutation sigma de range(m) ; phénotype : s = sigma[:n] (gène i = qubit physique du qubit logique i) ;
- population de N individus ; à chaque génération, N/2 couples choisis par sélection, croisés avec la probabilité P_c,
  enfants mutés (une transposition sigma ∘ (a b), a < n) avec la probabilité P_m ;
- remplacement (mu + lambda) sans doublons : on garde les N meilleurs placements distincts parmi parents et enfants ;
- options : population initiale filtrée par C, présélection des enfants par C (gratuite).
Chaque placement n'est évalué qu'une fois : un enfant identique à un placement déjà évalué reprend son coût.
"""

import numpy as np

from ..construction import construction_order, interaction_weights
from ..hybrid.hooks import improve_iteration, improve_solution, normalized
from ..representation import from_mapping, random_swap_indices, swap, to_mapping

name = "genetic"


# ------------------------------------------------------------------ croisements (enfant à partir de p1, p2)

def pmx(p1, p2, a, b):
    """PMX : segment [a, b] de p1 ; hors segment, gène de p2 suivi par phi(x) = p2[p1^-1(x)] tant qu'il est en conflit."""
    child = np.full(len(p1), -1)
    child[a:b + 1] = p1[a:b + 1]
    segment = set(p1[a:b + 1].tolist())
    inverse = np.argsort(p1)
    for j in list(range(a)) + list(range(b + 1, len(p1))):
        x = p2[j]
        while x in segment:
            x = p2[inverse[x]]
        child[j] = x
    return child


def cx(p1, p2, a=None, b=None):
    """CX : cycles de theta(j) = p1^-1(p2[j]) ; les cycles sont pris alternativement chez p1 et chez p2."""
    child = np.full(len(p1), -1)
    inverse = np.argsort(p1)
    take_first = True
    for start in range(len(p1)):
        if child[start] >= 0:
            continue
        # Parcours du cycle qui contient la position `start`.
        j = start
        while child[j] < 0:
            child[j] = p1[j] if take_first else p2[j]
            j = inverse[p2[j]]
        take_first = not take_first
    return child


def ox(p1, p2, a, b):
    """OX (cours) : segment [a, b] de p1 ; positions b+1..m-1 puis 0..a-1 remplies par p2 lu à partir de b+1, privé du segment."""
    m = len(p1)
    child = np.full(m, -1)
    child[a:b + 1] = p1[a:b + 1]
    segment = set(p1[a:b + 1].tolist())
    sequence = [x for x in np.roll(p2, -(b + 1)) if x not in segment]
    positions = list(range(b + 1, m)) + list(range(a))
    child[positions] = sequence
    return child


def uniform_permutation(p1, p2, mask):
    """Croisement uniforme de permutations (cours) : positions hors masque gardées de p1 ; les éléments de p1 situés sur le
    masque sont replacés sur ces positions dans l'ordre où ils apparaissent dans p2."""
    child = p1.copy()
    positions = np.flatnonzero(mask)
    moved = set(p1[positions].tolist())
    child[positions] = [x for x in p2 if x in moved]
    return child


CROSSOVERS = {"pmx": pmx, "cx": cx, "ox": ox}


def crossover(p1, p2, operator, rng):
    """Deux enfants d'un couple. Les points de coupe (ou le masque) sont tirés une fois et servent aux deux enfants."""
    m = len(p1)
    if operator == "uniform":
        mask = rng.random(m) < 0.5
        # Second enfant : rôles des parents inversés et masque complémentaire (cours).
        return uniform_permutation(p1, p2, mask), uniform_permutation(p2, p1, ~mask)
    a, b = sorted(rng.choice(m, size=2, replace=False))
    function = CROSSOVERS[operator]
    return function(p1, p2, a, b), function(p2, p1, a, b)


# ------------------------------------------------------------------ sélection

def select(costs, rng, selection, tournament_size, tournament_p):
    """Indice d'un parent. Tournoi : k individus tirés avec remise, le r-ième meilleur gagne avec p(1-p)^(r-1).
    Roulette : probabilité proportionnelle à 1/f (minimisation, cours)."""
    costs = np.asarray(costs, dtype=float)
    if selection == "roulette":
        weights = 1.0 / costs
        return int(rng.choice(len(costs), p=weights / weights.sum()))
    drawn = rng.integers(len(costs), size=tournament_size)
    ranked = drawn[np.argsort(costs[drawn], kind="stable")]
    # Probabilités p(1-p)^(r-1), le dernier rang recevant le reste (1-p)^(k-1).
    probabilities = tournament_p * (1 - tournament_p) ** np.arange(tournament_size)
    probabilities[-1] = (1 - tournament_p) ** (tournament_size - 1)
    return int(ranked[rng.choice(tournament_size, p=probabilities / probabilities.sum())])


# ------------------------------------------------------------------ indicateurs

def diversity(population, n):
    """D : part moyenne des gènes utiles (i < n) différents entre deux individus (distance de Hamming moyenne)."""
    genes = np.asarray(population)[:, :n]
    count = len(genes)
    if count < 2:
        return 0.0
    differences = (genes[:, None, :] != genes[None, :, :]).mean(axis=2)
    return float(differences.sum() / (count * (count - 1)))


def inheritance(child, p1, p2, n):
    """h(c) : part des gènes utiles hérités à la même position de l'un des deux parents."""
    return float(np.mean((child[:n] == p1[:n]) | (child[:n] == p2[:n])))


# ------------------------------------------------------------------ algorithme

def run(problem, rng, population_size=20, selection="tournament", tournament_size=2, tournament_p=1.0,
        crossover_operator="pmx", crossover_rate=0.8, mutation_rate=0.1, construction_genes=False,
        initial_candidates=1, preselection=1, hooks=None, initial_mapping=None):
    """Exécute l'algorithme génétique jusqu'à épuisement du budget.

    Paramètres :
    - population_size : N (= nombre d'enfants par génération, N/2 couples) ;
    - selection : "tournament" (tournament_size = k, tournament_p = p) ou "roulette" ;
    - crossover_operator : "pmx", "cx", "ox" ou "uniform" ; crossover_rate : P_c ;
    - mutation_rate : P_m, probabilité qu'un enfant subisse une transposition sigma ∘ (a b), a < n ;
    - construction_genes : True = les gènes sont rangés dans l'ordre de construction i_1..i_n pendant le croisement
      (qubits qui interagissent proches dans le chromosome) ;
    - initial_candidates : chaque individu initial est le meilleur selon C de ce nombre de permutations aléatoires ;
    - preselection : on génère preselection × N enfants et on n'évalue que les N meilleurs selon C ;
    - hooks : hybridation de bas niveau (optimizer/hybrid/hooks.py) ; « solution » s'applique à chaque enfant avant
      la présélection et l'évaluation (algorithme mémétique), « iteration » au meilleur individu après le remplacement ;
    - initial_mapping : placement inséré dans la population initiale (relais : départ de la meilleure solution d'une étape précédente).
    """
    n, m = problem.n, problem.m
    hooks = normalized(hooks)
    # Ordre des gènes pendant le croisement : identité, ou ordre de construction suivi des positions libres.
    gene_order = np.arange(m)
    if construction_genes:
        gene_order = np.array(construction_order(interaction_weights(problem.instance)) + list(range(n, m)))
    known = {}
    trace = problem.trace
    trace.update({"generations": []})

    def evaluate(sigma):
        """Coût d'un individu : relu s'il est déjà connu, sinon une vraie évaluation."""
        key = tuple(int(u) for u in sigma[:n])
        if key not in known:
            known[key] = problem.fitness_of(sigma)
        return known[key]

    # Population initiale (N évaluations).
    population = []
    for _ in range(population_size):
        candidates = [rng.permutation(m) for _ in range(initial_candidates)]
        population.append(min(candidates, key=problem.surrogate_of))
    if initial_mapping is not None:
        population[0] = from_mapping(initial_mapping, m)
    costs = [evaluate(sigma) for sigma in population]
    generation = 0
    while True:
        generation += 1
        start = problem.evaluations
        children, inherited = [], []
        # Génération des enfants (gratuite) : preselection × N enfants.
        while len(children) < preselection * population_size:
            i = select(costs, rng, selection, tournament_size, tournament_p)
            j = select(costs, rng, selection, tournament_size, tournament_p)
            p1, p2 = population[i], population[j]
            if rng.random() < crossover_rate:
                # Croisement dans l'ordre des gènes choisi, puis retour à l'ordre normal.
                c1, c2 = crossover(p1[gene_order], p2[gene_order], crossover_operator, rng)
                pair = []
                for c in (c1, c2):
                    child = np.empty(m, dtype=int)
                    child[gene_order] = c
                    pair.append(child)
                inherited += [inheritance(c, p1, p2, n) for c in pair]
            else:
                pair = [p1.copy(), p2.copy()]
            for child in pair:
                if rng.random() < mutation_rate:
                    child = swap(child, *random_swap_indices(n, m, rng))
                children.append(child)
        # Hooks « solution » : chaque enfant est amélioré avant d'être évalué (algorithme mémétique).
        if hooks["solution"]:
            children = [from_mapping(improve_solution(problem, to_mapping(child, n), hooks, rng), m) for child in children]
        # Présélection gratuite par C (sans effet si preselection = 1).
        if preselection > 1:
            children = sorted(children, key=problem.surrogate_of)[:population_size]
        children = children[:population_size]
        child_costs = [evaluate(child) for child in children]
        # Remplacement (mu + lambda) sans doublons : les N meilleurs placements DISTINCTS parmi parents et enfants
        # (sinon la population se remplit de copies du meilleur et la diversité D tombe à 0).
        pool = population + children
        pool_costs = costs + child_costs
        keep, seen = [], set()
        for k in np.argsort(pool_costs, kind="stable"):
            key = tuple(int(u) for u in pool[k][:n])
            if key not in seen:
                seen.add(key)
                keep.append(k)
            if len(keep) == population_size:
                break
        # Moins de N placements distincts : on complète avec les meilleurs doublons.
        if len(keep) < population_size:
            keep += [k for k in np.argsort(pool_costs, kind="stable") if k not in keep][: population_size - len(keep)]
        population = [pool[k] for k in keep]
        costs = [pool_costs[k] for k in keep]
        # Hooks « itération » : amélioration du meilleur individu (rang 0 après le tri) ; il le remplace s'il est meilleur.
        if hooks["iteration"]:
            improved, improved_cost = improve_iteration(problem, to_mapping(population[0], n), costs[0], hooks, rng)
            known.setdefault(tuple(improved), improved_cost)
            if improved_cost < costs[0] and tuple(improved) not in {tuple(int(u) for u in s[:n]) for s in population}:
                population[0], costs[0] = from_mapping(improved, m), improved_cost
        trace["generations"].append({
            "generation": generation,
            "evaluations": problem.evaluations,
            "new_evaluations": problem.evaluations - start,
            "children_costs": [int(c) for c in child_costs],
            "population_best": int(min(costs)),
            "population_mean": float(np.mean(costs)),
            "population_surrogate": float(np.mean([problem.surrogate_of(s) for s in population])),
            "diversity": diversity(population, n),
            "inheritance": float(np.mean(inherited)) if inherited else None,
        })
        # Garde-fou : si plus aucun enfant n'est nouveau, on force la diversité par une mutation de toute la population.
        if problem.evaluations == start:
            population = [swap(s, *random_swap_indices(n, m, rng)) for s in population]
            costs = [evaluate(s) for s in population]
