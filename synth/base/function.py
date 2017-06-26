#!/usr/bin/env python3

import math

import pyeda.parsing.pla
import pyeda.boolalg.expr as expr
import pyeda.boolalg.table as table
import pyeda.boolalg.minimization as minimization


class Function:
    def __init__(self, path, function):
        self.path = path or ""
        self.function = function
        self.isop_function = self._minimize(self.function)
        self.isop_dual = self._minimize(self._dual(self.function))

    def __repr__(self):
        arguments = (self.path, self.function)
        return '{}({})'.format(self.__class__.__name__,
                               ", ".join(repr(x) for x in arguments))

    def inputs(self):
        return len(self.function.support)

    def naive_lattice_bounds(self):
        rows = sum(1 for _ in self.products(self.isop_dual))
        columns = sum(1 for _ in self.products(self.isop_function))
        return (rows, columns)

    def upper_bound(self):
        (rows, columns) = self.naive_lattice_bounds()
        return rows * columns

    def lower_bound(self):
        isop_degree = max(sum(1 for _ in self.literals(p))
                          for p in self.products(self.isop_function))
        dual_degree = max(sum(1 for _ in self.literals(p))
                          for p in self.products(self.isop_dual))
        upper_bound = self.upper_bound()
        configurations = [(m, n) for m in range(1, upper_bound + 1)
                          for n in range(1, upper_bound + 1)
                          if m * n <= upper_bound and \
                          self._satisfies_inequal(isop_degree, dual_degree, m, n)]
        if not configurations: return 1
        return min(m * n for (m, n) in configurations)

    @staticmethod
    def _satisfies_inequal(isop_degree, dual_degree, m, n):
        snd_summand = (2 + -1**m + -1**n) / 2

        idegree_bnd = m if m <= 2 or n <= 1 else \
                      3 * math.ceil((m - 2) / 2) * math.ceil(n / 2) + snd_summand
        ddegree_bnd = n if m <= 3 or n <= 2 else \
                      2 * math.ceil((n - 2) / 2) * math.ceil(m / 2) + snd_summand

        return isop_degree <= idegree_bnd and dual_degree <= ddegree_bnd

    @classmethod
    def from_path(cls, path, *args, **kwargs):
        return cls(path, cls._read_pla(path), *args, **kwargs)

    @staticmethod
    def _vector_to_vars(vector):
        for (num, inp) in enumerate(vector):
            if inp == table.PC_ONE:
                yield expr.exprvar("input", num)
            elif inp == table.PC_ZERO:
                yield ~expr.exprvar("input", num)

    @staticmethod
    def _cover_to_expression(cover):
        inputs = (inp for (inp, outputs) in cover if outputs == (1,))
        terms = (expr.And(*Function._vector_to_vars(v)) for v in inputs)
        return expr.Or(*terms)

    @staticmethod
    def _read_pla(path):
        with open(path) as fd:
            pla = pyeda.parsing.pla.parse(fd.read())
            return Function._cover_to_expression(pla.get("cover"))

    @staticmethod
    def _minimize(function):
        dnf = function.to_dnf()
        if dnf.is_zero() or dnf.is_one(): return dnf
        return minimization.espresso_exprs(dnf)[0]

    @staticmethod
    def _dual(function):
        def recurse(expression):
            if expression.ASTOP == "or":
                return expr.And(*(recurse(e) for e in expression.xs))
            if expression.ASTOP == "and":
                return expr.Or(*(recurse(e) for e in expression.xs))
            elif expression.ASTOP == "lit":
                return expression
            elif expression.is_one() or expression.is_zero():
                return ~expression
            else: raise NotImplementedError(str(expression))
        return recurse(function.to_dnf())

    @staticmethod
    def products(expression):
        if expression.ASTOP == "or":
            yield from expression.xs
        elif expression.ASTOP == "and":
            yield expression
        elif expression.ASTOP == "lit":
            yield expression
        elif expression.is_one():
            yield expression
        elif expression.is_zero():
            pass
        else: raise NotImplementedError(str(expression))

    @staticmethod
    def literals(product):
        if product.ASTOP == "and":
            yield from product.xs
        elif product.ASTOP == "lit":
            yield product
        elif product.ASTOP == "or":
            raise ValueError("Invalid input")
        elif product.is_one():
            yield product
        elif product.is_zero():
            pass
        else: raise NotImplementedError(str(product))
