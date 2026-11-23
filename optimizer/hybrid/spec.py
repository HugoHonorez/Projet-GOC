"""Constructeur d'algorithmes hybrides, à utiliser dans les notebooks.

Exemple (cours : bas niveau + haut niveau en mode relais) :

    spec = (Hybrid("grasp", alpha=0.1)                      # métaheuristique principale
            .each_solution("surrogate_local_optimum")       # bas niveau : sur chaque solution candidate
            .each_iteration("fitness_descent", patience=2)  # bas niveau : à la fin de chaque itération
            .then_improver("fitness_descent", share=0.1, patience=20))  # haut niveau, relais : 10 % du budget à la fin
    algorithm, params = spec.build()
    results = run_grid({"grasp+ls": (algorithm, params)}, instances, seeds, budget)

La description produite est un dictionnaire JSON : elle s'enregistre avec les résultats et sert de clé de cache.
"""

import copy

from .hooks import normalized
from .improvers import IMPROVERS


class Hybrid:
    """Description d'un hybride : une liste d'étapes en relais, chaque métaheuristique pouvant porter des hooks."""

    def __init__(self, algorithm, **params):
        # La première étape reçoit tout le budget que les étapes suivantes ne prennent pas (share=None).
        self.stages = [{"algorithm": algorithm, "params": dict(params), "share": None}]

    def _last_algorithm_stage(self):
        """Étape métaheuristique la plus récente : c'est elle qui reçoit les hooks."""
        for stage in reversed(self.stages):
            if "algorithm" in stage:
                return stage
        raise ValueError("No metaheuristic stage to attach the hook to")

    def _hook(self, point, improver, params):
        if improver not in IMPROVERS:
            raise ValueError(f"Unknown improver {improver!r}; available: {sorted(IMPROVERS)}")
        hooks = self._last_algorithm_stage()["params"].setdefault("hooks", {})
        hooks.setdefault(point, []).append([improver, dict(params)])
        return self

    def each_solution(self, improver, **params):
        """Bas niveau : brique appliquée à chaque solution candidate avant son évaluation (ex. algorithme mémétique)."""
        return self._hook("solution", improver, params)

    def each_iteration(self, improver, **params):
        """Bas niveau : brique appliquée à la solution courante à la fin de chaque itération."""
        return self._hook("iteration", improver, params)

    def then_improver(self, improver, share, **params):
        """Haut niveau, relais : brique appliquée à la meilleure solution trouvée, avec la part `share` du budget."""
        if improver not in IMPROVERS:
            raise ValueError(f"Unknown improver {improver!r}; available: {sorted(IMPROVERS)}")
        self.stages.append({"improver": improver, "params": dict(params), "share": share})
        return self

    def then_algorithm(self, algorithm, share, start_from_best=True, **params):
        """Haut niveau, relais : une autre métaheuristique avec la part `share` du budget (démarre de la meilleure
        solution si elle accepte `initial_mapping`). Les hooks ajoutés ensuite s'appliquent à elle."""
        self.stages.append({"algorithm": algorithm, "params": dict(params), "share": share, "start_from_best": start_from_best})
        return self

    def build(self):
        """(fonction run, paramètres) à donner à run_grid ou à CONTENDERS. Les hooks sont vérifiés ici."""
        from ..algorithms import ALGORITHMS, hybrid

        stages = copy.deepcopy(self.stages)
        for stage in stages:
            if "algorithm" in stage:
                if stage["algorithm"] not in ALGORITHMS:
                    raise ValueError(f"Unknown algorithm {stage['algorithm']!r}; available: {sorted(ALGORITHMS)}")
                if "hooks" in stage["params"]:
                    stage["params"]["hooks"] = normalized(stage["params"]["hooks"])
        return hybrid.run, {"stages": stages}

    def describe(self):
        """Description lisible, une ligne par étape."""
        lines = []
        for k, stage in enumerate(self.stages, start=1):
            share = "rest of the budget" if stage["share"] is None else f"{stage['share']:.0%} of the budget"
            if "algorithm" in stage:
                params = {key: value for key, value in stage["params"].items() if key != "hooks"}
                lines.append(f"{k}. {stage['algorithm']} {params} — {share}")
                for point, steps in stage["params"].get("hooks", {}).items():
                    for improver, improver_params in steps:
                        lines.append(f"     each {point}: {improver} {improver_params}")
            else:
                lines.append(f"{k}. then {stage['improver']} {stage['params']} on the best solution — {share}")
        return "\n".join(lines)
