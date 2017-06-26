#!/usr/bin/env python3

import sys
import operator
import unittest
import hypothesis

from .util import lattice_dimensions_with_lower_bound

from synth.search import Simple
from synth.search import MinimizedSplit
from synth.search import BinaryPartition
from synth.search import Saddleback

class DummyFunction:
    def __init__(self, lower_bounds, upper_bounds):
        self._lower_bounds = lower_bounds
        self._upper_bounds = upper_bounds
        self.function = self

    def naive_lattice_bounds(self): return self._upper_bounds
    def lower_bound(self): return operator.mul(*self._lower_bounds)
    def upper_bound(self): return operator.mul(*self._upper_bounds)


class DummySynthesizer:
    def __init__(self, dimensions): self._dimensions = dimensions
    def __call__(self, _function, m, n): (self.m, self.n) = (m, n); return self
    def _get(self, m, n):
        try: return self._dimensions[m - 1][n - 1]
        except IndexError:
            if m > n: return self._get(m - 1, n)
            else: return self._get(m, n - 1)

    def synth(self, *args):
        if self._get(self.m, self.n):
            return {"solution": True, "solution_height": self.m,
                    "solution_width": self.n}
        return dict()


class SearchBase:
    @hypothesis.given(lattice_dimensions_with_lower_bound())
    def test_search(self, dimensions_and_lower_bound):
        (lower_bound, dimensions) = dimensions_and_lower_bound
        upper_bound = (len(dimensions), len(dimensions[0]))
        minimal_dim = min(((m, n) for (m, row) in enumerate(dimensions, 1)
                           for (n, value) in enumerate(row, 1)
                            if value), key=lambda x: x[0]*x[1])

        function = DummyFunction(lower_bound, upper_bound)
        synthesizer = DummySynthesizer(dimensions)

        result = self.SEARCH(function, synthesizer).synth()
        self.assertIsNotNone(result.get("solution"))

        result_dim = (result.get("solution_height"), result.get("solution_width"))
        self.assertEqual(operator.mul(*minimal_dim), operator.mul(*result_dim))


thismodule = sys.modules[__name__]

# MinimizedSplit is broken
for search in (Saddleback, BinaryPartition):
    class_name = "Test{}Search".format(search.__name__)
    clazz = type(class_name, (SearchBase, unittest.TestCase), {"SEARCH": search})
    setattr(thismodule, class_name, clazz)


if __name__ == '__main__':
    unittest.main()
