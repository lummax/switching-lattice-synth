#!/usr/bin/env python3

import time
import itertools as it

import synth

class SearchBase(synth.base.Synth):
    def __init__(self, function, synthesizer, *args):
        super().__init__(function)
        self.synthesizer = synthesizer
        self.synthesizer_counter = 0
        self.lower_bound = self.function_container.lower_bound()
        self.upper_bound = self.function_container.naive_lattice_bounds()

    @classmethod
    def with_qbf(cls, module, arguments):
        synthesizer = module.QBFSynth.from_arguments(arguments)
        def factory(function):
            return cls(function, synthesizer, arguments.upper_bound)
        factory.solver = synthesizer.solver
        return factory

    @classmethod
    def with_qbf_unfolded(cls, module, arguments):
        synthesizer = module.QBFUnfolded.from_arguments(arguments)
        def factory(function):
            return cls(function, synthesizer, arguments.upper_bound)
        factory.solver = synthesizer.solver
        return factory

    @classmethod
    def with_cegar(cls, module, arguments):
        synthesizer = module.CegarSynth.from_arguments(arguments)
        def factory(function):
            return cls(function, synthesizer, arguments.upper_bound)
        factory.solver = synthesizer.solver
        return factory

    def _synthesize(self, timer, m, n):
        self.synthesizer_counter += 1
        return self.synthesizer(self.function_container, m, n,).synth(timer)

    def _build_result(self, solution, elapsed, steps):
        result = {"time": elapsed, "steps": steps}
        result.update(solution)
        return result


class Simple(SearchBase):
    def __init__(self, function, synthesizer, upper_bound=None):
        super().__init__(function, synthesizer)
        if upper_bound: self.upper_bound = upper_bound

    def synth(self):
        timer = synth.timer.Timer()
        old_counter = self.synthesizer_counter
        (m, n) = self.upper_bound
        solution = self._synthesize(timer, m, n)
        return self._build_result(solution, timer.elapsed(), 1)


class MinimizedSplit(SearchBase):
    def _all_configurations(self, mid, failed):
        for (m, n) in it.product(range(1, mid + 1), range(1, mid +1)):
            if m * n <= mid and n * (m + 1) > mid and (n + 1) * m > mid and \
               all(m > m_ or n > n_ for (m_, n_) in failed):
                yield (m, n)

    def synth(self):
        timer = synth.timer.Timer()
        old_counter = self.synthesizer_counter

        lower_bound = self.lower_bound
        upper_bound = self.function_container.upper_bound()

        best_solution = dict()
        failed = set()

        while lower_bound <= upper_bound:
            mid = (lower_bound + upper_bound) // 2
            found = False

            configurations = sorted(self._all_configurations(mid, failed),
                                    key=lambda x: x[0] * x[1],
                                    reverse=True)

            for (m, n) in configurations:
                result = self._synthesize(timer, m, n)
                if result.get("solution") is None:
                    failed.add((m, n))
                else:
                    best_solution = result
                    upper_bound = n * m - 1
                    found = True
                if found: break

            if not found:
                lower_bound = mid + 1

        return self._build_result(best_solution, timer.elapsed(),
                                  self.synthesizer_counter - old_counter)


class BinaryPartition(SearchBase):
    def synth(self):
        timer = synth.timer.Timer()
        old_counter = self.synthesizer_counter
        solution = self._binary_partition(timer, (1, 1), self.upper_bound)
        return self._build_result(solution, timer.elapsed(),
                                  self.synthesizer_counter - old_counter)

    def _binary_partition(self, timer, lower, upper):
        (lower_m, lower_n) = lower
        (upper_m, upper_n) = upper

        if upper_m * upper_n < self.lower_bound or \
           lower_m > upper_m or lower_n > upper_n:
            return dict()

        if upper_m * lower_n < self.lower_bound:
            return self._binary_partition(timer, (lower_m, lower_n + 1), upper)
        if lower_m * upper_n < self.lower_bound:
            return self._binary_partition(timer, (lower_m + 1, lower_n), upper)

        horizontal = upper_m - lower_m > upper_n - lower_n
        partition = self._partition_horizontal if horizontal else self._partition_vertical
        return partition(timer, lower_m, lower_n, upper_m, upper_n)

    def _partition_vertical(self, timer, lower_m, lower_n, upper_m, upper_n):
        mid_column = lower_n + (upper_n - lower_n) // 2
        row_values = [(m, mid_column) for m in range(lower_m, upper_m + 1)]
        minimum = self._binary_minimum(timer, row_values)
        parting_row = minimum.get("solution_height")

        left_lower = (parting_row, lower_n)
        left_upper = (upper_m, mid_column - 1)

        right_lower = (lower_m, mid_column + 1)
        right_upper = (parting_row - 1, upper_n)

        results = (minimum,
                   self._binary_partition(timer, left_lower, left_upper),
                   self._binary_partition(timer, right_lower, right_upper))
        return min((r for r in results if r.get("solution")), default=dict(),
                   key=lambda r: r.get("solution_height") * r.get("solution_width"))

    def _partition_horizontal(self, timer, lower_m, lower_n, upper_m, upper_n):
        mid_row = lower_m + (upper_m - lower_m) // 2
        column_values = [(mid_row, n) for n in range(lower_n, upper_n + 1)]
        minimum = self._binary_minimum(timer, column_values)
        parting_column = minimum.get("solution_width")

        left_lower = (mid_row + 1, lower_n)
        left_upper = (upper_m, parting_column - 1)

        right_lower = (lower_m, parting_column)
        right_upper = (mid_row - 1, upper_n)

        results = (minimum,
                   self._binary_partition(timer, left_lower, left_upper),
                   self._binary_partition(timer, right_lower, right_upper))
        return min((r for r in results if r.get("solution")), default=dict(),
                   key=lambda r: r.get("solution_height") * r.get("solution_width"))

    def _binary_minimum(self, timer, values):
        """
        Returns the minimal value in `values` for which a solution is possible.
        """
        def recurse(lower, upper, cache):
            mid = (lower + upper) // 2
            result = self._synthesize(timer, *values[mid])
            cache[mid] = result

            if result.get("solution") is None:
                (new_lower, new_upper) = (mid + 1, upper)
            else: (new_lower, new_upper) = (lower, mid - 1)

            if new_upper < new_lower:
                if result.get("solution") is None:
                    if new_upper == len(values) - 1:
                        (upper_m, upper_n) = values[-1]
                        return {"solution_width": upper_n + 1,
                                "solution_height": upper_m + 1,
                                "solution": None}
                    return cache.get(mid + 1)
                else: return result
            return recurse(new_lower, new_upper, cache)

        return recurse(0, len(values) - 1, dict())


class Saddleback(SearchBase):
    def synth(self):
        timer = synth.timer.Timer()
        old_counter = self.synthesizer_counter
        solution = self._saddle_back(timer, (1, 1), self.upper_bound)
        return self._build_result(solution, timer.elapsed(),
                                  self.synthesizer_counter - old_counter)

    def _saddle_back(self, timer, lower, upper):
        (lower_m, lower_n) = lower
        (upper_m, upper_n) = upper

        best_solution = dict()
        best_dimensions = upper
        (row, column) = (lower_m, upper_n)
        while row <= upper_m and column >= lower_n:
            if row * column < self.lower_bound:
                row += 1
            else:
                result = self._synthesize(timer, row, column)
                if result.get("solution") is None:
                    row += 1
                else:
                    (best_m, best_n) = best_dimensions
                    if row * column <= best_m * best_n:
                        best_solution = result
                        best_dimensions = (row, column)
                    column -= 1
        return best_solution
