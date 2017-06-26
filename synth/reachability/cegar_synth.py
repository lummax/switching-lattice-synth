#!/usr/bin/env python3

import pyeda.boolalg.expr as expr

import synth
from synth.util import assert_cnf
from synth.reachability import QBFUnfolded

class CegarSynth(QBFUnfolded):
    @assert_cnf
    def _assert_negative_path_exists_if_function_true(self):
        elements = (self._inactive_switch(i, self.n) & \
                    self._position_unreachable(i, self.n, self._upper_path_bound())
                    for i in range(1, self.m + 1))
        yield expr.Implies(self.function, expr.Or(*elements)).to_cnf()

    @assert_cnf
    def _assert_path_exists_if_function_false(self):
        elements = (self._active_switch(self.m, j) & \
                    self._position_reachable(self.m, j, self._upper_path_bound())
                    for j in range(1, self.n + 1))
        yield expr.Implies(~self.function, expr.Or(*elements)).to_cnf()

    @assert_cnf
    def _all_counterexample_assertions(self):
        yield from self._assert_variables_set()
        yield from self._assert_one_literal_used()

        yield from super(QBFUnfolded, self)._assert_switch_active()
        yield from self._assert_positive_path()
        yield from self._assert_negative_path_exists_if_function_true()

        yield from super(QBFUnfolded, self)._assert_switch_inactive()
        yield from self._assert_negative_path()
        yield from self._assert_path_exists_if_function_false()

    def synth(self, timer=None):
        refining_solver = self.solver()
        cexample_solver = self.solver()

        for clause in self._assert_variables_set():
            refining_solver.add(clause)
        for clause in self._assert_one_literal_used():
            refining_solver.add(clause)

        for clause in self._all_counterexample_assertions():
            cexample_solver.add(clause)

        inputs = list(self.function.support)
        elements = list(self._all_literals_at_position())
        unfolding_steps = 0

        while True:
            solution = refining_solver.solve(of_interest=elements, timer=timer,
                                             simplify=True)
            if not solution:
                (num_clauses, num_variables) = refining_solver.num_clauses_variables()
                return self._build_result(None, unfolding_steps=unfolding_steps,
                                          num_clauses=num_clauses,
                                          num_variables=num_variables)

            counterexample = cexample_solver.solve(of_interest=inputs,
                                                   assumptions=solution,
                                                   timer=timer)

            if not counterexample:
                (num_clauses, num_variables) = refining_solver.num_clauses_variables()
                return self._build_result(solution, unfolding_steps=unfolding_steps,
                                          num_clauses=num_clauses,
                                          num_variables=num_variables)

            for clause in self._all_assertions_per_assignment(counterexample):
                refining_solver.add(clause)
            unfolding_steps += 1
