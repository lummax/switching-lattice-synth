#!/usr/bin/env python3

import unittest
import pyeda.boolalg.expr as expr

import synth.constraint.cardnet as cardnet

class TestBase(unittest.TestCase):
    def setUp(self):
        self.pos = tuple(expr.exprvar(p) for p in "abc")
        self.neg = tuple(expr.exprvar(p) for p in "uvwxyz")
        self.function = expr.And(*self.pos, ~expr.Or(*self.neg))


class TestCardnetAtMost(TestBase):
    def test_at_most_zero_small(self):
        (a, _b, _c) = self.pos
        self.function = a

        cardinality = cardnet.at_most(self.function.support, 0)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNone(sat)

    def test_at_most_zero(self):
        cardinality = cardnet.at_most(self.function.support, 0)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNone(sat)

    def test_at_most_one_small(self):
        (a, _b, _c) = self.pos
        self.function = a

        cardinality = cardnet.at_most(self.function.support, 1)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(a), 1)

    def test_at_most_one(self):
        cardinality = cardnet.at_most(self.function.support, 1)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNone(sat)

    def test_at_most_lower(self):
        cardinality = cardnet.at_most(self.function.support,
                                      len(self.pos) - 1)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNone(sat)

    def test_at_most_is(self):
        cardinality = cardnet.at_most(self.function.support,
                                      len(self.pos))
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)

        solution = {x: sat.get(x) for x in self.pos}
        self.assertEqual(solution, {x: 1 for x in self.pos})

    def test_at_most_higher(self):
        cardinality = cardnet.at_most(self.function.support,
                                      len(self.pos) + 1)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)

        solution = {x: sat.get(x) for x in self.pos}
        self.assertEqual(solution, {x: 1 for x in self.pos})

    def test_at_most_is_equivalent(self):
        at_most = expr.exprvar("at_most")
        cardinality = cardnet.at_most(self.function.support,
                                      len(self.pos),
                                      at_most)
        sat = expr.And(self.function, at_most, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(at_most), 1)

    def test_at_most_is_not_equivalent(self):
        at_most = expr.exprvar("at_most")
        cardinality = cardnet.at_most(self.function.support,
                                      len(self.pos),
                                      ~at_most)
        sat = expr.And(self.function, ~at_most, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(at_most), 0)

    def test_not_at_most_is_equivalent(self):
        at_most = expr.exprvar("at_most")
        cardinality = cardnet.at_most(self.function.support,
                                      len(self.pos) - 1,
                                      at_most)
        sat = expr.And(self.function, ~at_most, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(at_most), 0)

    def test_not_at_most_is_not_equivalent(self):
        at_most = expr.exprvar("at_most")
        cardinality = cardnet.at_most(self.function.support,
                                      len(self.pos) - 1,
                                      ~at_most)
        sat = expr.And(self.function, at_most, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(at_most), 1)


class TestCardnetAtLeast(TestBase):
    def test_at_least_zero(self):
        cardinality = cardnet.at_least(self.function.support, 0)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)

        solution = {x: sat.get(x) for x in self.pos}
        self.assertEqual(solution, {x: 1 for x in self.pos})

    def test_at_least_one(self):
        cardinality = cardnet.at_least(self.function.support, 1)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)

        solution = {x: sat.get(x) for x in self.pos}
        self.assertEqual(solution, {x: 1 for x in self.pos})

    def test_at_least_lower(self):
        cardinality = cardnet.at_least(self.function.support,
                                       len(self.pos) - 1)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)

        solution = {x: sat.get(x) for x in self.pos}
        self.assertEqual(solution, {x: 1 for x in self.pos})

    def test_at_least_is(self):
        cardinality = cardnet.at_least(self.function.support,
                                       len(self.pos))
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)

        solution = {x: sat.get(x) for x in self.pos}
        self.assertEqual(solution, {x: 1 for x in self.pos})

    def test_at_least_higher(self):
        cardinality = cardnet.at_least(self.function.support,
                                       len(self.pos) + 1)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNone(sat)

    def test_at_least_is_equivalent(self):
        at_least = expr.exprvar("at_least")
        cardinality = cardnet.at_least(self.function.support,
                                       len(self.pos),
                                       at_least)
        sat = expr.And(self.function, at_least, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(at_least), 1)

    def test_at_least_is_not_equivalent(self):
        at_least = expr.exprvar("at_least")
        cardinality = cardnet.at_least(self.function.support,
                                       len(self.pos),
                                       ~at_least)
        sat = expr.And(self.function, ~at_least, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(at_least), 0)


class TestCardnetEquals(TestBase):
    def test_equals_zero(self):
        cardinality = cardnet.equals(self.function.support, 0)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNone(sat)

    def test_equals_one_small(self):
        (a, _b, _c) = self.pos
        self.function = a

        cardinality = cardnet.equals(self.function.support, 1)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()

        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(a), 1)

    def test_equals_one(self):
        cardinality = cardnet.equals(self.function.support, 1)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNone(sat)

    def test_equals_lower(self):
        cardinality = cardnet.equals(self.function.support,
                                     len(self.pos) - 1)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNone(sat)

    def test_equals_is(self):
        cardinality = cardnet.equals(self.function.support,
                                     len(self.pos))
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)

        solution = {x: sat.get(x) for x in self.pos}
        self.assertEqual(solution, {x: 1 for x in self.pos})

    def test_equals_higher(self):
        cardinality = cardnet.equals(self.function.support,
                                     len(self.pos) + 1)
        sat = expr.And(self.function, *cardinality).to_cnf().satisfy_one()
        self.assertIsNone(sat)

    def test_equals_is_equivalent(self):
        equals = expr.exprvar("equals")
        cardinality = cardnet.equals(self.function.support,
                                     len(self.pos),
                                     equals)
        sat = expr.And(self.function, equals,
                       *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(equals), 1)

    def test_equals_is_not_equivalent(self):
        equals = expr.exprvar("equals")
        cardinality = cardnet.equals(self.function.support,
                                     len(self.pos),
                                     ~equals)
        sat = expr.And(self.function, ~equals, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(equals), 0)

    def test_not_equals_lower(self):
        equals = expr.exprvar("equals")
        cardinality = cardnet.equals(self.function.support,
                                     len(self.pos) - 1,
                                     equals)
        sat = expr.And(self.function, ~equals, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(equals), 0)

    def test_not_equals_lower_not_equivalent(self):
        equals = expr.exprvar("equals")
        cardinality = cardnet.equals(self.function.support,
                                     len(self.pos) - 1,
                                     ~equals)
        sat = expr.And(self.function, equals, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(equals), 1)

    def test_not_equals_higher(self):
        equals = expr.exprvar("equals")
        cardinality = cardnet.equals(self.function.support,
                                     len(self.pos) + 1,
                                     equals)
        sat = expr.And(self.function, ~equals, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(equals), 0)

    def test_not_equals_higher(self):
        equals = expr.exprvar("equals")
        cardinality = cardnet.equals(self.function.support,
                                     len(self.pos) + 1,
                                     ~equals)
        sat = expr.And(self.function, equals, *cardinality).to_cnf().satisfy_one()
        self.assertIsNotNone(sat)
        self.assertEqual(sat.get(equals), 1)


if __name__ == '__main__':
    unittest.main()
