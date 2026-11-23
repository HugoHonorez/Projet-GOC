"""Colonie d'abeilles artificielles, ABC (code de l'équipe : StudentCode (1).py), intégrée sans changer l'algorithme.

Algorithme d'origine (`colonie_abeilles`) :
- nb_sources sources (placements) tirées au hasard ; un compteur d'échecs par source ;
- voisin (`voisin_aleatoire`) : échange de deux qubits logiques, ou déplacement d'un qubit logique vers un qubit
  physique libre, avec une probabilité proportionnelle au nombre de mouvements de chaque type ;
- ouvrières : chaque source tente un voisin, gardé s'il est strictement meilleur (sinon échec + 1) ;
- spectatrices : nb_sources tentatives sur des sources tirées avec un poids (pire − f + 1) ;
- éclaireuses : une source qui atteint `limite` échecs est remplacée par une source aléatoire ;
- mémoire : un placement déjà évalué n'est jamais réévalué.

Adaptations au framework (l'algorithme est inchangé) :
- fitness → problem.fitness ; module `random` → générateur `random.Random` initialisé par la graine ;
- temps_max devient optionnel (max_seconds) : l'arrêt normal est l'épuisement du budget d'évaluations ;
- `print` et `sauvegarde` supprimés : le framework enregistre la meilleure solution et écrit les fichiers solutions.

Hybridation (optimizer/hybrid) : hooks « solution » sur chaque nouveau placement (voisin, source initiale ou
d'éclaireuse) avant son évaluation, hooks « itération » sur la meilleure source après les spectatrices (elle est
remplacée si l'amélioration est meilleure) ; initial_mapping remplace la première source.
"""

from ..hybrid.hooks import improve_iteration, improve_solution, normalized
from ..randomness import python_random

name = "bee_colony"


class BeeColony:
    """Les fonctions d'origine, avec le générateur aléatoire, la fitness et les hooks de l'exécution."""

    def __init__(self, problem, rng, hooks):
        self.problem = problem
        self.rng = rng
        self.random = python_random(rng)
        self.hooks = hooks

    def candidate(self, solution):
        """Hooks « solution » appliqués à un placement pas encore évalué (identité s'il n'y en a pas)."""
        if self.hooks["solution"]:
            return improve_solution(self.problem, solution, self.hooks, self.rng)
        return solution

    def initial_solution(self, n, m):
        """`solution_initiale` : renvoie une liste de n qubits physiques distincts parmi range(m)."""
        draw = self.random.sample(range(m), n)
        return self.candidate(draw)

    def random_neighbour(self, solution, m):
        """`voisin_aleatoire` : échange de deux qubits logiques ou déplacement vers un qubit physique libre."""
        n = len(solution)
        neighbour = solution[:]
        free_qubits = []
        for k in range(m):  # calcul des qubits libres
            if k not in solution:
                free_qubits.append(k)
        swap_count = n * (n - 1) // 2
        move_count = n * len(free_qubits)
        exchange = self.random.random() < swap_count / (swap_count + move_count)

        if exchange:
            i, j = self.random.sample(range(n), 2)
            neighbour[i], neighbour[j] = solution[j], solution[i]
        else:
            i = self.random.randrange(n)
            neighbour[i] = self.random.choice(free_qubits)
        return self.candidate(neighbour)

    def evaluate(self, solution, memory):
        """`evaluer` : fitness de la solution, calculée seulement si elle est absente de la mémoire."""
        key = tuple(solution)  # transformation de la liste en tuple
        if key not in memory:
            memory[key] = self.problem.fitness(solution)  # calcule et mémorise la clé si elle n'est pas en mémoire
        return memory[key]

    def try_improvement(self, i, sources, fitnesses, failures, m, memory):
        """`essayer_amelioration` : un voisin de la source i, gardé s'il est strictement meilleur."""
        neighbour = self.random_neighbour(sources[i], m)
        neighbour_fitness = self.evaluate(neighbour, memory)

        if neighbour_fitness < fitnesses[i]:
            sources[i] = neighbour
            fitnesses[i] = neighbour_fitness
            failures[i] = 0
        else:
            failures[i] += 1

    def choose_source(self, fitnesses):
        """`choisir_source` : tirage d'une source avec le poids (pire fitness − f + 1)."""
        worst_fitness = max(fitnesses)
        weights = [worst_fitness - f + 1 for f in fitnesses]
        return self.random.choices(range(len(fitnesses)), weights=weights, k=1)[0]

    def employed_phase(self, sources, fitnesses, failures, m, memory):
        """`phase_ouvrieres` : une tentative par source."""
        for i in range(len(sources)):
            self.try_improvement(i, sources, fitnesses, failures, m, memory)

    def onlooker_phase(self, sources, fitnesses, failures, m, memory):
        """`phase_spectatrices` : nb_sources tentatives sur des sources tirées selon leur qualité."""
        for _ in range(len(sources)):
            i = self.choose_source(fitnesses)
            self.try_improvement(i, sources, fitnesses, failures, m, memory)

    def scout_phase(self, sources, fitnesses, failures, n, m, memory, limit):
        """`phase_eclaireuses` : les sources épuisées (limit échecs) sont remplacées. Renvoie leur nombre."""
        replaced = 0
        for i in range(len(sources)):
            if failures[i] >= limit:
                sources[i] = self.initial_solution(n, m)
                fitnesses[i] = self.evaluate(sources[i], memory)
                failures[i] = 0
                replaced += 1
        return replaced


