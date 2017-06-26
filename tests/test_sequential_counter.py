#!/usr/bin/env python3

import unittest
import pyeda.boolalg.expr as expr

import synth.constraint as constraint


class TestBase(unittest.TestCase):
    def setUp(self):
        self.pos = expr.exprvar("a")
        self.neg = tuple(expr.exprvar(p) for p in "uvwxyz")
        self.function = expr.And(self.pos, ~expr.Or(*self.neg))


class TestSequentialCounterAtMost(TestBase):
    def test_at_most_one_small(self):
        self.function = self.pos

        cardinality = constraint.at_most_one(self.function.support)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(self.pos), 1)

    def test_at_most_one_zero(self):
        self.function = ~expr.Or(*self.neg)

        cardinality = constraint.at_most_one(self.function.support)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)

    def test_at_most_one(self):
        cardinality = constraint.at_most_one(self.function.support)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(self.pos), 1)

    def test_not_at_most_one(self):
        self.function = expr.And(self.pos, expr.exprvar("b"), ~expr.Or(*self.neg))

        cardinality = constraint.at_most_one(self.function.support)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNone(sat)

    def test_at_most_one_equivalent(self):
        at_most = expr.exprvar("at_most")
        cardinality = constraint.at_most_one(self.function.support, at_most)
        sat = expr.And(self.function, at_most, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(at_most), 1)

    def test_at_most_one_not_equivalent(self):
        at_most = expr.exprvar("at_most")
        cardinality = constraint.at_most_one(self.function.support, ~at_most)
        sat = expr.And(self.function, ~at_most, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(at_most), 0)

    def test_not_at_most_one_equivalent(self):
        self.function = expr.And(self.pos, expr.exprvar("b"), ~expr.Or(*self.neg))

        at_most = expr.exprvar("at_most")
        cardinality = constraint.at_most_one(self.function.support, at_most)
        sat = expr.And(self.function, ~at_most, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(at_most), 0)

    def test_not_at_most_one_not_equivalent(self):
        self.function = expr.And(self.pos, expr.exprvar("b"), ~expr.Or(*self.neg))

        at_most = expr.exprvar("at_most")
        cardinality = constraint.at_most_one(self.function.support, ~at_most)
        sat = expr.And(self.function, at_most, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(at_most), 1)


class TestSequentialCounterAtLeast(TestBase):
    def test_at_least_one_equivalent(self):
        at_least = expr.exprvar("at_least")
        cardinality = constraint.at_least_one(self.function.support, at_least)
        sat = expr.And(self.function, at_least, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(at_least), 1)

    def test_at_least_one_not_equivalent(self):
        at_least = expr.exprvar("at_least")
        cardinality = constraint.at_least_one(self.function.support, ~at_least)
        sat = expr.And(self.function, ~at_least, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(at_least), 0)

    def test_not_at_least_one_equivalent(self):
        self.function = ~expr.Or(*self.neg)

        at_least = expr.exprvar("at_least")
        cardinality = constraint.at_least_one(self.function.support, at_least)
        sat = expr.And(self.function, ~at_least, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(at_least), 0)

    def test_not_at_least_one_not_equivalent(self):
        self.function = ~expr.Or(*self.neg)

        at_least = expr.exprvar("at_least")
        cardinality = constraint.at_least_one(self.function.support, ~at_least)
        sat = expr.And(self.function, at_least, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(at_least), 1)


class TestSequentialCounterEquals(TestBase):
    def test_equals_one(self):
        self.function = self.pos

        cardinality = constraint.equals_one(self.function.support)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(self.pos), 1)

    def test_not_equals_one_zero(self):
        self.function = ~expr.Or(*self.neg)

        cardinality = constraint.equals_one(self.function.support)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNone(sat)

    def test_not_equals_one_two(self):
        self.function = expr.And(self.pos, expr.exprvar("b"), ~expr.Or(*self.neg))

        cardinality = constraint.equals_one(self.function.support)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNone(sat)

    def test_equals_one_equivalent(self):
        self.function = self.pos

        equals = expr.exprvar("equals")
        cardinality = constraint.equals_one(self.function.support, equals)
        sat = expr.And(self.function, equals, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(equals), 1)

    def test_equals_one_not_equivalent(self):
        self.function = self.pos

        equals = expr.exprvar("equals")
        cardinality = constraint.equals_one(self.function.support, ~equals)
        sat = expr.And(self.function, ~equals, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(equals), 0)

    def test_not_equals_one_equivalent(self):
        self.function = ~expr.Or(*self.neg)

        equals = expr.exprvar("equals")
        cardinality = constraint.equals_one(self.function.support, equals)
        sat = expr.And(self.function, ~equals, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(equals), 0)

    def test_not_equals_one_not_equivalent(self):
        self.function = ~expr.Or(*self.neg)

        equals = expr.exprvar("equals")
        cardinality = constraint.equals_one(self.function.support, ~equals)
        sat = expr.And(self.function, equals, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(equals), 1)


if __name__ == '__main__':
    unittest.main()
