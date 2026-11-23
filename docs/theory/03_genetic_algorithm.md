# 3. Algorithme génétique / évolutionnaire

Holland (1975). Code : `optimizer/algorithms/genetic.py`. Notebook : `06_genetic`.
Notations du problème : voir [00_problem_and_graphs.md](00_problem_and_graphs.md).

**Terminologie du cours.** Les *algorithmes génétiques* (AG) travaillent avec un codage binaire, les *algorithmes évolutionnaires* (AE) avec un codage réel ou entier. Notre codage étant une permutation d'entiers, on est formellement dans le cas AE. Le schéma (sélection, croisement, mutation, remplacement) est le même ; on garde le nom « algorithme génétique ».

---

## 3.1 Cas général (cours)

### Schéma

```
initialiser(population, N) ;  évaluer(population)
répéter
    parents ← sélectionner(population)             N/2 couples
    enfants ← croiser(parents, P_c)
    muter(enfants, P_m)
    évaluer(enfants)
    population ← remplacer(population, enfants, N)
    actualiser la meilleure solution
jusqu'à fin
```

**Version générique** du cours : $\mu$ parents, $\lambda$ enfants par génération. La population est notée $\mathcal{P}_t = \lbrace s^{(1)}, \dots, s^{(N)} \rbrace$, avec $N = \mu$.

**Génotype et phénotype.** Le génotype est la chaîne de symboles manipulée par les opérateurs. Le phénotype est la solution qu'elle code, dans le formalisme naturel du problème.

### Sélection pour la reproduction (minimisation)

**Roulette.** La probabilité est proportionnelle à la qualité, donc à $1/f$ quand on minimise :

$$
p_i = \frac{1/f(s^{(i)})}{\sum_{j=1}^{N} 1/f(s^{(j)})}
$$

Exemple du cours : coûts $10, 20, 60, 60, 60$. Alors $\sum 1/f = 0{,}1 + 0{,}05 + 3 \times \tfrac{1}{60} = 0{,}2$, d'où $p = \tfrac12, \tfrac14, \tfrac1{12}, \tfrac1{12}, \tfrac1{12}$.

**Tournoi.** On tire $k$ individus au hasard et on les classe : $r = 1$ est le meilleur. On retient celui de rang $r$ avec la probabilité

$$
\mathbb{P}(r) = p\,(1-p)^{r-1} \quad (r < k), \qquad \mathbb{P}(k) = (1-p)^{k-1}
$$

Cas limites (cours) : $(k = N,\ p = 1)$ sélectionne toujours le meilleur ; $k = 1$ est une sélection aléatoire.

Pour un tournoi déterministe ($p = 1$, tirage avec remise), la probabilité de sélectionner l'individu de rang global $r$ dans la population est :

$$
\mathbb{P}_{\mathrm{tournoi}}(r) = \frac{(N - r + 1)^k - (N - r)^k}{N^k}
$$

**Interprétation :**
- La **roulette** dépend des **valeurs** de $f$. Le rapport des probabilités extrêmes vaut $p_{\mathrm{meilleur}} / p_{\mathrm{pire}} = f_{\mathrm{pire}} / f_{\mathrm{meilleur}}$ : quand les coûts sont proches, la sélection devient presque aléatoire.
- Le **tournoi** ne dépend que des **rangs**. Il est invariant par toute transformation croissante de $f$. La pression de sélection se règle directement par $k$ et $p$.

### Croisement (probabilité $P_c$)

Chaque couple est croisé avec la probabilité $P_c$. Sinon, les deux enfants sont des copies des parents.

**Codage binaire** (cours) : croisement **1 point**, **2 points**, ou **uniforme** avec un masque $M \in \lbrace 0, 1 \rbrace^L$ :

$$
c^{(1)}_j = \begin{cases} p^{(1)}_j & M_j = 1 \\ p^{(2)}_j & M_j = 0 \end{cases}
$$

**Codage par permutation : le problème.** Couper et recoller deux permutations ne donne pas une permutation (cours, *GA for the TSP*) : par exemple $A' = 3\,5\,\vert\,2\,3\,4\,6\,\vert\,8\,6\,9$ contient deux fois 3 et deux fois 6. Le cours propose deux croisements adaptés.

