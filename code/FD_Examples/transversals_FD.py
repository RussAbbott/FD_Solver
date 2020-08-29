from __future__ import annotations

from random import randint, sample

from solver import All_Different, Solver_FD, Var_FD


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
    sol_str_set_0 = set()
    print(Solver_FD.to_str({Var_FD(set) for set in sets}), '\n')
    for Var_FD.propagate in [False, True]:
        for Var_FD.smallest_first in [False, True]:
            Var_FD.id = 0
            All_Different.sibs_dict = {}
            # Create an FV_Var for each set
            vars = {Var_FD(set) for set in sets}
            All_Different(vars)
            trace = Var_FD.propagate and Var_FD.smallest_first
            solver_fd = Solver_FD(vars, constraints={All_Different.all_satisfied}, trace=trace)
            sol_str_set_n = set()
            if solver_fd.trace:
                print(f'{"~" * 90}\n')
                print(Solver_FD.to_str(vars))
                print(f'propagate: {Var_FD.propagate}; smallest_first: {Var_FD.smallest_first};\n')
            for _ in solver_fd.solve():
                sol_string = Solver_FD.to_str(vars)
                sol_str_set_n |= {sol_string}
                solutions_nbr = len(sol_str_set_n)
                sol_nbr_str = f'{" " if solutions_nbr < 10 else ""}{solutions_nbr}'
                if solver_fd.trace:  print(f"\t\t=>\t{sol_nbr_str}. {sol_string}\n")

            if len(sol_str_set_0) != len(sol_str_set_n):
                for (n, s) in enumerate(sorted(sol_str_set_n)):
                    print(f'{" " if n < 9 else ""}{n+1}. {s}')
                print()
                sol_str_set_0 = sol_str_set_n
            print(f'propagate: {Var_FD.propagate}; smallest_first: {Var_FD.smallest_first}; '
                  f'solutions: {len(sol_str_set_n)}; lines: {solver_fd.line_no}')
            if solver_fd.trace and not sol_str_set_0: print(f'{"_" * 90}\n{"^" * 90}\n')
