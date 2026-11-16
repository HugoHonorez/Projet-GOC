"""Informations sur les puces : connexions entre qubits physiques et coordonnées pour les dessiner."""

import math

# Positions (ligne, colonne) des 27 qubits de la puce « heavy-hex » d'IBM (Fake27QPulseV1), pour un dessin fidèle.
HEAVY_HEX_27 = [
    (1, 0), (1, 1), (2, 1), (3, 1), (1, 2), (3, 2), (0, 3), (1, 3), (3, 3), (4, 3),
    (1, 4), (3, 4), (1, 5), (2, 5), (3, 5), (1, 6), (3, 6), (0, 7), (1, 7), (3, 7),
    (4, 7), (1, 8), (3, 8), (1, 9), (2, 9), (3, 9), (3, 10),
]

# Coordonnées (x, y) de dessin pour chaque puce connue, selon son nombre de qubits.
KNOWN_LAYOUTS = {
    # Puce 16 qubits : une échelle de 2 lignes de 8 (qubits 0 à 7 en haut, 15 à 8 en bas).
    16: [(q, 0) if q < 8 else (15 - q, 1) for q in range(16)],
    # Puce 20 qubits : une grille de 4 lignes de 5.
    20: [(q % 5, q // 5) for q in range(20)],
    # Puce 27 qubits : heavy-hex, on inverse (ligne, colonne) en (x, y).
    27: [(col, row) for row, col in HEAVY_HEX_27],
}


def coupling_edges(backend):
    """Liste des connexions physiques de la puce, sous forme de paires (a, b) triées avec a < b, sans doublon.

    La puce déclare chaque connexion dans les deux sens (a->b et b->a) : on ne garde qu'une paire.
    """
    return sorted({tuple(sorted(edge)) for edge in backend.coupling_map.get_edges()})


def circle_layout(num_qubits):
    """Coordonnées de secours : les qubits disposés en cercle (pour une puce inconnue)."""
    radius = max(2.0, num_qubits / (2 * math.pi))
    return [
        (radius + radius * math.cos(2 * math.pi * q / num_qubits), radius + radius * math.sin(2 * math.pi * q / num_qubits))
        for q in range(num_qubits)
    ]


def coordinates(num_qubits, edges):
    """Coordonnées de dessin [x, y] de chaque qubit physique.

    On utilise la disposition connue de la puce si elle existe et si chaque connexion relie bien
    deux positions voisines ; sinon on se rabat sur un cercle.
    """
    layout = KNOWN_LAYOUTS.get(num_qubits)
    if layout is None or not all(_is_drawable(layout, a, b) for a, b in edges):
        layout = circle_layout(num_qubits)
    return [list(point) for point in layout]


def _is_drawable(layout, a, b):
    """Vrai si les qubits a et b sont à distance 1 sur le dessin (la connexion se dessine comme un trait court)."""
    (xa, ya), (xb, yb) = layout[a], layout[b]
    return math.hypot(xa - xb, ya - yb) <= 1.0001
