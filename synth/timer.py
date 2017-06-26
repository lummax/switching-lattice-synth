#!/usr/bin/env python3

import resource
import contextlib

class Timer:
    def __init__(self):
        self._elapsed = 0

    def elapsed(self):
        return self._elapsed

    @contextlib.contextmanager
    def measure(self, process=False):
        flag = resource.RUSAGE_SELF if not process else resource.RUSAGE_CHILDREN
        start = resource.getrusage(flag).ru_utime
        yield
        self._elapsed += resource.getrusage(flag).ru_utime - start
