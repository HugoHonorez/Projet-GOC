# Théorie : le problème et les métaheuristiques

Développements mathématiques et interprétations, d'abord dans le cas général (notations du cours *Théorie des graphes et optimisation combinatoire, Métaheuristiques*), puis appliqués au placement de qubits.

| Document | Contenu |
|---|---|
| [00_problem_and_graphs.md](00_problem_and_graphs.md) | données d'une instance, graphe d'interaction $G_I$, graphe de la puce $G_C$, distance, espace $\Omega$ et codage, fitness $f$ et bruit, coût de distance $C$, voisinage et recherche locale, notations communes |
| [01_ant_colony.md](01_ant_colony.md) | colonies de fourmis : Ant System et MAX-MIN, puis l'application (phéromones $n \times m$, visibilité $1/(1+g_t)$, évaluation filtrée, mise à jour bornée) |
| [02_grasp.md](02_grasp.md) | GRASP : glouton randomisé, RCL, multi-départ, puis l'application (coût incrémental $g_t$, recherche locale sur $C$ ou sur $f$, lien avec l'ACO) |
| [03_genetic_algorithm.md](03_genetic_algorithm.md) | algorithme génétique : sélection, croisements de permutations, mutation, remplacement, schémas, puis l'application (positions absolues, budget, bruit) |

Lire d'abord le document 00 : les trois autres en reprennent les notations ($s$, $f$, $C$, $g_t$, $N(s)$, $B$).

**Lecture des formules :** les formules s'affichent dans l'aperçu Markdown de VS Code (`Ctrl+Maj+V`) et sur GitHub.
