from __future__ import annotations

from math import prod
from typing import Iterable, List

from solver import All_Different, Const_FD, Solver_FD, Var_FD


class Columns:

    def __init__(self, cols: List[List[Digit_FD]]):
        # Each col is a list of Digit_FD's
        self.cols = cols
        self.final_carry_out_var = Const_FD({0})

    def all_cols_ok(self):
        return all(self.col_is_ok(col_index) for col_index in range(len(self.cols)))

    def carry_out_domain(self, col_index):
        return frozenset({0}) if col_index == 0 else self.cols[col_index-1][0].domain

    def carry_out_var(self, col_index):
        return self.final_carry_out_var if col_index == 0 else self.cols[col_index-1][0]


    def col_is_ok(self, col_index):
        ok = self.summands_sum_upper_bound(col_index) >= self.target_lower_bound(col_index) and \
             self.summands_sum_lower_bound(col_index) <= self.target_upper_bound(col_index)
        return ok

    def complete_col(self, col_index):
        if self.col_is_ok(col_index):
            if  self.summands_sum_upper_bound(col_index) == self.summands_sum_lower_bound(col_index):
                (carry_out_var, sum_dig_var) = (self.carry_out_var(col_index), self.cols[col_index][-1])
                (carry_out, sum_dig) = divmod(self.summands_sum_upper_bound(col_index), 10)
                (carry_out_cvar, sum_dig_cvar) = (Const_FD({carry_out}), Const_FD({sum_dig}))
                yield from Solver_FD.unify_pairs_FD([(carry_out_var, carry_out_cvar), (sum_dig_var, sum_dig_cvar)])
            else: yield

    def instantiate_problem(self, col_index):
        # print('in', col_index)
        # if col_index == 0:
        #     print(col_index)
        for _ in self.complete_col(col_index):
            # print('out', col_index)
            if col_index == 0: yield
            else: yield from self.instantiate_problem(col_index - 1)

    def smallest_column_summand(self):
        """
        Find the Var in the column with the smallest number of
        available possibilities among its term vars. Then select
        the var with the smallest domain.
        """
        def summands_domains_sizes(col):
            return prod( [len(x.domain) for x in col[:-1]] )

        col_uninstans = [(self.cols[indx], summands_domains_sizes(self.cols[indx]), indx)
                         for indx in range(len(self.cols)) if summands_domains_sizes(self.cols[indx]) > 1 and
                                                              any(not d.was_propagated for d in self.cols[indx][1:-1])]
        (min_col, _, _) = min(col_uninstans, key=lambda cu: (cu[1], cu[2]))
        # col[1:-1]gets the middle elements
        smallest_var = min(min_col[1:-1], key=lambda x: len(x.domain) if len(x.domain) > 1 else float('inf'))
        return smallest_var

    def summands_sum_lower_bound(self, col_index):
        col = self.cols[col_index]
        summands_digits = col[:-1]
        return sum(d.lower_bound for d in summands_digits)

    def summands_sum_upper_bound(self, col_index):
        col = self.cols[col_index]
        summands_digits = col[:-1]
        return sum(d.upper_bound for d in summands_digits)

    def target_lower_bound(self, col_index):
        col = self.cols[col_index]
        return min(self.carry_out_domain(col_index))*10 + min(col[-1].domain)

    def target_upper_bound(self, col_index):
        col = self.cols[col_index]
        return max(self.carry_out_domain(col_index))*10 + max(col[-1].domain)


class Digit_FD(Var_FD):

    @staticmethod
    def letters_to_vars(st: Iterable, d: dict) -> List:
        """ Look up the elements in st in the dictionary d. """
        return [d[s] for s in st]

    @property
    def lower_bound(self):
        return min(self.domain)

    @staticmethod
    def terms_to_number_string(vs) -> str:
        """  Convert a list of Vars to a string of digits. """
        digits = "".join((str(v.value) if v.is_instantiated() else '_') for v in vs)
        return digits

    @staticmethod
    def terms_to_letter_string(vs) -> str:
        """  Convert a list of Vars to a string (of letters). """
        letters = "".join(v.var_name[0] for v in vs)
        return letters

    @property
    def upper_bound(self):
        return max(self.domain)


