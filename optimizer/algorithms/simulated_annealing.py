"""Recuit simulé (code de l'équipe : StudentCode (3).py), intégré au framework sans changer l'algorithme.

Algorithme d'origine :
- départ : placement identité [0, 1, ..., n-1] ;
- voisin (`choix_voisin`) : on tire au hasard un indice `base` parmi range(n) (sans répétition) jusqu'à trouver
  un voisin physique de `base` sur la puce qui n'est pas dans le placement ; le voisin remplace alors
  l'élément d'indice `base` du placement ;
- acceptation de Metropolis : diff ≤ 0, ou avec la probabilité exp(-diff / T) ;
- palier : 30 voisins par température ; refroidissement géométrique T ← 0,9 T de T = 5 jusqu'à T ≤ 0,05.

Adaptations au framework (l'algorithme est inchangé) :
- fitness → problem.fitness (budget d'évaluations, meilleure solution enregistrée automatiquement) ;
- module `random` → générateur `random.Random` initialisé par la graine (exécutions reproductibles) ;
- `backend` → problem.instance.backend ; les voisins sur la puce sont triés (Qiskit les renvoie dans un ordre
  variable, ce qui rendait le code d'origine non reproductible même avec une graine) ;
- les `print` sont remplacés par une trace par palier ;
- l'algorithme s'arrête à la fin du refroidissement, ou avant si le budget est épuisé.

Remarque sur le code d'origine (conservé tel quel) : dans `choix_voisin`, `base` sert à la fois d'indice de qubit
logique (sol_temp[base] = voisin) et de qubit physique (coupling_map.neighbors(base)). Les deux coïncident au départ
(placement identité), puis divergent dès que le placement a changé.

Hybridation (optimizer/hybrid) : hooks « solution » sur chaque voisin avant son évaluation, hooks « itération »
sur la solution courante à la fin de chaque palier de température ; initial_mapping remplace le départ identité.
"""

import math

from ..hybrid.hooks import improve_iteration, improve_solution, normalized
from ..randomness import python_random

name = "simulated_annealing"


def neighbour_choice(problem, current, random):
    """`choix_voisin` d'origine : renvoie (qubits physiques candidats, indice base), ou ([], -1) si aucun."""
    n = problem.n
    tested = []
    possible = []
    for i in range(n):
        possible.append(i)
    while len(tested) < len(current):
        base = random.choice(possible)
        if base not in tested:
            tested.append(base)
            # sorted : Qiskit renvoie les voisins dans un ordre qui change d'un appel à l'autre ; le tri rend
            # l'exécution reproductible sans changer la loi du tirage (random.choice uniforme sur les mêmes candidats).
            neighbours = sorted(problem.instance.backend.coupling_map.neighbors(base))
            check = False
            candidates = []
            for point in neighbours:
                if point not in current:
                    check = True
                    candidates.append(point)
            if check == True:
                return candidates, base
    return [], -1


def run(problem, rng, initial_temperature=5, cooling=0.9, moves_per_temperature=30, final_temperature=0.05, hooks=None, initial_mapping=None):
    """Exécute le recuit simulé.

    Paramètres (valeurs d'origine par défaut) :
    - initial_temperature : T de départ (5) ; cooling : facteur de refroidissement (0,9) ;
    - moves_per_temperature : voisins tirés par palier (30) ; final_temperature : arrêt quand T ≤ ce seuil (0,05) ;
    - hooks, initial_mapping : hybridation (voir l'en-tête du module).
    Renvoie (meilleur placement, meilleur coût) comme le code d'origine.
    """
    random = python_random(rng)
    hooks = normalized(hooks)
    n = problem.n
    trace = problem.trace
    trace.update({"temperatures": []})

    # Départ : placement identité (ou celui d'une étape précédente en relais).
    current = n * [0]
    for i in range(n):
        current[i] = i
    if initial_mapping is not None:
        current = [int(u) for u in initial_mapping]

    current_cost = problem.fitness(current)
    best = current
    best_cost = current_cost
    T = initial_temperature
    while T > final_temperature:
        accepted = uphill = 0
        for _ in range(moves_per_temperature):
            neighbours, base = neighbour_choice(problem, current, random)
            if base != -1:
                neighbour = random.choice(neighbours)
                candidate = current.copy()
                candidate[base] = neighbour
                # Hooks « solution » : le voisin est amélioré avant d'être évalué.
                if hooks["solution"]:
                    candidate = improve_solution(problem, candidate, hooks, rng)
                candidate_cost = problem.fitness(candidate)
                diff = candidate_cost - current_cost

                # Critère de Metropolis.
                if diff <= 0 or random.random() < math.exp(-diff / T):
                    accepted += 1
                    uphill += diff > 0
                    current = candidate
                    current_cost = candidate_cost
                    if current_cost < best_cost:
                        best = current
                        best_cost = current_cost
        # Hooks « itération » : la solution courante est améliorée à la fin du palier.
        if hooks["iteration"]:
            current, current_cost = improve_iteration(problem, current, current_cost, hooks, rng)
            if current_cost < best_cost:
                best, best_cost = current, current_cost
        trace["temperatures"].append({
            "temperature": T,
            "evaluations": problem.evaluations,
            "accepted": accepted,
            "uphill_accepted": int(uphill),
            "current_cost": int(current_cost),
            "best_cost": int(best_cost),
        })
        T *= cooling

    return best, best_cost
