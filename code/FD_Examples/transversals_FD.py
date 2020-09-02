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
    solver_fd = Solver_FD(vars, trace=trace)
    if solver_fd.trace:
        print(f'{"~" * 90}\n')
        print('Following is the trace of the final search.')
        print(Solver_FD.to_str(sets))
        print(f'propagate: {Solver_FD.propagate}; smallest_first: {Solver_FD.smallest_first};\n')
    return solver_fd


if __name__ == '__main__':
    sets = gen_sets()
    solution_count = None
    print("""
Given a collection of sets, a transversal is a selection of one element
from each set with the property that no elements are repeated.
           
This program first generate a collection of sets. Then it searches for
transversals. Often there are many transversals. Very occassionally, 
there are no transversals. It all depends on the original sets.
           
The search is a standard depth-first search with two heuristics: propagate
and smallest_first.
           
The search is done four time with different settings of propagate and smallest-first.
           
When propagate is true, once an element is selected as the representative of one set,
it is removed from consideration as a posible representative of other sets.

When smallest-first is true, the search selectes an element for an unrepresented set
by chosing the smallest unrepresented set to find a representative for.
           
When both propagate and smallest_first are true, a trace of the search is shown.
""")

    print('The sets for which to find a traversal are:\n', Solver_FD.to_str(sets), '\n')
    print('The (alphabetized) traversals are:')

    for Solver_FD.propagate in [False, True]:
        for Solver_FD.smallest_first in [False, True]:
            solver_fd = set_up_for_transversals(sets)
            sol_str_set = set()

            if solver_fd.trace:
                print('*: Var was directly instantiated--and propagated if propagation is on.\n'
                      '-: Var was indirectly instantiated but not propagated.\n')

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
                print("Following are the statistics for the searches that aren't traced."
                      "\nAll searches should find the same transversals. The difference"
                      "\nis in the number of steps the search takes.\n")
                solution_count = len(sol_str_set)

            print(f'propagate: {Solver_FD.propagate}; smallest_first: {Solver_FD.smallest_first}; '
                  f'solutions: {solution_count}; steps: {solver_fd.line_no}')
    print(f'{"_" * 90}\n{"^" * 90}\n')
