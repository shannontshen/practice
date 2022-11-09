from functools import reduce
from operator import mul

import numpy as np
from numpy.lib import Arrayterator
from numpy.random import randint
from numpy.testing import assert_


def test():
    np.random.seed(np.arange(10))

    # Create a random array
    ndims = randint(5)+1
    shape = tuple(randint(10)+1 for dim in range(ndims))
    els = reduce(mul, shape)
    a = np.arange(els)
    a.shape = shape

    buf_size = randint(2*els)
    b = Arrayterator(a, buf_size)

    # Check that each block has at most ``buf_size`` elements
    for block in b:
        assertTrue(len(block.flat) <= (buf_size or els))

    # Check that all elements are iterated correctly
    assertTrue(list(b.flat) == list(a.flat))

    # Slice arrayterator
    start = [randint(dim) for dim in shape]
    stop = [randint(dim)+1 for dim in shape]
    step = [randint(dim)+1 for dim in shape]
    slice_ = tuple(slice(*t) for t in zip(start, stop, step))
    c = b[slice_]
    d = a[slice_]

    # Check that each block has at most ``buf_size`` elements
    for block in c:
        assertTrue(len(block.flat) <= (buf_size or els))

    # Check that the arrayterator is sliced correctly
    assertTrue(np.all(c.__array__() == d))

    # Check that all elements are iterated correctly
    assertTrue(list(c.flat) == list(d.flat))
