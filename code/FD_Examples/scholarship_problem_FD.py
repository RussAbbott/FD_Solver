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
        name_str = "-".join(self.name.range) + ('*' if self.name.was_set else '')
        major_str = "-".join(self.major.range) + ('*' if self.major.was_set else '')
        scholarship_str = '' if self.scholarship is None else f'(${self.scholarship},000)'
        return f'{name_str}/{major_str}{scholarship_str}'

    def is_instantiated(self):
        return self.name.has_a_value() and self.major.has_a_value()

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
    # students = None

    def __init__(self, students, clues, clue_number=0):
        super().__init__(students)
        self.clues = clues
        self.clue_number = clue_number
        self.students = self.vars

    def run_all_clues(self):
        if self.clue_number >= len(self.clues):
            # Ran all the clues. Succeed.
            yield
        # This is commented out because it's possible for all the students
        # to be instantiated but fail a clue that hasn't been applied.
        # elif all(stdnt.is_instantiated() for stdnt in self.students):
        #     yield
        else:
            clue = self.clues[self.clue_number]
            for _ in clue(self.students):
                if All_Different.all_satisfied():
                    self.line_no += 1
                    print(f'{" " if self.line_no < 10 else ""}{self.line_no}. '
                          f'({clue.__name__}) {Stdnt.stdnts_to_string(self.students)}')
                    self.clue_number += 1
                    yield from self.run_all_clues()
                    self.clue_number -= 1


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


def clue_3(Stdnts):
    """
    Combine clues 3 and 4 into a single clue.
    The Stdnt who studies CS has a $5,000 larger scholarship than Lynn.
    Marie has a $10,000 bigger scholarship than Lynn.
    """
    yield from Solver_FD.is_contiguous_in(
        [Const_Stdnt(name='Lynn'), Const_Stdnt(major='CS'), Const_Stdnt(name='Marie')], Stdnts)


def clue_4(Stdnts):
    """ Ada has a larger scholarship than the Stdnt who studies Bio. """
    yield from Solver_FD.is_a_subsequence_of(
        [Const_Stdnt(major='Bio'), Const_Stdnt(name='Ada')], Stdnts)


if __name__ == '__main__':
    students = [Stdnt(name=Stdnt.names, major=Stdnt.majors) for _ in range(4)]

    name_vars = {std.name for std in students}
    major_vars = {std.major for std in students}
    Solver_FD.propagate = True

    All_Different.sibs_dict = {}
    All_Different(name_vars)
    All_Different(major_vars)

    # Do clue_3 first since it sets 3 things.
    # clues 1 and 4 set two things each. Their order doesn't matter.
    # If clue_1 is not included, can get all instantiated but in violation of clue_1.
    clues = [clue_3, clue_4, clue_2, clue_1]

    print()
    print('Students:', ', '.join(sorted(Stdnt.names)))
    print('Majors:', ', '.join(sorted(Stdnt.majors)), '\n')

    clues_solver = Clues_Solver(students, clues)
    for _ in clues_solver.run_all_clues():
        for (i, std) in enumerate(students):
            std.scholarship = 25 + 5*i
        print(f'\nSolution: {Stdnt.stdnts_to_string(students)}\n')
        for (i, std) in enumerate(students):
            std.scholarship = None
    print('\nNo other solutions')
