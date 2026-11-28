"""Reevaluation robuste des placements retenus par une campagne.

La fitness est aleatoire : le routage (SabreSwap) n'est pas graine, donc un meme placement
n'a pas toujours la meme profondeur. Le `best_cost` enregistre par une campagne est le minimum
sur des centaines de tirages bruites : il est systematiquement optimiste, et d'autant plus que
l'algorithme a fait d'evaluations. Comparer deux lignes d'un tableau de `best_cost`, c'est donc
comparer deux biais de selection autant que deux algorithmes.

Ce script corrige ce biais : il reprend le meilleur placement de chaque algorithme sur chaque
instance et le reevalue plusieurs fois independamment. La mediane de ces tirages est le niveau
reel du placement, celui qu'on obtiendrait a l'examen en le rendant.

    python reevaluer_ccl04.py
    python reevaluer_ccl04.py --tirages 11
    python reevaluer_ccl04.py --fichier results/hybrid/demo.jsonl --out results/hybrid/demo_reevalue.json
"""

import argparse
import collections
import json
import statistics
from concurrent.futures import ProcessPoolExecutor

from goc import source_bridge
from optimizer.instance import load_instance

FICHIER = "results/hybrid/ccl04_local_search.jsonl"
SORTIE = "results/hybrid/ccl04_reevaluation.json"


def meilleurs_par_algo(fichier):
    """Lit un fichier de resultats et garde, par instance et par algorithme, la meilleure graine.

    Renvoie {instance_id: {algorithme: (cout_annonce, placement)}}.
    """
    tableau = collections.defaultdict(dict)
    with open(fichier) as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne:
                continue
            d = json.loads(ligne)
            instance_id, algo = d["instance_id"], d["algorithm"]
            if algo not in tableau[instance_id] or d["best_cost"] < tableau[instance_id][algo][0]:
                tableau[instance_id][algo] = (d["best_cost"], d["best_mapping"])
    return tableau


def _reevaluer_instance(args):
    """Charge une instance une seule fois et reevalue tous ses candidats (un processus par instance)."""
    instance_id, candidats, tirages = args
    instance = load_instance(instance_id)
    resultats = {}
    for algo, (annonce, placement) in candidats.items():
        echantillon = sorted(
            source_bridge.fitness(placement, instance.circuit, instance.backend)
            for _ in range(tirages)
        )
        resultats[algo] = {
            "annonce": annonce,
            "mediane": statistics.median(echantillon),
            "min": echantillon[0],
            "max": echantillon[-1],
            "tirages": echantillon,
            "mapping": placement,
        }
    return instance_id, resultats


def reevaluer(fichier=FICHIER, tirages=7, workers=4):
    """Reevalue le meilleur placement de chaque algorithme, une instance par processus."""
    tableau = meilleurs_par_algo(fichier)
    taches = [(i, candidats, tirages) for i, candidats in sorted(tableau.items())]
    with ProcessPoolExecutor(max_workers=min(workers, len(taches))) as executor:
        return dict(executor.map(_reevaluer_instance, taches))


def tableau_texte(resultats, tirages):
    """Tableau `annonce -> mediane [min-max]`, une ligne par algorithme, une colonne par instance."""
    instances = sorted(resultats)
    algos = sorted({a for r in resultats.values() for a in r})
    lignes = [
        f"MEDIANE DE {tirages} REEVALUATIONS du meilleur placement de chaque algorithme",
        "(annonce = le chiffre unique de la campagne ; mediane = le niveau reel)",
        "",
        "algorithme".ljust(16) + "".join(f"inst {i}".ljust(20) for i in instances),
    ]
    for algo in algos:
        ligne = algo.ljust(16)
        for i in instances:
            r = resultats[i].get(algo)
            cellule = "-" if r is None else f"{r['annonce']} -> {r['mediane']:.0f} [{r['min']}-{r['max']}]"
            ligne += cellule.ljust(20)
        lignes.append(ligne)
    lignes.append("")
    for i in instances:
        gagnant = min(resultats[i], key=lambda a: resultats[i][a]["mediane"])
        r = resultats[i][gagnant]
        lignes.append(f"instance {i} : {gagnant}, mediane {r['mediane']:.0f} (annonce {r['annonce']})")
        lignes.append("    " + repr(r["mapping"]))
    return "\n".join(lignes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fichier", default=FICHIER, help="resultats a reevaluer (JSON Lines)")
    parser.add_argument("--tirages", type=int, default=7, help="evaluations independantes par placement")
    parser.add_argument("--workers", type=int, default=4, help="processus (une instance par processus)")
    parser.add_argument("--out", default=SORTIE, help="fichier JSON de sortie")
    args = parser.parse_args()

    resultats = reevaluer(args.fichier, args.tirages, args.workers)
    print(tableau_texte(resultats, args.tirages))

    with open(args.out, "w") as f:
        json.dump(
            {"source": args.fichier, "tirages": args.tirages,
             "resultats": {str(k): v for k, v in resultats.items()}},
            f, indent=1,
        )
    print(f"\nenregistre : {args.out}")


if __name__ == "__main__":
    main()
