from __future__ import annotations

from solver import All_Different, Solver_FD, Var_FD

"""
A puzzle from GeekOverdose: https://geekoverdose.wordpress.com/2015/10/31/solving-logic-puzzles-in-prolog-puzzle-1-of-3/
A relatively simple puzzle of this genre.
Prolog solution provided at that site.

                        ----------------------------------------------------------------

There are 4 students: Emmy, Lynn, Marie, and Ada. 
Each has one scholarship and one major subject.  
The available scholarships are: $25,000, $30,000, $35,000 and $40,000. 
The available majors are: CS, Bio, Math, and Phys. 

Using the following clues, determine which student has which scholarship and studies which subject.

1. The student who studies Phys gets a smaller scholarship than Emmy.
2. Emmy studies either Bio or Math.
3. The student who studies CS has a $5,000 bigger scholarship than Lynn.
4. Marie has a $10,000 bigger scholarship than Lynn.
5. Ada has a bigger scholarship than the student who studies Bio.

The (unique) solution.

Students: 
    Lynn(Bio, 25)
    Ada(CS, 30)
    Marie(Phys, 35)
    Emmy(Math, 40)

"""


class Stdnt(Var_FD):
    id = 0

    names = frozenset({'Ada', 'Emmy', 'Lynn', 'Marie'})
    majors = frozenset({'Bio', 'CS', 'Math', 'Phys'})

    def __init__(self, name=None, major=None):
        self.name = Var_FD(Stdnt.names if name is None else name)
        self.major = Var_FD(Stdnt.majors if major is None else major)
        self.scholarship = None

        super().__init__()

    def __str__(self):
        name_str = "-".join(self.name.range) + self.name.star_or_dash()
        major_str = "-".join(self.major.range) + self.major.star_or_dash()
        scholarship_str = '' if self.scholarship is None else f'(${self.scholarship},000)'
        return f'{name_str}/{major_str}{scholarship_str}'

    def is_instantiated(self):
        return self.name.is_instantiated() and self.major.is_instantiated()

    def narrow_range(self, new_value: Stdnt):
        """ Must do both name and major """
        for _ in self.name.narrow_range(new_value.name):
            yield from self.major.narrow_range(new_value.major)

    @staticmethod
    def stdnts_to_string(students):
        return ", ".join(str(std) for std in students)



class Const_Stdnt(Stdnt):

    def __init__(self, name=None, major=None):
        super().__init__(name, major)
        self.var_name = 'CS' + self.var_name[1:]

    def narrow_range(self, new_value: Stdnt):
        """ If we are a Const_Stdnt, and new_value is a Stdnt, turn the args around. """
        if type(new_value) == Stdnt:
            yield from new_value.narrow_range(self)
        else: return


class Clues_Solver(Solver_FD):

    def __init__(self, vars, students, clues, clue_index=0,
                 constraints=frozenset({All_Different.all_satisfied}), trace=False):
        super().__init__(vars, constraints=constraints, trace=trace)
        self.clue = None
        self.clues = clues
        self.clue_index = clue_index
        self.students = students

    def narrow(self):
        yield from self.run_a_clue()

    def problem_is_solved(self):
        problem_solved = self.clue_index >= len(self.clues)
        return problem_solved

    # def run_all_clues(self):
    #     if self.clue_index >= len(self.clues):
    #         # Ran all the clues. Succeed.
    #         yield
    #
    #     # The following is commented out because it's possible for all students
    #     # to be instantiated but fail a clue that hasn't been applied.
    #     # elif all(stdnt.is_instantiated() for stdnt in self.students):
    #     #     yield
    #     else:
    #         yield from self.run_a_clue()

    def run_a_clue(self):
        self.clue = self.clues[self.clue_index]
        # We know the current clue. Increment clue_index in anticipation of next call.
        self.clue_index += 1
        for _ in self.clue(self.students):
            if All_Different.all_satisfied():
                yield
        # Decrement clue_index back to where it was.
        self.clue_index -= 1

    def state_string(self, solved):
        self.clue = self.clues[self.clue_index-1]
        clue_name = 'at start' if self.clue_index == 0 else self.clue.__name__
        spacer = "* " if solved else ". "
        state_str = f'{" " if self.line_no < 10 else ""}{self.line_no}.' \
                    f'{" " * (10 - len(clue_name))}({clue_name}) '       \
                    f'{spacer * (self.clue_index + 1)}'                  \
                    f'{Stdnt.stdnts_to_string(self.students)}'
        return state_str


