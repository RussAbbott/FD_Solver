from __future__ import annotations

from collections.abc import Iterable
from typing import List, Set, Union


class All_Different:
    """ Each All_Different object is a collection of FD_Vars that must be different. """

    # sibs_dict is a dictionary. Each key is an FD_Var's; the value is a set of FD_Var's that must differ from it.
    # sibs_dict is a dictionary of siblings, where a sibling must have a different value.
    # sibs_dict = {FD_Var_x: {FD_Var_i that must be different from FD_Var_x}}
    # sibs_dict is aggregated from the All_Different declarations.
    sibs_dict = {}

    def __init__(self, vars: Set[Var_FD]):
        self.vars = vars
        for v in vars:
            All_Different.sibs_dict[v] = All_Different.sibs_dict.setdefault(v, set()) | (vars - {v})

    @staticmethod
    def all_satisfied():
        return all(All_Different.satisfied_for_var(v) for v in All_Different.sibs_dict)

    @staticmethod
    def propagate_value(var_1, value):
        for var_2 in All_Different.sibs_dict[var_1]:
            var_2.update_range(var_2.range - {value}, was_set=False)

    @staticmethod
    def satisfied_for_var(v: Var_FD):
        # Finally got to use the walrus operator.
        satisfied = (v_value := v.value()) is None or \
                    all(v_value != w.value() for w in All_Different.sibs_dict[v])
        return satisfied

    @staticmethod
    def to_string_sibs_dict():
        return f'{"{"}{", ".join([All_Different.to_string_sibs_entry(v) for v in All_Different.sibs_dict])}{"}"}'

    @staticmethod
    def to_string_sibs_entry(v):
        entry = f'{v.var_name}: ' + '{' + ", ".join(v.var_name for v in All_Different.sibs_dict[v]) + '}'
        return entry

    @staticmethod
    def undo_propagate_value(var):
        for v in All_Different.sibs_dict[var]:
            v.undo_update_range()


class Var_FD:
    """ A Finite Domain variable """
    
    id = 0

    def __init__(self, init_range=None, var_name=None):
        cls = type(self)
        cls.id += 1
        self.id = cls.id
        cls_first_letter = str(cls).split('.')[1][0]
        self.var_name = var_name if var_name else cls_first_letter + str(cls.id)

        self.range = set() if init_range is None else  \
                     {init_range} if type(init_range) in [int, str, float] else \
                     set(init_range)

        self.range_was_set_stack = []
        self.was_set = False
        
        self.unification_chain_next = None

    def __eq__(self, other: Var_FD):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        var_name_part = self.var_name + ('*' if self.was_set else '') + ':'
        return f'{var_name_part}{"{"}{", ".join([str(x) for x in sorted(self.range)])}{"}"}'

    def has_a_value(self):
        return len(self.range) == 1

    def member_FD(self, a_list: List[Union[Var_FD, int, str]]):
        """ Is v in a_list?  """
        # If a_list is empty, it can't have a member. So fail.
        if not a_list: return

        yield from self.narrow_range(a_list[0])
        yield from self.member_FD(a_list[1:])

    def narrow_range(self, other_var: Var_FD):
        common = self.range & other_var.range
        if len(common) == 0: return
        single_value = len(common) == 1
        self.update_range(common, single_value)
        if Solver_FD.propagate and single_value:
            new_value = list(common)[0]
            All_Different.propagate_value(self, new_value)
        yield
        self.undo_update_range()
        if Solver_FD.propagate and single_value:
            All_Different.undo_propagate_value(self)

    def undo_update_range(self):
        (self.range, self.was_set) = self.range_was_set_stack[-1]
        self.range_was_set_stack = self.range_was_set_stack[:-1]

    def update_range(self, new_range, was_set):
        self.range_was_set_stack = self.range_was_set_stack + [(self.range, self.was_set)]
        self.range = new_range
        self.was_set = self.was_set or was_set

    def value(self):
        return list(self.range)[0] if self.has_a_value() else None


class Const_FD(Var_FD):
    """ A class of objects whose ranges are constant. """

    id = 0

    def __init__(self, init_range, var_name=None):
        super().__init__(init_range, var_name)

    def narrow_range(self, other_var: Var_FD):
        if type(other_var) == Var_FD:
            yield from other_var.narrow_range(self)
        else: return


