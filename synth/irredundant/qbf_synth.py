#!/usr/bin/env python3

import pyeda.boolalg.expr as expr

import synth
import synth.sat
import synth.constraint as constraint
from synth.util import assert_cnf

class QBFSynth(synth.base.BaseSynth):
    @staticmethod
    def _select_solver(arguments):
        return arguments.qbf_solver

    def _parse_solver(self, solver):
        if solver is None: return synth.sat.QDimacs.from_known("depqbf")
        return synth.sat.QDimacs.from_known(solver)

    def _path_var(self, i, j):
        assert 1 <= i <= self.m
        assert 1 <= j <= self.n
        return expr.exprvar("path", (i, j))

    @assert_cnf
    def _assert_lattice_on_path(self):
        def _set(i, j, inp):
            return self._literal_at_position_is(i, j, inp) & inp
        def _negated(i, j, inp):
            return self._literal_at_position_is(i, j, ~inp)  & ~inp

        for i in range(1, self.m + 1):
            for j in range(1, self.n + 1):
                auxiliaries = list()
                for inp in self._inputs_plus():
                    aux = self._next_aux("on_path")
                    on_path = _set(i, j, inp) | _negated(i, j, inp)
                    auxiliaries.append(aux)
                    yield expr.Implies(aux, on_path).to_cnf()
                yield expr.Implies(self._path_var(i, j),
                                   expr.Or(*auxiliaries)).to_cnf()

    @assert_cnf
    def _assert_some_path_connected(self, path_var=None):
        path_var = self._path_var if path_var is None else path_var

        start_at_top = [path_var(1, j) for j in range(1, self.n + 1)]
        end_at_bottom = [path_var(self.m, j) for j in range(1, self.n + 1)]
        yield from constraint.at_most(start_at_top, 1)
        yield from constraint.at_most(end_at_bottom, 1)

        if self.m == 1:
            # covered by `_assert_path_exists_if_function_true()`
            pass
        elif self.n == 1:
            for i in range(1, self.m):
                yield expr.Implies(path_var(i + 1, 1),
                                   path_var(i, 1)).to_cnf()
        else:
            for j in range(1, self.n + 1):
                yield expr.Implies(path_var(1, j),
                                   path_var(2, j)).to_cnf()
                yield expr.Implies(path_var(self.m, j),
                                   path_var(self.m - 1, j)).to_cnf()

            for i in range(2, self.m):
                for j in range(1, self.n + 1):
                    elements = [path_var(i_, j_)
                                for (i_, j_) in self._adjacent_4(i, j)]
                    equals_two = self._next_aux("equals_two")
                    yield from constraint.equals(elements, 2, equals_two)
                    yield expr.Implies(path_var(i, j), equals_two).to_cnf()

    @assert_cnf
    def _assert_path_exists_if_function_true(self):
        elements = (self._path_var(self.m, j) for j in range(1, self.n + 1))
        yield expr.Implies(self.function, expr.Or(*elements)).to_cnf()

    def _negative_path_var(self, i, j):
        assert 1 <= i <= self.m
        assert 1 <= j <= self.n
        return expr.exprvar(("path", "negative"), (i, j))

    @assert_cnf
    def _assert_lattice_on_negative_path(self):
        def _set(i, j, inp):
            return self._literal_at_position_is(i, j, inp) & ~inp
        def _negated(i, j, inp):
            return self._literal_at_position_is(i, j, ~inp) & inp

        for i in range(1, self.m + 1):
            for j in range(1, self.n + 1):
                auxiliaries = list()
                for inp in self._inputs_plus():
                    aux = self._next_aux("on_neg_path")
                    on_neg_path = _set(i, j, inp) | _negated(i, j, inp)
                    auxiliaries.append(aux)
                    yield expr.Implies(aux, on_neg_path).to_cnf()
                yield expr.Implies(self._negative_path_var(i, j),
                                   expr.Or(*auxiliaries)).to_cnf()

    @assert_cnf
    def _assert_some_negative_path_connected(self, path_var=None):
        path_var = self._negative_path_var if path_var is None else path_var

        start_left = [path_var(i, 1)
                      for i in range(1, self.m + 1)]
        end_right = [path_var(i, self.n)
                     for i in range(1, self.m + 1)]
        yield from constraint.at_most(start_left, 1)
        yield from constraint.at_most(end_right, 1)

        if self.n == 1:
            # covered by `_assert_negative_path_exists_if_function_false()`
            pass
        elif self.m == 1:
            for j in range(1, self.n):
                yield expr.Implies(path_var(1, j + 1),
                                   path_var(1, j)).to_cnf()
        else:
            for i in range(1, self.m + 1):
                column_offset = [i_ for i_ in (i-1, i, i+1) if 1 <= i_ <= self.m]
                for (j, j_off) in ((1, 2), (self.n, self.n - 1)):
                    elements = [path_var(i_, j_off) for i_ in column_offset]
                    equals_one = self._next_aux("equals_one")
                    yield from constraint.cardnet.equals(elements, 1, equals_one)
                    yield expr.Implies(path_var(i, j), equals_one).to_cnf()

                for j in range(2, self.n):
                    elements = [path_var(i_, j_)
                                for (i_, j_) in self._adjacent_8(i, j)]
                    equals_two = self._next_aux("equals_two")
                    yield from constraint.equals(elements, 2, equals_two)
                    yield expr.Implies(path_var(i, j), equals_two).to_cnf()

    @assert_cnf
    def _assert_negative_path_exists_if_function_false(self):
        elements = (self._negative_path_var(i, self.n) for i in range(1, self.m + 1))
        yield expr.Implies(~self.function, expr.Or(*elements)).to_cnf()

    @assert_cnf
    def _all_assertions(self):
        yield from self._assert_variables_set()
        yield from self._assert_one_literal_used()
        yield from self._assert_lattice_on_path()
        yield from self._assert_some_path_connected()
        yield from self._assert_path_exists_if_function_true()
        yield from self._assert_lattice_on_negative_path()
        yield from self._assert_some_negative_path_connected()
        yield from self._assert_negative_path_exists_if_function_false()

    def synth(self, timer=None):
        inputs = list(self.function.support)
        elements = list(self._all_literals_at_position())

        solver = self.solver()
        solver.exists(elements)
        solver.forall(inputs)
        for clause in self._all_assertions():
            solver.add(clause)

        self.print_dimacs(solver, "irredundant")
        solution = solver.solve(of_interest=elements, no_decode=self.no_decode,
                                timer=timer)
        (num_clauses, num_variables) = solver.num_clauses_variables()
        return self._build_result(solution, num_clauses=num_clauses,
                                  num_variables=num_variables)
