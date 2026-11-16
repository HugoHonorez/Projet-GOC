"""Extraction d'informations simples à partir d'un circuit Qiskit : portes, interactions entre qubits, statistiques.

Ces données (des listes et dictionnaires Python) sont faciles à afficher, à envoyer au visualiseur web
ou à transformer en tableaux NumPy pour les calculs.
"""

from collections import Counter

# Opérations qui ne sont pas de vraies portes de calcul : on les ignore partout.
IGNORED_OPERATIONS = {"barrier", "measure"}


def format_param(value):
    """Transforme un paramètre de porte (angle, etc.) en texte court, par ex. 1.5707963 -> "1.5708"."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        # Paramètre symbolique (non numérique) : on le garde tel quel, en texte.
        return str(value)
    # « .6g » : 6 chiffres significatifs au maximum, notation compacte.
    return f"{number:.6g}"


def operations(circuit):
    """Liste des portes du circuit, dans l'ordre, sous la forme {"name", "qubits", "params"}."""
    result = []
    for instruction in circuit.data:
        name = instruction.operation.name
        # On saute les barrières et les mesures.
        if name in IGNORED_OPERATIONS:
            continue
        result.append({
            "name": name,
            # Indices des qubits touchés par la porte (find_bit convertit un objet qubit en numéro).
            "qubits": [circuit.find_bit(q).index for q in instruction.qubits],
            # Paramètres de la porte (angles), mis en forme.
            "params": [format_param(p) for p in instruction.operation.params],
        })
    return result


def gate_counts(circuit):
    """Nombre de portes de chaque type, par ex. {"cx": 50, "h": 10}."""
    counts = circuit.count_ops()
    return {name: count for name, count in counts.items() if name not in IGNORED_OPERATIONS}


def interactions(circuit):
    """Paires de qubits logiques qui partagent des portes à 2 qubits, avec le nombre de portes de chaque paire.

    Renvoie une liste de {"a", "b", "count"} avec a < b. C'est le « graphe d'interaction » du circuit :
    les sommets sont les qubits, les arêtes sont les paires, le poids est le nombre de portes.
    """
    # Counter compte automatiquement les occurrences de chaque paire.
    pairs = Counter()
    for instruction in circuit.data:
        # Numéros des qubits de la porte, triés pour que la paire (a, b) soit toujours écrite avec a < b.
        indices = sorted(circuit.find_bit(q).index for q in instruction.qubits)
        # Les portes à 1 qubit et les barrières/mesures ne créent pas d'interaction.
        if len(indices) < 2 or instruction.operation.name in IGNORED_OPERATIONS:
            continue
        # Pour une porte à 3 qubits (rare), on compte chaque paire de qubits.
        for i, a in enumerate(indices):
            for b in indices[i + 1:]:
                pairs[(a, b)] += 1
    # Conversion en liste de dictionnaires, triée par paire.
    return [{"a": a, "b": b, "count": count} for (a, b), count in sorted(pairs.items())]


def two_qubit_gate_count(circuit):
    """Nombre total de portes portant sur au moins 2 qubits."""
    return sum(
        1 for instruction in circuit.data
        if len(instruction.qubits) >= 2 and instruction.operation.name not in IGNORED_OPERATIONS
    )


def summary(circuit):
    """Résumé chiffré d'un circuit : nombre de qubits, profondeur, nombre de portes, portes à 2 qubits, types de portes."""
    return {
        "numQubits": circuit.num_qubits,
        # Profondeur = nombre de couches de portes exécutées en parallèle (c'est ce que mesure la fitness).
        "depth": circuit.depth(),
        "size": sum(gate_counts(circuit).values()),
        "twoQubitGates": two_qubit_gate_count(circuit),
        "gateCounts": gate_counts(circuit),
    }
