"""Écriture des fichiers à rendre, au format demandé dans le sujet.

Fichier `<Groupe>_Challenge_<instance>.txt` contenant une seule ligne : le placement puis son coût.
Exemple : `Groupe18_Challenge_0.txt` contenant `1 0 2 53`.
"""

from pathlib import Path

from goc.paths import SOLUTIONS_ROOT


def solution_filename(group, instance_id):
    """Nom du fichier de rendu, par ex. « Groupe18_Challenge_3.txt »."""
    return f"{group}_Challenge_{instance_id}.txt"


def solution_line(mapping, cost):
    """Contenu du fichier : les valeurs du placement puis le coût, séparés par des espaces."""
    return " ".join(str(int(v)) for v in [*mapping, cost])


def read_solution_cost(path, n):
    """Coût écrit dans un fichier solution existant (dernier nombre), ou None s'il n'y en a pas.

    Un fichier valide contient n + 1 nombres (placement + coût) ; sinon on considère qu'il n'a pas de coût.
    """
    values = Path(path).read_text(encoding="utf-8").split()
    return float(values[-1]) if len(values) == n + 1 else None


def write_solution(mapping, cost, instance_id, group="Groupe0", directory=SOLUTIONS_ROOT):
    """Écrit (ou remplace) le fichier solution d'une instance et renvoie son chemin."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / solution_filename(group, instance_id)
    path.write_text(solution_line(mapping, cost) + "\n", encoding="utf-8")
    return path


def write_solution_if_better(mapping, cost, instance_id, group="Groupe0", directory=SOLUTIONS_ROOT):
    """Écrit le fichier seulement si le nouveau coût est strictement meilleur que celui déjà enregistré.

    Évite d'écraser une meilleure solution trouvée lors d'un essai précédent.
    Renvoie (chemin, écrit ou non, ancien coût ou None).
    """
    path = Path(directory) / solution_filename(group, instance_id)
    # Coût actuellement enregistré (None si le fichier n'existe pas ou n'a pas de coût).
    previous = read_solution_cost(path, len(mapping)) if path.exists() else None
    if previous is not None and previous <= cost:
        return path, False, previous
    return write_solution(mapping, cost, instance_id, group, directory), True, previous


def write_result(result, group="Groupe0", directory=SOLUTIONS_ROOT):
    """Écrit le fichier solution à partir d'un `Result` (meilleur placement et meilleur coût)."""
    return write_solution(result.best_mapping, result.best_cost, result.instance_id, group, directory)


def write_result_if_better(result, group="Groupe0", directory=SOLUTIONS_ROOT):
    """Comme `write_result`, mais sans écraser une solution déjà meilleure."""
    return write_solution_if_better(result.best_mapping, result.best_cost, result.instance_id, group, directory)
