#!/usr/bin/env python3

import sys
import csv
import argparse

import pyeda.boolalg.expr

import synth
import synth.irredundant
import synth.reachability
from synth.search import Simple
from synth.search import MinimizedSplit
from synth.search import BinaryPartition
from synth.search import Saddleback

SAT_SOLVER = ("libcryptominisat", "libminisat") + tuple(synth.sat.Dimacs.SOLVER)

def parse_args():

    def upper_bound(argument):
        (m, n) = argument.split(",", 1)
        return (int(m), int(n))

    parser = argparse.ArgumentParser()
    parser.add_argument("--sat-solver", type=str.lower, default="libminisat",
                        choices=SAT_SOLVER,
                        help="Which SAT solver to use (default: libminisat).")
    parser.add_argument("--list-sat-solver", action="store_true",
                        help="Print available SAT solver.")
    parser.add_argument("--qbf-solver", choices=synth.sat.QDimacs.SOLVER,
                        default="depqbf", type=str.lower,
                        help="Which QBF solver to use (default: depqbf).")
    parser.add_argument("--list-qbf-solver", action="store_true",
                        help="Print available QBF solver.")
    parser.add_argument("--synthesizer", choices=("qbf", "qbfu", "cegar"),
                        action="append", default=[], type=str.lower,
                        help="Use this synthesizer technique (default: all).")
    parser.add_argument("--list-synthesizer", action="store_true",
                        help="Print available synthesizer.")
    parser.add_argument("--search", default="simple",
                        choices=("simple", "split", "partition", "saddleback"),
                        help="Use this search technique (default: simple).")
    parser.add_argument("--list-search", action="store_true",
                        help="Print available search techniques.")
    parser.add_argument("--method", default="irredundant",
                        choices=("irredundant", "reachability"),
                        help="Use this synth method (default: irredundant).")
    parser.add_argument("--list-method", action="store_true",
                        help="Print available synth methods.")
    parser.add_argument("--dump-csv", action="store_true",
                        help="Write statistics to as CSV to stdout.")
    parser.add_argument("--dump-csv-header", action="store_true",
                        help="Write CSV header to stdout.")
    parser.add_argument("--dump-dimacs", action="store_true",
                        help=("Write (q)dimacs CNF to file"
                              "(requires dimacs based solver)."))
    parser.add_argument("--no-decode", action="store_true",
                        help="Don't decode lattice solution.")
    parser.add_argument("--print-reference", action="store_true",
                        help="Print the reference DP construction.")
    parser.add_argument("--function", action="append",
                        type=pyeda.boolalg.expr.expr, default=[],
                        help="Parsable boolean functions to synthesize.")
    parser.add_argument("--upper-bound", type=upper_bound,
                        help="Lattice size for `simple` search (format `m,n`)")
    parser.add_argument("path", nargs="*",
                        help="Path to function definition in *.pla format.")
    arguments = parser.parse_args()

    if arguments.upper_bound and not arguments.search == "simple":
        parser.error("--upper-bound may only be given with --search=simple")

    return arguments


def select_synthesizer(search, synthesizer, arguments):
    module = synth.irredundant if arguments.method == "irredundant" \
                else synth.reachability

    search_class = {"simple": Simple, "split": MinimizedSplit,
                    "partition": BinaryPartition,
                    "saddleback": Saddleback}.get(search)
    selected = (("QBF", search_class.with_qbf(module, arguments)),
                ("QBFU", search_class.with_qbf_unfolded(module, arguments)),
                ("CEGAR", search_class.with_cegar(module, arguments)))
    return tuple((n, s) for (n, s) in selected if n.lower() in synthesizer) \
        or selected


def run_search(function, selected_synthesizer):
    (m, n) = function.naive_lattice_bounds()
    lower_bound = function.lower_bound()

    for (name, synthesizer_cls) in selected_synthesizer:
        synthesizer = synthesizer_cls(function)
        result = {"synthesizer": name, "solver": synthesizer_cls.solver,
                  "path": function.path, "upper_height": m, "upper_width": n,
                  "lower_bound": lower_bound, "inputs": function.inputs()}

        result.update(synthesizer.synth())
        yield result


def build_functions(arguments):
    for function in arguments.function:
        yield synth.Function(None, function)
    for path in arguments.path:
        yield synth.Function.from_path(path)


def iterate_functions(functions, arguments):
    for function in functions:
        reference = None if not arguments.print_reference else \
                    synth.DualProductConstruction(function).synth()

        synthesizer = select_synthesizer(arguments.search,
                                         arguments.synthesizer,
                                         arguments)

        for result in run_search(function, synthesizer):
            result["search"] = arguments.search
            result["method"] = arguments.method
            result["reference"] = reference
            yield result


def dump_csv(results, header=False):
    fieldnames = ["search", "method", "synthesizer", "solver", "path",
                  "upper_height", "upper_width", "time", "steps",
                  "solution_height", "solution_width", "lower_bound", "inputs",
                  "unfolding_steps", "num_variables", "num_clauses"]
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, extrasaction="ignore")
    if header: writer.writeheader()
    for row in results: writer.writerow(row)


def print_results(results):
    for row in results:
        print("{synthesizer} {path} {upper_height} {upper_width}".format(**row))
        (synth_time, steps) = (row.get("time"), row.get("steps"))
        solution = row.get("solution")
        print("Timing: {} in {} steps".format(synth_time, steps))
        if solution is None: print("No solution")
        else:
            print("Got solution: {solution_height} {solution_width}".format(**row))
            if solution is not True: print(*solution, sep="\n")
        reference = row.get("reference")
        if reference: print("DP reference:", *reference, sep="\n")
        print()


def main(*args):
    arguments = parse_args()
    if arguments.list_sat_solver:
        print(*SAT_SOLVER, sep="\n")
    elif arguments.list_qbf_solver:
        print(*synth.sat.QDimacs.SOLVER, sep="\n")
    elif arguments.list_synthesizer:
        print("qbf", "qbfu", "cegar", sep="\n")
    elif arguments.list_search:
        print("simple", "split", "partition", "saddleback", sep="\n")
    elif arguments.list_method:
        print("irredundant", "reachability", sep="\n")
    elif arguments.dump_csv_header:
        dump_csv((), header=True)
    else:
        functions = build_functions(arguments)
        results = iterate_functions(functions, arguments)
        if arguments.dump_csv: dump_csv(results)
        else: print_results(results)


if __name__ == "__main__":
    main(*sys.argv[1:])
