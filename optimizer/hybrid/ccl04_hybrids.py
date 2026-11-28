"""Hybrides « métaheuristique constructive × recherche locale de l'équipe sur f ».

Les deux formes de la classification du cours, pour GRASP et pour la colonie de fourmis,
avec la recherche locale de l'équipe (`descente` et `VND` de Recherche_locale.py) :

- bas niveau (intégratif) : la recherche locale est branchée DANS la métaheuristique, sur la
  solution de chaque itération (`each_iteration`), via les briques `ccl04_descente` / `ccl04_vnd` ;
- haut niveau (relais) : la métaheuristique constructive consomme (1 - part) du budget, puis
  `iterated_local_search` ou `variable_neighbourhood_search` reprend la meilleure solution trouvée
  avec la part restante (`then_algorithm`, qui lui passe `initial_mapping`).

Les témoins sans recherche locale sont inclus : c'est l'écart avec eux, au même budget, qui mesure
l'apport de la recherche locale. Les comparer à des budgets différents ne veut rien dire (voir le
commentaire sur le budget dans `run_ccl04_hybrids.py`).

Lancement : `python run_ccl04_hybrids.py` à la racine du dépôt.
"""

from .spec import Hybrid

# Paramètres des métaheuristiques constructives (réglages des notebooks 04 et 05).
GRASP = {"alpha": 0.2}
ACO = {"ants": 8, "evaluated": 3}
# Paramètres de la recherche locale de l'équipe.
ILS = {"k": 3}
VNS = {"k_max": 5}


def _specs(part, max_evaluations, grasp, aco, ils, vns):
    """Les douze descriptions d'hybrides, avant `build()`."""
    return {
        # --- témoins : les constructives seules, et la recherche locale seule ---------------
        "grasp": Hybrid("grasp", **grasp),
        "aco": Hybrid("ant_colony", **aco),
        "ils": Hybrid("iterated_local_search", **ils),
        "vns": Hybrid("variable_neighbourhood_search", **vns),

        # --- bas niveau : la recherche locale de l'équipe DANS la métaheuristique -----------
        "grasp+descente": Hybrid("grasp", **grasp).each_iteration("ccl04_descente", max_evaluations=max_evaluations),
        "grasp+vnd": Hybrid("grasp", **grasp).each_iteration("ccl04_vnd", max_evaluations=max_evaluations),
        "aco+descente": Hybrid("ant_colony", **aco).each_iteration("ccl04_descente", max_evaluations=max_evaluations),
        "aco+vnd": Hybrid("ant_colony", **aco).each_iteration("ccl04_vnd", max_evaluations=max_evaluations),

        # --- haut niveau : relais, la constructive puis la recherche locale -----------------
        "grasp>ils": Hybrid("grasp", **grasp).then_algorithm("iterated_local_search", share=part, **ils),
        "grasp>vns": Hybrid("grasp", **grasp).then_algorithm("variable_neighbourhood_search", share=part, **vns),
        "aco>ils": Hybrid("ant_colony", **aco).then_algorithm("iterated_local_search", share=part, **ils),
        "aco>vns": Hybrid("ant_colony", **aco).then_algorithm("variable_neighbourhood_search", share=part, **vns),
    }


def ccl04_hybrides(part=0.4, max_evaluations=200, grasp=None, aco=None, ils=None, vns=None):
    """{nom: (fonction run, paramètres)}, prêt à passer à `run_grid`.

    - part : part du budget laissée à la recherche locale dans les hybrides en relais ;
    - max_evaluations : part d'évaluations allouée à une descente dans les hybrides intégratifs ;
    - grasp / aco / ils / vns : dictionnaires pour écraser les paramètres par défaut ci-dessus.
    """
    specs = _specs(part, max_evaluations,
                   {**GRASP, **(grasp or {})}, {**ACO, **(aco or {})},
                   {**ILS, **(ils or {})}, {**VNS, **(vns or {})})
    return {nom: spec.build() for nom, spec in specs.items()}


def describe(part=0.4, max_evaluations=200):
    """Description lisible de chaque hybride, une ligne par étape."""
    specs = _specs(part, max_evaluations, GRASP, ACO, ILS, VNS)
    return "\n\n".join(f"[{nom}]\n{spec.describe()}" for nom, spec in specs.items())
