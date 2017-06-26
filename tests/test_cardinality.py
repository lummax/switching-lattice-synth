#!/usr/bin/env python3

import unittest
import pyeda.boolalg.expr as expr

import hypothesis
from .util import complex_functions

import synth.constraint as constraint

class TestCardinality(unittest.TestCase):
    @hypothesis.given(complex_functions())
    def test_at_most_one(self, function):
        cardinality_a = constraint.at_most_one(function.support)
        sat_a = expr.And(function, *cardinality_a).to_cnf().satisfy_one()

        cardinality_b = constraint.at_most(function.support, 1)
        sat_b = expr.And(function, *cardinality_b).to_cnf().satisfy_one()

        self.assertEqual(sat_a is None, sat_b is None)

    @hypothesis.given(complex_functions())
    def test_at_most_one_equivalent(self, function):
        equivalent = expr.exprvar("equivalent")

        cardinality_a = constraint.at_most_one(function.support, equivalent)
        sat_a = expr.And(function, equivalent, *cardinality_a).to_cnf().satisfy_one()

        cardinality_b = constraint.at_most(function.support, 1, equivalent)
        sat_b = expr.And(function, equivalent, *cardinality_b).to_cnf().satisfy_one()

        self.assertEqual(sat_a is None, sat_b is None)
        if sat_a or sat_b:
            self.assertEqual(sat_a.get(equivalent), sat_b.get(equivalent))

    @hypothesis.given(complex_functions())
    def test_at_most_one_not_equivalent(self, function):
        equivalent = expr.exprvar("equivalent")

        cardinality_a = constraint.at_most_one(function.support, ~equivalent)
        sat_a = expr.And(function, ~equivalent,
                         *cardinality_a).to_cnf().satisfy_one()

        cardinality_b = constraint.at_most(function.support, 1, ~equivalent)
        sat_b = expr.And(function, ~equivalent,
                         *cardinality_b).to_cnf().satisfy_one()

        self.assertEqual(sat_a is None, sat_b is None)
        if sat_a or sat_b:
            self.assertEqual(sat_a.get(equivalent), sat_b.get(equivalent))

    @hypothesis.given(complex_functions())
    def test_at_least_one(self, function):
        cardinality_a = constraint.at_least_one(function.support)
        sat_a = expr.And(function, *cardinality_a).to_cnf().satisfy_one()

        cardinality_b = constraint.at_least(function.support, 1)
        sat_b = expr.And(function, *cardinality_b).to_cnf().satisfy_one()

        self.assertEqual(sat_a is None, sat_b is None)

    @hypothesis.given(complex_functions())
    def test_at_least_one_equivalent(self, function):
        equivalent = expr.exprvar("equivalent")

        cardinality_a = constraint.at_least_one(function.support, equivalent)
        sat_a = expr.And(function, equivalent, *cardinality_a).to_cnf().satisfy_one()

        cardinality_b = constraint.at_least(function.support, 1, equivalent)
        sat_b = expr.And(function, equivalent, *cardinality_b).to_cnf().satisfy_one()

        self.assertEqual(sat_a is None, sat_b is None)
        if sat_a or sat_b:
            self.assertEqual(sat_a.get(equivalent), sat_b.get(equivalent))

    @hypothesis.given(complex_functions())
    def test_at_least_one_not_equivalent(self, function):
        equivalent = expr.exprvar("equivalent")

        cardinality_a = constraint.at_least_one(function.support, ~equivalent)
        sat_a = expr.And(function, ~equivalent,
                         *cardinality_a).to_cnf().satisfy_one()

        cardinality_b = constraint.at_least(function.support, 1, ~equivalent)
        sat_b = expr.And(function, ~equivalent,
                         *cardinality_b).to_cnf().satisfy_one()

        self.assertEqual(sat_a is None, sat_b is None)
        if sat_a or sat_b:
            self.assertEqual(sat_a.get(equivalent), sat_b.get(equivalent))

    @hypothesis.given(complex_functions())
    def test_equals_one(self, function):
        cardinality_a = constraint.equals_one(function.support)
        sat_a = expr.And(function, *cardinality_a).to_cnf().satisfy_one()

        cardinality_b = constraint.equals(function.support, 1)
        sat_b = expr.And(function, *cardinality_b).to_cnf().satisfy_one()

        self.assertEqual(sat_a is None, sat_b is None)

    @hypothesis.given(complex_functions())
    def test_equals_one_equivalent(self, function):
        equivalent = expr.exprvar("equivalent")

        cardinality_a = constraint.equals_one(function.support, equivalent)
        sat_a = expr.And(function, equivalent, *cardinality_a).to_cnf().satisfy_one()

        cardinality_b = constraint.equals(function.support, 1, equivalent)
        sat_b = expr.And(function, equivalent, *cardinality_b).to_cnf().satisfy_one()

        self.assertEqual(sat_a is None, sat_b is None)
        if sat_a or sat_b:
            self.assertEqual(sat_a.get(equivalent), sat_b.get(equivalent))

    @hypothesis.given(complex_functions())
    def test_equals_one_not_equivalent(self, function):
        equivalent = expr.exprvar("equivalent")

        cardinality_a = constraint.equals_one(function.support, ~equivalent)
        sat_a = expr.And(function, ~equivalent,
                         *cardinality_a).to_cnf().satisfy_one()

        cardinality_b = constraint.equals(function.support, 1, ~equivalent)
        sat_b = expr.And(function, ~equivalent,
                         *cardinality_b).to_cnf().satisfy_one()

        self.assertEqual(sat_a is None, sat_b is None)
        if sat_a or sat_b:
            self.assertEqual(sat_a.get(equivalent), sat_b.get(equivalent))


if __name__ == '__main__':
    unittest.main()
