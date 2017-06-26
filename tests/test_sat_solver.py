#!/usr/bin/env python3

import sys
import unittest
import itertools as it
import pyeda.boolalg.expr as expr

import synth.sat
import synth.constraint

from .util import solver_exists

class TestSat:
    def get_solver(self):
        factory = synth.sat.Dimacs.from_known(self.SOLVER)
        return factory()

    def setUp(self):
        super().setUp()
        self.pos = tuple(expr.exprvar(p) for p in "abcdef")
        self.neg = tuple(expr.exprvar(p) for p in "uvwxyz")

    def test_sat_positive(self):
        solver = self.get_solver()
        solver.add(expr.And(*self.pos))
        solver.add(expr.And(*(~n for n in self.neg)))

        solution = solver.solve()
        expected = dict(it.chain(((p, True) for p in self.pos),
                                 ((n, False) for n in self.neg)))

        self.assertIsNotNone(solution)
        self.assertEqual(expected, solution)

    def test_sat_negative(self):
        solver = self.get_solver()
        solver.add(expr.And(*self.pos))
        solver.add(expr.And(*(~p for p in self.pos)))

        solution = solver.solve()
        self.assertIsNone(solution)

    def test_sat_positive_assumption(self):
        solver = self.get_solver()
        solver.add(expr.And(*self.pos))
        solver.add(expr.And(*(~n for n in self.neg)))

        assumptions = {v: True for v in self.pos}

        solution = solver.solve(assumptions=assumptions)
        expected = dict(it.chain(((p, True) for p in self.pos),
                                 ((n, False) for n in self.neg)))

        self.assertIsNotNone(solution)
        self.assertEqual(expected, solution)

    def test_sat_negative_assumption(self):
        solver = self.get_solver()
        solver.add(expr.And(*(~p for p in self.pos)))

        assumptions = {v: True for v in self.pos}

        solution = solver.solve(assumptions=assumptions)
        self.assertIsNone(solution)


class TestQbf(TestSat):
    def get_solver(self):
        factory = synth.sat.QDimacs.from_known(self.SOLVER)
        return factory()

    def test_qbf_positive(self):
        solver = self.get_solver()
        solver.exists(self.pos)
        solver.add(expr.And(*self.pos))
        solver.add(expr.And(*(~n for n in self.neg)))

        solution = solver.solve()
        expected = dict(it.chain(((p, True) for p in self.pos),
                                 ((n, False) for n in self.neg)))

        self.assertIsNotNone(solution)
        self.assertEqual(expected, solution)

    def test_qbf_negative(self):
        solver = self.get_solver()
        solver.forall(self.pos)
        solver.add(expr.And(*self.pos))

        solution = solver.solve()
        self.assertIsNone(solution)

    def test_qbf_forall_cardnet(self):
        equals = expr.exprvar("equals")
        cardinality = synth.constraint.equals(self.pos + self.neg,
                                              len(self.neg), equals)
        function = expr.Or(*self.neg, *(~n for n in self.neg), simplify=False)

        solver = self.get_solver()
        solver.exists([equals])
        solver.forall(self.neg)

        solver.add(function)
        for constraint in cardinality:
            solver.add(constraint)
        solver.add(equals)

        sat = solver.solve([equals])

        self.assertIsNotNone(sat)
        self.assertTrue(sat.get(equals))


class TestMinisat(TestSat, unittest.TestCase):
    def get_solver(self):
        return synth.sat.Minisat()


class TestCryptominisat(TestSat, unittest.TestCase):
    def get_solver(self):
        return synth.sat.Cryptominisat()


thismodule = sys.modules[__name__]

for solver in synth.sat.Dimacs.SOLVER:
    if solver_exists(solver):
        class_name = "Test{}Dimacs".format(solver.capitalize())
        clazz = type(class_name, (TestSat, unittest.TestCase), {"SOLVER": solver})
        setattr(thismodule, class_name, clazz)

for solver in synth.sat.QDimacs.SOLVER:
    if solver_exists(solver):
        class_name = "Test{}QDimacs".format(solver.capitalize())
        clazz = type(class_name, (TestQbf, unittest.TestCase), {"SOLVER": solver})
        setattr(thismodule, class_name, clazz)


if __name__ == '__main__':
    unittest.main()
