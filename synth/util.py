#!/usr/bin/env python3

import functools

def assert_cnf(function):
    msg = "{}: {} is not in CNF"
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        for clause in function(*args, **kwargs):
            assert clause.is_cnf(), msg.format(function.__name__,
                                               clause)
            yield clause
    return wrapper


