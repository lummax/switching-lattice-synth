#!/usr/bin/env python3

import itertools as it
import pyeda.boolalg.expr as expr

from synth.util import assert_cnf

class Cardnet:
    _counter = it.count()

    @staticmethod
    def _next_aux(name=None, index=None):
        count = next(Cardnet._counter)
        names = ("cardnet", name) if name else "cardnet"
        indices = (index, count) if index else count
        return expr.exprvar(names, indices)

    @assert_cnf
    def _merger_basic_clauses(self, c1, c2, sequence_a, sequence_b):
        (a, b) = sequence_a + sequence_b
        yield expr.Or(~a, ~b, c2)
        yield expr.Or(~a, c1)
        yield expr.Or(~b, c1)

    @assert_cnf
    def _merger_recursive_clauses(self, d, e, c, sequence_length):
        for i in range(1, sequence_length + 1):
            yield expr.Or(~d[i], ~e[i - 1], c[2 * i])
            yield expr.Or(~d[i], c[2 * i - 1])
            yield expr.Or(~e[i - 1], c[2 * i - 1])

    def _h_merger(self, sequence_a, sequence_b):
        assert len(sequence_a) == len(sequence_b), "unequal lengths"
        assert len(sequence_a) > 0, "sequence_a of length 0"
        assert len(sequence_b) > 0, "sequence_b of length 0"

        seq_length = len(sequence_a)
        if seq_length == 1:
            (c1, c2) = (self._next_aux("hm_c", 1), self._next_aux("hm_c", 2))
            clauses = self._merger_basic_clauses(c1, c2, sequence_a, sequence_b)
            return ((c1, c2), clauses)

        (fst_vars, fst_cls) = self._h_merger(sequence_a[0::2], sequence_b[0::2])
        (snd_vars, snd_cls) = self._h_merger(sequence_a[1::2], sequence_b[1::2])
        (d, e) = (tuple(fst_vars), tuple(snd_vars))
        c = tuple(self._next_aux("hm_c", i + 1) for i in range(2 * seq_length + 1))

        mrg_vars = (d[0],) + c[1:2 * seq_length - 1] + (e[-1],)
        mrg_cls = self._merger_recursive_clauses(d, e, c, seq_length - 1)

        msg =  "must exactly return {} variables (is {})"
        result_len = 2 * seq_length
        assert result_len == len(mrg_vars), msg.format(result_len, len(mrg_vars))
        return (mrg_vars, it.chain(fst_cls, snd_cls, mrg_cls))

    def _half_sorter(self, sequence):
        seq_length = len(sequence)
        assert seq_length >= 2, "sequence must be length >= 2"

        if seq_length == 2:
            (a, b) = sequence
            (var, cls) = self._h_merger((a,), (b,))
            msg =  "must exactly return {} variables (is {})"
            assert seq_length == len(var), msg.format(seq_length, len(var))
            return (var, cls)

        (fst_vars, fst_cls) = self._half_sorter(sequence[:seq_length // 2])
        (snd_vars, snd_cls) = self._half_sorter(sequence[seq_length // 2:])
        (mrg_vars, mrg_cls) = self._h_merger(fst_vars, snd_vars)

        msg =  "must exactly return {} variables (is {})"
        assert seq_length == len(mrg_vars), msg.format(seq_length, len(mrg_vars))
        return (mrg_vars, it.chain(fst_cls, snd_cls, mrg_cls))

    def _s_merger(self, sequence_a, sequence_b):
        assert len(sequence_a) == len(sequence_b), "unequal lengths"
        assert len(sequence_a) > 0, "sequence_a of length 0"
        assert len(sequence_b) > 0, "sequence_b of length 0"

        seq_length = len(sequence_a)
        if seq_length == 1:
            (c1, c2) = (self._next_aux("sm_c", 1), self._next_aux("sm_c", 1))
            clauses = self._merger_basic_clauses(c1, c2, sequence_a, sequence_b)
            return ((c1, c2), clauses)

        (fst_vars, fst_cls) = self._s_merger(sequence_a[0::2], sequence_b[0::2])
        (snd_vars, snd_cls) = self._s_merger(sequence_a[1::2], sequence_b[1::2])
        (d, e) = (tuple(fst_vars), tuple(snd_vars))
        c = tuple(self._next_aux("sm_c", i + 1) for i in range(seq_length + 1))

        mrg_vars = (d[0],) + c[1:]
        mrg_cls = self._merger_recursive_clauses(d, e, c, seq_length // 2)

        msg =  "must exactly return {} variables (is {})"
        result_len = len(mrg_vars)
        assert seq_length + 1 == result_len, msg.format(seq_length + 1, result_len)
        return (mrg_vars, it.chain(fst_cls, snd_cls, mrg_cls))

    def _cardnet(self, variables, k):
        assert len(variables) >= k, "variables must be length >= k = {}".format(k)

        num_variables = len(variables)
        if num_variables == k:
            (var, cls) = self._half_sorter(variables)
            msg =  "must exactly return k = {} variables (is {})"
            assert len(var) == k, msg.format(k, len(var))
            return (var, cls)

        (fst_vars, fst_cls) = self._cardnet(variables[:k], k)
        (snd_vars, snd_cls) = self._cardnet(variables[k:], k)
        (mrg_vars, mrg_cls) = self._s_merger(fst_vars, snd_vars)

        msg =  "must exactly return k = {} variables (is {})"
        assert len(mrg_vars) - 1 == k, msg.format(k, len(mrg_vars) - 1)
        return (mrg_vars[:-1], it.chain(fst_cls, snd_cls, mrg_cls))

    def cardnet(self, variables, p):
        assert 0 <=  p, "p must not be negative ({})".format(p)
        k = 2 if p < 1 else 1 << p.bit_length()

        num_variables = len(variables)
        if num_variables % k == 0: add_var = 0
        else: add_var = k * (num_variables // k + 1) - num_variables
        additional_vars = [self._next_aux("a", i) for i in range(1, add_var + 1)]

        return self._cardnet(list(variables) + additional_vars, k)

@assert_cnf
def at_most(inputs, p, equivalent=None):
    assert inputs, "inputs must not be empty"
    (variables, clauses) = Cardnet().cardnet(inputs, p)
    condition = ~variables[p]
    yield from clauses
    if equivalent is None:
        yield condition
    else:
        yield expr.Implies(equivalent, condition).to_cnf()
        yield expr.Implies(condition, equivalent).to_cnf()

@assert_cnf
def at_least(inputs, p, equivalent=None):
    assert inputs, "inputs must not be empty"
    yield from at_most([~i for i in inputs],
                       len(inputs) - p,
                       equivalent)

@assert_cnf
def equals(inputs, p, equivalent=None):
    assert inputs, "inputs must not be empty"
    yield from at_most(inputs, p, equivalent)
    yield from at_least(inputs, p, equivalent)
