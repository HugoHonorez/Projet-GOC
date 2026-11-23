"""Hasard reproductible pour les algorithmes écrits avec le module standard `random`.

Les codes de l'équipe utilisent `random.choice`, `random.sample`, `random.random`... Pour les garder tels quels,
on leur donne un objet `random.Random` (même interface, mêmes tirages que le module `random`) dont la graine
est tirée du générateur NumPy `rng` de l'exécution : même graine d'exécution = même suite de tirages.
"""

import random as _random


def python_random(rng):
    """Générateur `random.Random` initialisé à partir de `rng` (np.random.Generator)."""
    return _random.Random(int(rng.integers(2**32)))
