#!/usr/bin/env python3


import subprocess
import hypothesis
import hypothesis.strategies as st
import pyeda.boolalg.expr as expr

import synth


def solver_exists(name):
    if name in ("libcryptominisat", "libminisat"): return True
    try: subprocess.run([name], input="", stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    except FileNotFoundError: return False
    except PermissionError: return False
    return True


@st.composite
def literals(draw):
    variables = tuple(expr.exprvar(x) for x in "abcdef")
    variable = draw(st.sampled_from(variables))
    negated = draw(st.booleans())
    if negated: return ~variable
    return variable


@st.composite
def functions(draw, children):
    operators = (expr.And, expr.Or)
    operator = draw(st.sampled_from(operators))
    return operator(*draw(children))


@st.composite
def complex_functions(draw, min_vars=2, max_vars=5):
    support_constr = lambda f: min_vars <= len(f.support) <= max_vars
    not_const = lambda f: not (f.is_one() or f.is_zero())
    extend = lambda c: functions(st.lists(c, min_size=2, max_size=4))

    recursive_functions = st.recursive(literals(), extend)
    return draw(recursive_functions.filter(support_constr).filter(not_const))


@st.composite
def function_and_bounds(draw, min_bound=None, max_bound=None):
    function = synth.Function(None, draw(complex_functions()))
    solution = synth.DualProductConstruction(function).synth()
    hypothesis.assume(len(solution) != 0)
    (m, n) = (len(solution), len(solution[0]))
    hypothesis.assume(m > 1 and n > 0)
    if min_bound is not None: hypothesis.assume(m * n >= min_bound)
    if max_bound is not None: hypothesis.assume(m * n <= max_bound)
    return (function, (m, n))


@st.composite
def lattice_dimensions_with_lower_bound(draw):
    boolean = st.booleans()
    integers = st.integers(min_value=1, max_value=21)
    (m, n) = draw(st.tuples(integers, integers))
    dimensions = sorted(sorted(draw(st.booleans()) for _ in range(n))
                        for _ in range(m))
    dimensions[-1][-1] = True
    (min_m, min_n) = min(((m, n) for (m, row) in enumerate(dimensions, 1)
                        for (n, value) in enumerate(row, 1)
                        if value), key=lambda x: x[0]*x[1])
    lower_bound = draw(st.tuples(st.integers(min_value=1, max_value=min_m),
                                 st.integers(min_value=1, max_value=min_n)))
    return (lower_bound, dimensions)


def adjacent(m, n, i, j):
    for i_ in range(1, m + 1):
        for j_ in range(1, n + 1):
            if abs(i + 1 - i_) + abs(j + 1 - j_) == 1:
                yield (i_ - 1, j_ - 1)


def path_in_lattice(lattice, inputs):
    def active(x):
        if x is True: return True
        if x is False: return False
        return x in inputs

    is_active = [[active(x) for x in row] for row in lattice]

    (m, n) = (len(lattice), len(lattice[0]))
    reachable = [[False for _ in range(n)] for _ in range(m)]
    for j in range(n): reachable[0][j]= True

    to_visit = set((0, j) for j in range(n))
    visited = set()

    while to_visit:
        (i, j) = to_visit.pop()
        visited.add((i, j))
        if is_active[i][j]:
            for (i_, j_) in adjacent(m, n, i, j):
                if (i_, j_) not in visited:
                    reachable[i_][j_] = True
                    to_visit.add((i_, j_))

    return any(reachable[-1][j] and is_active[-1][j] for j in range(n))


def lattice_equivalent(function, lattice, assignment):
    evaluated = function.compose(assignment).simplify().is_one()
    inputs = [x if v else ~x for (x, v) in assignment.items()]
    path_exists = path_in_lattice(lattice, inputs)
    return evaluated == path_exists


def test_lattice(function, lattice):
    return all(lattice_equivalent(function.function, lattice, assignment)
               for assignment in function.function.iter_domain())
