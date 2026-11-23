"""Le résultat d'une exécution d'algorithme, sous une forme facile à analyser et à sauvegarder."""

from dataclasses import asdict, dataclass, field


@dataclass
class Result:
    """Tout ce qu'on garde d'une exécution : réglages, meilleure solution, historique et trace interne."""

    algorithm: str  # nom de l'algorithme (ou du réglage), par ex. « aco_filtered »
    instance_id: int  # instance résolue
    seed: int | None  # graine du générateur aléatoire (pour pouvoir reproduire l'exécution)
    best_mapping: list  # meilleur placement trouvé
    best_cost: float  # sa fitness (la plus petite observée)
    evaluations: int  # nombre de vraies évaluations utilisées
    seconds: float  # durée de l'exécution
    params: dict = field(default_factory=dict)  # paramètres de l'algorithme
    # Budget demandé (None dans les anciens fichiers) : un algorithme peut s'arrêter seul avant (evaluations < budget).
    budget: int | None = None
    # repr=False : ces champs volumineux ne s'affichent pas quand on imprime un Result.
    history: list = field(default_factory=list, repr=False)  # (évaluation, coût, meilleur coût, temps)
    trace: dict = field(default_factory=dict, repr=False)  # informations internes propres à l'algorithme

    @classmethod
    def from_problem(cls, problem, algorithm, seed, params, budget=None):
        """Construit le résultat à partir de l'état final d'un `Problem`."""
        return cls(
            algorithm=algorithm,
            instance_id=problem.instance.instance_id,
            seed=seed,
            best_mapping=problem.best_mapping,
            best_cost=problem.best_cost,
            evaluations=problem.evaluations,
            seconds=problem.elapsed,
            params=dict(params),
            budget=budget,
            history=list(problem.history),
            trace=dict(problem.trace),
        )

    def summary(self):
        """Version courte (sans historique ni trace) : une ligne de tableau de résultats."""
        data = asdict(self)
        data.pop("history")
        data.pop("trace")
        return data

    def to_dict(self):
        """Version complète sous forme de dictionnaire (pour l'écrire en JSON)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        """Reconstruit un Result depuis un dictionnaire lu en JSON (les tuples de l'historique redeviennent des tuples)."""
        return cls(**{**data, "history": [tuple(h) for h in data.get("history", [])], "trace": data.get("trace", {})})
