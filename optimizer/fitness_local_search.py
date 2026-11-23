"""Recherche locale sur f de l'équipe (Recherche_locale.py, branche « recherche-locale »), sans changer les fonctions.

Fonctions d'origine, regroupées dans la classe `FitnessLocalSearch` (pour leur donner le générateur aléatoire de l'exécution) :
- `solution_aleatoire` → random_solution ; `est_valide` → is_valid ;
- `voisins_echange` → swap_neighbours (échange de deux qubits logiques) ;
- `voisins_deplacement` → move_neighbours (un qubit logique vers un qubit physique libre) ; `voisins` → neighbours ;
- `descente` → descent : première amélioration, voisinage complet mélangé, réévaluation du départ ;
- `VND` → vnd : descente à voisinages variables, du plus petit voisinage au plus grand (première amélioration ; retour
  au premier voisinage après chaque amélioration, voisinage suivant sinon ; arrêt quand aucun n'améliore) ;
- `perturbation` → perturbation : k mouvements aléatoires (échange ou déplacement, une chance sur deux).
Utilisées par multi_start, iterated_local_search et variable_neighbourhood_search (optimizer/algorithms/).

Adaptations (le code des fonctions est inchangé) :
- module `random` → générateur `random.Random` initialisé par la graine de l'exécution ;
- `end` (instant limite) vaut +inf sans limite de temps : c'est alors le budget d'évaluations qui arrête la recherche.

Seule correction du code d'origine (demandée par l'utilisateur, 23/11/2026) : dans `VND`, la boucle était écrite
`while i > len(structures)` (jamais exécutée, i = 0) et le test de temps était inversé (`if time.time() < end: return`) ;
VND se réduisait à l'évaluation de son départ. Les deux conditions sont corrigées (`i < len(structures)`, `>= end`).

Remarque (conservée telle quelle) : `descente` et `VND` réévaluent toujours leur point de départ (1 évaluation de plus).
"""

import time

from .randomness import python_random


class FitnessLocalSearch:
    """Les fonctions de Recherche_locale.py, avec le générateur aléatoire de l'exécution."""

    def __init__(self, rng):
        self.random = python_random(rng)

    def random_solution(self, n, m):
        """`solution_aleatoire` : n qubits physiques distincts tirés parmi range(m)."""
        population = [i for i in range(m)]
        return self.random.sample(population, n)

    @staticmethod
    def is_valid(solution, n, m):
        """`est_valide` : n valeurs distinctes dans range(m)."""
        ensemble = set(solution)
        if len(solution) != n:
            return False
        if len(solution) != len(ensemble):
            return False
        for elem in solution:
            if not (0 <= elem < m):
                return False
        return True

    @staticmethod
    def swap_neighbours(solution):
        """`voisins_echange` : tous les échanges de deux qubits logiques."""
        neighbour_list = []
        for i in range(len(solution)):
            for j in range(i + 1, len(solution)):
                v = solution.copy()
                v[i], v[j] = v[j], v[i]
                neighbour_list.append(v)
        return neighbour_list

    @staticmethod
    def move_neighbours(solution, m):
        """`voisins_deplacement` : tous les déplacements d'un qubit logique vers un qubit physique libre."""
        free = [i for i in range(m) if i not in solution]
        neighbour = []
        for i in range(len(solution)):
            for p in free:
                v = list(solution)
                v[i] = p
                neighbour.append(v)
        return neighbour

    def neighbours(self, solution, m):
        """`voisins` : échanges puis déplacements."""
        return self.swap_neighbours(solution) + self.move_neighbours(solution, m)

    def descent(self, start, fitness, m, end):
        """`descente` : première amélioration sur le voisinage complet mélangé, jusqu'à un optimum local (ou `end`)."""
        current = start
        current_cost = fitness(current)
        improvement = True
        while improvement:
            improvement = False
            all_neighbours = self.neighbours(current, m)
            self.random.shuffle(all_neighbours)
            for v in all_neighbours:
                if time.time() < end:
                    cost = fitness(v)
                    if cost < current_cost:
                        current_cost = cost
                        current = v
                        improvement = True
                        break
                else:
                    break
        return current, current_cost

    def vnd(self, start, fitness, m, end):
        """`VND` (variable neighborhood descent), avec les deux conditions corrigées (voir l'en-tête du module)."""
        current = list(start)
        current_cost = fitness(current)
        n = len(current)

        # classe les voisinages du plus petit au plus grand
        structures = [
            (n * (m - n), lambda s: self.move_neighbours(s, m)),
            (n * (n - 1) // 2, self.swap_neighbours),
        ]
        structures = sorted((t, g) for t, g in structures if t > 0)

        i = 0
        # Corrigé (à la demande) : `while i > len(structures)` ne s'exécutait jamais et le test de temps était inversé.
        while i < len(structures):
            if time.time() >= end:
                return current, current_cost

            neighbour_list = structures[i][1](current)
            self.random.shuffle(neighbour_list)
            improvement = False

            for v in neighbour_list:
                if time.time() >= end:
                    return current, current_cost
                cost = fitness(v)
                if cost < current_cost:
                    current, current_cost = v, cost
                    improvement = True
                    break

            i = 0 if improvement else i + 1
        return current, current_cost

    def perturbation(self, local_minimum, k, n, m):
        """`perturbation` : k mouvements aléatoires (échange, ou déplacement si des qubits physiques sont libres)."""
        cop = local_minimum.copy()
        for i in range(k):
            pull = self.random.randint(1, 2)
            if pull == 1 or m == n:
                cop = self.random.choice(self.swap_neighbours(cop))
            if pull == 2 and n != m:
                cop = self.random.choice(self.move_neighbours(cop, m))
        return cop
