"""Paquet « optimizer » : le socle commun pour écrire, lancer et comparer des métaheuristiques.

Ce fichier regroupe les fonctions les plus utilisées pour pouvoir écrire simplement
`from optimizer import load_instance, Problem, run_grid` au lieu d'importer chaque module séparément.
"""

from .experiment import history_frame, load_results, results_frame, run_algorithm, run_grid, save_results
from .instance import InstanceData, available_instances, load_instance
from .problem import BudgetExhausted, Problem
from .result import Result
from .solution_files import write_result, write_result_if_better, write_solution, write_solution_if_better
from .surrogate import direct_gate_ratio, distance_cost, pair_distances
