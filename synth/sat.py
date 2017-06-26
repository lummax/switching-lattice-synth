#!/usr/bin/env python3

import sys
import tempfile
import subprocess
import itertools as it
import pyeda.boolalg.expr as expr

import minisolvers
import cryptominisat

import synth

class Solver:
    def __init__(self):
        self._next_literal = 1
        self._var_to_literal_map = dict()
        self._literal_to_var_map = list()

    def _add_clause(self, clause):
        raise NotImplementedError()

    def _solve(self, assumptions=None, no_decode=False, timer=None, **kwargs):
        raise NotImplementedError()

    def _encode_literal(self, literal):
        assert isinstance(literal, expr.Literal), "input is not a literal ({})".format(literal)
        negated = isinstance(literal, expr.Complement)
        var = ~literal if negated else literal

        integer = self._var_to_literal_map.setdefault(var, self._next_literal)
        if integer == self._next_literal:
            self._literal_to_var_map.append(var)
            self._next_literal += 1

        if negated: return -integer
        return integer

    def _encode_clause(self, clause):
        assert isinstance(clause, (expr.OrOp, expr.Literal)), "clause must be disjunction/literal ({})".format(clause)

        if isinstance(clause, expr.OrOp):
            return [self._encode_literal(l) for l in clause.xs]
        return [self._encode_literal(clause)]

    def _encode_cnf(self, cnf):
        assert cnf.is_cnf(), "input {} is not in CNF".format(cnf)

        if isinstance(cnf, expr.AndOp):
            yield from (self._encode_clause(c) for c in cnf.xs)
        else:
            yield self._encode_clause(cnf)

    def _encode_assumptions(self, assumptions=None):
        if assumptions is not None:
            for (var, value) in assumptions.items():
                if value: yield [self._encode_literal(var)]
                else: yield [self._encode_literal(~var)]

    def add(self, cnf):
        for clause in self._encode_cnf(cnf):
            self._add_clause(clause)

    def solve(self, of_interest=None, assumptions=None, no_decode=False,
              timer=None, simplify=False):
        sat = self._solve(assumptions=assumptions, no_decode=no_decode,
                          timer=timer, simplify=simplify)
        if sat is None: return None
        elif no_decode: return True

        solution = {self._literal_to_var_map[abs(s) - 1]: s > 0 for s in sat}
        if of_interest is None: return solution

        return {v: b for (v, b) in solution.items() if v in of_interest}


class Dimacs(Solver):
    SOLVER = {"cryptominisat5": {},
              "minisat": {"mode": "file"}}
    PREPROCESSOR = {}

    def __init__(self, executable, args=(), mode="stdin", preprocessor=None,
                 **kwargs):
        super().__init__()
        self._clauses = list()
        self._executable = executable
        self._options = list(args)
        self._mode = mode
        self._preprocessor = preprocessor

    @classmethod
    def from_known(cls, name, **kwargs):
        def factory():
            chained = dict(it.chain(Dimacs.SOLVER.get(name).items(),
                                    kwargs.items()))
            if name == "minisat":
                return DimacsMinisat(name, **chained)
            return cls(name, **chained)
        if name in Dimacs.SOLVER:
            return factory
        raise ValueError("Unknown solver {}".format(name))

    def num_clauses_variables(self):
        return (len(self._clauses), len(self._literal_to_var_map))

    def _generate_input(self, assumptions=None):
        assumption_clauses = list(self._encode_assumptions(assumptions))

        yield "p cnf {} {}".format(len(self._literal_to_var_map),
                                   len(self._clauses) + len(assumption_clauses))
        for clause in self._clauses:
            yield " ".join(str(x) for x in clause) + " 0"
        for clause in assumption_clauses:
            yield " ".join(str(x) for x in clause) + " 0"

    def _parse_output(self, output, no_decode=False):
        result = (l for l in output.splitlines() if not l.startswith("c"))
        answer = (line.split()[1:] for line in result if line.startswith("v"))
        solution = list(it.chain.from_iterable(answer))
        if not solution: return None
        elif no_decode: return True
        return [int(x) for x in solution[:-1]]

    def _add_clause(self, clause):
        self._clauses.append(clause)

    def _solve(self, assumptions=None, no_decode=False, timer=None, **kwargs):
        command = [self._executable] + self._options
        dimacs = "\n".join(self._generate_input(assumptions))
        if self._mode == "stdin":
            if self._preprocessor:
                dimacs = self._run_preprocessor(dimacs, timer=timer)
            return self._run_solver(command, dimacs, no_decode=no_decode,
                                    timer=timer)
        else:
            with tempfile.NamedTemporaryFile(mode="w") as fob:
                if self._preprocessor:
                    dimacs = self._run_preprocessor(dimacs, timer=timer)
                print(dimacs, end="", file=fob, flush=True)
                command.append(fob.name)
                return self._run_solver(command, None, no_decode=no_decode,
                                        timer=timer)

    def _run_solver(self, command, input, no_decode=False, timer=None):
        timer = timer or synth.timer.Timer()
        with timer.measure(process=True):
            completed = subprocess.run(command, input=input,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       universal_newlines=True)

        return self._parse_output(completed.stdout, no_decode=no_decode)

    def _run_preprocessor(self, input, timer=None):
        timer = timer or synth.timer.Timer()
        preprocessor = self.PREPROCESSOR.get(self._preprocessor, {})
        command = [self._preprocessor] + list(preprocessor.get("args", ()))
        with timer.measure(process=True):
            completed = subprocess.run(command, input=input,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       universal_newlines=True)
        if len(completed.stdout.splitlines()) == 1: return input
        return completed.stdout

    def print_dimacs(self, file=sys.stdout):
        literal_to_var = list(enumerate(self._literal_to_var_map, 1))
        for index in range(0, len(literal_to_var), 3):
            print("c", literal_to_var[index:index + 3], file=file)
        for line in self._generate_input():
            print(line, file=file)


