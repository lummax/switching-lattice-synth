#!/usr/bin/env python3

import itertools as it
import pyeda.boolalg.expr as expr

from synth.util import assert_cnf

_counter = it.count()

@assert_cnf
def at_most_one(inputs, equivalent=None):
    assert inputs, "inputs must not be empty"
    count = next(_counter)

    def a(i):
        return expr.exprvar("sinz", (i, count))

    def clauses(variables):
        length = len(variables)
        (first, rest, last) = (variables[0], variables[1:-1], variables[-1])

        yield expr.Or(~first, a(1))
        yield expr.Or(~last, ~a(length - 1))

        for (i, x) in zip(range(2, length), rest):
            yield expr.Or(~x, a(i))
            yield expr.Or(~a(i - 1), a(i))
            yield expr.Or(~x, ~a(i - 1))

    if equivalent is None:
        yield from clauses(tuple(inputs))
    else:
        auxiliaries = list()
        for clause in clauses(tuple(inputs)):
            aux = expr.exprvar(("sinz", "eq"), next(_counter))
            yield expr.Implies(aux, clause).to_cnf()
            yield expr.Implies(clause, aux).to_cnf()
            auxiliaries.append(aux)
        constraint = expr.And(*auxiliaries)
        yield expr.Implies(constraint, equivalent).to_cnf()
        yield expr.Implies(equivalent, constraint).to_cnf()


@assert_cnf
def at_least_one(inputs, equivalent=None):
    assert inputs, "inputs must not be empty"
    constraint = expr.Or(*inputs)
    if equivalent is None:
        yield constraint
    else:
        yield expr.Implies(equivalent, constraint).to_cnf()
        yield expr.Implies(constraint, equivalent).to_cnf()


@assert_cnf
def equals_one(inputs, equivalent=None):
    assert inputs, "inputs must not be empty"
    yield from at_most_one(inputs, equivalent)
    yield from at_least_one(inputs, equivalent)
