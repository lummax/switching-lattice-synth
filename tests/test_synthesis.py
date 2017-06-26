#!/usr/bin/env python3

import sys
import unittest
import hypothesis

from .util import solver_exists
from .util import test_lattice
from .util import complex_functions
from .util import function_and_bounds

import synth
import synth.irredundant
import synth.reachability


class TestDualProductConstruction(unittest.TestCase):
    @hypothesis.given(complex_functions(min_vars=2))
    def test_dp_construction(self, bool_function):
        function = synth.Function(None, bool_function)
        solution = synth.DualProductConstruction(function).synth()
        hypothesis.assume(len(solution) != 0)
        self.assertTrue(test_lattice(function, solution))


class SynthBase:
    def synthesizer(self, function, m, n, no_decode=False):
        method = self.METHOD.with_solver(self.SOLVER, no_decode)
        return method(function, m, n)

    @hypothesis.given(function_and_bounds())
    def test_synthesis_no_decode(self, function_bounds):
        (function, (m, n)) = function_bounds
        solution = self.synthesizer(function, m, n, True).synth().get("solution")
        self.assertIsNotNone(solution)
        self.assertTrue(solution)


class SynthBaseExtended(SynthBase):
    @hypothesis.given(function_and_bounds())
    def test_synthesis(self, function_bounds):
        (function, (m, n)) = function_bounds
        solution = self.synthesizer(function, m, n).synth().get("solution")
        self.assertIsNotNone(solution)
        self.assertTrue(test_lattice(function, solution))


thismodule = sys.modules[__name__]
modules = (("irredundant", synth.irredundant),
           ("reachability", synth.reachability))

for solver in ("libminisat", ): #synth.sat.Dimacs.SOLVER:
    if solver_exists(solver):
        for (method_name, method_module) in modules:
            class_name = "TestQBFUnfolded{}{}".format(solver.capitalize(),
                                                      method_name.capitalize())
            clazz = type(class_name, (SynthBaseExtended, unittest.TestCase),
                        {"METHOD": method_module.QBFUnfolded, "SOLVER": solver})
            setattr(thismodule, class_name, clazz)

for solver in ("libminisat", ): #synth.sat.Dimacs.SOLVER:
    if solver_exists(solver):
        for (method_name, method_module) in modules:
            class_name = "TestCegarSynth{}{}".format(solver.capitalize(),
                                                      method_name.capitalize())
            clazz = type(class_name, (SynthBaseExtended, unittest.TestCase),
                        {"METHOD": method_module.CegarSynth, "SOLVER": solver})
            setattr(thismodule, class_name, clazz)

if solver_exists("depqbf"):
    for (method_name, method_module) in modules:
        class_name = "TestQBFSynth{}{}".format("depqbf".capitalize(),
                                               method_name.capitalize())
        clazz = type(class_name, (SynthBaseExtended, unittest.TestCase),
                    {"METHOD": method_module.QBFSynth, "SOLVER": "depqbf"})
        setattr(thismodule, class_name, clazz)

if solver_exists("rareqs"):
    for (method_name, method_module) in modules:
        class_name = "TestQBFSynth{}{}".format("rareqs".capitalize(),
                                               method_name.capitalize())
        clazz = type(class_name, (SynthBase, unittest.TestCase),
                    {"METHOD": method_module.QBFSynth, "SOLVER": "rareqs"})
        setattr(thismodule, class_name, clazz)

if __name__ == '__main__':
    unittest.main()
