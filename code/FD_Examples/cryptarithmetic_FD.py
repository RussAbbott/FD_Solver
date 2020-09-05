from __future__ import annotations

from math import prod
from typing import Iterable, List

from solver import All_Different, Solver_FD, Var_FD


# def complete_column(carry_out: int, Carry_Out_Dig,
#                     sum_dig: int, Sum_Dig,
#                     digits_in: List[int], Leading_Digits):
#   """
#   If Sum_Dig (the variable representing the digit in the sum for this column) is not yet instantiated,
#   instantiate it to sum_dig  (if that digit is available). If Sum_Dig is already instantiated, ensure
#   it is consistent with the sum_dig. Instantiate Carry_Out_Dig to carry_out.
#   """
#   # Is Sum_Dig uninstantiated? If so, instantiate it to sum_digit if possible.
#   # Then instantiate Carry_Out_Dig, and return (yield) digits_in with sum_digit removed.
#   if not Sum_Dig.is_instantiated():
#     if sum_dig not in digits_in:
#       # sum_dig is not available in digits_in. Fail, i.e., return instead of yield.
#       return
#
#     # sum_dig is available in digits_in. Give it to Sum_Dig as long as this does not give
#     # 0 to one of the leading digits.
#     if not (sum_dig == 0 and Sum_Dig in Leading_Digits):
#       for _ in unify_pairs([(Carry_Out_Dig, carry_out), (Sum_Dig, sum_dig)]):
#         # Remove sum_digit from digits_in
#         i = digits_in.index(sum_dig)
#         yield digits_in[:i] + digits_in[i + 1:]
#
#   # If Sum_Dig is instantiated, is it equal to sum_digit?
#   # If so, instantiate Carry_Out_Dig and return the current digits_in.
#   elif sum_dig == Sum_Dig.get_py_value( ):
#     for _ in unify(Carry_Out_Dig, carry_out):
#       yield digits_in
#
#
# def solve(Carries: List[PyValue],
#           Term1: List[PyValue],
#           Term2: List[PyValue],
#           Sum: List[PyValue],
#           Leading_Digits: List[PyValue]):
#   """
#   Solve the problem.
#   The two embedded functions below refer to the lists in solve's params.
#   The lists never change, but their elements are unified with values.
#   No point is copying the lists repeatedly. So embed the functions that refer to them.
#   """
#
#   def fill_column(PVs: List[PyValue], index: int, digits_in: List[int]):
#     """
#     PVs are the digits in the current column to be added together, one from each term.
#     digits-in are the digits that have not yet been assigned to a Var.
#     Find digits in digits_in that make the column add up properly.
#     Return (through yield) the digits that are not yet used after the new assignments.
#     We do this recursively on PVs--even though we are currently assuming only two terms.
#     """
#     if not PVs:
#       # We have instantiated the digits to be added.
#       # Instantiate Sum_Dig (if possible) and Carries[index - 1] to the total.
#       # Completing the column is a bit more work than it might seem.
#       (carry_in, digit_1, digit_2) = (D.get_py_value( ) for D in [Carries[index], Term1[index], Term2[index]])
#       total = sum([carry_in, digit_1, digit_2])
#       (carry_out, sum_dig) = divmod(total, 10)
#       yield from complete_column(carry_out, Carries[index-1], sum_dig, Sum[index], digits_in, Leading_Digits)
#
#     else:
#       # Get head and tail of PVs.
#       [PV, *PVs] = PVs
#       # If PV already has a value, nothing to do. Go on to the remaining PVs.
#       if PV.is_instantiated( ):
#         yield from fill_column(PVs, index, digits_in)
#       else:
#         # Give PV one of the available digits. Through "backup" all digits will be tried.
#         for i in range(len(digits_in)):
#           if not (digits_in[i] == 0 and PV in Leading_Digits):
#             for _ in unify(PV, digits_in[i]):
#               yield from fill_column(PVs, index, digits_in[:i] + digits_in[i + 1:])
#
#   def solve_aux(index: int, digits_in: List[int]):
#     """ Traditional addition: work from right to left. """
#     # When we reach 0, we're done.
#     if index == 0:
#       # Can't allow a carry to this position.
#       if Carries[0].get_py_value() == 0:
#         yield
#       else:
#         # If we reach index == 0 but have a carry into the last column, fail.
#         # Won't have such a carry with only two terms. But it might happen with many terms,.
#         return
#     else:
#       for digits_out in fill_column([Term1[index], Term2[index]], index, digits_in):
#           yield from solve_aux(index-1, digits_out)
#
#   yield from solve_aux(len(Carries)-1, list(range(10)))
#
#
class Columns:

    def __init__(self, cols: List[List[Var_FD]], carry_out: Var_FD):
        self.cols = cols
        self.carry_out_term = carry_out

    def carry_in_value(self, col_indx):
        return self.cols[col_indx][0].value

    def carry_out_value(self, col_indx):
        return 0 if col_indx == 0 else self.cols[col_indx - 1][0].value

    def check_a_col(self, col_indx):
        # noinspection PyUnboundLocalVariable
        return (sum := self.col_sum_value(col_indx)) is None \
               or (target := self.col_target_value(col_indx)) is None \
               or sum == target


    def col_sum_value(self, col_indx):
        col_sum_values = [c.value for c in self.cols[col_indx][1:-1]]
        return None if None in col_sum_values else sum(col_sum_values)\

    def col_target_value(self, col_indx):
        col_target_values = [self.cols[col_indx-1][0], self.cols[col_indx][3]]
        return None if None in col_target_values else sum(col_target_values)

    def middle_terms(self, col_indx):
        return [c.value for c in self.cols[col_indx][1:-1]]

    def smallest_column_term_var(self):
        """
        Find the Var in the column with the smallest number of
        available possibilities among its term vars. Then select
        the var with the smallest domain.
        """
        def term_domains_sizes(col):
            # col[1:-1]gets the middle elements
            return prod( [len(x.domain) for x in col[1:-1]] )

        col_uninstans = [(self.cols[indx], term_domains_sizes(self.cols[indx]), indx)
                         for indx in range(len(self.cols)) if term_domains_sizes(self.cols[indx]) > 1]
        (min_col, _, _) = min(col_uninstans, key=lambda cu: (cu[1], cu[2]))
        smallest_var = min(min_col[1:-1], key=lambda x: len(x.domain) if len(x.domain) > 1 else float('inf'))
        return smallest_var