class Solver_FD:

    propagate = False
    smallest_first = False

    def __init__(self, vars, constraints=frozenset(), trace=False, narrow=None):
        self.constraints = constraints
        self.depth = 0
        self.line_no = 0
        self.narrow = Solver_FD.instantiate_a_var if narrow is None else narrow
        self.trace = trace
        self.vars = vars

    def constraints_satisfied(self):
        return all(constraint() for constraint in self.constraints)

    @staticmethod
    def instantiate_a_var(vars):
        not_set_vars: Set[Var_FD] = {v for v in vars if not v.was_set}
        nxt_var = min(not_set_vars, key=lambda v: len(v.range)) if Solver_FD.smallest_first else \
                  not_set_vars.pop()
        # Sort nxt_var.range so that it will be more intuitive to trace. Makes no functional difference.
        # for _ in Solver_FD.member_FD(nxt_var, [Const_FD(elt) for elt in sorted(nxt_var.range)]):
        for _ in nxt_var.member_FD([Const_FD(elt) for elt in sorted(nxt_var.range)]):
            yield

    @staticmethod
    def is_a_subsequence_of(As: List, Zs: List):
        """
        As may be spread out in Zs but must be in the same order as in Zs.
        """
        if not As:
            # If no more As to match, we're done. Succeed.
            yield

        elif not Zs:
            # If no more Zs to match the remaining As, fail.
            return

        else:
            for _ in As[0].narrow_range(Zs[0]):
                yield from Solver_FD.is_a_subsequence_of(As[1:], Zs[1:])

            yield from Solver_FD.is_a_subsequence_of(As, Zs[1:])

    @staticmethod
    def is_contiguous_in(As: List, Zs: List):
        """
        As must be together in Zs but can start anywhere in Zs.
        """
        # If not enough Zs to match the As, fail.
        if len(Zs) < len(As): return

        yield from Solver_FD.unify_pairs_FD(zip(As, Zs))
        yield from Solver_FD.is_contiguous_in(zip(As, Zs[1:]))

    # @staticmethod
    # def member_FD(var, a_list: List[Union[Var_FD, int, str]]):
    #     """ Is v in a_list?  """
    #     # If a_list is empty, it can't have a member. So fail.
    #     if not a_list: return
    #
    #     yield from var.narrow_range(a_list[0])
    #     yield from Solver_FD.member_FD(var, a_list[1:])

    # def member_FD(self, a_list: List[Union[Var_FD, int, str]]):
    #     """ Is v in a_list?  """
    #     # If a_list is empty, it can't have a member. So fail.
    #     if not a_list: return
    #
    #     yield from self.narrow_range(a_list[0])
    #     yield from self.member_FD(a_list[1:])
    #
    def show_vars(self):
        self.line_no += 1
        if self.trace:
            line_no_str = f'{" " if self.line_no < 10 else ""}{str(self.line_no)}'
            line_str = f'{line_no_str}{".  " * (self.depth + 1)}{Solver_FD.to_str(self.vars)}'
            print(line_str)

    def solve(self):
        # If any vars have an empty range, the solver has reached a dead end. Fail.
        if any(not v.range for v in self.vars): return

        # If any constraints are not satisfied, Fail.
        elif not self.constraints_satisfied(): return

        # If all variables are instanatiated, we have a solution. Yield.
        elif all(v.has_a_value() for v in self.vars): yield

        # Otherwise, show_vars and instantiate a variable.
        else:
            self.show_vars()
            self.depth += 1
            for _ in self.narrow(self.vars):
                yield from self.solve()
            self.depth -= 1

    @staticmethod
    def to_str(xs):
        if isinstance(xs, Iterable):
            xs_string = ", ".join(Solver_FD.to_str(x) for x in xs)
        else:
            xs_string = str(xs)
        return xs_string

    # @staticmethod
    # def unify_FD(v1: Var_FD, v2: Var_FD):
    #     # Call narrow_range on the argument that is an Var_FD.
    #     yield from v1.narrow_range(v2)   # if type(v1) == Var_FD else v2.narrow_range(v1)

    @staticmethod
    def unify_pairs_FD(tuples: List[Tuple[Var_FD, Var_FD]]):
      """ Apply unify to pairs of terms. """
      # If no more tuples, we are done.
      if not tuples:
        yield
      else:
        # Get the first tuple from the tuples list.
        [(Left, Right), *restOfTuples] = tuples
        # If they unify, go on to the rest of the tuples list.
        for _ in Left.narrow_range(Left, Right):
          yield from Solver_FD.unify_pairs_FD(restOfTuples)

