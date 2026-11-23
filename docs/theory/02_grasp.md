# 2. GRASP (*Greedy Randomized Adaptive Search Procedure*)

Feo et Resende (1989, 1995).
Code : `optimizer/algorithms/grasp.py`. Notebook : `05_grasp`.
Notations du problème : voir [00_problem_and_graphs.md](00_problem_and_graphs.md).

---

## 2.1 Cas général (cours)

### Algorithme glouton

Un glouton construit une solution en ajoutant un élément à chaque étape. L'élément ajouté l'est **définitivement**. À une solution partielle $s$ on associe un **coût incrémental** $c(e)$, le coût d'ajout de l'élément $e$ ; le glouton choisit l'élément de coût minimal :

$$
e^\star = \arg\min_{e \in \mathrm{RESTE}} c(e), \qquad \mathrm{RESTE} = \text{éléments} \setminus s
$$

### Glouton randomisé et liste restreinte de candidats (RCL)

$$
c_{\min} = \min_{e \in \mathrm{RESTE}} c(e), \qquad c_{\max} = \max_{e \in \mathrm{RESTE}} c(e)
$$

$$
\mathrm{RCL} = \big\lbrace e \in \mathrm{RESTE} \;:\; c_{\min} \le c(e) \le c_{\min} + \alpha\,(c_{\max} - c_{\min}) \big\rbrace, \qquad \alpha \in [0, 1]
$$

$$
\mathrm{prob}[e] =
\begin{cases}
1 / \lvert \mathrm{RCL} \rvert & \text{si } e \in \mathrm{RCL} \\
0 & \text{sinon}
\end{cases}
$$

**Exemple du cours** (TSP, plus proche voisin) : arêtes de coûts 1, 2, 3, 4, 5, donc $c_{\min} = 1$ et $c_{\max} = 5$.
- $\alpha = 0$ : $[1, 1]$, RCL = {1}, choix glouton.
- $\alpha = 0{,}3$ : $[1;\ 2{,}2]$, RCL = {1, 2}, chacun avec la probabilité 1/2.
- $\alpha = 1$ : $[1, 5]$, choix aléatoire.

### Le schéma GRASP

```
pour k = 1 … iterations_max :
    s  ← glouton_probabilité(α)              (construction)
    s' ← recherche_locale(s)                 (amélioration, cf. 0.8)
    meilleure ← min(meilleure, s')
renvoyer meilleure
```

**Paramètres** (cours) : `iterations_max` et $\alpha$, le « taux d'acceptation ».

### Interprétation mathématique

**Bornes de $\alpha$** (cours) :
- $\alpha = 0$ : glouton + recherche locale. La construction est déterministe, aux égalités près.
- $\alpha = 1$ : recherche aléatoire + recherche locale, c'est-à-dire une recherche locale à départs multiples aléatoires.

Le cours précise que GRASP donne son plein potentiel pour **$\alpha$ proche de 0, mais pas nul**.

**Diversité d'une construction.** Les choix successifs sont uniformes dans les RCL, donc la probabilité de construire une solution donnée $s$ est

$$
\mathbb{P}(s) = \prod_{t=1}^{n} \frac{\mathbf{1}\big[s_t \in \mathrm{RCL}_t\big]}{\lvert \mathrm{RCL}_t \rvert}
$$

$\lvert \mathrm{RCL}_t \rvert$ croît avec $\alpha$. Plus $\alpha$ est grand, plus les constructions sont variées et moins chacune est probable : c'est la diversification. Plus $\alpha$ est petit, plus elles se ressemblent et sont proches du glouton : c'est l'intensification.

**Multi-départ indépendant.** Les itérations n'ont **aucune mémoire** les unes des autres : ce sont des tirages indépendants et identiquement distribués. Soit $q$ la probabilité qu'une itération aboutisse dans un ensemble cible $S^{\mathrm{bon}}$ (par exemple « à moins de 5 % de $f^\star$ ») :

$$
\mathbb{P}\big(\text{au moins un succès en } K \text{ itérations}\big) = 1 - (1-q)^K, \qquad K_{95\,\%} = \left\lceil \frac{\ln 0{,}05}{\ln(1-q)} \right\rceil \approx \frac{3}{q}
$$

**Interprétation :** l'efficacité de GRASP se résume à rendre $q$ grand. La construction gloutonne place le départ dans une bonne région ; la recherche locale élargit le « bassin d'attraction » qui mène à $S^{\mathrm{bon}}$. Conséquence : GRASP se parallélise naturellement (cours).

### Variantes classiques (toujours du GRASP)

