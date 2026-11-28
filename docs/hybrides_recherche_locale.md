# Hybrides « métaheuristique constructive × recherche locale sur f »

Ce document décrit l'hybridation de la recherche locale de l'équipe (`descente` et `VND` de
`Recherche_locale.py`, intégrées dans `optimizer/fitness_local_search.py`) avec GRASP et la
colonie de fourmis.

## Ce qui manquait

Le système d'hybridation (`optimizer/hybrid/`) était en place, mais le registre `IMPROVERS` ne
contenait que trois briques : deux descentes sur le coût de distance (gratuites) et une descente
échantillonnée sur `f`. La recherche locale de l'équipe n'était pas branchable, donc aucun hybride
de la forme « GRASP dont la recherche locale est la VND de l'équipe » n'était exprimable.

Les seuls hybrides mesurés (`results/hybrid/demo.jsonl`) étaient quatre démonstrations :
`grasp > fitness descent`, `aco + local optimum (iteration)`, `memetic (genetic + local optimum)`
et `grasp > genetic`. Aucune ne couplait GRASP ou la colonie à `descente` / `VND`.

## Ce qui a été ajouté

**Deux briques** dans `optimizer/hybrid/improvers.py`, enregistrées dans `IMPROVERS` :

| brique | recherche locale |
|---|---|
| `ccl04_descente` | `descente` : première amélioration sur le voisinage complet mélangé (échanges + déplacements) |
| `ccl04_vnd` | `VND` : voisinages alternés, du plus petit au plus grand, retour au premier après chaque amélioration |

Les deux consomment des évaluations et prennent un paramètre `max_evaluations` (200 par défaut)
qui **borne la descente**. Cette borne est nécessaire : une descente complète consomme 250 à 400
évaluations sur l'instance 1, donc sans borne une seule descente branchée sur chaque solution
candidate dévore le budget d'une construction. Quand la part est épuisée en cours de descente, la
brique rend le meilleur placement rencontré pendant son exécution. `BudgetExhausted` (fin du budget
global) n'est pas interceptée et remonte normalement.

**Douze hybrides** dans `optimizer/hybrid/ccl04_hybrids.py`, les deux formes de la classification du
cours pour chacune des deux métaheuristiques constructives, plus les témoins :

- témoins, sans recherche locale : `grasp`, `aco`, `ils`, `vns` ;
- bas niveau (intégratif, la recherche locale **dans** la métaheuristique, sur la solution de chaque
  itération) : `grasp+descente`, `grasp+vnd`, `aco+descente`, `aco+vnd` ;
- haut niveau (relais, la constructive puis la recherche locale sur sa meilleure solution) :
  `grasp>ils`, `grasp>vns`, `aco>ils`, `aco>vns`.

Les témoins font partie de la liste : c'est l'écart entre un hybride et son témoin, **au même
budget**, qui mesure l'apport de la recherche locale.

**Un script** `run_ccl04_hybrids.py` à la racine, qui lance les douze avec `run_grid`, enregistre dans
`results/hybrid/ccl04_local_search.jsonl` et affiche le tableau des médianes.

```
python run_ccl04_hybrids.py                                        # 2000 evaluations, instances 1 2 5 9
python run_ccl04_hybrids.py --budget 5000 --workers 4
python run_ccl04_hybrids.py --instances 1 --seeds 0 --budget 400   # essai rapide
python run_ccl04_hybrids.py --describe                             # liste des hybrides
python reevaluer_ccl04.py                                          # reevaluation robuste des resultats
```

## Le budget de comparaison

Les mesures de `results/comparison/` ont toutes été faites à **200 évaluations** par exécution.
C'est moins que le coût d'une seule descente de la recherche locale de l'équipe (250 à 400
évaluations, mesuré sur l'instance 1). Dans ce réglage, `multi_start`, `iterated_local_search` et
`variable_neighbourhood_search` n'ont pas le temps de terminer leur premier pas de descente : ils
sont notés sur un échauffement, et tout hybride qui les utilise est handicapé de la même façon.

