#!/usr/bin/env python3

import pyeda.boolalg.expr as expr

import synth
import synth.sat
from synth.util import assert_cnf

from synth.irredundant import QBFSynth

class QBFUnfolded(QBFSynth):
    @staticmethod
    def _select_solver(arguments):
        return arguments.sat_solver

    def _parse_solver(self, solver):
        if solver is None or solver == "libminisat":
            return synth.sat.Minisat
        elif solver == "libcryptominisat":
            return synth.sat.Cryptominisat
        return synth.sat.Dimacs.from_known(solver)

    @assert_cnf
    def _assert_lattice_on_path(self, assignment, path_var):
        for i in range(1, self.m + 1):
            for j in range(1, self.n + 1):
                elements = list(self._literal_at_position_is(i, j, inp)
                            for inp in self._input_literals()
                            if inp.compose(assignment).simplify().is_one())
                assert elements, "list of literal variables must not be empty"
                yield expr.Implies(path_var(i, j),
                                   expr.Or(*elements)).to_cnf()

    @assert_cnf
    def _assert_path_exists_if_function_true(self, path_var):
        elements = (path_var(self.m, j) for j in range(1, self.n + 1))
        yield expr.Or(*elements)

    @assert_cnf
    def _assert_lattice_on_negative_path(self, assignment, path_var):
        for i in range(1, self.m + 1):
            for j in range(1, self.n + 1):
                elements = list(self._literal_at_position_is(i, j, inp)
                            for inp in self._input_literals()
                            if inp.compose(assignment).simplify().is_zero())
                assert elements, "list of literal variables must not be empty"
                yield expr.Implies(path_var(i, j),
                                   expr.Or(*elements)).to_cnf()

    @assert_cnf
    def _assert_negative_path_exists_if_function_false(self, path_var):
        elements = (path_var(i, self.n) for i in range(1, self.m + 1))
        yield expr.Or(*elements)

    @assert_cnf
    def _all_assertions_per_assignment(self, assignment):
        # XXX hacky
        count = self._increment_counter()

        def path_var(i, j):
            assert 1 <= i <= self.m
            assert 1 <= j <= self.n
            return expr.exprvar("path", (i, j, count))

        evaluated = self.function.compose(assignment).simplify().is_one()
        if evaluated:
            yield from self._assert_lattice_on_path(assignment, path_var)
            yield from self._assert_some_path_connected(path_var)
            yield from self._assert_path_exists_if_function_true(path_var)
        else:
            yield from self._assert_lattice_on_negative_path(assignment, path_var)
            yield from self._assert_some_negative_path_connected(path_var)
            yield from self._assert_negative_path_exists_if_function_false(path_var)

    @assert_cnf
    def _all_assertions(self):
        yield from self._assert_variables_set()
        yield from self._assert_one_literal_used()

        for assignment in self.function.iter_domain():
            yield from self._all_assertions_per_assignment(assignment)

    def synth(self, timer=None):
        elements = list(self._all_literals_at_position())
        solver = self.solver()
        for clause in self._all_assertions():
            solver.add(clause)

        self.print_dimacs(solver, "irredundant")
        solution = solver.solve(of_interest=elements, no_decode=self.no_decode,
                                timer=timer, simplify=True)

        (num_clauses, num_variables) = solver.num_clauses_variables()
        return self._build_result(solution, num_clauses=num_clauses,
                                  num_variables=num_variables)