- **RCL par cardinalité** : RCL = les $k$ meilleurs éléments, quels que soient les écarts de coût. C'est plus stable quand les $c(e)$ sont très regroupés ou très dispersés.
- **GRASP réactif.** $\alpha$ est tiré dans $\lbrace \alpha_1, \dots, \alpha_K \rbrace$ avec les probabilités $p_k$. Ces probabilités sont réajustées périodiquement :

$$
p_k = \frac{q_k}{\sum_l q_l}, \qquad q_k = \frac{f(s^{\mathrm{bs}})}{\bar f_k}
$$

où $\bar f_k$ est le coût moyen obtenu avec $\alpha_k$. Les valeurs de $\alpha$ qui donnent de bonnes solutions sont tirées plus souvent.

---

## 2.2 Application au placement de qubits

### a) Éléments et ordre d'ajout

Un « élément » est l'affectation du qubit logique courant à un qubit physique libre. On reprend l'**ordre de construction** des colonies de fourmis ([01_ant_colony.md](01_ant_colony.md), 1.2 b) :

$$
i_1 = \arg\max_i \mathrm{str}(i), \qquad i_t = \arg\max_{i \notin L_t} \Big(\textstyle\sum_{j \in L_t} w_{ij},\ \mathrm{str}(i),\ -i\Big)
$$

À l'étape $t$ : $\mathrm{RESTE}_t = J_t = P \setminus \lbrace s(i_1), \dots, s(i_{t-1}) \rbrace$, les qubits physiques libres.

### b) Coût incrémental

C'est l'augmentation du coût de distance $C$ (voir 0.7) due au choix de $u$ :

$$
c_t(u) = g_t(u) = \sum_{j \in L_t} w_{i_t j}\,\big(d(u, s(j)) - 1\big), \qquad u \in J_t
$$

Elle est **adaptative** (le « A » de GRASP) : $c_t$ dépend des affectations déjà faites, donc on la recalcule à chaque étape.

**Premier qubit** ($L_1 = \emptyset$, donc $g_1 \equiv 0$). On utilise la centralité, convertie en coût :

$$
c_1(u) = \max_v \deg_C(v) - \deg_C(u)
$$

Si $i_t$ n'a aucun partenaire déjà placé (composante connexe de $G_I$ distincte), on utilise la même règle.

**Propriété** (identique à l'ACO) : $\sum_t g_t(s(i_t)) = C(s)$. Le glouton pur ($\alpha = 0$) minimise donc $C$ étape par étape.

### c) RCL

$$
\mathrm{RCL}_t = \big\lbrace u \in J_t \;:\; c_t(u) \le c_t^{\min} + \alpha\,(c_t^{\max} - c_t^{\min}) \big\rbrace, \qquad s(i_t) \sim \mathcal{U}(\mathrm{RCL}_t)
$$

**Exemple** (même étape que l'exemple de l'ACO : instance 6, étape 3, $w = 2$). Les coûts possibles sont $g \in \lbrace 0, 2, 4, 6 \rbrace$ pour 2, 6, 7 et 3 qubits libres. On a $c^{\min} = 0$ et $c^{\max} = 6$ :

| $\alpha$ | seuil $6\alpha$ | RCL | $\lvert \mathrm{RCL} \rvert$ | probabilité de chaque élément |
|---|---|---|---|---|
| 0 | 0 | $\lbrace g = 0 \rbrace$ | 2 | 1/2 |
| 0,2 | 1,2 | $\lbrace g = 0 \rbrace$ | 2 | 1/2 |
| 0,4 | 2,4 | $\lbrace g \le 2 \rbrace$ | 8 | 1/8 |
| 1 | 6 | tous | 18 | 1/18 |

**Interprétation :**
- **Coûts entiers et regroupés.** Les coûts sont des entiers petits, avec beaucoup d'égalités. $\lvert \mathrm{RCL} \rvert$ varie donc **par paliers** avec $\alpha$, et même $\alpha = 0$ laisse du hasard grâce aux égalités, d'où l'intérêt de la variante par cardinalité.
- **Différence avec l'ACO.** Une fourmi aurait donné 0,33 à chaque voisin et 0,04 à chaque qubit à distance 2. GRASP coupe net : probabilité uniforme dans la RCL, 0 en dehors.

### d) Recherche locale : deux options

Un parcours complet de $N(s)$ avec $f$ coûte de 105 à 350 évaluations (voir 0.8), soit plus que $B$.

**Option A : descente sur $C$ (gratuite).** On descend sur $C$ jusqu'à un optimum local de $C$, avec le voisinage par transposition et $\Delta C$ incrémental, puis on évalue $f$ **une fois** :

$$
s' = \mathrm{descente}_C(s), \qquad \text{coût d'une itération GRASP} = 1 \text{ évaluation} \quad\Longrightarrow\quad K = B = 200 \text{ itérations}
$$