Le budget de l'examen correspond à **2 000 à 15 000 évaluations** selon l'instance : 15 minutes pour
3 instances, soit 300 secondes chacune, pour un coût par évaluation mesuré entre 15 ms (instance 1,
bon placement) et 550 ms (instance 2, placement aléatoire). Le budget par défaut de
`run_ccl04_hybrids.py` est donc 2 000, et non 200.

À titre de repère, l'instance 1 admet un placement à 23 — stable sur 10 réévaluations — trouvé par
`ILS` lancé 120 secondes. Le meilleur coût de tout `results/comparison/` sur cette instance est 25.

## Resultats de la campagne

144 executions : 12 algorithmes x instances 1, 2, 5, 9 x 3 graines, 2 000 evaluations chacune,
12 processus en parallele, 2 h 08 de calcul. Resultats dans deux fichiers :
`ccl04_local_search_resume.jsonl` (56 ko, une ligne par execution avec son meilleur placement et son
cout) et `ccl04_local_search.jsonl` (35 Mo, le meme avec l'historique evaluation par evaluation et les
traces internes, pour tracer les courbes de convergence). Le resume suffit a reproduire les tableaux
ci-dessous ; le fichier complet est volumineux et peut rester local.

Mediane du `best_cost` sur les trois graines, plus petit = mieux :

| algorithme | inst. 1 | inst. 2 | inst. 5 | inst. 9 |
|---|---|---|---|---|
| grasp | 28 | 59 | 320 | 51 |
| grasp+descente | 27 | 59 | 316 | 47 |
| grasp+vnd | 27 | 59 | 319 | 43 |
| grasp>ils | 27 | 59 | 319 | 39 |
| grasp>vns | **23** | 59 | 314 | **37** |
| aco | 25 | 59 | 319 | 49 |
| aco+descente | 27 | 59 | 316 | 48 |
| aco+vnd | 28 | 59 | **314** | 57 |
| aco>ils | 27 | 59 | 313 | 44 |
| aco>vns | 28 | 59 | 317 | 46 |
| ils | 26 | 62 | 315 | 51 |
| vns | 27 | 62 | **312** | 55 |

Ce qui se lit dans ce tableau :

**La recherche locale apporte quelque chose a GRASP, et l'apport grandit avec l'instance.** Sur
l'instance 9, la plus grosse (25 qubits logiques sur 27 physiques), GRASP seul plafonne a 51 sur les
trois graines, et les quatre hybrides descendent a 47, 43, 39 et 37. L'ecart est net et reproductible
graine par graine (51/51/51 contre 42/36/37 pour `grasp>vns`), ce n'est pas du bruit.

**La forme relais bat la forme integrative.** `grasp>vns` et `grasp>ils`, qui laissent la constructive
travailler puis donnent sa meilleure solution a la recherche locale, battent `grasp+vnd` et
`grasp+descente`, qui branchent une descente bornee sur chaque solution candidate. L'explication est
le budget : une descente complete coute 250 a 400 evaluations, donc la version integrative doit la
borner a 200 et ne rend jamais un optimum local, tandis que la version relais depense 40 % du budget
en une seule descente qui va jusqu'au bout.

