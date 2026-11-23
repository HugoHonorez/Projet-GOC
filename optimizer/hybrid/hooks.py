"""Points d'accroche (hybridation de bas niveau) : briques appliquées à l'intérieur d'une métaheuristique.

Une métaheuristique qui accepte le paramètre `hooks` appelle ces fonctions aux deux moments suivants :
- `improve_solution` : sur chaque solution candidate, avant son évaluation (fourmi, construction GRASP, enfant...) ;
- `improve_iteration` : à la fin de chaque itération, sur la solution « courante » de la métaheuristique
  (meilleure fourmi de l'itération, solution de l'itération GRASP, meilleur individu de la population...).

Format de `hooks` (dictionnaire JSON) : {"solution": [[nom, paramètres], ...], "iteration": [[nom, paramètres], ...]}.
"""

from .improvers import IMPROVERS


def normalized(hooks):
    """Les deux listes de briques, vides si absentes ; vérifie que chaque nom existe."""
    hooks = hooks or {}
    result = {"solution": [list(step) for step in hooks.get("solution", [])], "iteration": [list(step) for step in hooks.get("iteration", [])]}
    for name, _ in result["solution"] + result["iteration"]:
        if name not in IMPROVERS:
            raise ValueError(f"Unknown improver {name!r}; available: {sorted(IMPROVERS)}")
    unknown = set(hooks) - {"solution", "iteration"}
    if unknown:
        raise ValueError(f"Unknown hook point(s) {sorted(unknown)}; use 'solution' and 'iteration'")
    return result


def improve_solution(problem, mapping, hooks, rng):
    """Applique les briques « solution » à un placement pas encore évalué. Renvoie le placement amélioré."""
    for name, params in hooks["solution"]:
        mapping, _ = IMPROVERS[name](problem, list(mapping), None, rng, **params)
    return list(mapping)


def improve_iteration(problem, mapping, cost, hooks, rng):
    """Applique les briques « itération » à un placement évalué. Renvoie (placement, fitness), la fitness étant
    réévaluée si une brique gratuite a changé le placement."""
    for name, params in hooks["iteration"]:
        mapping, cost = IMPROVERS[name](problem, list(mapping), cost, rng, **params)
        if cost is None:
            cost = problem.fitness(mapping)
    return list(mapping), cost
