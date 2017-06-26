#!/usr/bin/env python3

import synth

class DualProductConstruction(synth.base.Synth):
    def synth(self):
        isop_function = self.function_container.isop_function
        isop_dual = self.function_container.isop_dual
        column_sets = [set(synth.Function.literals(p))
                       for p in synth.Function.products(isop_function)]
        row_sets = [set(synth.Function.literals(p))
                    for p in synth.Function.products(isop_dual)]
        return [[next(iter(row & column)) for column in column_sets]
                for row in row_sets]
