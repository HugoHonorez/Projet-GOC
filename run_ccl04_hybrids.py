"""Lance les hybrides « constructive x recherche locale de l'équipe » et enregistre les résultats.

    python run_ccl04_hybrids.py                                        # 2000 evaluations, instances 1 2 5 9
    python run_ccl04_hybrids.py --budget 5000 --workers 4
    python run_ccl04_hybrids.py --instances 1 --seeds 0 --budget 400   # essai rapide
    python run_ccl04_hybrids.py --describe                             # juste la liste des hybrides

ATTENTION AU BUDGET. Les mesures de `results/comparison/` ont été faites à 200 évaluations.
Une seule descente de la recherche locale de l'équipe en consomme 250 à 400 : à 200 évaluations
elle n'a pas le temps de terminer son premier pas, et tout hybride qui l'utilise est condamné
d'avance. Le budget de l'examen correspond à 2 000 à 15 000 évaluations selon l'instance
(15 min pour 3 instances, de 15 ms à 550 ms par évaluation). C'est dans ce régime qu'il faut
comparer, et c'est pourquoi le budget par défaut ici est 2 000 et non 200.
"""

import argparse
import collections
import statistics

from optimizer.experiment import run_grid, save_results
from optimizer.hybrid.ccl04_hybrids import describe, ccl04_hybrides


def tableau(results):
    """Médiane du meilleur coût par algorithme et par instance, sur les graines."""
    data = collections.defaultdict(list)
    for result in results:
        data[(result.algorithm, result.instance_id)].append(result.best_cost)
    algorithmes = sorted({a for a, _ in data})
    instances = sorted({i for _, i in data})
    lignes = ["", "MEDIANE du meilleur cout sur les graines (plus petit = mieux)",
              "algorithme".ljust(18) + "".join(f"{i:>7}" for i in instances)]
    for algorithme in algorithmes:
        cellules = "".join(f"{statistics.median(data[(algorithme, i)]):>7.0f}" if (algorithme, i) in data else "      -"
                           for i in instances)
        lignes.append(algorithme.ljust(18) + cellules)
    return "\n".join(lignes)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--budget", type=int, default=2000, help="evaluations par execution (defaut 2000)")
    parser.add_argument("--instances", type=int, nargs="+", default=[1, 2, 5, 9])
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--workers", type=int, default=1, help="nombre de processus en parallele")
    parser.add_argument("--share", type=float, default=0.4, help="part du budget pour la recherche locale en relais")
    parser.add_argument("--max-evaluations", type=int, default=200, help="part d'evaluations d'une descente branchee")
    parser.add_argument("--out", default="results/hybrid/ccl04_local_search.jsonl")
    parser.add_argument("--describe", action="store_true", help="affiche les hybrides et sort")
    args = parser.parse_args()

    if args.describe:
        print(describe(args.share, args.max_evaluations))
        return

    algorithmes = ccl04_hybrides(part=args.share, max_evaluations=args.max_evaluations)
    executions = len(algorithmes) * len(args.instances) * len(args.seeds)
    print(f"{len(algorithmes)} algorithmes x {len(args.instances)} instances x {len(args.seeds)} graines "
          f"= {executions} executions a {args.budget} evaluations")
    if args.budget < 1000:
        print("ATTENTION : a ce budget la recherche locale ne termine pas une descente (voir l'en-tete du fichier).")

    results = run_grid(algorithmes, args.instances, args.seeds, args.budget, workers=args.workers)
    chemin = save_results(results, args.out)
    print(tableau(results))
    print(f"\nresultats : {chemin}")


if __name__ == "__main__":
    main()
