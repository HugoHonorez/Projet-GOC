"""Recherche tabou (code de l'équipe : StudentCode(1).py), intégrée sans changer l'algorithme.

Algorithme d'origine (`recherche_taboue`) :
- départ : placement aléatoire ;
- voisinage complet (`generer_voisin`) : tous les échanges de deux qubits logiques, puis tous les déplacements d'un
  qubit logique vers un qubit physique libre ; chaque voisin porte les attributs (position, qubit physique) qu'il quitte ;
- à chaque itération, TOUS les voisins sont évalués (avec mémoire : un placement n'est évalué qu'une fois) et on se
  déplace vers le meilleur voisin autorisé, même s'il est moins bon que la solution courante ;
- tabou : un voisin est interdit s'il réinstalle un attribut quitté il y a moins de `duree_tabou` itérations,
  sauf critère d'aspiration (il est strictement meilleur que la meilleure solution connue) ;
- les attributs quittés par le mouvement sont interdits jusqu'à l'itération + duree_tabou.

Adaptations au framework (l'algorithme est inchangé) :
- fitness → problem.fitness ; module `random` → générateur `random.Random` initialisé par la graine ;
- temps_max devient optionnel (max_seconds) : l'arrêt normal est l'épuisement du budget d'évaluations ;
- `print` et `sauvegarde` supprimés : le framework enregistre la meilleure solution et écrit les fichiers solutions ;
- dans le code d'origine, la meilleure solution était enregistrée dans une variable mal orthographiée
  (`meilleur = courante[:]`) : la valeur renvoyée restait la solution de départ. C'est corrigé ici ; la recherche
  elle-même n'est pas affectée (seul f_meilleure, qui était correct, sert au critère d'aspiration).

Coût : une itération évalue jusqu'à |N(s)| = n(n−1)/2 + n(m−n) voisins (105 à 350 selon l'instance).

Hybridation (optimizer/hybrid) : hooks « itération » sur la solution courante après chaque mouvement (la liste
tabou est conservée) ; les hooks « solution » ne sont pas acceptés, car modifier chaque voisin changerait
le voisinage et les attributs tabou ; initial_mapping remplace le départ aléatoire.
"""

from ..hybrid.hooks import improve_iteration, normalized
from ..randomness import python_random

name = "tabu_search"


class TabuSearch:
    """Les fonctions d'origine, avec le générateur aléatoire et la fitness de l'exécution."""

    def __init__(self, problem, rng):
        self.problem = problem
        self.random = python_random(rng)

    def initial_solution(self, n, m):
        """`solution_initiale` : renvoie une liste de n qubits physiques distincts parmi range(m)."""
        draw = self.random.sample(range(m), n)
        return draw

    @staticmethod
    def generate_neighbours(solution, m):
        """`generer_voisin` : liste des voisins sous la forme (attributs_quittes, voisin)."""
        n = len(solution)
        neighbours = []

        for i in range(n):
            for j in range(i + 1, n):
                neighbour = solution[:]  # copie de la solution
                neighbour[i], neighbour[j] = solution[j], solution[i]  # échange de deux valeurs
                left_attributes = [(i, solution[i]), (j, solution[j])]  # attributs que la liste tabou interdira de remettre pendant quelques itérations
                neighbours.append((left_attributes, neighbour))  # ajout du couple à la liste de résultats

        free_qubits = []
        for k in range(m):  # calcul des qubits libres
            if k not in solution:
                free_qubits.append(k)
        for i in range(n):  # boucle sur chaque qubit
            for k in free_qubits:  # boucle sur les qubits libres
                neighbour = solution[:]  # copie
                neighbour[i] = k
                left_attributes = [(i, solution[i])]  # si le qubit logique i était sur son ancien qubit physique
                neighbours.append((left_attributes, neighbour))
        return neighbours

    def evaluate(self, solution, memory):
        """`evaluer` : fitness de la solution, calculée seulement si elle est absente de la mémoire."""
        key = tuple(solution)  # transformation de la liste en tuple
        if key not in memory:
            memory[key] = self.problem.fitness(solution)  # calcule et mémorise la clé si elle n'est pas en mémoire
        return memory[key]

    @staticmethod
    def is_tabu(neighbour, left_attributes, tabu, iteration):
        """`taboue` : indique si le mouvement qui mène à ce voisin est interdit."""
        for position, _ in left_attributes:  # positions touchées par le mouvement
            new_attribute = (position, neighbour[position])  # ce que le voisin installe
            if tabu.get(new_attribute, -1) > iteration:  # interdiction encore active ?
                return True  # un seul suffit : tabou
        return False  # aucun interdit : autorisé

    @staticmethod
    def update_tabu(tabu, left_attributes, iteration, tabu_tenure):
        """`mise_a_jour_taboue` : interdit les attributs quittés jusqu'à l'itération iteration + tabu_tenure."""
        for attribute in left_attributes:  # boucle sur les attributs quittés
            tabu[attribute] = iteration + tabu_tenure  # date de fin d'interdiction (écrase l'ancienne)

    def best_neighbour(self, current, m, memory, tabu, iteration, best_fitness):
        """`meilleur_voisin` : (fitness, voisin, attributs_quittes) du meilleur voisin autorisé, ou None."""
        best_candidate = None  # rien retenu pour l'instant
        for left_attributes, neighbour in self.generate_neighbours(current, m):  # boucle sur le voisinage
            neighbour_fitness = self.evaluate(neighbour, memory)  # évaluation

            forbidden = self.is_tabu(neighbour, left_attributes, tabu, iteration)  # test tabou
            if forbidden and neighbour_fitness >= best_fitness:
                continue
            if best_candidate is None or neighbour_fitness < best_candidate[0]:
                best_candidate = (neighbour_fitness, neighbour, left_attributes)
        return best_candidate


