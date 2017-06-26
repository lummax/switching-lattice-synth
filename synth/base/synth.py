#!/usr/bin/env python3

import os.path
import itertools as it

import pyeda.boolalg.expr as expr

import synth.constraint as constraint
from synth.util import assert_cnf

class Synth:
    def __init__(self, function):
        self.function_container = function
        self.function = self.function_container.function

    @classmethod
    def from_path(cls, path, *args, **kwargs):
        function = Function.from_path(path)
        return cls(function, *args, **kwargs)


class BaseSynth(Synth):
    _counter = it.count()

    def __init__(self, function, m, n, solver=None, no_decode=False,
                 dump_dimacs=False):
        super().__init__(function)
        assert 1 <= m, "1 must be smaller or equal to m = {}".format(m)
        assert 1 <= n, "1 must be smaller or equal to n = {}".format(n)
        self.m = m
        self.n = n
        self.solver = self._parse_solver(solver)
        self.no_decode = no_decode
        self.dump_dimacs = dump_dimacs

    @staticmethod
    def _select_solver(arguments):
        raise NotImplementedError()

    def _parse_solver(self, solver):
        raise NotImplementedError()

    @classmethod
    def with_solver(cls, solver=None, no_decode=False, dump_dimacs=False):
        def factory(function, m, n):
            return cls(function, m, n, solver, no_decode, dump_dimacs)
        factory.solver = solver
        return factory

    @classmethod
    def from_arguments(cls, arguments):
        solver = cls._select_solver(arguments)
        return cls.with_solver(solver, arguments.no_decode, arguments.dump_dimacs)

    @staticmethod
    def _increment_counter():
        return next(BaseSynth._counter)

    @staticmethod
    def _next_aux(name=None, index=None):
        count = BaseSynth._increment_counter()
        names = ("synth", name) if name else "synth"
        indices = (index, count) if index else count
        return expr.exprvar(names, indices)

    def _lattice_from_solution(self, solution):
        result = [[0 for _ in range(self.n)] for _ in range(self.m)]
        for conf in (l for (l, v) in solution.items() if v):
            (i, j, var) = self._parse_position_variable(conf)
            result[i - 1][j - 1] = var

        return result

    def _build_result(self, solution, **kwargs):
        result = dict(kwargs)
        if solution is not None:
            result["solution_height"] = self.m
            result["solution_width"] = self.n
            result["solution"] = self._lattice_from_solution(solution) \
                                 if not self.no_decode else True
        return result

    def _inputs_plus(self):
        yield from self.function.support
        yield expr.exprvar("constant")

    def _input_literals(self):
        for inp in self._inputs_plus():
            yield inp
            yield ~inp

    def _literal_at_position_is(self, i, j, input_variable):
        negated = isinstance(input_variable, expr.Complement)
        name = ("literal", "negated") if negated else ("literal", "positive")
        variable = ~input_variable if negated else input_variable
        return expr.exprvar(name + variable.names,
                            (i, j) + variable.indices)

    def _parse_position_variable(self, variable):
        (_literal, kind, *names) = variable.names
        (i, j, *indices) = variable.indices

        if tuple(names) == ("constant",):
            if kind == "positive": return (i, j, True)
            elif kind == "negated": return (i, j, False)
        else:
            var = expr.exprvar(tuple(names), tuple(indices))
            if kind == "positive": return (i, j, var)
            elif kind == "negated": return (i, j, ~var)
        raise ValueError("Unparseable variable ({})".format(variable))

    def _all_literals_at_position(self):
        for i in range(1, self.m + 1):
            for j in range(1, self.n + 1):
                for inp in self._input_literals():
                    yield self._literal_at_position_is(i, j, inp)

    def _adjacent_4(self, i, j):
        for i_ in range(1, self.m + 1):
            for j_ in range(1, self.n + 1):
                if abs(i - i_) + abs(j - j_) == 1:
                    yield (i_, j_)

    def _adjacent_8(self, i, j):
        for i_ in (i_ for i_ in range(1, self.m + 1) if abs(i - i_) <= 1):
            for j_ in (j_ for j_ in range(1, self.n + 1) if abs(j - j_) <= 1):
                if (i, j) != (i_, j_):
                    yield (i_, j_)

    @assert_cnf
    def _assert_variables_set(self):
        yield expr.exprvar("constant")

    @assert_cnf
    def _assert_one_literal_used(self):
        for i in range(1, self.m + 1):
            for j in range(1, self.n + 1):
                elements = [self._literal_at_position_is(i, j, inp)
                            for inp in self._input_literals()]
                yield from constraint.equals(elements, 1)

    def print_dimacs(self, solver, infix):
        if self.dump_dimacs and hasattr(solver, "print_dimacs"):
            fpath = os.path.basename(self.function_container.path)
            dimacs_name = "qbfu_{}_{}.dimacs".format(infix, fpath)
            with open(dimacs_name, "w") as fob: solver.print_dimacs(fob)