*Croisement uniforme de permutations* (cours). Les positions $j \notin M$ gardent le gène de $p^{(1)}$. Les éléments $\lbrace p^{(1)}_j : j \in M \rbrace$ sont replacés sur les positions de $M$ **dans l'ordre où ils apparaissent dans $p^{(2)}$**. Le second enfant s'obtient de manière symétrique, avec le masque complémentaire.
Exemple du cours : $p^{(1)} = 12345$, $p^{(2)} = 54321$, positions à réordonner $\lbrace 1, 2, 4 \rbrace$. Les éléments $\lbrace 1, 2, 4 \rbrace$ apparaissent dans l'ordre $4, 2, 1$ dans $p^{(2)}$, ce qui donne $c^{(1)} = 4\,2\,3\,1\,5$.
Le croisement à deux points de l'exemple « illustration d'une génération » est le cas où $M$ est un segment.

*Croisement OX* (cours). On tire deux points de coupe $a \le b$. L'enfant reçoit le segment de $A$ :

$$
c_{[a,b]} = A_{[a,b]}
$$

Les positions $b+1, \dots, m, 1, \dots, a-1$ reçoivent, dans cet ordre, la suite $B_{b+1}, \dots, B_m, B_1, \dots, B_b$ **privée des éléments de $A_{[a,b]}$**.
Exemple du cours : $A = 35\vert 7124 \vert 869$ et $B = 19\vert 2346 \vert 875$ donnent $B' = 36\vert 7124 \vert 859$.

