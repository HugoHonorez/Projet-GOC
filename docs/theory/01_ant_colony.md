# 1. Colonies de fourmis (ACO)

Dorigo (1992), *Ant System*. Variante utilisée dans le projet : *MAX-MIN Ant System* (Stützle et Hoos, 2000).
Code : `optimizer/algorithms/ant_colony.py`. Notebook : `04_ant_colony`.
Notations du problème : voir [00_problem_and_graphs.md](00_problem_and_graphs.md).

---

## 1.1 Cas général (cours, exemple du TSP)

Une itération $t$ : chacune des $N$ fourmis construit une solution complète, élément par élément, puis les pistes sont mises à jour.

**Règle de transition** (4.1). La fourmi $k$ est sur la ville $i$ ; $J_i^k$ est l'ensemble des villes qu'elle n'a pas encore visitées :

$$
p_{ij}^k(t) =
\begin{cases}
\dfrac{\big(\tau_{ij}(t)\big)^\alpha \cdot \big(\eta_{ij}\big)^\beta}{\sum_{l \in J_i^k} \big(\tau_{il}(t)\big)^\alpha \cdot \big(\eta_{il}\big)^\beta} & \text{si } j \in J_i^k \\[3mm]
0 & \text{si } j \notin J_i^k
\end{cases}
$$

- $\tau_{ij}(t)$ : **intensité de la piste** (phéromone), la mémoire globale qui évolue par apprentissage ;
- $\eta_{ij} = 1/d_{ij}$ : **visibilité**, une information statique et locale.

**Dépôt** (4.2). $T^k(t)$ est le trajet de la fourmi $k$ et $L^k(t)$ sa longueur :

$$
\Delta\tau_{ij}^k(t) =
\begin{cases}
\dfrac{Q}{L^k(t)} & \text{si } (i, j) \in T^k(t) \\[2mm]
0 & \text{sinon}
\end{cases}
\qquad\qquad
\Delta\tau_{ij}(t) = \sum_{k=1}^{N} \Delta\tau_{ij}^k(t)
$$

**Évaporation et mise à jour** (4.3) :

$$
\tau_{ij}(t+1) = (1 - \rho)\,\tau_{ij}(t) + \Delta\tau_{ij}(t), \qquad \rho \in [0, 1]
$$

### Interprétation mathématique

**Oubli géométrique.** Sans nouveau dépôt, une piste décroît comme $\tau_{ij}(t+h) = (1-\rho)^h\,\tau_{ij}(t)$. Un dépôt perd la moitié de son poids en

$$
h_{1/2} = \frac{\ln 2}{-\ln(1-\rho)} \approx \frac{0{,}69}{\rho} \text{ itérations.}
$$

$\rho$ fixe donc la **longueur de la mémoire** de la colonie (≈ $1/\rho$ itérations).

**Point fixe.** Une arête qui reçoit un dépôt constant $\Delta$ à chaque itération converge vers

$$
\bar\tau = (1-\rho)\,\bar\tau + \Delta \quad\Longrightarrow\quad \bar\tau = \frac{\Delta}{\rho}
$$

Les arêtes souvent empruntées par de bonnes solutions montent vers $\Delta/\rho$, les autres tendent vers 0 : c'est le renforcement positif.

**Rôle de $\alpha$ et $\beta$.**
- $\alpha = 0$ : $p$ ne dépend que de $\eta$. On obtient un glouton randomisé, sans mémoire (proche de GRASP, voir [02_grasp.md](02_grasp.md)).
- $\beta = 0$ : $p$ ne dépend que de $\tau$. Sans information locale, la colonie suit ses premières pistes et **converge prématurément**.

**Intensification et diversification** (cours) : plus de phéromone, c'est plus de mémoire et donc plus d'intensification ; moins de phéromone, c'est plus de diversification.

| Paramètre | Rôle | Si on l'augmente |
|---|---|---|
| $N$ | nombre de fourmis par itération | plus d'échantillons par itération, mais moins d'itérations pour le même budget |
| $\alpha$ | poids de la phéromone | plus de mémoire, donc intensification |
| $\beta$ | poids de la visibilité | choix plus gloutons (proches) |
| $Q$ | quantité déposée | pistes plus fortes |
| $\rho$ | évaporation | mémoire plus courte, donc diversification |

