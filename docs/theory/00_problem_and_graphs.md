# 0. Le problème, les graphes et les outils communs

Notations du cours (*Métaheuristiques, parties 1 et 2*) : $\Omega$ l'espace des solutions, $s$ une solution, $f$ la fonction objectif, $N(s)$ le voisinage, $f^\star = \min_{s \in \Omega} f(s)$.

---

## 0.1 Données d'une instance

Une instance est un couple (circuit quantique $Q$, puce). Elle est chargée par `source.instance_selector(k)`.

| Symbole | Signification |
|---|---|
| $L = \lbrace 0, \dots, n-1 \rbrace$ | qubits **logiques** (ceux du circuit $Q$) |
| $P = \lbrace 0, \dots, m-1 \rbrace$ | qubits **physiques** (ceux de la puce), $n \le m$ |
| $W = (w_{ij}) \in \mathbb{N}^{n \times n}$ | nombre de portes à 2 qubits entre $i$ et $j$ |
| $d(u, v)$ | distance sur la puce entre $u, v \in P$ |
| $B$ | budget de vraies évaluations de $f$ (ici $B = 200$) |

| Instance | $n$ | $m$ | Puce | $\lvert E_I \rvert$ | $\sum w_{ij}$ | $\lvert E_C \rvert$ | diamètre | $\lvert \Omega \rvert$ | $\lvert N(s) \rvert$ |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 16 | échelle 2×8 | 11 | 11 | 22 | 8 | $8{,}7 \cdot 10^{11}$ | 114 |
| 2 | 16 | 16 | échelle 2×8 | 15 | 150 | 22 | 8 | $2{,}1 \cdot 10^{13}$ | 120 |
| 3 | 10 | 16 | échelle 2×8 | 45 | 50 | 22 | 8 | $2{,}9 \cdot 10^{10}$ | 105 |
| 4 | 19 | 20 | grille (IBM 20 q.) | 18 | 18 | 23 | 7 | $2{,}4 \cdot 10^{18}$ | 190 |
| 5 | 12 | 20 | grille (IBM 20 q.) | 31 | 148 | 23 | 7 | $6{,}0 \cdot 10^{13}$ | 162 |
| 6 | 14 | 20 | grille (IBM 20 q.) | 14 | 28 | 23 | 7 | $3{,}4 \cdot 10^{15}$ | 175 |
| 7 | 20 | 27 | heavy-hex (IBM 27 q.) | 19 | 19 | 28 | 12 | $2{,}2 \cdot 10^{24}$ | 330 |
| 8 | 20 | 27 | heavy-hex (IBM 27 q.) | 20 | 20 | 28 | 12 | $2{,}2 \cdot 10^{24}$ | 330 |
| 9 | 25 | 27 | heavy-hex (IBM 27 q.) | 24 | 24 | 28 | 12 | $5{,}4 \cdot 10^{27}$ | 350 |

($\lvert \Omega \rvert$ et $\lvert N(s) \rvert$ sont définis en 0.5 et 0.8.)

---

## 0.2 Graphe d'interaction $G_I$ (le circuit)

On parcourt les portes du circuit. Chaque porte à 2 qubits sur $(a, b)$ incrémente un compteur :

$$
w_{ab} \leftarrow w_{ab} + 1, \qquad w_{ba} = w_{ab}, \qquad w_{ii} = 0
$$

$$
G_I = (L, E_I, w), \qquad E_I = \lbrace \lbrace i, j \rbrace : w_{ij} > 0 \rbrace
$$

- **Poids** $w_{ij}$ : nombre de portes entre $i$ et $j$, qui doivent toutes être exécutées sur deux qubits physiques voisins.
- **Force** d'un qubit, c'est-à-dire son nombre total de portes à 2 qubits :

$$
\mathrm{str}(i) = \sum_{j \in L} w_{ij}
$$

- **Interprétation** : $G_I$ ne dépend que du circuit, pas de la puce. Les portes à 1 qubit n'y apparaissent pas : elles ne posent jamais de problème de placement.

