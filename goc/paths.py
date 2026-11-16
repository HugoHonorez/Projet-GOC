"""Chemins importants du projet, calculés une seule fois pour être réutilisés partout."""

from pathlib import Path

# Dossier racine du projet : ce fichier est dans goc/, donc la racine est le dossier parent de goc/.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Dossier de travail temporaire (utilisé seulement si le dossier d'instances ne s'appelle pas « Instances »).
CACHE_ROOT = PROJECT_ROOT / ".goc_cache"
# Dossier où les notebooks enregistrent leurs mesures et exécutions (le « cahier de laboratoire »).
RESULTS_ROOT = PROJECT_ROOT / "results"
# Dossier où sont écrits les fichiers à rendre (GroupeX_Challenge_N.txt).
SOLUTIONS_ROOT = PROJECT_ROOT / "solutions"


def find_instances_dir(root=PROJECT_ROOT):
    """Renvoie le dossier qui contient les fichiers Instance_*.qasm.

    On cherche d'abord un dossier nommé exactement « Instances » (le nom attendu par source.py),
    puis n'importe quel dossier dont le nom commence par « Instances » (ex. « Instances-20261109 »).
    """
    # Liste des candidats : « Instances » en premier, puis les autres variantes triées par nom.
    candidates = [root / "Instances", *sorted(root.glob("Instances*"))]
    for candidate in candidates:
        # On garde le premier dossier qui existe et qui contient au moins un fichier d'instance.
        if candidate.is_dir() and any(candidate.glob("Instance_*.qasm")):
            return candidate
    # Aucun dossier trouvé : on arrête avec un message clair.
    raise FileNotFoundError(f"No directory containing Instance_*.qasm found in {root}")