Deux croisements classiques complètent ceux du cours (ils n'y figurent pas) :

*PMX* (*Partially Mapped Crossover*). Après copie du segment de $p^{(1)}$, on définit la correspondance

$$
\varphi(x) = p^{(2)}\big((p^{(1)})^{-1}(x)\big)
$$

Hors du segment, $c_j = \varphi^{\kappa}(p^{(2)}_j)$, où $\kappa \ge 0$ est le plus petit entier tel que $\varphi^{\kappa}(p^{(2)}_j) \notin p^{(1)}([a,b])$.

*CX* (*Cycle Crossover*). Les cycles $\mathcal{C}_1, \dots, \mathcal{C}_r$ de l'application des positions $\theta(j) = (p^{(1)})^{-1}(p^{(2)}_j)$ partitionnent les positions. L'enfant prend les cycles alternativement chez chaque parent :

$$
c_j = p^{(1)}_j \text{ si } j \in \mathcal{C}_\ell \text{ avec } \ell \text{ impair}, \qquad c_j = p^{(2)}_j \text{ sinon}
$$

### Mutation (probabilité $P_m$)

Chaque enfant est muté avec la probabilité $P_m$ (cours : `si random(0,1) ≤ β alors muter(e)`).
- Codage binaire : inversion d'un bit.
- Permutation : échange de deux éléments **consécutifs** (cours), transposition quelconque, ou inversion d'un segment (2-opt pour le TSP).

### Remplacement (sélection pour la survie)

On choisit $N$ individus parmi les anciens individus et les enfants.

$$
\text{générationnel : } \mathcal{P}_{t+1} = \text{enfants}, \qquad
(\mu + \lambda) : \ \mathcal{P}_{t+1} = \mathrm{best}_N\big(\mathcal{P}_t \cup \text{enfants}\big)
$$

$$
\text{élitisme de taille } e : \ \mathcal{P}_{t+1} = \mathrm{best}_e(\mathcal{P}_t) \cup \mathrm{best}_{N-e}(\text{enfants})
$$

### Paramètres (cours)

| Paramètre | Valeurs usuelles (cours) |
|---|---|
| $N$ : taille de la population | dépend du problème |
| nombre maximal de générations | dépend du problème |
| $P_c$ : probabilité de croisement | $[0{,}5;\ 0{,}9]$ |
| $P_m$ : probabilité de mutation | $[0{,}05;\ 0{,}1]$ |

### Interprétation mathématique

**Pourquoi le croisement peut marcher (théorème des schémas, Holland).** Un schéma $H$ fixe les gènes d'un ensemble de positions $I_H$. On note :
- $o(H) = \lvert I_H \rvert$ son ordre (nombre de gènes fixés) ;
- $\delta(H) = \max I_H - \min I_H$ sa longueur utile ;
- $\phi = 1/f$ la qualité ;
- $m(H, t)$ le nombre d'individus porteurs de $H$ à la génération $t$.

Pour la roulette, le croisement 1 point et la mutation par gène $p_g$ :

$$
\mathbb{E}\big[m(H, t+1)\big] \;\ge\; m(H, t)\;\frac{\bar\phi(H)}{\bar\phi(\mathcal{P}_t)}\;\Big[\,1 - P_c\,\frac{\delta(H)}{L - 1} - o(H)\,p_g\Big]
$$

**Interprétation :**
- un schéma meilleur que la moyenne de la population ($\bar\phi(H) > \bar\phi(\mathcal{P}_t)$) se propage ;
- il est d'autant plus détruit qu'il est long (par le croisement) ou qu'il fixe beaucoup de gènes (par la mutation).

Les « briques » courtes et bonnes se combinent : c'est l'hypothèse des blocs de construction.

**Perte de diversité.** La sélection recopie les bons individus. Sans mutation, la population converge vers des clones (cours, *algorithmes mémétiques*) et le croisement de deux clones ne produit plus rien de nouveau.

**Effet de $P_m$.** Chaque mutation éloigne l'enfant de ses parents (une transposition change au plus 2 gènes). Augmenter $P_m$ augmente donc la distance moyenne enfant-parent : c'est de l'**exploration**. Le cours l'associe à l'intensification ; mathématiquement, son effet est de maintenir la diversité $D$ (voir 3.2 f).

---

## 3.2 Application au placement de qubits

### a) Génotype et phénotype

$$
\text{génotype : } \sigma \in \mathfrak{S}_m, \qquad \text{phénotype : } s = (\sigma(0), \dots, \sigma(n-1))
$$

Le gène en position $i < n$ a un **sens absolu** : c'est le qubit physique du qubit logique $i$. Les gènes en positions $\ge n$ forment l'ensemble des qubits physiques libres, dont l'ordre est sans importance.

**Conséquence :** un bon placement est fait de **positions** correctes (« $q_3$ sur $P_5$ et $q_7$ sur $P_6$ »), pas d'un **ordre** relatif. Les opérateurs doivent donc conserver des positions absolues, à l'inverse du TSP, où seul l'ordre compte.

**Mesure : héritage positionnel d'un enfant $c$** (part des gènes utiles hérités tels quels d'un des deux parents) :

$$
h(c) = \frac{1}{n} \sum_{i=0}^{n-1} \mathbf{1}\big[c(i) \in \lbrace p^{(1)}(i),\ p^{(2)}(i) \rbrace\big] \in [0, 1]
$$

| Croisement | Ce qui est conservé | $h(c)$ |
|---|---|---|
| CX | chaque gène garde la position qu'il a chez un des parents | $= 1$ |
| PMX | segment de $p^{(1)}$ ; hors segment, position de $p^{(2)}$ sauf conflit | élevé |
| uniforme de permutations (cours) | positions hors masque de $p^{(1)}$ ; le reste suit l'**ordre** de $p^{(2)}$ | moyen |
| OX (cours) | segment de $p^{(1)}$ ; le reste suit l'**ordre** de $p^{(2)}$ (décalé) | plus faible |

**Hypothèse à tester :** CX et PMX devraient dominer, OX être le moins adapté. Le croisement est l'opérateur à comparer en priorité.

**Ordre des gènes et théorème des schémas.** $\delta(H)$ est petit si les qubits qui interagissent ont des indices proches. On peut renuméroter les positions selon l'ordre de construction $i_1, \dots, i_n$ (voir [01_ant_colony.md](01_ant_colony.md), 1.2 b) : la position $t$ porte alors $s(i_t)$. Cela n'a d'effet que pour les croisements à segment (OX, PMX, deux points).