def clue_1(Stdnts):
    """ The student who studies Phys gets a smaller scholarship than Emmy. """
    yield from Solver_FD.is_a_subsequence_of(
        [Const_Stdnt(major='Phys'), Const_Stdnt(name='Emmy')], Stdnts)


def clue_2(Stdnts):
    """ Emmy studies either Math or Bio. """
    yield from Const_Stdnt(name='Emmy', major={'Bio', 'Math'}).member_FD(Stdnts)


# def clue_3(Stdnts):
#     """ The Stdnt who studies CS has a $5,000 larger scholarship than Lynn. """
#     yield from Solver_FD.is_contiguous_in(
#         [Const_Stdnt(name='Lynn'), Const_Stdnt(major='CS')], Stdnts)


def clues_3_4(Stdnts):
    """
    Combine clues 3 and 4 into a single clue.
    The Stdnt who studies CS has a $5,000 larger scholarship than Lynn.
    Marie has a $10,000 bigger scholarship than Lynn.
    """
    yield from Solver_FD.is_contiguous_in(
        [Const_Stdnt(name='Lynn'), Const_Stdnt(major='CS'), Const_Stdnt(name='Marie')], Stdnts)


def clue_5(Stdnts):
    """ Ada has a larger scholarship than the Stdnt who studies Bio. """
    yield from Solver_FD.is_a_subsequence_of(
        [Const_Stdnt(major='Bio'), Const_Stdnt(name='Ada')], Stdnts)


def clue_d(Stdnts):
    """ A derived clue.  From the other clues can exclude some values at the start and end."""
    yield from Solver_FD.is_a_subsequence_of(
        [Const_Stdnt(name=Stdnt.names-{'Ada', 'Marie', 'Emmy'}, major=Stdnt.majors-{'CS'}),
         Const_Stdnt(), Const_Stdnt(),
         Const_Stdnt(name=Stdnt.names-{'Lynn'}, major=Stdnt.majors-{'Bio', 'CS', 'Phys'})], Stdnts)


if __name__ == '__main__':
    students = [Stdnt(name=Stdnt.names, major=Stdnt.majors) for _ in range(4)]

    name_vars = {std.name for std in students}
    major_vars = {std.major for std in students}
    Solver_FD.propagate = True

    All_Different.sibs_dict = {}
    All_Different(name_vars)
    All_Different(major_vars)

    # Do the derived clue first since it sets 3 things and has no alternatives.
    # Do clue_3_4 next since it sets 3 things and after the derived clue has no alternatives.
    # Then clue_2 since it now has no alternatives.
    # Clue_5 finishes the job, again with no alternatives.
    # Can drop clue_1 since it is satisfied after clue 2.
    clues = [clue_d, clues_3_4, clue_2, clue_5]  #, clue_1]

    print('\nStudents:', ', '.join(sorted(Stdnt.names)))
    print('Majors:', ', '.join(sorted(Stdnt.majors)))
    print(""" The original clues
    1. The student who studies Phys gets a smaller scholarship than Emmy.
    2. Emmy studies either Bio or Math.
    3. The student who studies CS has a $5,000 bigger scholarship than Lynn.
    4. Marie has a $10,000 bigger scholarship than Lynn.
    5. Ada has a bigger scholarship than the student who studies Bio.
    
    Clues 3 and 4 can be run together as a single clue called 'clues_3_4'.
    
    Can generate a derived clue, called 'clue_d', that eliminates possible
    values from the two ends of the list. For example, from clue 5, one can
    conclude that Ada is not the first person in the list and Bio is not
    the major of the last.
    
    The best ordering for the clues is as follows:
    1. Do the derived clue first since it sets 3 things and has no alternatives.
    2. Do clue_3_4 next since it sets 3 things and after the derived clue has no alternatives.
    3. Then clue_2 since it now has no alternatives.
    4. Clue_5 finishes the job, again with no alternatives.
    Can drop clue_1 since it is satisfied after clue 2.
""")

    print('*: Var was directly instantiated--and propagated if propagation is on.\n'
          '-: Var was indirectly instantiated but not propagated.\n')

    clues_solver = Clues_Solver(name_vars | major_vars, students, clues, trace=True)
    for _ in clues_solver.solve():
        for (i, std) in enumerate(students):
            std.scholarship = 25 + 5*i
        print(f'\nSolution: {Stdnt.stdnts_to_string(students)}\n')
        for (i, std) in enumerate(students):
            std.scholarship = None
    print('\nNo other solutions')