def run(problem, rng, nb_sources=20, limit=30, max_iter=500, max_seconds=None, hooks=None, initial_mapping=None):
    """Exécute la colonie d'abeilles (`colonie_abeilles`).

    Paramètres (valeurs du script de l'équipe par défaut) :
    - nb_sources : nombre de sources (20) ; limit : échecs avant abandon d'une source (30) ;
    - max_iter : nombre maximal d'itérations (500) ; max_seconds : limite de temps optionnelle (temps_max) ;
    - hooks, initial_mapping : hybridation (voir l'en-tête du module).
    Renvoie (meilleur placement, meilleur coût) comme le code d'origine.
    """
    hooks = normalized(hooks)
    colony = BeeColony(problem, rng, hooks)
    n, m = problem.n, problem.m
    trace = problem.trace
    trace.update({"iterations": []})

    sources = []
    for _ in range(nb_sources):
        new_source = colony.initial_solution(n, m)
        sources.append(new_source)
    if initial_mapping is not None:
        sources[0] = [int(u) for u in initial_mapping]

    memory = {}
    fitnesses = [colony.evaluate(s, memory) for s in sources]
    failures = [0] * nb_sources

    i_best = fitnesses.index(min(fitnesses))
    best = sources[i_best][:]
    best_fitness = fitnesses[i_best]

    for iteration in range(max_iter):
        if max_seconds is not None and problem.elapsed > max_seconds:
            break
        colony.employed_phase(sources, fitnesses, failures, m, memory)
        colony.onlooker_phase(sources, fitnesses, failures, m, memory)
        i_best = fitnesses.index(min(fitnesses))
        # Hooks « itération » : amélioration de la meilleure source, qui est remplacée si c'est mieux.
        if hooks["iteration"]:
            improved, improved_cost = improve_iteration(problem, sources[i_best], fitnesses[i_best], hooks, rng)
            memory.setdefault(tuple(improved), improved_cost)
            if improved_cost < fitnesses[i_best]:
                sources[i_best], fitnesses[i_best], failures[i_best] = improved, improved_cost, 0
        if fitnesses[i_best] < best_fitness:
            best_fitness = fitnesses[i_best]
            best = sources[i_best][:]
        replaced = colony.scout_phase(sources, fitnesses, failures, n, m, memory, limit)
        trace["iterations"].append({
            "iteration": iteration,
            "evaluations": problem.evaluations,
            "best": int(best_fitness),
            "mean_source_fitness": sum(fitnesses) / nb_sources,
            "scouts": replaced,
            "memory_size": len(memory),
        })
    return best, best_fitness
