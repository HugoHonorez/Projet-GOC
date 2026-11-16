"""Pont vers `source.py` : charger une instance et calculer la fitness avec le code du cours, sans le modifier.

Toutes les évaluations de fitness du projet passent par ce fichier, ce qui garantit qu'on mesure
exactement la même chose que la fonction `fitness_inner` fournie par l'enseignant.
"""

import contextlib
import os
import shutil
import sys
import warnings
from pathlib import Path

from qiskit.transpiler import Layout
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from .paths import CACHE_ROOT, PROJECT_ROOT, find_instances_dir

# Numéros d'instance que `source.instance_selector` sait charger (les autres retombent sur l'instance 1).
SUPPORTED_INSTANCES = (1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13)

# Pour pouvoir écrire « import source », le dossier racine du projet doit être dans le chemin de recherche de Python.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# On empêche Python de créer un dossier __pycache__ à côté de source.py (on ne touche pas aux fichiers du cours).
_write_bytecode = sys.dont_write_bytecode
sys.dont_write_bytecode = True
# source.py déclenche des avertissements (chemins Windows, fonctions Qiskit dépréciées) : on les masque à l'import.
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import source
# On remet le réglage d'origine.
sys.dont_write_bytecode = _write_bytecode


@contextlib.contextmanager
def instances_workdir(instances_dir):
    """Se place temporairement dans un dossier où `.\\Instances\\Instance_N.qasm` existe.

    `source.instance_selector` lit le fichier QASM avec un chemin relatif au dossier courant.
    - Si le dossier d'instances s'appelle déjà « Instances », on se place dans son dossier parent.
    - Sinon, on copie les instances dans `.goc_cache/workspace/Instances` et on se place dans `.goc_cache/workspace`.
    À la fin (même en cas d'erreur), on revient dans le dossier de départ.
    """
    if instances_dir.name == "Instances":
        workdir = instances_dir.parent
    else:
        workdir = CACHE_ROOT / "workspace"
        target = workdir / "Instances"
        # On repart d'une copie propre pour refléter exactement le contenu actuel du dossier d'instances.
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(instances_dir, target)
    # On mémorise le dossier courant pour pouvoir y revenir.
    previous = os.getcwd()
    os.chdir(workdir)
    try:
        # Le code placé dans le bloc « with » s'exécute ici, depuis le bon dossier.
        yield
    finally:
        os.chdir(previous)


def load_instance(instance_id, instances_dir=None):
    """Charge une instance avec `source.instance_selector` et renvoie (backend, circuit, n, m).

    - backend : la puce (ses qubits physiques et leurs connexions) ;
    - circuit : le circuit quantique à placer ;
    - n : nombre de qubits logiques du circuit ; m : nombre de qubits physiques de la puce.
    """
    if instance_id not in SUPPORTED_INSTANCES:
        raise ValueError(f"Instance {instance_id} is not supported by source.instance_selector")
    # Dossier d'instances donné explicitement, ou trouvé automatiquement.
    directory = Path(instances_dir) if instances_dir else find_instances_dir()
    # On se place dans le bon dossier et on masque les avertissements de Qiskit pendant le chargement.
    with instances_workdir(directory.resolve()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return source.instance_selector(instance_id)


def fitness(mapping, circuit, backend):
    """Calcule la fitness officielle : la profondeur du circuit après routage (appel direct à `fitness_inner`).

    `mapping[i]` est le qubit physique attribué au qubit logique i. Le résultat est bruité :
    deux appels avec le même placement peuvent donner des valeurs différentes.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return source.fitness_inner(list(mapping), circuit, backend)


def routed_circuit(mapping, circuit, backend):
    """Reproduit la chaîne de `fitness_inner` mais renvoie le circuit routé lui-même, pas seulement sa profondeur.

    Sert uniquement à visualiser ce que Qiskit fabrique (portes traduites, SWAP ajoutés).
    Les 6 lignes ci-dessous sont les mêmes que dans `source.fitness_inner`.
    """
    # Le registre de qubits logiques du circuit (q[0], q[1], ...).
    register = circuit.qregs[0]
    # Le placement initial imposé : qubit logique i -> qubit physique mapping[i].
    layout = Layout({register[i]: mapping[i] for i in range(len(mapping))})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Chaîne de transpilation de niveau 3 (optimisation maximale) pour cette puce et ce placement.
        manager = generate_preset_pass_manager(3, backend, initial_layout=layout)
        # On retire deux étapes de placement automatique, exactement comme fitness_inner, pour garder notre placement.
        manager.layout.remove(1)
        manager.layout.remove(1)
        # Exécution : traduction des portes, routage (ajout de SWAP), optimisation.
        return manager.run(circuit)