class Crypto_FD(Solver_FD):

    def __init__(self, carries, term_1_vars, term_2_vars, sum_vars, columns, problem_vars, trace):
        # Store the variables in lists from left to right.
        # Process the columns starting at position len(sum_vars)
        self.col_index = len(sum_vars)
        self.carries = carries
        self.term_1_vars = term_1_vars
        self.term_2_vars = term_2_vars
        self.sum_vars = sum_vars
        self.columns = Columns(columns)
        super().__init__(problem_vars | set(carries), trace=trace)

    def constraints_satisfied(self):
        return self.columns.all_cols_ok()

    def problem_is_solved(self):
        """ The solution condition for transversals. (But not necessarily all problems.) """
        problem_solved = all(v.is_instantiated() for v in self.vars)
        return problem_solved

    def propagate_consequences(self):
        yield from self.columns.instantiate_problem(len(self.columns.cols)-1)

    def select_var_to_instantiate(self):
        nxt_var = self.columns.smallest_column_summand()
        return nxt_var

    def state_string(self, solved=True):
        vars_list = sorted(self.vars, key=lambda v: v.var_name)
        ln2 = (len(vars_list) - 5) // 2
        ln_sums = len(self.sum_vars)
        if not solved:
            domains = f'{Solver_FD.to_str(vars_list[5:(5 + ln2)])}\n' \
                      f'{Solver_FD.to_str(vars_list[(5 + ln2):])}\n' \
                      f'==================================================================='
        else:
            domains = ''
        return f'{"C"*len(self.sum_vars)} -> {Digit_FD.terms_to_number_string(self.carries)}\n' \
               f'{Crypto_FD.vars_to_letters_and_numbers(self.term_1_vars)}' \
               f'{Crypto_FD.vars_to_letters_and_numbers(self.term_2_vars)}' \
               f'{"-" * ln_sums}    {"-" * ln_sums}\n' \
               f'{Crypto_FD.vars_to_letters_and_numbers(self.sum_vars)}' \
               f'{domains}'

    @staticmethod
    def vars_to_letters_and_numbers(vars):
        return f'{Digit_FD.terms_to_letter_string(vars)} -> {Digit_FD.terms_to_number_string(vars)}\n' \



def run_problem(trace=False):
    # See http://bach.istc.kobe-u.ac.jp/llp/crypt.html (and links) for these and many(!) more.
    # noinspection LongLine
    for (term_1, term_2, sum) in [
        ('SEND', 'MORE', 'MONEY'),        # 9567 + 1085 = 10652
        ('BASE', 'BALL', 'GAMES'),        # 7483 + 7455 = 14938
        ('SATURN', 'URANUS', 'PLANETS'),  # 546790 + 794075 = 1340865
        ('POTATO', 'TOMATO', 'PUMPKIN')   # 168486 + 863486 = 1031972
        ]:
        crypto_solver = set_up(term_1, term_2, sum, trace=trace)
        print()
        # crypto_solver.show_state("Start", solved=False)

        for _ in crypto_solver.solve():
            # crypto_solver.show_state("Solution", solved=True)
            print(f'{crypto_solver.state_string(solved=True)}')
        print('No more solutions')
        print(f'=================')


def set_up(term_1: str, term_2: str, sum: str, trace=False):
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
    vars_dict = {letter: Digit_FD(frozenset(init_domain), var_name=letter) for letter in var_letters}
    zero = Digit_FD(frozenset({0}), var_name='_')
    zero.was_propagated = True
    sum_length = len(sum)
    term_1_vars = [zero]*(sum_length - len(term_1)) + Digit_FD.letters_to_vars(term_1, vars_dict)
    term_2_vars = [zero]*(sum_length - len(term_2)) + Digit_FD.letters_to_vars(term_2, vars_dict)
    sum_vars =                                        Digit_FD.letters_to_vars(sum, vars_dict)

    problem_vars = set(vars_dict.values())
    All_Different(problem_vars)

    # # Leading_Digit_FDs are the variables that should not be assigned 0.
    # Leading_Digit_FDs = letters_to_vars({term_1[0], term_2[0], sum[0]}, vars_dict)
    carries = [Digit_FD(frozenset({0, 1}), var_name=f'C{i}') for i in range(sum_length)]
    for c in carries:
        c.was_propagated = True
    columns = list(zip(carries, term_1_vars, term_2_vars, sum_vars))

    # Mark carries as was_propagated since they are never propagated.
    carries[-1].set_init_domain(frozenset({0}), was_propagated=True)
    if len(term_1) == len(term_2) == len(sum)-1:
        carries[0].set_init_domain(frozenset({1}), was_propagated=True)
        sum_vars[0].set_init_domain(frozenset({1}), was_propagated=True)
        for v in problem_vars-{sum_vars[0]}:
            v.set_init_domain(v.domain-{1}, was_propagated=False)

    crypto_solver = Crypto_FD(carries, term_1_vars, term_2_vars, sum_vars, columns, problem_vars, trace=trace)
    return crypto_solver


if __name__ == '__main__':
    run_problem()