GRASP explore alors l'ensemble des **optima locaux de $C$**. C'est efficace si $C$ et $f$ sont corrélés (instances 2 et 6 à 9 : $\rho_S \ge 0{,}74$), risqué sinon (instances 1, 3, 4, 5).

**Option B : descente échantillonnée sur $f$.** À chaque pas, on tire $V$ voisins, on les classe par $C$ et on évalue les $L$ meilleurs avec $f$. On se déplace si l'un d'eux améliore $f$, et on s'arrête après $R$ pas sans amélioration :

$$
\text{coût d'une itération} = 1 + L \times (\text{nombre de pas}) \quad\Longrightarrow\quad K \ll B
$$

On fait moins d'itérations, mais chacune optimise la vraie fitness. **Attention au bruit** : accepter $s'$ parce que $f(s') < f(s)$ alors que $F(s') \ge F(s)$ arrive avec une probabilité non négligeable quand $\lvert F(s') - F(s) \rvert \lesssim \varsigma$ (voir 0.6).

**Doublons.** Deux itérations peuvent produire le même $s'$, surtout pour $\alpha$ petit. On ne réévalue pas un $s'$ déjà évalué : cela épargne le budget.

### e) Lien avec les colonies de fourmis

Avec les notations de l'ACO, la règle de choix de GRASP s'écrit :

$$
p^{\mathrm{GRASP}}_{i_t u} = \frac{\mathbf{1}\big[g_t(u) \le \text{seuil}_t(\alpha)\big]}{\lvert \mathrm{RCL}_t \rvert}
\qquad\text{contre}\qquad
p^{\mathrm{ACO}}_{i_t u} = \frac{\tau_{i_t u}^{\alpha}\,\eta_{i_t u}^{\beta}}{\sum_v \tau_{i_t v}^{\alpha}\,\eta_{i_t v}^{\beta}}
$$

| | GRASP | ACO |
|---|---|---|
| Information locale | $g_t(u)$, filtrée par seuil | $\eta = 1/(1+g_t(u))$, pondérée par puissance |
| Mémoire entre itérations | **aucune** | phéromones $\tau$ |
| Amélioration | recherche locale explicite | aucune (sauf variante `_ls`) |
| Limite déterministe | $\alpha = 0$ : glouton | $\beta \to \infty$ : glouton |

**Intérêt expérimental :** GRASP et l'ACO partagent la même information locale $g_t$. Les comparer revient à mesurer ce qu'apporte la **mémoire** des phéromones (ACO) par rapport à la **recherche locale** (GRASP).

### f) Étapes à effectuer

```
calculer l'ordre i_1, …, i_n                               (une fois)
pour k = 1 … K tant que le budget le permet :
    s ← solution vide
    pour t = 1 … n :                                       (construction, gratuite)
        calculer c_t(u) pour tout u ∈ J_t
        construire RCL_t avec α
        tirer s(i_t) uniformément dans RCL_t
    s' ← recherche_locale(s)                               (option A : sur C ; option B : sur f)
    si s' n'a pas déjà été évalué : évaluer f(s')          (coûte 1 évaluation, ou plus en option B)
    mettre à jour la meilleure solution
renvoyer la meilleure solution
```

### g) Paramètres à étudier

| Paramètre | Cours | Proposition | Effet attendu |
|---|---|---|---|
| $\alpha$ | taux d'acceptation | 0,2 ; étude sur $\lbrace 0;\ 0{,}1;\ 0{,}2;\ 0{,}4;\ 1 \rbrace$ | petit : intensification ; grand : diversification |
| type de RCL | par valeur | valeur, ou cardinalité $k \in \lbrace 2, 3, 5 \rbrace$ | la cardinalité est plus stable avec des coûts entiers |
| `iterations_max` | nombre d'itérations | déterminé par $B$ | $K = B$ (option A) |
| recherche locale | descente | option A, puis option B en variante | A : beaucoup d'itérations ; B : chaque itération optimise $f$ |

---

## 2.3 Récapitulatif : général et appliqué

| Élément | Cas général (cours) | Placement de qubits |
|---|---|---|
| Élément ajouté | une arête ou une ville | une affectation $i_t \mapsto u$ |
| Coût incrémental | longueur de l'arête ajoutée | $g_t(u)$ : coût de distance ajouté |
| Adaptatif | oui (dépend de la solution partielle) | oui ($g_t$ dépend de $s(L_t)$) |
| RCL | $[c_{\min},\ c_{\min} + \alpha(c_{\max} - c_{\min})]$ | idem, sur $g_t$ |
| Recherche locale | descente sur $f$ | descente sur $C$ (gratuite), ou descente échantillonnée sur $f$ |
| Coût d'une itération | négligeable | 1 évaluation de $f$ (option A) |
| Mémoire | aucune | aucune |
