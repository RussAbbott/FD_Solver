from __future__ import annotations

from random import randint, sample

from solver import All_Different, Const_FD, Solver_FD, Var_FD


def gen_sets(nbr_sets=5):
    sets_size_low = 2
    sets_size_high = nbr_sets
    vals_size = nbr_sets
    (vals_range_start_min, vals_range_start_max) = (ord('a'), ord('z') + 1 - vals_size)
    alpha_low = randint(vals_range_start_min, vals_range_start_max)
    vals = [chr(alpha_low + k) for k in range(vals_size)]
    sets = [Const_FD(sample(vals, randint(sets_size_low, sets_size_high)))
            for _ in range(nbr_sets)]
    return sets


def set_up_for_transversals(sets):
    """ Set up the solver and All_Different for the transversals problem. """
    Var_FD.id = 0
    All_Different.sibs_dict = {}
    # Create a Var_FD for each set. Its initial range is the entire set.
    vars = {Var_FD(s.range) for s in sets}
    All_Different(vars)
    trace = Solver_FD.propagate and Solver_FD.smallest_first
    solver_fd = Solver_FD(vars, constraints={All_Different.all_satisfied}, trace=trace)
    if solver_fd.trace:
        print(f'{"~" * 90}\n')
        print(Solver_FD.to_str(sets))
        print(f'propagate: {Solver_FD.propagate}; smallest_first: {Solver_FD.smallest_first};\n')
    return solver_fd


if __name__ == '__main__':
    sets = gen_sets()
    solution_count = None
    print('\n', Solver_FD.to_str(sets), '\n')

    for Solver_FD.propagate in [False, True]:
        for Solver_FD.smallest_first in [False, True]:
            solver_fd = set_up_for_transversals(sets)
            sol_str_set = set()

            for _ in solver_fd.solve():
                sol_string = Solver_FD.to_str(solver_fd.vars)
                sol_str_set |= {sol_string}
                if solver_fd.trace:
                    solutions_nbr = len(sol_str_set)
                    sol_nbr_str = f'{" " if solutions_nbr < 10 else ""}{solutions_nbr}'
                    print(f"\t\t=>\t{sol_nbr_str}. {sol_string}\n")

            if solution_count != len(sol_str_set):
                for (n, s) in enumerate(sorted(sol_str_set)):
                    print(f'{" " if n < 9 else ""}{n+1}. {s}')
                print()
                solution_count = len(sol_str_set)

            print(f'propagate: {Solver_FD.propagate}; smallest_first: {Solver_FD.smallest_first}; '
                  f'solutions: {solution_count}; lines: {solver_fd.line_no}')
    print(f'{"_" * 90}\n{"^" * 90}\n')