class Crypto_FD(Solver_FD):

    def __init__(self, carries, term_1_vars, term_2_vars, sum_vars, columns, problem_vars):
        # Store the variables in lists from left to right.
        # Process the columns starting at position len(sum_vars)
        self.col_index = len(sum_vars)
        self.carries = carries
        self.term_1_vars = term_1_vars
        self.term_2_vars = term_2_vars
        self.sum_vars = sum_vars
        self.columns = Columns(columns, carries[0])
        super().__init__(problem_vars | set(carries))

    # def add_col(self, col_vars_terms, col_var_sum):
    #     # Must be expanded
    #     print(self, col_vars_terms, col_var_sum)
    #     yield

    def narrow(self):
        yield from self.run_a_col()

    def problem_is_solved(self):
        return self.col_index < 0

        # Increment col_index back to where it was.


def var_to_str(var):
    return ' ' if var.var_name == "Zero" else str(var.value()) if var.is_instantiated else Solver_FD.to_str(var)


def letters_to_vars(st: Iterable, d: dict) -> List:
    """ Look up the elements in st in the dictionary d. """
    return [d[s] for s in st]


def run_problem():
    # See http://bach.istc.kobe-u.ac.jp/llp/crypt.html (and links) for these and many(!) more.
    for (term_1, term_2, sum) in [
        ('SEND', 'MORE', 'MONEY'),
        # ('BASE', 'BALL', 'GAMES'),
        # ('SATURN', 'URANUS', 'PLANETS'),
        # ('POTATO', 'TOMATO', 'PUMPKIN')
        ]:
        crypto_solver = set_up(term_1, term_2, sum)

        # print(f'\nCarries: {", ".join(map(Solver_FD.to_str, crypto_solver.carries))}\n')
        print(f'\nCarries: {Solver_FD.to_str(crypto_solver.carries)}\n')
        print(f'{term_to_string(crypto_solver.carries)} -> {term_to_number(crypto_solver.carries)}')
        print(f'{term_to_string(crypto_solver.term_1_vars[0:])} -> {term_to_number(crypto_solver.term_1_vars)}')
        print(f'{term_to_string(crypto_solver.term_2_vars[0:])} -> {term_to_number(crypto_solver.term_2_vars)}')
        print(f'{term_to_string(crypto_solver.sum_vars)} -> {term_to_number(crypto_solver.sum_vars)}\n')

        print(f'{" ".join(term_to_string(col) for col in crypto_solver.columns.cols)}')
        print(f'{" ".join(term_to_number(col) for col in crypto_solver.columns.cols)}')

        print(Solver_FD.to_str(crypto_solver.vars).replace('}, ', '}\n'))

        # This tests smallest_column_term_var
        crypto_solver.term_1_vars[2].update_domain({3, 4})
        crypto_solver.term_1_vars[4].update_domain({1, 2, 7})
        crypto_solver.term_2_vars[2].update_domain({5})
        print()
        print(crypto_solver.term_1_vars[2], crypto_solver.term_1_vars[4], crypto_solver.term_2_vars[2])
        print(crypto_solver.columns.smallest_column_term_var())  # => E:{3, 4} D:{1, 2, 7} O-:{5}
                                                                 #    E:{3, 4}
        crypto_solver.term_1_vars[2].undo_update_domain()
        crypto_solver.term_1_vars[4].undo_update_domain()
        crypto_solver.term_2_vars[2].undo_update_domain()
        print()
        print(crypto_solver.term_1_vars[2], crypto_solver.term_1_vars[4], crypto_solver.term_2_vars[2])
        # noinspection LongLine
        print(crypto_solver.columns.smallest_column_term_var())  # => E:{0, 2, 3, 4, 5, 6, 7, 8, 9} D:{0, 2, 3, 4, 5, 6, 7, 8, 9} O:{0, 2, 3, 4, 5, 6, 7, 8, 9}
                                                                 # S:{0, 2, 3, 4, 5, 6, 7, 8, 9}



