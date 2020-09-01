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

        # init_range may be None, a single value, or an iterable collection of values
        self.range = None if init_range is None else  \
                     {init_range} if type(init_range) in [int, str, float] else \
                     set(init_range)

        # self.range_was_set_stack stores previous values of range and was_set
        # when a new value is assigned. Used for backtracking.
        self.range_was_set_stack = []

        # Set to True when this Var_FD is assigned a single value--and hence that value
        # is propagated through the other Var_FD's that must be distict from this one.
        self.was_set = False

        # So far not used. Haven't needed unification yet.
        self.unification_chain_next = None

    def __eq__(self, other: Var_FD):
        return self.id == other.id and type(self) == type(other)

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        var_name_part = self.var_name + self.star_or_dash() + ':'
        return f'{var_name_part}{"{"}{", ".join([str(x) for x in sorted(self.range)])}{"}"}'

    def is_at_deadend(self):
        return not self.range

    def is_instantiated(self):
        return len(self.range) == 1

    def member_FD(self, a_list: List[Union[Var_FD, int, str]]):
        """ Is self in a_list?  """
        # If a_list is empty, it can't have a member. So fail.
        if not a_list: return

        yield from self.narrow_range(a_list[0])
        yield from self.member_FD(a_list[1:])

    def narrow_range(self, other_var: Var_FD):
        """
        Should be called with the Var_FD as the subject. other_var may be a Const_Var.
        Limit the self.range by other_var.range.
        """
        common = self.range & other_var.range
        if len(common) == 0: return
        single_value = len(common) == 1 and not self.was_set
        self.update_range(common, single_value)
        if Solver_FD.propagate and single_value:
            new_value = list(common)[0]
            All_Different.propagate_value(self, new_value)
        yield
        self.undo_update_range()
        if Solver_FD.propagate and single_value:
            All_Different.undo_propagate_value(self)

    def star_or_dash(self):
        return ('*' if self.was_set else '-' if self.is_instantiated() else '')

    def undo_update_range(self):
        (self.range, self.was_set) = self.range_was_set_stack[-1]
        self.range_was_set_stack = self.range_was_set_stack[:-1]

    def update_range(self, new_range, was_set):
        self.range_was_set_stack = self.range_was_set_stack + [(self.range, self.was_set)]
        self.range = new_range
        self.was_set = self.was_set or was_set

    def value(self):
        return list(self.range)[0] if self.is_instantiated() else None


class Const_FD(Var_FD):
    """ A class of objects whose ranges are constant. """

    id = 0

    def __init__(self, init_range, var_name=None):
        super().__init__(init_range, var_name)

    def narrow_range(self, other_var: Var_FD):
        """
        Should be called with the Var_FD as the subject. other_var may be a Const_Var.
        If the args are reversed, call again with the args in the right order.
        """
        if type(other_var) == Var_FD:
            yield from other_var.narrow_range(self)
        else: return


class Solver_FD:

    propagate = False
    smallest_first = False

    def __init__(self, vars, constraints=frozenset({All_Different.all_satisfied}), trace=False, narrow=None):
        self.constraints = constraints
        self.depth = 0
        self.line_no = 0
        self.trace = trace
        self.vars = vars

    def constraints_satisfied(self):
        return all(constraint() for constraint in self.constraints)

    def instantiate_a_var(self):
        not_set_vars: Set[Var_FD] = {v for v in self.vars if not v.was_set}
        nxt_var = min(not_set_vars, key=lambda v: len(v.range)) if Solver_FD.smallest_first else \
                  not_set_vars.pop()
        # Sort nxt_var.range so that it will be more intuitive to trace. Makes no functional difference.
        for _ in nxt_var.member_FD([Const_FD(elt) for elt in sorted(nxt_var.range)]):
            yield

    @staticmethod
    def is_a_subsequence_of(As: List, Zs: List):
        """
        As may be spread out in Zs but must be in the same order as in As.
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
        yield from Solver_FD.is_contiguous_in(As, Zs[1:])

    def narrow(self):
        yield from self.instantiate_a_var()

    def problem_is_solved(self):
        """ The solution condition for transversals. (But not necessarily all problems.) """
        return all(v.is_instantiated() for v in self.vars)

    def show_state(self):
        self.line_no += 1
        if self.trace:
            line_str = self.state_string()
            print(line_str)

    def state_string(self):
        line_no_str = f'{" " if self.line_no < 10 else ""}{str(self.line_no)}'
        state_str = f'{line_no_str}{".  " * (self.depth + 1)}{Solver_FD.to_str(self.vars)}'
        return state_str

    def solve(self):
        """ self is the Solver object. It holds the vars. """
        # If any vars have an empty range, the solver has reached a dead end. Fail.
        # if any(not v.range for v in self.vars): return
        if any(v.is_at_deadend() for v in self.vars): return

        # If any constraints are not satisfied, Fail.
        elif not self.constraints_satisfied(): return

        # # Check to see if we have a solution. If so, Yield.
        elif self.problem_is_solved(): yield

        # Otherwise, show_vars and narrow the range of some variable.
        # self.narrow is a variable. A method is assigned to it.
        # The default method is instantiate_a_var
        else:
            self.show_state()
            self.depth += 1
            for _ in self.narrow():
                yield from self.solve()
            self.depth -= 1

    @staticmethod
    def to_str(xs):
        if isinstance(xs, Iterable):
            xs_string = ", ".join(Solver_FD.to_str(x) for x in xs)
        else:
            xs_string = str(xs)
        return xs_string

    @staticmethod
    def unify_pairs_FD(tuples: List[Tuple[Var_FD, Var_FD]]):
      """ Apply unify to pairs of terms. """
      # If no more tuples, we are done.
      if not tuples: yield
      else:
        # Get the first tuple from the tuples list.
        [(Left, Right), *restOfTuples] = tuples
        # If they unify, go on to the rest of the tuples list.
        for _ in Left.narrow_range(Right):
          yield from Solver_FD.unify_pairs_FD(restOfTuples)