### Variante MAX-MIN Ant System

Elle diffère de l'Ant System sur trois points :
1. Seule la **meilleure** fourmi dépose (celle de l'itération, ou la meilleure depuis le début).
2. Les pistes sont **bornées** : $\tau_{\min} \le \tau_{ij} \le \tau_{\max}$.
3. Les pistes sont **initialisées à $\tau_{\max}$** : aucune préférence au départ, donc exploration maximale.

Les bornes garantissent que chaque choix garde une probabilité non nulle :

$$
p_{ij}^k \;\ge\; \frac{\tau_{\min}^\alpha\,\eta_{ij}^\beta}{\sum_{l \in J_i^k} \tau_{\max}^\alpha\,\eta_{il}^\beta} > 0
$$

La colonie ne peut donc pas se figer définitivement : la **stagnation** est évitée.

---

## 1.2 Application au placement de qubits

### a) Le graphe de construction : affectation, pas tournée

Dans le TSP, la phéromone est posée sur une **arête entre deux villes consécutives**, parce que le coût dépend de l'ordre. Ici, $f(s)$ dépend de **quel qubit logique est sur quel qubit physique**. C'est un problème d'**affectation**, proche du problème d'affectation quadratique (QAP). La phéromone est donc posée sur les couples (qubit logique, qubit physique) :

$$
\tau \in \mathbb{R}_{>0}^{\,n \times m}, \qquad \tau_{iu} = \text{intérêt appris de placer } i \text{ sur } u
$$

| Cours (TSP) | Projet |
|---|---|
| ville courante $i$ | qubit logique $i_t$ à placer à l'étape $t$ |
| ville candidate $j$ | qubit physique libre $u$ |
| $J_i^k$ : villes non visitées | $J_t = P \setminus \lbrace s(i_1), \dots, s(i_{t-1}) \rbrace$ : qubits physiques libres |
| $\tau_{ij}$ : arête ville-ville | $\tau_{iu}$ : case qubit logique-qubit physique |
| $\eta_{ij} = 1/d_{ij}$ | $\eta_{i_t u} = 1/(1 + g_t(u))$ (ci-dessous) |
| $L^k$ : longueur du tour | $f(s^k)$ : profondeur après routage |

### b) Ordre de construction (fixe)

Les qubits logiques sont placés dans un ordre $i_1, \dots, i_n$ calculé une seule fois. On part du plus fort, puis on prend toujours le plus lié aux qubits déjà placés $L_t = \lbrace i_1, \dots, i_{t-1} \rbrace$ :

$$
i_1 = \arg\max_{i \in L} \mathrm{str}(i), \qquad
i_t = \arg\max_{i \notin L_t} \Big( \sum_{j \in L_t} w_{ij},\ \mathrm{str}(i),\ -i \Big) \quad \text{(ordre lexicographique)}
$$

**Interprétation :** au moment de son placement, chaque qubit a déjà le plus possible de partenaires sur la puce pour guider son choix.

### c) Visibilité : le coût ajouté

À l'étape $t$, placer $i_t$ sur le qubit physique libre $u$ ajoute au coût de distance :

$$
g_t(u) = \sum_{j \in L_t} w_{i_t j}\,\big(d(u, s(j)) - 1\big) \;\ge\; 0
$$

On en déduit la visibilité :

$$
\eta_{i_t u} =
\begin{cases}
\dfrac{1}{1 + g_t(u)} & \text{si } i_t \text{ a au moins un partenaire déjà placé} \\[3mm]
\dfrac{\deg_C(u)}{\max_v \deg_C(v)} & \text{sinon (premier qubit : centralité)}
\end{cases}
$$

- $\eta = 1 \iff g_t(u) = 0 \iff u$ est voisin de tous les partenaires déjà placés.
- Le « $+1$ » évite la division par zéro.

**Propriété clé.** Chaque arête $\lbrace i, j \rbrace \in E_I$ est comptée exactement une fois, au placement du second de ses deux qubits. Donc :

$$
\sum_{t=1}^{n} g_t\big(s(i_t)\big) = C(s)
$$

**Interprétation :** une fourmi avec $\beta \to \infty$ est un **glouton qui minimise $C$ étape par étape**. La visibilité pousse donc la colonie vers les bonnes solutions **au sens de $C$**, ce qui est un piège sur les instances où $C$ est mal corrélé à $f$ (1, 3, 4, 5). Seule la phéromone, apprise à partir de $f$, peut corriger ce biais.

### d) Règle de transition (forme du cours)

$$
p_{i_t u}^k(t) = \frac{\tau_{i_t u}^{\,\alpha}\;\eta_{i_t u}^{\,\beta}}{\sum_{v \in J_t} \tau_{i_t v}^{\,\alpha}\;\eta_{i_t v}^{\,\beta}}, \qquad u \in J_t
$$

**Exemple numérique** (notebook 04, instance 6, $m = 20$, étape 3, première itération). On place $q_{11}$ ; son seul partenaire déjà placé est $q_0$, sur $P_{12}$, avec $w = 2$. La phéromone est uniforme, donc $\tau^\alpha$ se simplifie. Avec $\beta = 2$ :

| $d(u, P_{12})$ | nombre de $u$ libres | $g_3(u) = 2(d-1)$ | $\eta$ | $\eta^2$ |
|---|---|---|---|---|
| 1 | 2 | 0 | 1 | 1 |
| 2 | 6 | 2 | 1/3 | 1/9 |
| 3 | 7 | 4 | 1/5 | 1/25 |
| 4 | 3 | 6 | 1/7 | 1/49 |

$$
\sum \eta^2 = 2 + \tfrac{6}{9} + \tfrac{7}{25} + \tfrac{3}{49} \approx 3{,}008
\quad\Longrightarrow\quad
p = \frac{1}{3{,}008} \approx 0{,}332 \ \text{pour chacun des 2 voisins}, \qquad p = \frac{1/49}{3{,}008} \approx 0{,}007 \ \text{à distance 4}
$$

Le notebook 04 retrouve bien $p = 0{,}3325$.

### e) Évaluation filtrée

Le budget porte sur $f$, pas sur le nombre de fourmis. À chaque itération :
1. construire $N$ fourmis (gratuit) et supprimer les doublons ;
2. les classer par $C$ (gratuit) ;
3. n'évaluer avec $f$ que les $N_e \le N$ meilleures.

$$
\text{nombre d'itérations} = \left\lceil \frac{B}{N_e} \right\rceil
$$

Avec $B = 200$ : `aco_all` ($N = N_e = 10$) fait 20 itérations ; `aco_filtered` ($N = 30$, $N_e = 5$) en fait 40.

### f) Mise à jour (MAX-MIN)

Notations : $s^{\mathrm{it}}$ est la meilleure fourmi évaluée de l'itération, $s^{\mathrm{bs}}$ la meilleure solution depuis le début, $e$ le poids élitiste (`elite_weight`).

$$
\begin{aligned}
\tau_{iu} &\leftarrow (1-\rho)\,\tau_{iu} && \text{(évaporation)} \\
\tau_{i\,s^{\mathrm{it}}(i)} &\leftarrow \tau_{i\,s^{\mathrm{it}}(i)} + \frac{f(s^{\mathrm{bs}})}{f(s^{\mathrm{it}})} && \text{(dépôt de l'itération, forme } Q/L^k \text{ avec } Q = f(s^{\mathrm{bs}})\text{)} \\
\tau_{i\,s^{\mathrm{bs}}(i)} &\leftarrow \tau_{i\,s^{\mathrm{bs}}(i)} + e && \text{(dépôt élitiste)} \\
\tau_{iu} &\leftarrow \min\big(\tau_{\max}, \max(\tau_{\min}, \tau_{iu})\big) && \text{(bornes)}
\end{aligned}
$$

- **Dépôt de l'itération** : il vaut $f(s^{\mathrm{bs}})/f(s^{\mathrm{it}}) \in (0, 1]$, et vaut 1 si $s^{\mathrm{it}}$ égale le meilleur connu. C'est le $Q/L^k$ du cours, normalisé.
- **Bornes** : $\tau_{\max} = 1/\rho$ est le point fixe $\bar\tau = \Delta/\rho$ pour un dépôt $\Delta = 1$. On pose $\tau_{\min} = r\,\tau_{\max}$, avec $r$ = `tau_min_ratio`.
- **Initialisation** : $\tau_{iu} = \tau_{\max}$ partout. À la première itération, $p$ ne dépend donc que de $\eta$.
- **Exploration minimale garantie** : le rapport des phéromones entre deux cases est au plus $\tau_{\max}/\tau_{\min} = 1/r = 20$.

### g) Indicateurs de convergence (graphiques du notebook 04)

**Entropie normalisée des pistes.** Elle vaut 1 si les phéromones sont uniformes et 0 si chaque qubit logique a un seul choix possible :

$$
\bar H = \frac{1}{n \ln m} \sum_{i \in L} \Big( -\sum_{u \in P} \pi_{iu} \ln \pi_{iu} \Big), \qquad \pi_{iu} = \frac{\tau_{iu}}{\sum_v \tau_{iv}}
$$

**Diversité des fourmis** (distance de Hamming moyenne entre fourmis). Elle vaut 0 si toutes les fourmis sont identiques :

$$
D = \frac{1}{N(N-1)} \sum_{k \ne k'} \frac{1}{n} \sum_{i \in L} \mathbf{1}\big[s^k(i) \ne s^{k'}(i)\big]
$$

### h) Étapes à effectuer

```
calculer l'ordre i_1, …, i_n                               (une fois)
τ ← τ_max partout ;  s_bs ← aucune
répéter jusqu'à épuisement de B :
    pour k = 1 … N :                                       (construction, gratuite)
        pour t = 1 … n :
            calculer g_t(u) et η pour tout u ∈ J_t
            tirer s_k(i_t) = u avec la probabilité p_{i_t u}
    supprimer les doublons, trier par C, garder les N_e meilleures
    évaluer f sur ces N_e fourmis                          (coûte N_e évaluations)
    mettre à jour s_it et s_bs
    évaporation, dépôt s_it, dépôt s_bs, bornes
renvoyer s_bs
```

### i) Paramètres du projet

| Cours | Code | `aco_filtered` | `aco_all` |
|---|---|---|---|
| $N$ | `ants` | 30 | 10 |
| $N_e$ (hors cours) | `evaluated` | 5 | 10 |
| $\alpha$ | `alpha` | 1 | 1 |
| $\beta$ | `beta` | 2 | 2 |
| $\rho$ | `rho` | 0,2 ($h_{1/2} \approx 3$ itérations) | 0,2 |
| $\tau_{\min}/\tau_{\max}$ | `tau_min_ratio` | 0,05 | 0,05 |
| $e$ | `elite_weight` | 1 | 1 |

La variante `aco_filtered_ls` du notebook 04 applique en plus à chaque fourmi, avant le tri, $K = 200$ essais de descente sur $C$ (`surrogate_descent`, voir 0.8).

---

## 1.3 Récapitulatif : général et appliqué

| Élément | Cas général (cours) | Placement de qubits |
|---|---|---|
| Solution construite | tournée (ordre des villes) | affectation $s : L \to P$ injective |
| Support des phéromones | arêtes ville-ville, $\tau_{ij}$ | cases qubit logique-qubit physique, $\tau_{iu}$ |
| Visibilité | $1/d_{ij}$, statique | $1/(1 + g_t(u))$, dépend de la solution partielle |
| Coût à minimiser | $L^k$, exact et gratuit | $f(s)$, bruitée et coûteuse |
| Qui dépose | toutes les fourmis (Ant System) | meilleure de l'itération et meilleure globale (MAX-MIN) |
| Bornes | aucune | $[\,r/\rho,\ 1/\rho\,]$ |
| Évaluations par itération | $N$ | $N_e \le N$, après tri par $C$ |
