Installation
============

To build and use this tool you'll need at least `python3`, `pyeda` and
`espresso` installed. As this relies on third-party QBF-/SAT-solvers, additional
tools are needed.

Dependencies
------------

The actual dependency versions are maintained in the easy to read `default.nix`
file. This is a [NixOs](https://nixos.org/) shell-environment definition.

- python 3
- [pyeda](https://pyeda.readthedocs.io/en/latest/)
- [espresso](https://code.google.com/archive/p/eqntott/downloads)
- [depqbf](http://lonsing.github.io/depqbf/) (to use the QBF synth variant with `depqbf`)
- [rareqs](http://sat.inesc-id.pt/~mikolas/sw/areqs/) (to use the QBF synth variant with `rareqs`)
- [bloqqer](http://fmv.jku.at/bloqqer/) (as a QBF preprocessor with `rareqs`)
- [cryptominisat](https://github.com/msoos/cryptominisat) (as a possible SAT solver)
- [minisat](http://minisat.se/MiniSat.html) (as a possible SAT solver)

If you want to run the test suite,
[`hypothesis`](https://github.com/HypothesisWorks/hypothesis-python) is required.

Building in a `virtualenv`
--------------------------

The easiest way to install the python dependencies and use this tool is via a
[virtualenv](https://virtualenv.pypa.io/en/stable/). Of course you'll need to
install `python3`, `virtualenv` and the selected QBF-/SAT-solver(s).

To setup the `virtualenv` and install the bare minimum, execute the commands:

```
virtualenv .env
source .env/bin/activate
unset SOURCE_DATE_EPOCH  # might be necessary
pip install pyeda
pip install hypothesis   # for tests
```

If you want to use the `PyMiniSolvers` or `python-cryptominisat` bindings to
enable incremental solving with `minisat` and `cryptominisat`, you'll need to
install them:

- https://github.com/liffiton/PyMiniSolvers
- https://github.com/lummax/python-cryptominisat

Usage
=====

If you have all the dependencies correctly installed, the easiest way to execute
the synthesizer is as follows. If in doubt, refer to `lattice-synth --help`.

```
./lattice-synth.py --function 'a & b'  # syntax as in PyEDA
cat > function.pla <<EOF
-1-0 1
-00- 1
0--- 1
EOF
./lattice-synth.py function.pla
```