### b) Sélection

**La roulette est à éviter ici.** Le rapport $p_{\mathrm{meilleur}} / p_{\mathrm{pire}} = f_{\mathrm{pire}} / f_{\mathrm{meilleur}}$ est proche de 1. Sur l'instance 5, par exemple, les coûts vont de 315 à 335, soit un rapport d'environ 1,06 : la sélection est presque aléatoire.

**Le tournoi est recommandé**, car il ne dépend que des rangs, donc ni de l'échelle de $f$ (de 19 à 380 selon les instances) ni des écarts absolus.

**Effet du bruit sur un tournoi à deux.** Soit $\Delta = F(s_b) - F(s_a) > 0$ le vrai écart entre deux individus, chacun évalué une fois :

$$
\mathbb{P}(\text{le moins bon gagne}) = \Phi\!\left(-\frac{\Delta}{\varsigma\sqrt{2}}\right)
$$

Exemple sur l'instance 8 ($\varsigma \approx 4{,}7$) avec $\Delta = 4$ : $\Phi(-0{,}60) \approx 0{,}27$. Un tournoi sur quatre se trompe : la pression de sélection reste orientée dans le bon sens, mais affaiblie.

### c) Croisement

On l'applique sur $\sigma$ (toutes les $m$ positions), donc l'enfant est toujours une permutation valide. Seules les $n$ premières positions comptent pour $f$.

### d) Mutation

Mutation par transposition, c'est-à-dire exactement un mouvement du voisinage $N(s)$ (voir 0.8) :

$$
\sigma' = \sigma \circ (a\ b), \qquad a \sim \mathcal{U}\lbrace 0, \dots, n-1 \rbrace, \quad b \sim \mathcal{U}\big(\lbrace 0, \dots, m-1 \rbrace \setminus \lbrace a \rbrace\big)
$$

L'échange d'éléments **consécutifs** du cours n'a pas de sens ici : deux positions voisines dans $\sigma$ ne correspondent à rien sur la puce.

**Variante guidée :** prendre $\sigma(b)$ parmi les voisins sur la puce de $\sigma(a)$, c'est-à-dire avec $d(\sigma(a), \sigma(b)) = 1$, pour une mutation plus « locale ».

### e) Budget : la contrainte principale

Population initiale de $N$ individus, puis $\lambda$ enfants évalués par génération :

$$
N + G\,\lambda \le B \quad\Longrightarrow\quad G = \left\lfloor \frac{B - N}{\lambda} \right\rfloor, \qquad B = 200,\ N = \lambda = 20 \;\Rightarrow\; G = 9 \text{ générations}
$$

C'est très peu pour un algorithme génétique, qui en compte habituellement des centaines. Trois leviers :

1. **Ne pas réévaluer les copies.** Un couple non croisé et non muté produit des copies déjà évaluées. Le nombre attendu d'enfants nouveaux, donc à évaluer, par génération ($N/2$ couples) est

$$
\mathbb{E}[\text{nouveaux}] = N\,\big[P_c + (1 - P_c)\,P_m\big]
$$

   Avec $P_c = 0{,}8$, $P_m = 0{,}1$ et $N = 20$, cela fait 16,4 enfants.

2. **Présélection par $C$** (même idée que `aco_filtered`). On génère $\Lambda \gg \lambda$ enfants (gratuit) et on n'évalue que les $\lambda$ meilleurs selon $C$ :

$$
O^{\mathrm{éval}}_t = \text{les } \lambda \text{ enfants de plus petit } C(\cdot) \text{ parmi } \Lambda
$$

   C'est efficace si $C$ est corrélé à $f$ (instances 2 et 6 à 9), risqué sinon.

3. **Population initiale.** Elle est aléatoire uniforme dans le cours ($\sigma \sim \mathcal{U}(\mathfrak{S}_m)$). Variante : chaque individu est le meilleur selon $C$ de $R$ permutations aléatoires, comme la référence `surrogate_filtered`. Cela donne de meilleurs départs, gratuitement.

### f) Diversité de la population