**Les fourmis profitent moins de l'hybridation que GRASP.** `aco` seul est deja bon la ou `grasp` seul
est faible (25 contre 28 sur l'instance 1), et ses hybrides gagnent moins. La colonie fait deja une
forme d'intensification par les pheromones : la recherche locale est en partie redondante avec elle.

**L'instance 2 ne discrimine pas.** Tout le monde trouve 59, sauf `ils` et `vns` lances d'un placement
aleatoire qui restent a 62. Elle a autant de qubits physiques que logiques (16 et 16), donc le
voisinage de deplacement est vide et il ne reste que les echanges ; et sa solution a 59 est une simple
rotation, que n'importe quelle construction gloutonne trouve immediatement. Elle sert de temoin
negatif, pas de point de comparaison.

**Les temoins `ils` et `vns` seuls tiennent le rang.** A 2 000 evaluations ils sont dans le peloton,
et sur l'instance 5 `vns` seul est le meilleur de tous (312). La recherche locale n'a pas besoin d'une
constructive pour etre competitive ; c'est sur les grosses instances, ou un depart aleatoire coute
trop cher a rattraper, que le couplage paye.

## Le bruit de la fitness

Le routage (SabreSwap) n'est pas graine : un meme placement n'a pas toujours la meme profondeur. Le
`best_cost` d'une execution est donc le **minimum sur des centaines de tirages bruites**, c'est-a-dire
une valeur systematiquement optimiste, et d'autant plus optimiste que l'algorithme a fait
d'evaluations. Comparer deux lignes d'un tableau de `best_cost`, c'est comparer deux biais de
selection autant que deux algorithmes. Mesures sur l'instance 5 : un placement fixe donne entre 351
et 436, et le classement de 25 placements par un tirage unique ne correle qu'a 0,49 avec le meme
classement refait independamment, contre 0,94 pour une mediane de 5 tirages.

Dans le reste du depot ce biais n'est pas traite : `Problem.fitness_samples` existe mais n'est utilise
par aucun algorithme, et tous les couts enregistres sont des tirages uniques.

`reevaluer_ccl04.py` le corrige apres coup. Il reprend le meilleur placement de chaque algorithme sur
chaque instance et le reevalue 7 fois independamment ; la mediane de ces tirages est le niveau reel du
placement, celui qu'on obtiendrait en le rendant a l'examen. Resultat dans
`results/hybrid/ccl04_reevaluation.json`, sous la forme `annonce -> mediane [min-max]` :

| algorithme | inst. 1 | inst. 5 | inst. 9 |
|---|---|---|---|
| grasp | 25 -> 25 | 316 -> 336 | 51 -> 51 |
| grasp+descente | 25 -> 41 | 315 -> 385 | 42 -> 42 |
| grasp+vnd | 26 -> 26 | 315 -> 317 | 42 -> 42 |
| grasp>ils | **22 -> 22** | 317 -> 319 | 37 -> 40 |
| grasp>vns | 22 -> 22 | 308 -> 344 | **36 -> 39** |
| aco | 24 -> 24 | 317 -> 335 | 48 -> 51 |
| aco+descente | 25 -> 25 | 315 -> 332 | 47 -> 47 |
| aco+vnd | 27 -> 29 | 312 -> 340 | 46 -> 46 |
| aco>ils | 23 -> 23 | 308 -> 315 | 44 -> 44 |
| aco>vns | 27 -> 33 | 313 -> **314** | 43 -> 43 |
| ils | 25 -> 25 | 311 -> 376 | 48 -> 51 |
| vns | 23 -> 23 | 311 -> 317 | 42 -> 42 |

(L'instance 2 est omise : tous les placements y sont stables, 59 annonce et 59 reevalue.)

Deux lectures importantes.

**Certains chiffres annonces sont des coups de chance, d'autres sont solides.** Un placement stable
donne la meme valeur aux 7 tirages : `grasp>ils` sur l'instance 1 donne 22 sept fois sur sept, c'est
un vrai 22. A l'inverse `grasp>vns` annonce 308 sur l'instance 5 mais retombe a 344 de mediane : le
308 etait le tirage bas d'un placement qui vaut en realite 344, et le meilleur placement reel de
l'instance 5 est celui de `aco>vns`, annonce 313 et reevalue a 314. Le classement change avec la
reevaluation ; c'est exactement pour ca qu'elle est necessaire.

**Un bon placement est un placement stable.** Les placements stables sont ceux qui ne demandent
presque pas de routage : il n'y a rien a randomiser, donc la profondeur est reproductible. Les
placements dont la reevaluation s'effondre sont ceux qui dependent du hasard du routage. Le choix de
rendre a l'examen un placement a mediane 22 stable plutot qu'un placement annonce 308 mais instable
n'est donc pas de la prudence statistique, c'est le meilleur choix tout court.

Le repere de l'instance 1 est desormais **22**, trouve par `grasp>ils` et par `grasp>vns`, stable sur
7 reevaluations. Le meilleur cout de tout `results/comparison/` sur cette instance est 25.
