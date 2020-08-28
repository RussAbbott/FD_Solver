from __future__ import annotations

from random import randint, sample

from control_structures import Trace
from solver import All_Different, FD_Solver, FD_Var


def gen_sets(nbr_sets=5):
    sets_size_low = 2
    sets_size_high = nbr_sets
    vals_size = nbr_sets
    (vals_range_start_min, vals_range_start_max) = (ord('a'), ord('z') + 1 - vals_size)
    alpha_low = randint(vals_range_start_min, vals_range_start_max)
    vals = [chr(alpha_low + k) for k in range(vals_size)]
    sets = [{k for k in sample(vals, randint(sets_size_low, sets_size_high))}
            for _ in range(nbr_sets)]
    return sets


if __name__ == '__main__':
    print()
    sets = gen_sets()
    for FD_Var.propagate in [False, True]:
        for FD_Var.smallest_first in [False, True]:
            FD_Var.id = 0
            All_Different.sibs_dict = {}
            # Create an FV_Var for each set
            vars = {FD_Var(set) for set in sets}
            All_Different(vars)
            fd_solver = FD_Solver(vars, {All_Different.all_satisfied})
            Trace.line_no = 0
            Trace.trace = True
            Trace.trace = False
            solutions = 0
            print(f'{"~" * 90}')
            print(Trace.to_str(vars))

            print(f'propagate: {FD_Var.propagate}; smallest_first: {FD_Var.smallest_first};\n')
            for _ in fd_solver.solve():
                solutions += 1
                if Trace.trace:  print()
                print(f"{solutions}. {Trace.to_str(vars)}")
                if Trace.trace:  print()
            print(f'propagate: {FD_Var.propagate}; smallest_first: {FD_Var.smallest_first}; '
                  f'solutions: {solutions}; lines: {Trace.line_no}')
            print(f'{"_" * 90}\n{"^" * 90}\n')