def set_up(term_1: str, term_2: str, sum: str):
    """
    Convert the initial string representation to (uninstantiated) FD_Vars.
    term_1 and term_2 are the numbers to be added. sum is the sum.
    zero is 0. It will be replaced by leading blanks.
    """
    var_letters = sorted(list(set(term_1 + term_2 + sum)))
    if len(var_letters) > 10:
        print(f'Too many variables: {var_letters}')
        return
    # noinspection PyUnboundLocalVariable
    init_domain = set(range(10))
    vars_dict = {letter: Var_FD(frozenset(init_domain), var_name=letter) for letter in var_letters}
    zero = Var_FD(frozenset({0}), var_name='0')
    sum_length = len(sum)
    term_1_vars = [zero]*(sum_length - len(term_1)) + letters_to_vars(term_1, vars_dict)
    term_2_vars = [zero]*(sum_length - len(term_2)) + letters_to_vars(term_2, vars_dict)
    sum_vars = [zero] * (sum_length - len(sum)) + letters_to_vars(sum, vars_dict)

    problem_vars = set(vars_dict.values())
    All_Different(problem_vars)

    # # Leading_Digits are the variables that should not be assigned 0.
    # Leading_Digits = letters_to_vars({term_1[0], term_2[0], sum[0]}, vars_dict)
    carries = [Var_FD(frozenset({0, 1}), var_name=f'C{i}') for i in range(sum_length)]
    columns = list(zip(carries, term_1_vars, term_2_vars, sum_vars))

    # Mark carries as was_propagated since they are never propagated.
    carries[-1].set_init_domain(frozenset({0}), was_propagated=True)
    if len(term_1) == len(term_2) == len(sum)-1:
        sum_vars[0].set_init_domain(frozenset({1}), was_propagated=True)
        for v in problem_vars:
            if v is not sum_vars[0]:
                v.set_init_domain(v.domain-{1}, was_propagated=False)
        carries[0].set_init_domain(frozenset({1}), was_propagated=True)

    crypto_solver = Crypto_FD(carries, term_1_vars, term_2_vars, sum_vars, columns, problem_vars)
    return crypto_solver


