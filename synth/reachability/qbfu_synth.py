#!/usr/bin/env python3

import pyeda.boolalg.expr as expr

import synth
import synth.sat
from synth.util import assert_cnf

from synth.reachability import QBFSynth

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
    def _assert_switch_active(self, assignment, switch_var):
        for i in range(1, self.m + 1):
            for j in range(1, self.n + 1):
                elements = list(self._literal_at_position_is(i, j, inp)
                            for inp in self._input_literals()
                            if inp.compose(assignment).simplify().is_one())
                assert elements, "list of literal variables must not be empty"
                yield expr.Implies(switch_var(i, j),
                                   expr.Or(*elements)).to_cnf()

    @assert_cnf
    def _assert_path_exists_if_function_true(self, switch_var, position_var):
        elements = (switch_var(self.m, j) & \
                    position_var(self.m, j, self._upper_path_bound())
                    for j in range(1, self.n + 1))
        yield expr.Or(*elements).to_cnf()

    @assert_cnf
    def _assert_switch_inactive(self, assignment, switch_var):
        for i in range(1, self.m + 1):
            for j in range(1, self.n + 1):
                elements = list(self._literal_at_position_is(i, j, inp)
                            for inp in self._input_literals()
                            if inp.compose(assignment).simplify().is_zero())
                assert elements, "list of literal variables must not be empty"
                yield expr.Implies(switch_var(i, j),
                                   expr.Or(*elements)).to_cnf()

    @assert_cnf
    def _assert_negative_path_exists_if_function_false(self, switch_var,
                                                       position_var):
        elements = (switch_var(i, self.n) & \
                    position_var(i, self.n, self._upper_path_bound())
                    for i in range(1, self.m + 1))
        yield expr.Or(*elements).to_cnf()

    @assert_cnf
    def _all_assertions_per_assignment(self, assignment):
        # XXX hacky
        count = self._increment_counter()

        def position_var(i, j, rnd):
            assert 1 <= i <= self.m
            assert 1 <= j <= self.n
            return expr.exprvar("reachable", (i, j, rnd, count))

        def switch_var(i, j):
            assert 1 <= i <= self.m
            assert 1 <= j <= self.n
            return expr.exprvar("switch", (i, j, count))

        evaluated = self.function.compose(assignment).simplify().is_one()
        if evaluated:
            yield from self._assert_switch_active(assignment, switch_var)
            yield from self._assert_positive_path(switch_var, position_var)
            yield from self._assert_path_exists_if_function_true(switch_var,
                                                                 position_var)
        else:
            yield from self._assert_switch_inactive(assignment, switch_var)
            yield from self._assert_negative_path(switch_var, position_var)
            yield from self._assert_negative_path_exists_if_function_false(switch_var, position_var)

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

        self.print_dimacs(solver, "reachability")
        solution = solver.solve(of_interest=elements, no_decode=self.no_decode,
                                timer=timer, simplify=True)

        (num_clauses, num_variables) = solver.num_clauses_variables()
        return self._build_result(solution, num_clauses=num_clauses,
                                  num_variables=num_variables)
