from __future__ import annotations

from solver import All_Different, Solver_FD, Var_FD

from typing import List, Union

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

    =================================================================================================================
      This and the zebra problem are both written so that they can use either LinkedLists or one of the
      PySequence options: PyList or PyTuple. Make a choice at the bottom of the file.
    =================================================================================================================
"""


def run_all_clues(students, clues, clue_number=0):
    if clue_number >= len(clues):
        # Ran all the clues. Succeed.
        yield
    else:
        clue = clues[clue_number]
        for _ in clue(students):
            if All_Different.all_satisfied():
                yield from run_all_clues(students, clues, clue_number + 1)

def clue_1(Stdnts):
    """ The student who studies Phys gets a smaller scholarship than Emmy. """
    yield from Solver_FD.is_a_subsequence_of(
        [Const_Stdnt(major='Phys'), Const_Stdnt(name='Emmy')], Stdnts)

def clue_2(Stdnts):
    """ Emmy studies either Math or Bio. """
    yield from Solver_FD.member_FD(Stdnt(name='Emmy', major=Var_FD({'Bio', 'Math'})), Stdnts)

def clue_3(Stdnts):
    """ The Stdnt who studies CS has a $5,000 larger scholarship than Lynn. """
    yield from Solver_FD.is_contiguous_in(
        [Stdnt(name='Lynn'), Stdnt(major='CS')], Stdnts)

def clue_4(Stdnts):
    """ Marie has a $10,000 larger scholarship than Lynn. """
    yield from Solver_FD.is_contiguous_in(
        [Stdnt(name='Lynn'), Stdnt(), Stdnt(name='Marie')], Stdnts)

def clue_5(Stdnts):
    """ Ada has a larger scholarship than the Stdnt who studies Bio. """
    yield from Solver_FD.is_a_subsequence_of(
        [Stdnt(major='Bio'), Stdnt(name='Ada')], Stdnts)


class Stdnt(Var_FD):
    id = 0

    names = frozenset({'Ada', 'Emmy', 'Lynn', 'Marie'})
    majors = frozenset({'Bio', 'CS', 'Math', 'Phys'})

    def __init__(self, name=None, major=None, scholarship=None):
        self.name = Var_FD(Stdnt.names if name is None else name)
        self.major = Var_FD(Stdnt.majors if major is None else major)

        super().__init__()

    def __str__(self):
        return f'{self.var_name}<{self.name}/{self.major}>'

    def narrow_range(self, new_value: Stdnt):
        """ Must do both values """
        ...

    @staticmethod
    def unify_FD(v1: Stdnt, v2: Stdnt):
        yield from v1.narrow_range(v2) if isinstance(v1, Stdnt) and not isinstance(v1, Const_Stdnt) else v2.narrow_range(v1)


class Const_Stdnt(Var_FD):

    def __init__(self, name=None, major=None):
        super().__init__(name, major)
        self.var_name = 'CS' + self.var_name[1:]
        print(self)


if __name__ == '__main__':
    students = [Stdnt(name=Stdnt.names, major=Stdnt.majors) for _ in range(4)]

    print('\n'.join([str(std) for std in students]))

    name_vars = {std.name for std in students}
    major_vars = {std.major for std in students}

    All_Different.sibs_dict = {}
    All_Different(name_vars)
    All_Different(major_vars)

    clues = [clue_1, clue_2, clue_3, clue_4, clue_5]

    for _ in run_all_clues(students, clues, 0):
        print(students)
