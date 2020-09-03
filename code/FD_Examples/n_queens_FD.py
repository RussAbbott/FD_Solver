from math import log10

from solver import All_Different, Solver_FD, Var_FD

from typing import Set


class Queen_FD(Var_FD):

    vars = None

    def __init__(self, init_range=None, board_size=8):
        init_range = {c+1 for c in range(board_size)} if init_range is None else init_range
        super().__init__(init_range=init_range)
        self.board_size = board_size
        self.diagonals_stack = []

    @property
    def col(self):
        return self.id

    def narrow_range(self, other_var: Var_FD):
        """
        Same as for Var_FD except that diagonals are propagated as well.
        """
        common = self.range & other_var.range
        if len(common) == 0: return
        is_single_value = len(common) == 1 and not self.was_set
        self.update_range(common, is_single_value)
        if Solver_FD.propagate and is_single_value:
            new_row = list(common)[0]
            self.propagate_all(new_row)
        yield
        self.undo_update_range()
        if Solver_FD.propagate and is_single_value:
            self.undo_propagate_all()

    def propagate_all(self, new_row):
        for v in Queen_FD.vars - {self}:
            v.diagonals_stack += [v.range]
            diff = abs(self.col - v.col)
            v.range -= {new_row, new_row + diff, new_row - diff}

    @property
    def row(self):
        return self.value()

    def undo_propagate_all(self, ):
        for v in Queen_FD.vars - {self}:
            v.range = v.diagonals_stack[-1]
            v.diagonals_stack = v.diagonals_stack[:-1]


class Queens_Solver_FD(Solver_FD):

    def problem_is_solved(self):
        """ The solution condition for transversals. (But not necessarily all problems.) """
        problem_solved = all(v.was_set for v in self.vars)
        return problem_solved


# ############  Display functions  ############ #

def layout(queens: Set[Queen_FD], board_size: int) -> str:
    """ Format the queens for display. """
    queens_sorted_by_row = sorted(queens, key=lambda q: q.row)
    # The values of the queens for each row.
    queen_values_by_row = [(q.row, q.col) for q in queens_sorted_by_row]
    offset = ord('a')
    # Generate the column headers.
    col_hdrs = ' '*(4+int(log10(board_size))) + \
               '  '.join([f'{chr(n+offset)}' for n in range(board_size)]) + '  col#\n'
    display = col_hdrs + '\n'.join([one_row(r, c, board_size) for (r, c) in queen_values_by_row])
    return display


def one_row(row: int, col: int, board_size: int) -> str:
    """ Generate one row of the board. """
    # (row, col) is the queen position expressed for this row.
    return f'{space_offset(row, board_size)}{row}. ' + \
           f'{" . "*(col-1)} Q {" . "*(board_size - col)} {space_offset(col, board_size)}({col})'


def space_offset(n, board_size):
    return " "*( int(log10(board_size)) - int(log10(n)) )


# ############  End display functions  ############ #


def set_up(board_size, trace=False):
    """ Set up the solver and All_Different for the transversals problem. """
    Solver_FD.set_up()
    Solver_FD.propagate = True
    Solver_FD.smallest_first = True

    # Create a Queen_FD for each column. Each has an initial range of {c+1 for c in range(board_size)}.
    vars = {Queen_FD(board_size=board_size) for _ in range(board_size)}
    All_Different(vars)

    # Keep a record of the vars in Queen_FD so that we can propagate diagonals.
    Queen_FD.vars = vars

    solver_fd = Queens_Solver_FD(vars, set())
    solver_fd.trace = trace
    return solver_fd


if __name__ == "__main__":
    board_size = 6
    solver_fd = set_up(board_size=board_size, trace=board_size == 6)
    sols = 0
    board_string = None
    current_sol = None
    print()
    for _ in solver_fd.solve():
        sols += 1
        # Keep a copy of the vars for the current solution.
        # Must copy the vars since they are modified as the search continues.
        current_sol = {v.copy() for v in solver_fd.vars}
        if board_size < 11:
            board_string = layout(current_sol, board_size=board_size)
            print(f'{sols}.')
            print(board_string, '\n')
        elif sols % 1000 == 1:
            print(sols)
    print('Solutions:', sols)
    # Print the final solution if 11 <= board_size <= 26.
    if 11 <= board_size <= 26:
        board_string = layout(current_sol, board_size=board_size)
        print(f'\nSolution {sols}:\n{board_string}')
