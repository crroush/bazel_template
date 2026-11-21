"""A small Python API backed by the shared C++ greeting library."""

import numpy as np

from ._greeting import greet

__all__ = ["greet", "greet_many"]

_greet_array = np.vectorize(greet, otypes=[str])


def greet_many(names):
    """Return a NumPy array of C++ greetings with the same shape as names."""
    return _greet_array(names)
