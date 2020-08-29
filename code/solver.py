from __future__ import annotations

from typing import List, Set, Union


class All_Different:
    """ Each All_Different object is a collection of FD_Vars that must be different. """

    # sibs_dict is a dictionary. Each key is an FD_Var's; the value is a set of FD_Var's that must differ from it.
    # sibs_dict = {FD_Var_x: {FD_Var_i that must be different from FD_Var_x}}
    # sibs_dict  is aggregated from the All_Different declarations.
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
            var_2.update_range(var_2.range - {value})

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
        entry = f'{v.name}: ' + '{' + ", ".join(v.name for v in All_Different.sibs_dict[v]) + '}'
        return entry

    @staticmethod
    def undo_propagate_value(var):
        for v in All_Different.sibs_dict[var]:
            v.undo_update_range()


class Var_FD:
    """ A Finite Domain variable """
    id = 0

    propagate = False
    smallest_first = False

    def __init__(self, init_range=None, name=None):
        cls = self.__class__
        cls.id += 1
        self.id = cls.id
        cls_first_letter = str(cls).split('.')[1][0]
        self.name = name if name else cls_first_letter + str(cls.id)

        self.range = set() if init_range is None else  \
                     {init_range} if type(init_range) in [int, str, float] else \
                     init_range

        self.range_was_set_stack = []
        self.was_set = False
        self.unification_chain_next = None

    def __eq__(self, other: Var_FD):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        name_part = self.name + ('*' if self.was_set else '') + ':'
        return f'{name_part}{"{"}{", ".join([str(x) for x in sorted(self.range)])}{"}"}'

    def is_instantiated(self):
        return len(self.range) == 1

    def set_value(self, other_var: Var_FD):
        common = self.range & other_var.range
        if len(common) != 1: return
        self.update_range(common, True)
        if Var_FD.propagate:
            new_value = list(common)[0]
            All_Different.propagate_value(self, new_value)
        yield
        self.undo_update_range()
        if Var_FD.propagate:
            All_Different.undo_propagate_value(self)

    def undo_update_range(self):
        (self.range, self.was_set) = self.range_was_set_stack[-1]
        self.range_was_set_stack = self.range_was_set_stack[:-1]

    def update_range(self, new_range, was_set=False):
        self.range_was_set_stack = self.range_was_set_stack + [(self.range, self.was_set)]
        self.range = new_range
        self.was_set = self.was_set or was_set

    def value(self):
        return list(self.range)[0] if self.is_instantiated() else None


class Const_FD(Var_FD):
    """ A class of objects whose ranges are constant. """

    id = 0

    def __init__(self, init_range, name=None):
        super().__init__(init_range, name)


class Solver_FD:

    def __init__(self, vars, narrow=None, constraints=None, trace=False):
        self.constraints = set() if constraints is None else constraints
        self.depth = self.line_no = 0
        self.narrow = Solver_FD.pick_one if narrow is None else narrow
        self.trace = trace
        self.vars = vars

    def constraints_satisfied(self):
        return all(constraint() for constraint in self.constraints)

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
            for _ in Solver_FD.unify_FD(As[0], Zs[0]):
                for _ in Solver_FD.is_a_subsequence_of(As[1:], Zs[1:]):
                    yield

    @staticmethod
    def member_FD(var, a_list: List[Union[Var_FD, int, str]]):
        """ Is v in a_list?  """
        # If a_list is empty, it can't have a member. So fail.
        if not a_list: return

        yield from Solver_FD.unify_FD(var, a_list[0])
        yield from Solver_FD.member_FD(var, a_list[1:])

    @staticmethod
    def pick_one(vars):
        not_set_vars: Set[Var_FD] = {v for v in vars if not v.was_set}
        nxt_var = min(not_set_vars, key=lambda v: len(v.range)) if Var_FD.smallest_first else \
            not_set_vars.pop()
        for _ in Solver_FD.member_FD(nxt_var, [Const_FD(elt) for elt in nxt_var.range]):
            yield

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
        elif all(v.is_instantiated() for v in self.vars): yield

        # Otherwise, show_vars and instantiate a variable.
        else:
            self.show_vars()
            self.depth += 1
            for _ in self.narrow(self.vars):
                yield from self.solve()
            self.depth -= 1

    @staticmethod
    def to_str(xs):
        if type(xs) in [frozenset, list, set, tuple]:
            xs_string = ", ".join(Solver_FD.to_str(x) for x in xs)
        else:
            xs_string = str(xs)
        return xs_string

    @staticmethod
    def unify_FD(v1: Var_FD, v2: Var_FD):
        # Call set_value on the argument that is an Var_FD.
        yield from v1.set_value(v2) if type(v1) == Var_FD else v2.set_value(v1)
