from synth.constraint import cardnet

from synth.constraint.sequential_counter import at_most_one
from synth.constraint.sequential_counter import at_least_one
from synth.constraint.sequential_counter import equals_one


def at_most(inputs, p, equivalent=None):
    if p == 1: yield from at_most_one(inputs, equivalent)
    else: yield from cardnet.at_most(inputs, p, equivalent)

def at_least(inputs, p, equivalent=None):
    if p == 1: yield from at_least_one(inputs, equivalent)
    else: yield from cardnet.at_least(inputs, p, equivalent)

def equals(inputs, p, equivalent=None):
    if p == 1: yield from equals_one(inputs, equivalent)
    else: yield from cardnet.equals(inputs, p, equivalent)
