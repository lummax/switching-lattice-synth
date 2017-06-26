#!/usr/bin/env python3

import pyeda.boolalg.expr as expr

import synth
import synth.sat
from synth.util import assert_cnf

class QBFSynth(synth.base.BaseSynth):
    @staticmethod
    def _select_solver(arguments):
        return arguments.qbf_solver

    def _parse_solver(self, solver):
        if solver is None: return synth.sat.QDimacs.from_known("depqbf")
        return synth.sat.QDimacs.from_known(solver)

    def _upper_path_bound(self):
        return (self.m * self.n) // 2

    def _active_switch(self, i, j):
        assert 1 <= i <= self.m
        assert 1 <= j <= self.n
        return expr.exprvar("switch", (i, j))

    def _position_reachable(self, i, j, rnd):
        assert 1 <= i <= self.m
        assert 1 <= j <= self.n
        return expr.exprvar("reachable", (i, j, rnd))

    def _inactive_switch(self, i, j):
        assert 1 <= i <= self.m
        assert 1 <= j <= self.n
        return expr.exprvar(("switch", "inactive"), (i, j))

    def _position_unreachable(self, i, j, rnd):
        assert 1 <= i <= self.m
        assert 1 <= j <= self.n
        return expr.exprvar("unreachable", (i, j, rnd))

    @assert_cnf
    def _assert_switch_active(self):
        def _set(i, j, inp):
            return self._literal_at_position_is(i, j, inp) & inp
        def _negated(i, j, inp):
            return self._literal_at_position_is(i, j, ~inp)  & ~inp

        for i in range(1, self.m + 1):
            for j in range(1, self.n + 1):
                auxiliaries = list()
                for inp in self._inputs_plus():
                    aux = self._next_aux("switch_active")
                    on_path = _set(i, j, inp) | _negated(i, j, inp)
                    auxiliaries.append(aux)
                    yield expr.Implies(aux, on_path).to_cnf()
                yield expr.Implies(self._active_switch(i, j),
                                   expr.Or(*auxiliaries)).to_cnf()

    @assert_cnf
    def _assert_positive_path(self, switch_var=None, position_var=None):
        switch_var = self._active_switch if switch_var is None else switch_var
        position_var = self._position_reachable if position_var is None \
                       else position_var

        if self.m == 1 or self.n == 1:
            upper = self._upper_path_bound()
            for i in range(1, self.m + 1):
                for j in range(1, self.n + 1):
                    yield expr.Implies(position_var(i, j, upper),
                                       switch_var(i, j)).to_cnf()
            if self.n == 1:
                for i in range(1, self.m):
                    yield expr.Implies(position_var(i + 1, 1, upper),
                                       position_var(i, 1, upper)).to_cnf()
        else:
            for i in range(1, self.m + 1):
                for j in range(1, self.n + 1):
                    reachable = position_var(i, j, 0)
                    if i == 1: yield reachable
                    else: yield ~reachable

            for rnd in range(1, self._upper_path_bound() + 1):
                for i in range(1, self.m + 1):
                    for j in range(1, self.n + 1):
                        reachable = position_var(i, j, rnd)
                        elements = [position_var(i_, j_, rnd - 1) & \
                                    switch_var(i_, j_)
                                    for (i_, j_) in self._adjacent_4(i, j)]
                        elements.append(position_var(i, j, rnd - 1))
                        yield expr.Implies(reachable, expr.Or(*elements)).to_cnf()

    @assert_cnf
    def _assert_path_exists_if_function_true(self):
        elements = (self._active_switch(self.m, j) & \
                    self._position_reachable(self.m, j, self._upper_path_bound())
                    for j in range(1, self.n + 1))
        yield expr.Implies(self.function, expr.Or(*elements)).to_cnf()

    @assert_cnf
    def _assert_switch_inactive(self):
        def _set(i, j, inp):
            return self._literal_at_position_is(i, j, inp) & ~inp
        def _negated(i, j, inp):
            return self._literal_at_position_is(i, j, ~inp) & inp

        for i in range(1, self.m + 1):
            for j in range(1, self.n + 1):
                auxiliaries = list()
                for inp in self._inputs_plus():
                    aux = self._next_aux("switch_inactive")
                    on_neg_path = _set(i, j, inp) | _negated(i, j, inp)
                    auxiliaries.append(aux)
                    yield expr.Implies(aux, on_neg_path).to_cnf()
                yield expr.Implies(self._inactive_switch(i, j),
                                   expr.Or(*auxiliaries)).to_cnf()

    @assert_cnf
    def _assert_negative_path(self, switch_var=None, position_var=None):
        switch_var = self._inactive_switch if switch_var is None else switch_var
        position_var = self._position_unreachable if position_var is None \
                       else position_var

        if self.m == 1 or self.n == 1:
            upper = self._upper_path_bound()
            for i in range(1, self.m + 1):
                for j in range(1, self.n + 1):
                    yield expr.Implies(position_var(i, j, upper),
                                       switch_var(i, j)).to_cnf()
            if self.m == 1:
                for j in range(1, self.n):
                    yield expr.Implies(position_var(1, j + 1, upper),
                                       position_var(1, j, upper)).to_cnf()
        else:
            for i in range(1, self.m + 1):
                for j in range(1, self.n + 1):
                    reachable = position_var(i, j, 0)
                    if j == 1: yield reachable
                    else: yield ~reachable

            for rnd in range(1, self._upper_path_bound() + 1):
                for i in range(1, self.m + 1):
                    for j in range(1, self.n + 1):
                        reachable = position_var(i, j, rnd)
                        elements = [position_var(i_, j_, rnd - 1) & \
                                    switch_var(i_, j_)
                                    for (i_, j_) in self._adjacent_8(i, j)]
                        elements.append(position_var(i, j, rnd - 1))
                        yield expr.Implies(reachable, expr.Or(*elements)).to_cnf()

    @assert_cnf
    def _assert_negative_path_exists_if_function_false(self):
        elements = (self._inactive_switch(i, self.n) & \
                    self._position_unreachable(i, self.n, self._upper_path_bound())
                    for i in range(1, self.m + 1))
        yield expr.Implies(~self.function, expr.Or(*elements)).to_cnf()

    @assert_cnf
    def _all_assertions(self):
        yield from self._assert_variables_set()
        yield from self._assert_one_literal_used()

        yield from self._assert_switch_active()
        yield from self._assert_positive_path()
        yield from self._assert_path_exists_if_function_true()

        yield from self._assert_switch_inactive()
        yield from self._assert_negative_path()
        yield from self._assert_negative_path_exists_if_function_false()

    def synth(self, timer=None):
        inputs = list(self.function.support)
        elements = list(self._all_literals_at_position())

        solver = self.solver()
        solver.exists(elements)
        solver.forall(inputs)
        for clause in self._all_assertions():
            solver.add(clause)

        self.print_dimacs(solver, "reachability")
        solution = solver.solve(of_interest=elements, no_decode=self.no_decode,
                                timer=timer)

        (num_clauses, num_variables) = solver.num_clauses_variables()
        return self._build_result(solution, num_clauses=num_clauses,
                                  num_variables=num_variables)