Même mesure que pour l'ACO (distance de Hamming moyenne sur les gènes utiles) :

$$
D(\mathcal{P}_t) = \frac{2}{N(N-1)} \sum_{a < b} \frac{1}{n} \sum_{i=0}^{n-1} \mathbf{1}\big[\sigma^{(a)}(i) \ne \sigma^{(b)}(i)\big] \in [0, 1]
$$

$D \to 0$ signale une convergence prématurée : il faut alors augmenter $P_m$ ou $N$, ou réduire la pression de sélection.

### g) Remplacement et bruit

$(\mu + \lambda)$ et l'élitisme ne perdent jamais le meilleur individu, mais avec le bruit, **un individu évalué une seule fois avec un tirage chanceux survit indéfiniment**. Parades possibles :
- réévaluer les survivants de temps en temps, en moyennant leurs évaluations ;
- garder pour chaque individu la moyenne de ses évaluations plutôt que la première valeur.

Avec $r$ évaluations moyennées, l'écart-type du bruit est divisé par $\sqrt{r}$, pour $r$ fois plus d'évaluations.

### h) Étapes à effectuer

```
P ← N permutations aléatoires (ou filtrées par C) ;  évaluer f sur P   (N évaluations)
tant que le budget le permet :
    former N/2 couples par tournoi (k, p)
    pour chaque couple : avec la probabilité P_c, croiser (CX / PMX / OX / uniforme), sinon copier
    pour chaque enfant : avec la probabilité P_m, transposition σ∘(a b), a < n
    (option) générer Λ enfants et garder les λ meilleurs selon C
    évaluer f sur les enfants nouveaux uniquement
    P ← remplacement (μ+λ) ou générationnel avec élitisme e
    mesurer D(P), mettre à jour la meilleure solution
renvoyer la meilleure solution
```

### i) Paramètres à étudier

| Paramètre | Proposition | Ce qu'on cherche à voir |
|---|---|---|
| croisement | CX, PMX, OX, uniforme | effet de l'héritage positionnel $h$ |
| $N$ (= $\lambda$) | 10, 20, 30 | compromis diversité / nombre de générations $G$ |
| sélection | tournoi $k \in \lbrace 2, 3 \rbrace$, $p = 1$ | pression de sélection |
| $P_c$ | 0,8 (dans $[0{,}5;\ 0{,}9]$) | quantité de recombinaison |
| $P_m$ | 0,1 ; étude sur $\lbrace 0{,}05;\ 0{,}1;\ 0{,}3 \rbrace$ | maintien de la diversité $D$ |
| remplacement | $(\mu+\lambda)$, ou générationnel avec $e = 2$ | conservation du meilleur |
| $\Lambda / \lambda$ | 1 (sans filtre), 5 | apport de la présélection par $C$ |

**Remarque :** l'*algorithme mémétique* du cours (recherche locale à la place de la mutation) est une **hybridation**. Il est hors du périmètre actuel du projet.

---

## 3.3 Récapitulatif : général et appliqué

| Élément | Cas général (cours) | Placement de qubits |
|---|---|---|
| Codage | binaire (AG) ou réel (AE) | permutation $\sigma \in \mathfrak{S}_m$, les $n$ premiers gènes forment $s$ |
| Sens d'un gène | dépend du problème | position absolue : qubit physique du qubit logique $i$ |
| Sélection | roulette, tournoi | tournoi (roulette inefficace : coûts trop proches) |
| Croisement | 1 point, 2 points, uniforme ; OX, uniforme de permutations | CX, PMX (positions) contre OX, uniforme (ordre) |
| Mutation | bit, échange consécutif, inversion | transposition $\sigma \circ (a\ b)$, $a < n$ |
| Évaluation | gratuite | 1 évaluation de $f$ par enfant nouveau (bruitée) |
| Nombre de générations | centaines | $G = \lfloor (B - N)/\lambda \rfloor \approx 9$ |
| Remplacement | générationnel, $(\mu+\lambda)$, élitisme | $(\mu+\lambda)$ ou élitisme, avec réévaluations contre le bruit |
