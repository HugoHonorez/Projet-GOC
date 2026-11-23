"""Hybride essaim particulaire + évolution différentielle (code de l'équipe : StudentCode (4).py), intégré sans
changer l'algorithme.

Algorithme d'origine (`hybride_pso_de`) :
- représentation continue : position x ∈ [0, 1]^m, décodée par SPV (`decodeur_spv`) : les n indices des plus
  petites composantes, dans l'ordre croissant des valeurs, forment le placement ;
- pour chaque particule i, à chaque itération :
  1. pas PSO : v ← w v + c1 r1 (p_i − x) + c2 r2 (g − x), vitesse bornée à ±0,2 (borne_max − borne_min),
     position bornée ; évaluation, mise à jour de p_i et de g ;
  2. pas DE (rand/1/bin sur les meilleures positions personnelles) : mutant p_a + F (p_b − p_c), croisement binomial
     de taux CR avec une dimension forcée ; l'essai remplace p_i (et x_i) s'il n'est pas pire ;
- 2 évaluations par particule et par itération.
C'est une hybridation intégrée (les deux mises à jour alternent dans la même boucle) : elle est gardée telle quelle
dans ce module, et ne passe donc pas par le relais d'étapes d'optimizer/hybrid.

Adaptations au framework (l'algorithme est inchangé) :
- fonction_cout → problem.fitness ; dimension = m ; décodeur SPV avec nb_elements = n ;
- module `random` → générateur `random.Random` initialisé par la graine ;
- arrêt après nb_iterations, ou avant si le budget est épuisé ; trace par itération.

Hybridation (optimizer/hybrid) : hooks « solution » sur le placement décodé avant son évaluation (la position n'est
pas modifiée : effet baldwinien), hooks « itération » sur le placement de la meilleure position globale g à la fin
de chaque itération (s'il est meilleur, g est remplacée par une position qui le décode) ; initial_mapping fixe la
position initiale de la première particule.
"""

from ..hybrid.hooks import improve_iteration, improve_solution, normalized
from ..randomness import python_random

name = "pso_de"


def spv_decoder(position, nb_elements):
    """`decodeur_spv` d'origine : transforme un vecteur continu en une liste de `nb_elements` indices distincts."""
    return sorted(range(len(position)), key=lambda i: position[i])[:nb_elements]


def spv_encoder(mapping, m, lower=0.0, upper=1.0):
    """Position de [lower, upper]^m dont le décodage SPV donne `mapping` (qubits libres placés après)."""
    used = set(mapping)
    order = list(mapping) + [u for u in range(m) if u not in used]
    position = [0.0] * m
    for rank, u in enumerate(order):
        position[u] = lower + (upper - lower) * (rank + 0.5) / m
    return position


def run(problem, rng, lower_bound=0.0, upper_bound=1.0, nb_particles=30, nb_iterations=100, inertia=0.7,
        cognitive_coeff=1.5, social_coeff=1.5, mutation_factor=0.8, crossover_rate=0.9, hooks=None, initial_mapping=None):
    """Exécute l'hybride PSO-DE.

    Paramètres (valeurs d'origine par défaut ; le script de l'équipe utilisait nb_particles=10, nb_iterations=20) :
    - lower_bound, upper_bound : bornes des positions ; nb_particles, nb_iterations ;
    - inertia (w), cognitive_coeff (c1), social_coeff (c2) : PSO ;
    - mutation_factor (F), crossover_rate (CR) : DE ;
    - hooks, initial_mapping : hybridation (voir l'en-tête du module).
    Renvoie (meilleur placement, meilleur coût) comme le code d'origine.
    """
    random = python_random(rng)
    hooks = normalized(hooks)
    n, dimension = problem.n, problem.m
    trace = problem.trace
    trace.update({"iterations": []})

    def evaluate(position):
        """Coût d'une position : placement décodé (amélioré par les hooks « solution » s'il y en a), puis fitness."""
        mapping = spv_decoder(position, n)
        if hooks["solution"]:
            mapping = improve_solution(problem, mapping, hooks, rng)
        return problem.fitness(mapping)

    max_speed = 0.2 * (upper_bound - lower_bound)

    positions = [
        [random.uniform(lower_bound, upper_bound) for _ in range(dimension)]
        for _ in range(nb_particles)
    ]
    speeds = [
        [random.uniform(-max_speed, max_speed) for _ in range(dimension)]
        for _ in range(nb_particles)
    ]
    if initial_mapping is not None:
        positions[0] = spv_encoder(initial_mapping, dimension, lower_bound, upper_bound)

    personal_best_positions = [pos[:] for pos in positions]
    personal_best_costs = [evaluate(pos) for pos in positions]

    best_index = min(range(nb_particles), key=lambda i: personal_best_costs[i])
    global_best_position = personal_best_positions[best_index][:]
    global_best_cost = personal_best_costs[best_index]

    for iteration in range(nb_iterations):
        pso_improvements = de_successes = 0
        for i in range(nb_particles):
            # Essaim particulaire
            for d in range(dimension):
                cognitive_draw = random.random()
                social_draw = random.random()
                speed = (
                    inertia * speeds[i][d]
                    + cognitive_coeff * cognitive_draw * (personal_best_positions[i][d] - positions[i][d])
                    + social_coeff * social_draw * (global_best_position[d] - positions[i][d])
                )
                speed = max(-max_speed, min(max_speed, speed))
                position = max(lower_bound, min(upper_bound, positions[i][d] + speed))
                speeds[i][d] = speed
                positions[i][d] = position

            pso_cost = evaluate(positions[i])
            if pso_cost < personal_best_costs[i]:
                pso_improvements += 1
                personal_best_costs[i] = pso_cost
                personal_best_positions[i] = positions[i][:]
                if pso_cost < global_best_cost:
                    global_best_cost = pso_cost
                    global_best_position = positions[i][:]

            # Evolution différentielle
            candidates = [index for index in range(nb_particles) if index != i]
            a, b, c = random.sample(candidates, 3)
            forced_dimension = random.randrange(dimension)

            trial = []
            for d in range(dimension):
                if d == forced_dimension or random.random() < crossover_rate:
                    mutant_value = personal_best_positions[a][d] + mutation_factor * (
                        personal_best_positions[b][d] - personal_best_positions[c][d]
                    )
                    trial.append(max(lower_bound, min(upper_bound, mutant_value)))
                else:
                    trial.append(personal_best_positions[i][d])

            trial_cost = evaluate(trial)
            if trial_cost <= personal_best_costs[i]:
                de_successes += 1
                personal_best_costs[i] = trial_cost
                personal_best_positions[i] = trial[:]
                positions[i] = trial[:]
                if trial_cost < global_best_cost:
                    global_best_cost = trial_cost
                    global_best_position = trial[:]

        # Hooks « itération » : amélioration du placement de g ; s'il est meilleur, g est remplacée.
        if hooks["iteration"]:
            improved, improved_cost = improve_iteration(problem, spv_decoder(global_best_position, n), global_best_cost, hooks, rng)
            if improved_cost < global_best_cost:
                global_best_position = spv_encoder(improved, dimension, lower_bound, upper_bound)
                global_best_cost = improved_cost
        trace["iterations"].append({
            "iteration": iteration + 1,
            "evaluations": problem.evaluations,
            "global_best": int(global_best_cost),
            "mean_personal_best": sum(personal_best_costs) / nb_particles,
            "pso_improvements": pso_improvements,
            "de_successes": de_successes,
        })

    best_solution = spv_decoder(global_best_position, n)
    return best_solution, global_best_cost
