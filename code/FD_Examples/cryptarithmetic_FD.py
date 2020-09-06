from __future__ import annotations

from math import prod
from typing import Iterable, List

from solver import All_Different, Solver_FD, Var_FD


class Columns:

    def __init__(self, cols: List[List[Var_FD]], carry_out: Var_FD):
        self.cols = cols
        self.carry_out_term = carry_out

    def all_cols_ok(self):
        return all(self.col_is_ok(col_indx) for col_indx in range(len(self.cols)))

    def carry_in_value(self, col_indx):
        return self.cols[col_indx][0].value

    def carry_out_value(self, col_indx):
        return 0 if col_indx == 0 else self.cols[col_indx-1][0].value

    # def col_sum_high(self, col_indx):
    #     return self.carry_out_value(col) * 10 + self.domain_high(col[-1])
    #
    # def col_sum_low(self, col_indx):
    #     return self.carry_in_value(col) * 10 + self.domain_high(col[-1])
    #
    def col_is_ok(self, col_indx):
        # noinspection PyUnboundLocalVariable
        return (sum := self.col_sum_value(col_indx)) is None \
               or (target := self.col_target_value(col_indx)) is None \
               or sum == target

    # def col_is_ok(self, col):
    #     sum([self.domain_high(v) for v in col[:-1]])

    def col_sum_value(self, col_indx):
        col_sum_values = [c.value for c in self.cols[col_indx][:-1]]
        return None if None in col_sum_values else sum(col_sum_values)

    def col_target_value(self, col_indx):
        [carry_val, digit_val] = [self.carry_out_value(col_indx), self.cols[col_indx][-1].value]
        return None if None in [carry_val, digit_val] else carry_val*10 + digit_val

    # def domain_high(self, v):
    #     return max(v.domain)
    #
    # def domain_low(self, v):
    #     return min(v.domain)
    #
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


class Digit_FD(Var_FD):

    def __str__(self):
        return ' ' if self.var_name == "Zero" else str(self.value) if self.is_instantiated else super().__str__()

    @staticmethod
    def letters_to_vars(st: Iterable, d: dict) -> List:
        """ Look up the elements in st in the dictionary d. """
        return [d[s] for s in st]

    @staticmethod
    def term_to_number(vs) -> str:
        """  Convert a list of Vars to a string of digits. """
        digits = "".join((str(v.value) if v.is_instantiated() else '_') for v in vs)
        return digits

    @staticmethod
    def term_to_string(vs) -> str:
        """  Convert a list of Vars to a string (of letters). """
        letters = "".join(v.var_name[0] for v in vs)
        return letters


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

    def constraints_satisfied(self):
        return self.columns.all_cols_ok()

    def select_var_to_instantiate(self):
        nxt_var = self.columns.smallest_column_term_var()
        return nxt_var

    def state_string(self, solved):
        vars_list = sorted(self.vars, key=lambda v: v.var_name)
        ln2 = (len(vars_list) - 5) // 2
        return f'\n{"C"*len(self.sum_vars)} -> {Digit_FD.term_to_number(self.carries)}\n' +\
               f'{Digit_FD.term_to_string(self.term_1_vars[0:])} -> {Digit_FD.term_to_number(self.term_1_vars)}\n' + \
               f'{Digit_FD.term_to_string(self.term_2_vars[0:])} -> {Digit_FD.term_to_number(self.term_2_vars)}\n' + \
               f'{"-" * (len(self.sum_vars))}    {"-" * len(self.sum_vars)}\n' + \
               f'{Digit_FD.term_to_string(self.sum_vars)} -> {Digit_FD.term_to_number(self.sum_vars)}\n\n' + \
               f'{Solver_FD.to_str(vars_list[5:(5 + ln2)])}\n' + \
               f'{Solver_FD.to_str(vars_list[(5 + ln2):])}'


def run_problem():
    # See http://bach.istc.kobe-u.ac.jp/llp/crypt.html (and links) for these and many(!) more.
    # noinspection LongLine
    for (term_1, term_2, sum) in [
        ('SEND', 'MORE', 'MONEY'),
        # ('BASE', 'BALL', 'GAMES'),
        # ('SATURN', 'URANUS', 'PLANETS'),
        # ('POTATO', 'TOMATO', 'PUMPKIN')
        ]:
        crypto_solver = set_up(term_1, term_2, sum)
        print(crypto_solver.state_string(False))

        # for _ in crypto_solver.solve():


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
    vars_dict = {letter: Digit_FD(frozenset(init_domain), var_name=letter) for letter in var_letters}
    zero = Digit_FD(frozenset({0}), var_name='0')
    sum_length = len(sum)
    term_1_vars = [zero]*(sum_length - len(term_1)) + Digit_FD.letters_to_vars(term_1, vars_dict)
    term_2_vars = [zero]*(sum_length - len(term_2)) + Digit_FD.letters_to_vars(term_2, vars_dict)
    sum_vars =                                        Digit_FD.letters_to_vars(sum, vars_dict)

    problem_vars = set(vars_dict.values())
    All_Different(problem_vars)

    # # Leading_Digit_FDs are the variables that should not be assigned 0.
    # Leading_Digit_FDs = letters_to_vars({term_1[0], term_2[0], sum[0]}, vars_dict)
    carries = [Digit_FD(frozenset({0, 1}), var_name=f'C{i}') for i in range(sum_length)]
    columns = list(zip(carries, term_1_vars, term_2_vars, sum_vars))

    # Mark carries as was_propagated since they are never propagated.
    carries[-1].set_init_domain(frozenset({0}), was_propagated=True)
    if len(term_1) == len(term_2) == len(sum)-1:
        carries[0].set_init_domain(frozenset({1}), was_propagated=True)
        sum_vars[0].set_init_domain(frozenset({1}), was_propagated=True)
        for v in problem_vars-{sum_vars[0]}:
            v.set_init_domain(v.domain-{1}, was_propagated=False)

    crypto_solver = Crypto_FD(carries, term_1_vars, term_2_vars, sum_vars, columns, problem_vars)
    return crypto_solver


if __name__ == '__main__':

    run_problem()