class DimacsMinisat(Dimacs):
    def _parse_output(self, output, no_decode=False):
        (sat, *model) = output.splitlines()
        if sat != "SAT": return None
        elif no_decode: return True
        return [int(x) for line in model for x in line.split()]

    def _run_solver(self, command, input, no_decode=False, timer=None):
        timer = timer or synth.timer.Timer()
        with tempfile.NamedTemporaryFile() as fob:
            command.append(fob.name)
            with timer.measure(process=True):
                completed = subprocess.run(command, input=input,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           universal_newlines=True)
            fob.seek(0)
            return self._parse_output(fob.read().decode(), no_decode=no_decode)

    def print_dimacs(self, file=sys.stdout):
        literal_to_var = list(enumerate(self._literal_to_var_map, 1))
        for index in range(0, len(literal_to_var), 3):
            print("c", literal_to_var[index:index + 3], file=file)
        for line in self._generate_input():
            print(line, file=file)


class QDimacs(Dimacs):
    SOLVER = {"depqbf": {"args": ("--qdo",)},
              "rareqs": {"preprocessor": "bloqqer"}}
    PREPROCESSOR = {"bloqqer": {"args": ("--partial-assignment",)}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._quant_sets = list()

    @classmethod
    def from_known(cls, name, **kwargs):
        def factory():
            chained = dict(it.chain(QDimacs.SOLVER.get(name).items(),
                                    kwargs.items()))
            return cls(name, **chained)
        if name in QDimacs.SOLVER:
            return factory
        raise ValueError("Unknown solver {}".format(name))

    def _generate_input(self, assumptions=None):
        assumption_clauses = list(self._encode_assumptions(assumptions))

        yield "p cnf {} {}".format(len(self._literal_to_var_map),
                                   len(self._clauses) + len(assumption_clauses))

        not_quantified = set(self._literal_to_var_map)

        for (kind, literals) in self._quant_sets:
            quantified = set(self._literal_to_var_map[abs(x) - 1] for x in literals)
            not_quantified.difference_update(quantified)
            yield kind + " " + " ".join(str(x) for x in literals) + " 0"

        if not_quantified and self._quant_sets and self._quant_sets[-1][0] != "e":
            literals = [self._encode_literal(x) for x in not_quantified]
            yield "e " + " ".join(str(x) for x in literals) + " 0"

        for clause in self._clauses:
            yield " ".join(str(x) for x in clause) + " 0"
        for clause in assumption_clauses:
            yield " ".join(str(x) for x in clause) + " 0"

    def _parse_output(self, output, no_decode=False):
        result = [l for l in output.splitlines() if not l.startswith("c")]
        try: solution = next(line for line in result if line.startswith("s"))
        except StopIteration: return None

        (_s, _cnf, sat) = solution.split()[:3]
        if sat != "1": return None

        answer = [x for line in result if line.startswith("V")
                  for x in line.split()]
        if not answer: return None
        elif no_decode: return True
        return [int(x) for x in answer if x not in ("V", "0")]

    def exists(self, variables):
        assert not self._quant_sets or self._quant_sets[-1][0] != "e"
        literals = [abs(self._encode_literal(l)) for l in variables]
        self._quant_sets.append(("e", literals))

    def forall(self, variables):
        assert not self._quant_sets or self._quant_sets[-1][0] != "a"
        literals = [abs(self._encode_literal(l)) for l in variables]
        self._quant_sets.append(("a", literals))


class Minisat(Solver):
    def __init__(self):
        super().__init__()
        self._solver = minisolvers.MinisatSolver()

    def num_clauses_variables(self):
        return (self._solver.nclauses(), self._solver.nvars())

    def _add_clause(self, clause):
        max_var = max(abs(x) for x in clause)
        if max_var > self._solver.nvars():
            for _ in range(max_var - self._solver.nvars()):
                self._solver.new_var()
        self._solver.add_clause(clause)

    def _solve(self, assumptions=None, no_decode=False, timer=None,
               simplify=False, **kwargs):
        timer = timer or synth.timer.Timer()
        assumption_clauses = self._encode_assumptions(assumptions)
        assumptions_flat = list(it.chain.from_iterable(assumption_clauses))
        with timer.measure():
            if simplify: self._solver.simplify()
            sat = self._solver.solve(assumptions=assumptions_flat)
        if not sat: return None
        elif no_decode: return True
        solution = self._solver.get_model()
        return [i if x else -i for (i, x) in enumerate(solution, 1)]


class Cryptominisat(Solver):
    def __init__(self):
        super().__init__()
        self._solver = cryptominisat.Solver(no_simplify_at_startup=True)

    def num_clauses_variables(self):
        return (0, 0)

    def _add_clause(self, clause):
        self._solver.add_clause(clause)

    def _solve(self, assumptions=None, no_decode=False, timer=None, simplify=False,
               **kwargs):
        timer = timer or synth.timer.Timer()
        assumption_clauses = self._encode_assumptions(assumptions)
        assumptions_flat = list(it.chain.from_iterable(assumption_clauses))
        with timer.measure():
            if simplify: self._solver.simplify(assumptions=assumptions_flat)
            (sat, solution) = self._solver.solve(assumptions=assumptions_flat)
        if not sat: return None
        elif no_decode: return True
        return [i if x else -i for (i, x) in enumerate(solution[1:], 1)]