def run(problem, rng, tabu_tenure=10, max_iter=500, max_seconds=None, hooks=None, initial_mapping=None):
    """Exécute la recherche tabou (`recherche_taboue`).

    Paramètres (valeurs du script de l'équipe par défaut) :
    - tabu_tenure : durée tabou (10) ; max_iter : nombre maximal d'itérations (500) ;
    - max_seconds : limite de temps optionnelle (temps_max) ;
    - hooks, initial_mapping : hybridation (voir l'en-tête du module).
    Renvoie (meilleure solution, meilleure fitness) comme le code d'origine.
    """
    hooks = normalized(hooks)
    if hooks["solution"]:
        raise ValueError("tabu_search accepts only 'iteration' hooks (a 'solution' hook would change the neighbourhood and the tabu attributes)")
    search = TabuSearch(problem, rng)
    n, m = problem.n, problem.m
    trace = problem.trace
    trace.update({"iterations": []})

    current = search.initial_solution(n, m)  # départ
    if initial_mapping is not None:
        current = [int(u) for u in initial_mapping]
    memory = {}  # mémoire des fitness
    tabu = {}  # mémoire des interdictions

    best_fitness = search.evaluate(current, memory)  # meilleure fitness
    best = current[:]  # copie de la meilleure solution

    for iteration in range(max_iter):
        if max_seconds is not None and problem.elapsed > max_seconds:  # limite de temps
            break
        start = problem.evaluations
        result = search.best_neighbour(current, m, memory, tabu, iteration, best_fitness)  # meilleur voisin autorisé
        if result is None:  # tout est interdit
            continue

        neighbour_fitness, neighbour, left_attributes = result  # déplacement
        current = neighbour

        search.update_tabu(tabu, left_attributes, iteration, tabu_tenure)  # mise à jour tabou

        if neighbour_fitness < best_fitness:  # potentiel nouveau record
            best_fitness = neighbour_fitness
            best = current[:]
        # Hooks « itération » : amélioration de la solution courante après le mouvement.
        current_fitness = neighbour_fitness
        if hooks["iteration"]:
            current, current_fitness = improve_iteration(problem, current, neighbour_fitness, hooks, rng)
            memory.setdefault(tuple(current), current_fitness)
            if current_fitness < best_fitness:
                best_fitness, best = current_fitness, current[:]
        trace["iterations"].append({
            "iteration": iteration,
            "evaluations": problem.evaluations,
            "new_evaluations": problem.evaluations - start,
            "current": int(current_fitness),
            "best": int(best_fitness),
            "active_tabu": sum(1 for end in tabu.values() if end > iteration),
        })

    return best, best_fitness  # résultat
