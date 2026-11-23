"""Hybridation de métaheuristiques (classification du cours).

- Bas niveau : une brique (recherche locale...) est un composant d'une métaheuristique, via son paramètre `hooks`
  (voir hooks.py) : sur chaque solution candidate, ou à la fin de chaque itération.
- Haut niveau, mode relais : des étapes indépendantes enchaînées, chacune avec une part du budget, la sortie de l'une
  étant l'entrée de la suivante (voir optimizer/algorithms/hybrid.py).
- Le constructeur `Hybrid` (spec.py) compose les deux dans un notebook.
"""

from .hooks import improve_iteration, improve_solution, normalized
from .improvers import IMPROVERS
from .spec import Hybrid
