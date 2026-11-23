"""Lancer des algorithmes, en série ou en parallèle, et transformer leurs résultats en tableaux.

- `run_algorithm` : une exécution (un algorithme, une instance, un budget, une graine) ;
- `run_grid` : toutes les combinaisons algorithmes × instances × graines, à budget égal ;
- `results_frame` / `history_frame` : tableaux pandas pour les analyses ;
- `save_results` / `load_results` : sauvegarde dans results/ (format JSON Lines : une exécution par ligne).
"""

import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

from .instance import load_instance
from .problem import BudgetExhausted, Problem
from .result import Result


def algorithm_name(algorithm):
    """Nom par défaut d'un algorithme : le nom de son module (par ex. « random_search »)."""
    return getattr(algorithm, "name", None) or algorithm.__module__.rsplit(".", 1)[-1]


def run_algorithm(algorithm, instance_id, budget, seed=None, name=None, **params):
    """Exécute un algorithme jusqu'à épuisement du budget (ou jusqu'à ce qu'il s'arrête seul) et renvoie un `Result`.

    `algorithm` est une fonction `run(problem, rng, **params)` ; `params` sont ses paramètres.
    """
    # Le problème : l'instance + le budget de vraies évaluations.
    problem = Problem(load_instance(instance_id), budget)
    # Générateur aléatoire initialisé avec la graine : même graine = même exécution (hors bruit de la fitness).
    rng = np.random.default_rng(seed)
    try:
        # L'algorithme tourne en boucle ; il est arrêté par BudgetExhausted à la fin du budget.
        algorithm(problem, rng, **params)
    except BudgetExhausted:
        pass
    return Result.from_problem(problem, name or algorithm_name(algorithm), seed, params, budget)


def _run_task(task):
    """Exécute une tâche (tuple de paramètres). Fonction séparée pour pouvoir être envoyée à un autre processus."""
    algorithm, instance_id, budget, seed, name, params = task
    return run_algorithm(algorithm, instance_id, budget, seed, name, **params)


def _report(done, total, started, result):
    """Affiche l'avancement environ tous les 10 % (et à la fin)."""
    step = max(1, total // 10)
    if done % step == 0 or done == total:
        print(f"[{done}/{total}] {time.perf_counter() - started:.0f} s | last: {result.algorithm}, instance {result.instance_id}, seed {result.seed} -> {result.best_cost}")


def run_grid(algorithms, instance_ids, seeds, budget, workers=1, progress=True):
    """Lance chaque algorithme sur chaque instance avec chaque graine, au même budget.

    `algorithms` est un dictionnaire {nom: (fonction, paramètres)}.
    `workers` > 1 répartit les exécutions sur plusieurs processus (plusieurs cœurs du processeur) ;
    il faut alors que les algorithmes soient définis dans optimizer/algorithms/ (pas dans un notebook).
    Les résultats sont renvoyés dans l'ordre des tâches, quel que soit l'ordre de fin.
    """
    # Liste de toutes les combinaisons à exécuter.
    tasks = [
        (algorithm, instance_id, budget, seed, name, params)
        for name, (algorithm, params) in algorithms.items()
        for instance_id in instance_ids
        for seed in seeds
    ]
    started = time.perf_counter()
    # Mode simple : une exécution après l'autre, dans ce processus.
    if workers <= 1:
        results = []
        for task in tasks:
            results.append(_run_task(task))
            if progress:
                _report(len(results), len(tasks), started, results[-1])
        return results
    # Une fonction définie dans un notebook (module « __main__ ») ne peut pas être envoyée aux autres processus.
    local = sorted({name for name, (algorithm, _) in algorithms.items() if algorithm.__module__ == "__main__"})
    if local:
        raise ValueError(f"Algorithms defined in a notebook cannot run in parallel ({', '.join(local)}): move them to optimizer/algorithms or use workers=1")
    # Emplacements réservés pour ranger chaque résultat à la position de sa tâche.
    results = [None] * len(tasks)
    # Pool de processus : chaque processus charge ses propres instances et exécute des tâches.
    with ProcessPoolExecutor(max_workers=workers) as pool:
        # On soumet toutes les tâches ; on retient la position de chacune.
        futures = {pool.submit(_run_task, task): index for index, task in enumerate(tasks)}
        # as_completed renvoie les tâches au fur et à mesure qu'elles se terminent.
        for done, future in enumerate(as_completed(futures), start=1):
            results[futures[future]] = future.result()
            if progress:
                _report(done, len(tasks), started, results[futures[future]])
    return results


def results_frame(results):
    """Tableau pandas avec une ligne par exécution (algorithme, instance, graine, meilleur coût, temps...)."""
    return pd.DataFrame([r.summary() for r in results])


def history_frame(results):
    """Tableau pandas avec une ligne par évaluation de chaque exécution (pour tracer les convergences)."""
    rows = []
    for r in results:
        for evaluation, cost, best, seconds in r.history:
            rows.append({"algorithm": r.algorithm, "instance_id": r.instance_id, "seed": r.seed, "evaluation": evaluation, "cost": cost, "best": best, "seconds": seconds})
    return pd.DataFrame(rows)


def save_results(results, path):
    """Enregistre les résultats dans un fichier JSON Lines (une exécution complète par ligne)."""
    path = Path(path)
    # Crée le dossier parent s'il n'existe pas encore.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for r in results:
            handle.write(json.dumps(r.to_dict()) + "\n")
    return path


def load_results(path):
    """Relit un fichier écrit par `save_results` et renvoie la liste des `Result`."""
    with Path(path).open(encoding="utf-8") as handle:
        return [Result.from_dict(json.loads(line)) for line in handle if line.strip()]