Exemples : l'instance 3 (QFT) a un graphe complet $K_{10}$ ($\lvert E_I \rvert = 45 = \binom{10}{2}$). Les instances 1, 4, 7, 8 et 9 ont un graphe proche d'une chaîne ou d'un arbre ($\lvert E_I \rvert \approx n - 1$).

---

## 0.3 Graphe de couplage $G_C$ (la puce)

$$
G_C = (P, E_C), \qquad \lbrace u, v \rbrace \in E_C \iff \text{une porte à 2 qubits est possible entre } u \text{ et } v
$$

$E_C$ est fourni par le backend Qiskit de `source.py`. Les trois puces ont toutes un degré maximal de 3 :

$$
\deg_C(u) = \lvert \lbrace v : \lbrace u, v \rbrace \in E_C \rbrace \rvert \le 3
$$

**Interprétation :** un qubit logique de force élevée ne peut avoir que 3 voisins directs au plus. Tout sommet de $G_I$ de degré supérieur à 3 (par exemple dans la QFT) impose donc des SWAP, quel que soit le placement.

---

## 0.4 Distance sur la puce

$d(u, v)$ est la longueur (en nombre d'arêtes) d'un plus court chemin de $u$ à $v$ dans $G_C$.

**Calcul par parcours en largeur (BFS)** depuis chaque $u \in P$. On construit les « couches » successives :

$$
D_0(u) = \lbrace u \rbrace, \qquad D_{k+1}(u) = \Big\lbrace v \notin \textstyle\bigcup_{l \le k} D_l(u) \;:\; \exists\, x \in D_k(u),\ \lbrace x, v \rbrace \in E_C \Big\rbrace
$$

$$
d(u, v) = k \iff v \in D_k(u)
$$

- La matrice $D = (d(u,v))$, de taille $m \times m$, est calculée une seule fois en $O\big(m\,(m + \lvert E_C \rvert)\big)$ (fonction `distance_matrix` dans `optimizer/instance.py`).
- **Propriétés** : $d$ est une distance (symétrique, inégalité triangulaire). De plus, $d(u, v) = 1 \iff \lbrace u, v \rbrace \in E_C$.
- **Diamètre** : $\max_{u,v} d(u, v)$, soit 8, 7 et 12 pour les trois puces.

**Interprétation :** pour exécuter une porte entre deux qubits physiques à distance $d$, le routage doit les rapprocher. Chaque SWAP réduit la distance d'au plus 1, donc il faut au moins $d - 1$ SWAP si la porte est considérée seule.

---

## 0.5 Espace des solutions $\Omega$ et codage

Une **solution** (un placement) est une application injective : chaque qubit logique va sur un qubit physique distinct.

$$
s : L \to P, \qquad s(i) \ne s(j) \;\; \forall i \ne j
$$

$$
\Omega = \lbrace s : L \to P \text{ injective} \rbrace, \qquad \lvert \Omega \rvert = \frac{m!}{(m - n)!}
$$

Le format du rendu est le vecteur $(s(0), \dots, s(n-1))$.

**Codage par permutation** (`optimizer/representation.py`). On travaille sur $\sigma \in \mathfrak{S}_m$, une permutation de $P$ :

$$
s(i) = \sigma(i) \quad (0 \le i < n), \qquad \lbrace \sigma(n), \dots, \sigma(m-1) \rbrace = \text{qubits physiques libres}
$$

- **Validité garantie** : toute permutation donne une solution valide, et toute transposition de $\sigma$ en donne une autre.
- **Redondance** : chaque $s \in \Omega$ est représenté par $(m-n)!$ permutations, puisque l'ordre des libres n'a pas d'importance.

**Interprétation :** $\lvert \Omega \rvert$ va de $10^{10}$ à $10^{27}$, alors que $B = 200$. On n'évaluera donc jamais qu'une fraction $\le 10^{-8}$ de l'espace : l'énumération est exclue, d'où le recours aux métaheuristiques.

---

## 0.6 La fonction objectif $f$ (fitness)

$$
f(s) = \mathrm{depth}\big(R(Q, s)\big)
$$

Ici, $R(Q, s)$ est le circuit compilé par Qiskit (`fitness_inner`, niveau d'optimisation 3) avec le placement initial $s$ imposé. Le routage Sabre insère les SWAP nécessaires pour que chaque porte à 2 qubits porte sur une arête de $E_C$.

**Profondeur.** Le circuit est un graphe orienté acyclique de portes (une porte dépend des portes précédentes sur ses qubits). La profondeur est le nombre de portes du plus long chemin :

$$
\mathrm{depth}(R) = \max_{\gamma \,\in\, \text{chemins du DAG}} \lvert \gamma \rvert
$$

C'est le nombre minimal de « couches » de portes exécutables en parallèle.

**Bruit.** Le routage Sabre est aléatoire (sans graine fixée), donc $f(s)$ est une **variable aléatoire** :

$$
f(s) = F(s) + \varepsilon_s, \qquad F(s) = \mathbb{E}[f(s)], \qquad \operatorname{Var}(\varepsilon_s) = \varsigma_s^2
$$

Valeurs mesurées dans le notebook 02 (écart-type moyen $\bar\varsigma$ sur 10 réévaluations) :

| Instance | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| $\bar\varsigma$ | 2,2 | 10,6 | 6,8 | 1,6 | 3,5 | 2,6 | 0,9 | 4,7 | 1,3 |
| $\bar\varsigma / \bar f$ | 4,6 % | 8,4 % | 3,8 % | 2,8 % | 0,9 % | 4,4 % | 0,9 % | 8,6 % | 0,9 % |

**Problème d'optimisation** (le cours, avec budget) :

$$
f^\star = \min_{s \in \Omega} f(s) \qquad \text{en au plus } B \text{ évaluations de } f
$$

**Coût.** Une évaluation prend de 0,03 à 0,3 s. C'est le budget $B$, et non le temps de calcul des algorithmes, qui limite la recherche.

**Malédiction du vainqueur.** Le meilleur coût observé est biaisé vers le bas :

$$
\mathbb{E}\Big[\min_{k \le K} f(s_k)\Big] \;\le\; \min_{k \le K} F(s_k)
$$

Plus on évalue de solutions, plus le minimum observé est optimiste. D'où les réévaluations des meilleures solutions dans les notebooks.

---

## 0.7 Le coût de distance $C$ (substitut gratuit)

$$
C(s) = \sum_{\lbrace i, j \rbrace \in E_I} w_{ij}\,\big(d(s(i), s(j)) - 1\big)
$$

- **Signe** : $C(s) \ge 0$. De plus, $C(s) = 0 \iff$ toute paire qui interagit est placée sur une arête de la puce, c'est-à-dire que $s$ est un plongement de $G_I$ dans $G_C$. Aucun SWAP n'est alors nécessaire.
- **Interprétation** : chaque terme est une borne inférieure du nombre de SWAP qu'imposeraient les $w_{ij}$ portes entre $i$ et $j$ si elles étaient routées seules. $C$ estime donc la quantité de routage.
- **Coût** : $O(\lvert E_I \rvert)$, quelques microsecondes, contre environ 0,1 s pour $f$.
- **Limite** : $C$ ignore l'ordre des portes et le parallélisme, alors que $f$ mesure une profondeur.

Corrélation de Spearman $\rho_S(C, F)$ mesurée dans le notebook 02 :

| Instance | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| $\rho_S$ | 0,16 | 0,81 | 0,27 | 0,27 | 0,33 | 0,76 | 0,85 | 0,84 | 0,74 |

**Conséquence pour toutes les métaheuristiques :** $C$ est un bon guide sur les instances 2 et 6 à 9, un guide médiocre sur les instances 1, 3, 4 et 5. Toute méthode qui s'appuie fortement sur $C$ risque donc d'être piégée sur ces dernières.

---

## 0.8 Voisinage, recherche locale, optimum local

**Mouvement** (cours : *transposition*). On échange les positions $a$ et $b$ de $\sigma$, avec $a < n$ :

$$
\sigma' = \sigma \circ (a\ b)
$$

- Si $b < n$ : les qubits logiques $a$ et $b$ échangent leurs qubits physiques.
- Si $b \ge n$ : le qubit logique $a$ est déplacé vers le qubit physique libre $\sigma(b)$.

Une transposition entre deux libres ($a, b \ge n$) ne change pas $s$ : elle est exclue.

**Voisinage :**

$$
N(s) = \lbrace \sigma \circ (a\ b) : 0 \le a < n,\ a < b < m \rbrace, \qquad \lvert N(s) \rvert = \binom{m}{2} - \binom{m-n}{2} = n(m-1) - \frac{n(n-1)}{2}
$$

**Variation incrémentale de $C$.** Elle se calcule en $O(\deg_I(a) + \deg_I(b))$ au lieu de $O(\lvert E_I \rvert)$. Notons $u = s(a)$ et $v = s(b)$.

*Échange de deux qubits logiques $a, b$.* L'arête $\lbrace a, b \rbrace$ elle-même ne change pas, car $d$ est symétrique :

$$
\Delta C = \sum_{k \in N_I(a) \setminus \lbrace b \rbrace} w_{ak}\,\big[d(v, s(k)) - d(u, s(k))\big] \;+\; \sum_{k \in N_I(b) \setminus \lbrace a \rbrace} w_{bk}\,\big[d(u, s(k)) - d(v, s(k))\big]
$$

*Déplacement de $a$ vers un qubit physique libre $v$ :*

$$
\Delta C = \sum_{k \in N_I(a)} w_{ak}\,\big[d(v, s(k)) - d(u, s(k))\big]
$$

**Optimum local** (cours) : $s$ est un minimum local relativement à $N$ si $f(s) \le f(s')$ pour tout $s' \in N(s)$.

**Méthode de descente** (cours, partie 1) :

```
s ← s0
répéter
    choisir s' ∈ N(s)
    si f(s') < f(s) alors s ← s'
jusqu'à f(s') ≥ f(s) pour tout s' ∈ N(s)
```

**Appliquée à notre problème :**
- **Sur $f$**, un parcours complet de $N(s)$ coûte 105 à 350 évaluations, soit plus que $B$. Une descente complète sur $f$ est donc impossible ; on ne peut qu'échantillonner $N(s)$.
- **Sur $C$**, la descente est gratuite. Le projet la fournit avec `surrogate_descent`, qui fait $K$ essais aléatoires et accepte si $\Delta C \le 0$ ; le « $\le$ » permet de traverser les plateaux. Elle mène à un optimum local **de $C$**, pas de $f$.

---

## 0.9 Intensification et diversification

D'après le cours :
- **intensifier**, c'est concentrer l'effort autour des meilleures solutions (recherche locale) ;
- **diversifier**, c'est explorer d'autres régions (recherche aléatoire).

Avec un budget aussi petit ($B = 200$), le cours indique qu'il faut **favoriser l'intensification**. Ici, le bruit ($\varsigma$) ajoute une contrainte : intensifier sur des écarts de $f$ inférieurs à $\varsigma$ revient à suivre le bruit.

---

## 0.10 Tableau récapitulatif des notations

| Symbole | Signification | Dans le code |
|---|---|---|
| $n, m$ | nombres de qubits logiques et physiques | `instance.n`, `instance.m` |
| $w_{ij}$ | portes à 2 qubits entre $i$ et $j$ | `instance.pairs`, `instance.weights` |
| $E_C$ | arêtes de la puce | `instance.edges` |
| $d(u,v)$ | distance sur la puce | `instance.distances[u, v]` |
| $s$, $\sigma$ | solution, permutation qui la code | `mapping`, `permutation` |
| $f(s)$ | vraie fitness (bruitée, coûteuse) | `problem.fitness(mapping)` |
| $C(s)$ | coût de distance (gratuit) | `problem.surrogate(mapping)` |
| $B$ | budget d'évaluations | `problem.budget` |
| $N(s)$ | voisinage par transposition | `representation.swap_moves` |