def term_to_number(vs) -> str:
    """  Convert a list of Vars to a string of digits. """
    digits = "".join((str(v.value) if v.is_instantiated() else '_') for v in vs)
    return digits


def term_to_string(vs) -> str:
    """  Convert a list of Vars to a string (of letters). """
    letters = "".join(v.var_name[0] for v in vs)
    return letters


# def solve_crypto(term_1: str, term_2: str, sum: str):
#   _Z = PyValue(0)
#   (Carries, T1, T2, Sum, Leading_Digits) = set_up_puzzle(term_1, term_2, sum, _Z)
#   want_more = None
#   Blank = PyValue(' ')
#   for _ in solve(Carries, T1, T2, Sum, Leading_Digits):
#     # We have a solution.
#     # Replace the leading _Z zeros with blanks and convert each number to a string.
#     # We can discard T1[0], T2[0], and Sum[0] because we know they will be 0.
#     (term_1_out, term_2_out, tot_out) = (solution_to_string(T, _Z, Blank) for T in [T1[1:], T2[1:], Sum[1:]])
#     print()
#     print(f'  {term_1}  -> {term_1_out}')
#     print(f'+ {term_2}  -> {term_2_out}')
#     print(f'{"-" * (len(sum)+1)}     {"-" * len(sum)}')
#     print(f' {sum}  -> {tot_out}')
#     ans = input('\nLook for more solutions? (y/n) > ').lower( )
#     want_more = ans[0] if len(ans) > 0 else 'n'
#     if want_more != 'y':
#       break
#   if want_more == 'y':
#     print('No more solutions.')


if __name__ == '__main__':

    run_problem()

    # # See http://bach.istc.kobe-u.ac.jp/llp/crypt.html (and links) for these and many(!) more.
    # for (term_1, term_2, sum) in [
    #     ('SEND', 'MORE', 'MONEY'),
    #     # ('BASE', 'BALL', 'GAMES'),
    #     # ('SATURN', 'URANUS', 'PLANETS'),
    #     # ('POTATO', 'TOMATO', 'PUMPKIN')
    #     ]:
    #     crypto_solver = set_up(term_1, term_2, sum)
    #
    #     print(f'\nCarries: {", ".join(map(Solver_FD.to_str, crypto_solver.carries))}\n')
    #     print(f'{term_to_string(crypto_solver.carries)} -> {term_to_number(crypto_solver.carries)}')
    #     print(f' {term_to_string(crypto_solver.term_1_vars[0:])} ->  {term_to_number(crypto_solver.term_1_vars)}')
    #     print(f' {term_to_string(crypto_solver.term_2_vars[0:])} ->  {term_to_number(crypto_solver.term_2_vars)}')
    #     print(f' {term_to_string(crypto_solver.sum_vars)} ->  {term_to_number(crypto_solver.sum_vars)}\n')
    #
    #     print(f'{" ".join(term_to_string(col) for col in crypto_solver.cols)}')
    #     print(f'{" ".join(term_to_number(col) for col in crypto_solver.cols)}')
    #
    #     print(crypto_solver.smallest_column_var())
