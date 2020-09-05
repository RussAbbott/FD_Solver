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
            var_2.update_domain(var_2.domain - {value}, was_propagated=False)

    @staticmethod
    def satisfied_for_var(v: Var_FD):
        # Finally got to use the walrus operator.
        satisfied = (v_value := v.value) is None or \
                    all(v_value != w.value for w in All_Different.sibs_dict[v])
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
            v.undo_update_domain()


class Var_FD:
    """ A Finite Domain variable """
    
    id = 0
    solver = None

    def __init__(self, init_domain=None, var_name=None):
        cls = type(self)
        cls.id += 1
        self.id = cls.id
        cls_first_letter = str(cls).split('.')[1][0]
        self.var_name = var_name if var_name else cls_first_letter + str(cls.id)

        # init_domain may be None, a single value, or an iterable collection of values
        # Make self.domain a frozenset--and keep it frozen.
        self.domain = None if init_domain is None else  \
                     frozenset({init_domain}) if type(init_domain) in [int, str, float] else \
                     frozenset(init_domain)

        # self.domain_was_propagated_stack stores previous values of range and was_propagated
        # when a new value is assigned. Used for backtracking.
        self.domain_was_propagated_stack = []

        # Set to True when this Var_FD is assigned a single value--and hence that value
        # is propagated through the other Var_FD's that must be distict from this one.
        self.was_propagated = False

        # So far not used. Haven't needed unification yet.
        self.unification_chain_next = None

    def __eq__(self, other: Var_FD):
        return self.id == other.id and type(self) == type(other)

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        var_name_part = self.var_name + self.star_or_dash() + ':'
        return f'{var_name_part}{"{"}{", ".join([str(x) for x in sorted(self.domain)])}{"}"}'

    def copy(self):
        cls = type(self)
        cpy = cls(self.domain)
        cpy.id = self.id
        return cpy

    def is_at_deadend(self):
        return not self.domain

    def is_instantiated(self):
        return len(self.domain) == 1

    def member_FD(self, a_list: List[Union[Var_FD, int, str]]):
        """ Is self in a_list?  """
        # If a_list is empty, it can't have a member. So fail.
        if not a_list: return

        yield from self.narrow_domain(a_list[0])
        yield from self.member_FD(a_list[1:])

    def narrow_domain(self, other_var: Var_FD):
        """
        Should be called with the Var_FD as the subject. other_var may be a Const_Var.
        Limit the self.domain by other_var.domain.
        """
        common = self.domain & other_var.domain
        if len(common) == 0: return
        should_propagate = len(common) == 1 and not self.was_propagated
        self.update_domain(common, should_propagate)
        if Var_FD.solver.propagate and should_propagate:
            new_value = list(common)[0]
            All_Different.propagate_value(self, new_value)
        yield
        self.undo_update_domain()
        if Var_FD.solver.propagate and should_propagate:
            All_Different.undo_propagate_value(self)

    def set_init_domain(self, new_domain, was_propagated=False):
        self.update_domain(new_domain, was_propagated=was_propagated, track_in_stack=False)

    def star_or_dash(self):
        return ('*' if self.was_propagated else '-' if self.is_instantiated() else '')

    def undo_update_domain(self):
        (self.domain, self.was_propagated) = self.domain_was_propagated_stack[-1]
        self.domain_was_propagated_stack = self.domain_was_propagated_stack[:-1]

    def update_domain(self, new_domain, was_propagated=False, track_in_stack=True):
        if track_in_stack:
            self.domain_was_propagated_stack = self.domain_was_propagated_stack + [(self.domain, self.was_propagated)]
        self.domain = new_domain
        self.was_propagated = self.was_propagated or was_propagated

    @property
    def value(self):
        return list(self.domain)[0] if self.is_instantiated() else None


class Const_FD(Var_FD):
    """ A class of objects whose ranges are constant. """

    id = 0

    def __init__(self, init_domain, var_name=None):
        super().__init__(init_domain, var_name)

    def narrow_domain(self, other_var: Var_FD):
        """
        Should be called with the Var_FD as the subject. other_var may be a Const_Var.
        If the args are reversed, call again with the args in the right order.
        """
        if type(other_var) == Var_FD:
            yield from other_var.narrow_domain(self)
        else: return


class Solver_FD:

    def __init__(self, vars, constraints=frozenset({All_Different.all_satisfied}),
                 propagate=True, smallest_first=True, trace=False):
        self.constraints = constraints
        self.depth = 0
        self.line_no = 0
        self.propagate = propagate
        self.smallest_first = smallest_first
        self.trace = trace
        self.vars = vars

        Var_FD.solver = self

    def constraints_satisfied(self):
        return all(constraint() for constraint in self.constraints)

    # def instantiate_a_var(self):
    #     not_set_vars: Set[Var_FD] = {v for v in self.vars if not v.was_propagated}
    #     nxt_var = min(not_set_vars, key=lambda v: len(v.domain)) if Solver_FD.smallest_first else \
    #               not_set_vars.pop()
    #     # Sort nxt_var.domain so that it will be more intuitive to trace. Makes no functional difference.
    #     for _ in nxt_var.member_FD([Const_FD(elt) for elt in sorted(nxt_var.domain)]):
    #         yield
    #
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
            for _ in As[0].narrow_domain(Zs[0]):
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
        # The default is to instantiate a var
        nxt_var = self.select_var_to_instantiate()
        # Sort nxt_var.domain so that it will be more intuitive to trace. Makes no functional difference.
        for _ in nxt_var.member_FD([Const_FD(elt) for elt in sorted(nxt_var.domain)]):
            yield

    def problem_is_solved(self):
        """ The solution condition for transversals. (But not necessarily all problems.) """
        problem_solved = all(v.is_instantiated() for v in self.vars)
        return problem_solved

    def select_var_to_instantiate(self):
        not_set_vars: Set[Var_FD] = {v for v in self.vars if not v.was_propagated}
        nxt_var = min(not_set_vars, key=lambda v: len(v.domain)) if self.smallest_first else \
                  not_set_vars.pop()
        return nxt_var

    @staticmethod
    def set_up():
        Var_FD.id = 0
        All_Different.sibs_dict = {}

    def show_state(self, solved=False):
        self.line_no += 1
        if self.trace:
            line_str = self.state_string(solved)
            print(line_str)

    def solve(self):
        """ self is the Solver object. It holds the vars. """
        # If any vars have an empty range, the solver has reached a dead end. Fail.
        # if any(not v.domain for v in self.vars): return
        if any(v.is_at_deadend() for v in self.vars): return

        # If any constraints are not satisfied, Fail.
        elif not self.constraints_satisfied(): return

        # # Check to see if we have a solution. If so, Yield.
        elif self.problem_is_solved():
            self.show_state(solved=True)
            yield

        # Otherwise, show_vars and narrow the range of some variable.
        # The default method is to instantiate a var.
        else:
            self.show_state()
            self.depth += 1
            for _ in self.narrow():
                yield from self.solve()
            self.depth -= 1

    def state_string(self, solved):
        line_no_str = f'{" " if self.line_no < 10 else ""}{str(self.line_no)}'
        spacer = "* " if solved else ". "
        state_str = f'{line_no_str}. {spacer * (self.depth)}{Solver_FD.to_str(self.vars)}'
        return state_str

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
        for _ in Left.narrow_domain(Right):
          yield from Solver_FD.unify_pairs_FD(restOfTuples)


if __name__ == "__main__":
    solver_fd = Solver_FD(set(), set())
    solver_fd.solve()
