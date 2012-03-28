"""
The pad.py module contains a group of functions to pad values onto the edges
of an n-dimensional array.
"""

import numpy as np

__all__ = [
           'pad_minimum',
           'pad_maximum',
           'pad_mean',
           'pad_median',
           'pad_linear_ramp',
           'pad_reflect',
           'pad_constant',
           'pad_wrap',
           'pad_edge',
           'pad_symmetric',
           ]


################################################################################
# Private utility functions.


def _create_vector(vector, pad_tuple, before_val, after_val):
    '''
    Private function which creates the padded vector.

    Parameters
    ----------
    vector : ndarray of rank 1, length N + pad_tuple[0] + pad_tuple[1]
        Input vector including blank padded values.  `N` is the lenth of the
        original vector.
    pad_tuple : tuple of 2 ints
        This tuple represents the (before, after) width of the padding along
        this particular iaxis.
    before_val : scalar or ndarray of rank 1, length pad_tuple[0]
        This is the value(s) that will pad the beginning of `vector`.
    after_val : scalar or ndarray of rank 1, length pad_tuple[1]
        This is the value(s) that will pad the end of the `vector`.

    Returns
    -------
    _create_vector : ndarray of rank 1, length N + pad_tuple[0] + pad_tuple[1]
        Vector with before_val and after_val replacing the blank pad values.
    '''
    vector[:pad_tuple[0]] = before_val
    if pad_tuple[1] > 0:
        vector[-pad_tuple[1]:] = after_val
    return vector


def _normalize_shape(narray, shape):
    '''
    Private function which does some checks and normalizes the possibly much
    simpler representations of 'pad_width', 'stat_length', 'constant_values',
    'end_values'.

    Parameters
    ----------
    narray : ndarray
        Input ndarray
    shape : {sequence of N sequences(int,int), sequence(int,int),
            sequence(int,), int}, optional
        The width of padding (pad_width) or the number of elements on the edge
        of the narray used for statistics (stat_length).
        ((before_1, after_1), ... (before_N, after_N)) unique number of
        elements for each axis where `N` is rank of `narray`.
        ((before, after),) yields same before and after constants for each
        axis.
        (constant,) or int is a shortcut for before = after = constant for all
        axes.

    Returns
    -------
    _normalize_shape : int 2-tuple of tuples
        int                               => ((int, int), (int, int), ...)
        [[int1, int2], [int3, int4], ...] => ((int1, int2), (int3, int4), ...)
        ((int1, int2), (int3, int4), ...) => no change
        [[int1, int2], ]                  => ((int1, int2), (int1, int2), ...]
        ((int1, int2), )                  => ((int1, int2), (int1, int2), ...)
        [[int ,     ), )                  => ((int, int), (int, int), ...)
        ((int ,     ), )                  => ((int, int), (int, int), ...)
    '''
    normshp = None
    shapelen = len(np.shape(narray))
    if (isinstance(shape, int)):
        normshp = ((shape, shape), ) * shapelen
    elif (isinstance(shape, (tuple, list))
            and isinstance(shape[0], (tuple, list))
            and len(shape) == shapelen):
        normshp = shape
        for i in normshp:
            if len(i) != 2:
                raise ValueError("Unable to create correctly shaped tuple from %s"
                                  % (normshp,))
    elif (isinstance(shape, (tuple, list))
            and isinstance(shape[0], (int, float, long))
            and len(shape) == 1):
        normshp = ((shape[0], shape[0]), ) * shapelen
    elif (isinstance(shape, (tuple, list))
            and isinstance(shape[0], (int, float, long))
            and len(shape) == 2):
        normshp = (shape, ) * shapelen
    if normshp == None:
        raise ValueError("Unable to create correctly shaped tuple from %s"
                          % (shape,))
    return normshp


def _validate_lengths(narray, number_elements):
    '''
    Private function which does some checks and reformats pad_width and
    stat_length using _normalize_shape.

    Parameters
    ----------
    narray : ndarray
        Input ndarray
    number_elements : {sequence of N sequences(int,int), sequence(int,int),
                       sequence(int,), int}, optional
        The width of padding (pad_width) or the number of elements on the edge
        of the narray used for statistics (stat_length).
        ((before_1, after_1), ... (before_N, after_N)) unique number of
        elements for each axis.
        ((before, after),) yields same before and after constants for each
        axis.
        (constant,) or int is a shortcut for before = after = constant for all
        axes.

    Returns
    -------
    _validate_lengths : int 2-tuple of tuples
        int                               => ((int, int), (int, int), ...)
        [[int1, int2], [int3, int4], ...] => ((int1, int2), (int3, int4), ...)
        ((int1, int2), (int3, int4), ...) => no change
        [[int1, int2], ]                  => ((int1, int2), (int1, int2), ...]
        ((int1, int2), )                  => ((int1, int2), (int1, int2), ...)
        [[int ,     ), )                  => ((int, int), (int, int), ...)
        ((int ,     ), )                  => ((int, int), (int, int), ...)
    '''
    shapelen = len(np.shape(narray))
    normshp = _normalize_shape(narray, number_elements)
    for i in normshp:
        if i[0] < 0 or i[1] < 0:
            raise ValueError(
                  "Cannot have negative values in %s to represent number of elements."
                  % (number_elements,))
    return normshp


def _loop_across(array, pad_width, function, **kwds):
    '''
    Private function to prepare the data for the np.apply_along_axis command
    to move through the array.

    Parameters
    ----------
    array : array_like
        Input array to be padded.
    pad_width : {sequence of N sequences(int,int), sequence(int,int),
                 sequence(int,), int}, optional
        Number of values padded to each edge of each axis.
        ((before_1, after_1), ... (before_N, after_N)) unique pad widths for
        each axis.
        ((before, after),) yields same before and after pad for each axis.
        (pad,) or int is a shortcut for before = after = pad width for all
        axes.
        Default is 1.
    function: function
        Function applied along each axis.  Must accept a vector (rank-1 array)
        that includes empty padded values on each edge, tuple of pad_width for
        that axis, and an integer representing the axis.  Possible keywords
        are 'stat_length' (for functions that need to calculate statistics
        from the original array), 'end_values' (for pad_linear_ramp), and
        'constant_values' (for pad_constant).
    **kwds:
    stat_length : {sequence of N sequences(int,int), sequence(int,int),
                   sequence(int,), int}, optional
        Number of values at edge of each axis used to calculate the statistic
        value.
        ((before_1, after_1), ... (before_N, after_N)) unique statistic
        lengths for each axis.
        ((before, after),) yields same before and after statistic lengths for
        each axis.
        (stat_length,) or int is a shortcut for before = after = statistic
        length for all axes.
        If ``None``, will use the entire vector.
    end_values : {sequence of N sequences(int,int), sequence(int,int),
                  sequence(int,), int}, optional
        The values used for the edge of the vector and ending value of the
        linear_ramp.
        ((before_1, after_1), ... (before_N, after_N)) unique end values
        for each axis.
        ((before, after),) yields same before and after end values for each
        axis.
        (constant,) or int is a shortcut for before = after = end value for all
        axes.
    constant_values : {sequence of N sequences(int,int), sequence(int,int),
                       sequence(int,), int}, optional
        The values to set the padded values for each axis.
        ((before_1, after_1), ... (before_N, after_N)) unique pad constants
        for each axis.
        ((before, after),) yields same before and after constants for each
        axis.
        (constant,) or int is a shortcut for before = after = constant for all
        axes.

    Return
    ------
    _loop_across : ndarray with rank of array and shape of array plus
                   'pad_width's
    '''
    narray = np.array(array)
    pad_width = _validate_lengths(narray, pad_width)

    # Need to only normalize particular keywords.
    for i in kwds:
        if i == 'stat_length' and kwds[i]:
            kwds[i] = _validate_lengths(narray, kwds[i])
        if i in ['end_values', 'constant_values']:
            kwds[i] = _normalize_shape(narray, kwds[i])

    # Create a new padded array
    rank = range(len(narray.shape))
    total_dim_increase = [np.sum(pad_width[i]) for i in rank]
    offset_slices = [slice(pad_width[i][0],
                           pad_width[i][0] + narray.shape[i])
                     for i in rank]
    new_shape = np.array(narray.shape) + total_dim_increase
    newmat = np.zeros(new_shape).astype(narray.dtype)

    # Insert the original array into the padded array
    newmat[offset_slices] = narray

    # This is the core of pad_*...
    for iaxis in rank:
        np.apply_along_axis(function,
                            iaxis,
                            newmat,
                            pad_width[iaxis],
                            iaxis,
                            kwds)
    return newmat


def _create_stat_vectors(vector, pad_tuple, iaxis, kwds):
    '''
    Returns the portion of the vector required for any statistic.

    Parameters
    ----------
    vector : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Input vector that already includes empty padded values.
    pad_tuple : tuple of 2 ints
        This tuple represents the (before, after) width of the padding along
        this particular iaxis.
    iaxis : int
        The axis currently being looped across.
    kwds : keyword arguments
        Keyword arguments.  Only 'stat_length' is used.  'stat_length'
        defaults to the entire vector if not supplied.

    Return
    ------
    _create_stat_vectors : (ndarray of length stat_length[iaxis][0],
                            ndarray of length stat_length[iaxis][1]) OR
                           (ndarray of length N,
                            ndarray of length N)
        The values from the original vector that will be used to calculate the
        statistic.
    '''

    # Can't have 0 represent the end if a slice... a[1:0] doesnt' work
    pt1 = -pad_tuple[1]
    if pt1 == 0:
        pt1 = None

    # Default is the entire vector from the original array.
    sbvec = vector[pad_tuple[0]:pt1]
    savec = vector[pad_tuple[0]:pt1]

    if kwds['stat_length']:
        stat_length = kwds['stat_length'][iaxis]
        sl0 = min(stat_length[0], len(sbvec))
        sl1 = min(stat_length[1], len(savec))
        sbvec = np.arange(0)
        savec = np.arange(0)
        if pad_tuple[0] > 0:
            sbvec = vector[pad_tuple[0]:pad_tuple[0] + sl0]
        if pad_tuple[1] > 0:
            savec = vector[-pad_tuple[1] - sl1:pt1]
    return (sbvec, savec)


def _maximum(vector, pad_tuple, iaxis, kwds):
    '''
    Private function to calculate the before/after vectors for pad_maximum.

    Parameters
    ----------
    vector : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Input vector that already includes empty padded values.
    pad_tuple : tuple of 2 ints
        This tuple represents the (before, after) width of the padding along
        this particular iaxis.
    iaxis : int
        The axis currently being looped across.
    kwds : keyword arguments
        Keyword arguments.  Only 'stat_length' is used.  'stat_length'
        defaults to the entire vector if not supplied.

    Return
    ------
    _maximum : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Padded vector
    '''
    sbvec, savec = _create_stat_vectors(vector, pad_tuple, iaxis, kwds)

    bvec = np.zeros(pad_tuple[0])
    avec = np.zeros(pad_tuple[1])
    bvec[:] = max(sbvec)
    avec[:] = max(savec)
    return _create_vector(vector, pad_tuple, bvec, avec)


def _minimum(vector, pad_tuple, iaxis, kwds):
    '''
    Private function to calculate the before/after vectors for pad_minimum.

    Parameters
    ----------
    vector : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Input vector that already includes empty padded values.
    pad_tuple : tuple of 2 ints
        This tuple represents the (before, after) width of the padding along
        this particular iaxis.
    iaxis : int
        The axis currently being looped across.
    kwds : keyword arguments
        Keyword arguments.  Only 'stat_length' is used.  'stat_length'
        defaults to the entire vector if not supplied.

    Return
    ------
    _minimum : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Padded vector
    '''
    sbvec, savec = _create_stat_vectors(vector, pad_tuple, iaxis, kwds)

    bvec = np.zeros(pad_tuple[0])
    avec = np.zeros(pad_tuple[1])
    bvec[:] = min(sbvec)
    avec[:] = min(savec)
    return _create_vector(vector, pad_tuple, bvec, avec)


def _median(vector, pad_tuple, iaxis, kwds):
    '''
    Private function to calculate the before/after vectors for pad_median.

    Parameters
    ----------
    vector : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Input vector that already includes empty padded values.
    pad_tuple : tuple of 2 ints
        This tuple represents the (before, after) width of the padding along
        this particular iaxis.
    iaxis : int
        The axis currently being looped across.
    kwds : keyword arguments
        Keyword arguments.  Only 'stat_length' is used.  'stat_length'
        defaults to the entire vector if not supplied.

    Return
    ------
    _median : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Padded vector
    '''
    sbvec, savec = _create_stat_vectors(vector, pad_tuple, iaxis, kwds)

    bvec = np.zeros(pad_tuple[0])
    avec = np.zeros(pad_tuple[1])
    bvec[:] = np.median(sbvec)
    avec[:] = np.median(savec)
    return _create_vector(vector, pad_tuple, bvec, avec)


def _mean(vector, pad_tuple, iaxis, kwds):
    '''
    Private function to calculate the before/after vectors for pad_mean.

    Parameters
    ----------
    vector : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Input vector that already includes empty padded values.
    pad_tuple : tuple of 2 ints
        This tuple represents the (before, after) width of the padding along
        this particular iaxis.
    iaxis : int
        The axis currently being looped across.
    kwds : keyword arguments
        Keyword arguments.  Only 'stat_length' is used.  'stat_length'
        defaults to the entire vector if not supplied.

    Return
    ------
    _mean : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Padded vector
    '''
    sbvec, savec = _create_stat_vectors(vector, pad_tuple, iaxis, kwds)

    bvec = np.zeros(pad_tuple[0])
    avec = np.zeros(pad_tuple[1])
    bvec[:] = np.average(sbvec)
    avec[:] = np.average(savec)
    return _create_vector(vector, pad_tuple, bvec, avec)


def _constant(vector, pad_tuple, iaxis, kwds):
    '''
    Private function to calculate the before/after vectors for pad_constant.

    Parameters
    ----------
    vector : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Input vector that already includes empty padded values.
    pad_tuple : tuple of 2 ints
        This tuple represents the (before, after) width of the padding along
        this particular iaxis.
    iaxis : int
        The axis currently being looped across.
    kwds : keyword arguments
        Keyword arguments.  Need 'constant_values' keyword argument.

    Return
    ------
    _constant : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Padded vector
    '''
    nconstant = kwds['constant_values'][iaxis]
    bvec = np.zeros(pad_tuple[0])
    avec = np.zeros(pad_tuple[1])
    bvec[:] = nconstant[0]
    avec[:] = nconstant[1]
    return _create_vector(vector, pad_tuple, bvec, avec)


def _linear_ramp(vector, pad_tuple, iaxis, kwds):
    '''
    Private function to calculate the before/after vectors for pad_linear_ramp.

    Parameters
    ----------
    vector : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Input vector that already includes empty padded values.
    pad_tuple : tuple of 2 ints
        This tuple represents the (before, after) width of the padding along
        this particular iaxis.
    iaxis : int
        The axis currently being looped across.  Not used in _linear_ramp.
    kwds : keyword arguments
        Keyword arguments. Not used in _linear_ramp.

    Return
    ------
    _linear_ramp : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Padded vector
    '''
    end_values = kwds['end_values'][iaxis]
    before_delta = ((vector[pad_tuple[0]] - end_values[0])
                    / float(pad_tuple[0]))
    after_delta = ((vector[-pad_tuple[1] - 1] - end_values[1])
                   / float(pad_tuple[1]))

    before_vector = np.ones((pad_tuple[0], )) * end_values[0]
    before_vector = before_vector.astype(vector.dtype)
    for i in range(len(before_vector)):
        before_vector[i] = before_vector[i] + i * before_delta

    after_vector = np.ones((pad_tuple[1], )) * end_values[1]
    after_vector = after_vector.astype(vector.dtype)
    for i in range(len(after_vector)):
        after_vector[i] = after_vector[i] + i * after_delta
    after_vector = after_vector[::-1]

    return _create_vector(vector, pad_tuple, before_vector, after_vector)


def _reflect(vector, pad_tuple, iaxis, kwds):
    '''
    Private function to calculate the before/after vectors for pad_reflect.

    Parameters
    ----------
    vector : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Input vector that already includes empty padded values.
    pad_tuple : tuple of 2 ints
        This tuple represents the (before, after) width of the padding along
        this particular iaxis.
    iaxis : int
        The axis currently being looped across.  Not used in _reflect.
    kwds : keyword arguments
        Keyword arguments. Not used in _reflect.

    Return
    ------
    _reflect : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Padded vector
    '''
    # Can't have pad_tuple[1] be used in the slice if == to 0.
    if pad_tuple[1] == 0:
        after_vector = vector[pad_tuple[0]:None]
    else:
        after_vector = vector[pad_tuple[0]:-pad_tuple[1]]

    reverse = after_vector[::-1]

    before_vector = np.resize(
                        np.concatenate(
                        (after_vector[1:-1], reverse)), pad_tuple[0])[::-1]
    after_vector = np.resize(
                       np.concatenate(
                       (reverse[1:-1], after_vector)), pad_tuple[1])

    if kwds['reflect_type'] == 'even':
        pass
    elif kwds['reflect_type'] == 'odd':
        before_vector = 2 * vector[pad_tuple[0]] - before_vector
        after_vector = 2 * vector[-pad_tuple[-1] - 1] - after_vector
    else:
        raise ValueError("The keyword '%s' cannot have the value '%s'."
                          % ('reflect_type', kwds['reflect_type']))
    return _create_vector(vector, pad_tuple, before_vector, after_vector)


def _symmetric(vector, pad_tuple, iaxis, kwds):
    '''
    Private function to calculate the before/after vectors for pad_symmetric.

    Parameters
    ----------
    vector : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Input vector that already includes empty padded values.
    pad_tuple : tuple of 2 ints
        This tuple represents the (before, after) width of the padding along
        this particular iaxis.
    iaxis : int
        The axis currently being looped across.  Not used in _symmetric.
    kwds : keyword arguments
        Keyword arguments. Not used in _symmetric.

    Return
    ------
    _symmetric : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Padded vector
    '''
    if pad_tuple[1] == 0:
        after_vector = vector[pad_tuple[0]:None]
    else:
        after_vector = vector[pad_tuple[0]:-pad_tuple[1]]

    before_vector = np.resize(
                        np.concatenate(
                        (after_vector, after_vector[::-1])), pad_tuple[0])[::-1]
    after_vector = np.resize(
                       np.concatenate(
                       (after_vector[::-1], after_vector)), pad_tuple[1])

    if kwds['reflect_type'] == 'even':
        pass
    elif kwds['reflect_type'] == 'odd':
        before_vector = 2 * vector[pad_tuple[0]] - before_vector
        after_vector = 2 * vector[-pad_tuple[1] - 1] - after_vector
    else:
        raise ValueError("The keyword '%s' cannot have the value '%s'."
                          % ('reflect_type', kwds['reflect_type']))
    return _create_vector(vector, pad_tuple, before_vector, after_vector)


def _wrap(vector, pad_tuple, iaxis, kwds):
    '''
    Private function to calculate the before/after vectors for pad_wrap.

    Parameters
    ----------
    vector : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Input vector that already includes empty padded values.
    pad_tuple : tuple of 2 ints
        This tuple represents the (before, after) width of the padding along
        this particular iaxis.
    iaxis : int
        The axis currently being looped across.  Not used in _wrap.
    kwds : keyword arguments
        Keyword arguments. Not used in _wrap.

    Return
    ------
    _wrap : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Padded vector
    '''
    if pad_tuple[1] == 0:
        after_vector = vector[pad_tuple[0]:None]
    else:
        after_vector = vector[pad_tuple[0]:-pad_tuple[1]]

    before_vector = np.resize(after_vector[::-1], pad_tuple[0])[::-1]
    after_vector = np.resize(after_vector, pad_tuple[1])

    return _create_vector(vector, pad_tuple, before_vector, after_vector)


def _edge(vector, pad_tuple, iaxis, kwds):
    '''
    Private function to calculate the before/after vectors for pad_edge.

    Parameters
    ----------
    vector : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Input vector that already includes empty padded values.
    pad_tuple : tuple of 2 ints
        This tuple represents the (before, after) width of the padding along
        this particular iaxis.
    iaxis : int
        The axis currently being looped across.  Not used in _edge.
    kwds : keyword arguments
        Keyword arguments. Not used in _edge.

    Return
    ------
    _edge : ndarray of rank 1, length N + pad_tuple(0) + pad_tuple(1)
        Padded vector
    '''

    bvec = np.zeros(pad_tuple[0])
    avec = np.zeros(pad_tuple[1])
    bvec[:] = vector[pad_tuple[0]]
    avec[:] = vector[-pad_tuple[1] - 1]
    return _create_vector(vector, pad_tuple, bvec, avec)


################################################################################
# Public functions


def pad_maximum(array, pad_width=1, stat_length=None):
    """
    Pads with the maximum value of all or part of the vector along each axis.

    Parameters
    ----------
    array : array_like of rank N
        Input array
    pad_width : {sequence of N sequences(int,int), sequence(int,int),
                 sequence(int,), int}, optional
        Number of values padded to each edge of each axis.
        ((before_1, after_1), ... (before_N, after_N)) unique pad widths for
        each axis.
        ((before, after),) yields same before and after pad for each axis.
        (pad,) or int is a shortcut for before = after = pad width for all
        axes.
        Default is 1.
    stat_length : {sequence of N sequences(int,int), sequence(int,int),
                   sequence(int,), int}, optional
        Number of values at edge of each axis used to calculate the statistic
        value.
        ((before_1, after_1), ... (before_N, after_N)) unique statistic
        lengths for each axis.
        ((before, after),) yields same before and after statistic lengths for
        each axis.
        (stat_length,) or int is a shortcut for before = after = statistic
        length for all axes.
        Default is ``None``, to use the entire axis.

    Returns
    -------
    pad_maximum : ndarray of rank N
        Padded array.

    See Also
    --------
    pad_constant
    pad_edge
    pad_linear_ramp
    pad_mean
    pad_median
    pad_minimum
    pad_reflect
    pad_symmetric
    pad_wrap

    Notes
    -----
    For `array` with rank greater than 1, some of the padding of later axes is
    calculated from padding of previous axes.  This is easiest to think about
    with a rank 2 array where the corners of the padded array are calculated
    by using padded values from the first axes.

    Examples
    --------
    >>> a = [1, 2, 3, 4, 5]
    >>> np.lib.pad_maximum(a, (2,))
    array([5, 5, 1, 2, 3, 4, 5, 5, 5])

    >>> np.lib.pad_maximum(a, (1, 7))
    array([5, 1, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5])

    >>> np.lib.pad_maximum(a, (0, 7))
    array([1, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5])

    """
    return _loop_across(array, pad_width, _maximum, stat_length=stat_length)


def pad_minimum(array, pad_width=1, stat_length=None):
    """
    Pads with the minimum value of all or part of the vector along each axis.

    Parameters
    ----------
    array : array_like of rank N
        Input array
    pad_width : {sequence of N sequences(int,int), sequence(int,int),
                 sequence(int,), int}, optional
        Number of values padded to each edge of each axis.
        ((before_1, after_1), ... (before_N, after_N)) unique pad widths for
        each axis.
        ((before, after),) yields same before and after pad for each axis.
        (pad,) or int is a shortcut for before = after = pad width for all
        axes.
        Default is 1.
    stat_length : {sequence of N sequences(int,int), sequence(int,int),
                   sequence(int,), int}, optional
        Number of values at edge of each axis used to calculate the statistic
        value.
        ((before_1, after_1), ... (before_N, after_N)) unique statistic
        lengths for each axis.
        ((before, after),) yields same before and after statistic lengths for
        each axis.
        (stat_length,) or int is a shortcut for before = after = statistic
        length for all axes.
        Default is ``None``, to use the entire axis.

    Returns
    -------
    pad_minimum : ndarray of rank N
        Padded array.

    See Also
    --------
    pad_constant
    pad_edge
    pad_linear_ramp
    pad_maximum
    pad_mean
    pad_median
    pad_reflect
    pad_symmetric
    pad_wrap

    Notes
    -----
    For `array` with rank greater than 1, some of the padding of later axes is
    calculated from padding of previous axes.  This is easiest to think about
    with a rank 2 array where the corners of the padded array are calculated
    by using padded values from the first axes.

    Examples
    --------
    >>> a = [1, 2, 3, 4, 5, 6]
    >>> np.lib.pad_minimum(a, (2,))
    array([1, 1, 1, 2, 3, 4, 5, 6, 1, 1])

    >>> np.lib.pad_minimum(a, (4, 2))
    array([1, 1, 1, 1, 1, 2, 3, 4, 5, 6, 1, 1])

    >>> a = [[1,2], [3,4]]
    >>> np.lib.pad_minimum(a, ((3, 2), (2, 3)))
    array([[1, 1, 1, 2, 1, 1, 1],
           [1, 1, 1, 2, 1, 1, 1],
           [1, 1, 1, 2, 1, 1, 1],
           [1, 1, 1, 2, 1, 1, 1],
           [3, 3, 3, 4, 3, 3, 3],
           [1, 1, 1, 2, 1, 1, 1],
           [1, 1, 1, 2, 1, 1, 1]])

    """
    return _loop_across(array, pad_width, _minimum, stat_length=stat_length)


def pad_median(array, pad_width=1, stat_length=None):
    """
    Pads with the median value of all or part of the vector along each axis.

    Parameters
    ----------
    array : array_like of rank N
        Input array
    pad_width : {sequence of N sequences(int,int), sequence(int,int),
                 sequence(int,), int}, optional
        Number of values padded to each edge of each axis.
        ((before_1, after_1), ... (before_N, after_N)) unique pad widths for
        each axis.
        ((before, after),) yields same before and after pad for each axis.
        (pad,) or int is a shortcut for before = after = pad width for all
        axes.
        Default is 1.
    stat_length : {sequence of N sequences(int,int), sequence(int,int),
                   sequence(int,), int}, optional
        Number of values at edge of each axis used to calculate the statistic
        value.
        ((before_1, after_1), ... (before_N, after_N)) unique statistic
        lengths for each axis.
        ((before, after),) yields same before and after statistic lengths for
        each axis.
        (stat_length,) or int is a shortcut for before = after = statistic
        length for all axes.
        Default is ``None``, to use the entire axis.

    Returns
    -------
    pad_median : ndarray of rank N
        Padded array.

    See Also
    --------
    pad_constant
    pad_edge
    pad_linear_ramp
    pad_maximum
    pad_mean
    pad_minimum
    pad_reflect
    pad_symmetric
    pad_wrap

    Notes
    -----
    For `array` with rank greater than 1, some of the padding of later axes is
    calculated from padding of previous axes.  This is easiest to think about
    with a rank 2 array where the corners of the padded array are calculated
    by using padded values from the first axes.

    Examples
    --------
    >>> a = [1, 2, 3, 4, 5]
    >>> np.lib.pad_median(a, (2,))
    array([3, 3, 1, 2, 3, 4, 5, 3, 3])

    >>> np.lib.pad_median(a, (4, 0))
    array([3, 3, 3, 3, 1, 2, 3, 4, 5])

    """
    return _loop_across(array, pad_width, _median, stat_length=stat_length)


def pad_mean(array, pad_width=1, stat_length=None):
    """
    Pads with the mean value of all or part of the vector along each axis.

    Parameters
    ----------
    array : array_like of rank N
        Input array
    pad_width : {sequence of N sequences(int,int), sequence(int,int),
                 sequence(int,), int}, optional
        Number of values padded to each edge of each axis.
        ((before_1, after_1), ... (before_N, after_N)) unique pad widths for
        each axis.
        ((before, after),) yields same before and after pad for each axis.
        (pad,) or int is a shortcut for before = after = pad width for all
        axes.
        Default is 1.
    stat_length : {sequence of N sequences(int,int), sequence(int,int),
                   sequence(int,), int}, optional
        Number of values at edge of each axis used to calculate the statistic
        value.
        ((before_1, after_1), ... (before_N, after_N)) unique statistic
        lengths for each axis.
        ((before, after),) yields same before and after statistic lengths for
        each axis.
        (stat_length,) or int is a shortcut for before = after = statistic
        length for all axes.
        Default is ``None``, to use the entire axis.

    Returns
    -------
    pad_mean : ndarray of rank N
        Padded array.

    See Also
    --------
    pad_constant
    pad_edge
    pad_linear_ramp
    pad_maximum
    pad_median
    pad_minimum
    pad_reflect
    pad_symmetric
    pad_wrap

    Notes
    -----
    For `array` with rank greater than 1, some of the padding of later axes is
    calculated from padding of previous axes.  This is easiest to think about
    with a rank 2 array where the corners of the padded array are calculated
    by using padded values from the first axes.

    Examples
    --------
    >>> a = [1, 2, 3, 4, 5]
    >>> np.lib.pad_mean(a, (2,))
    array([3, 3, 1, 2, 3, 4, 5, 3, 3])

    """
    return _loop_across(array, pad_width, _mean, stat_length=stat_length)


def pad_constant(array, pad_width=1, constant_values=0):
    """
    Pads with a constant value.

    Parameters
    ----------
    array : array_like of rank N
        Input array
    pad_width : {sequence of N sequences(int,int), sequence(int,int),
                 sequence(int,), int}, optional
        Number of values padded to each edge of each axis.
        ((before_1, after_1), ... (before_N, after_N)) unique pad widths for
        each axis.
        ((before, after),) yields same before and after pad for each axis.
        (pad,) or int is a shortcut for before = after = pad width for all
        axes.
        Default is 1.
    constant_values : {sequence of N sequences(int,int), sequence(int,int),
                       sequence(int,), int}, optional
        The values to set the padded values for each axis.
        ((before_1, after_1), ... (before_N, after_N)) unique pad constants
        for each axis.
        ((before, after),) yields same before and after constants for each
        axis.
        (constant,) or int is a shortcut for before = after = constant for all
        axes.
        Default is 0.

    Returns
    -------
    pad_constant : ndarray of rank N
        Padded array.

    See Also
    --------
    pad_edge
    pad_linear_ramp
    pad_maximum
    pad_mean
    pad_median
    pad_minimum
    pad_reflect
    pad_symmetric
    pad_wrap

    Notes
    -----
    For `array` with rank greater than 1, some of the padding of later axes is
    calculated from padding of previous axes.  This is easiest to think about
    with a rank 2 array where the corners of the padded array are calculated
    by using padded values from the first axes.

    Examples
    --------
    >>> a = [1, 2, 3, 4, 5]
    >>> np.lib.pad_constant(a, (2,3), (4,6))
    array([4, 4, 1, 2, 3, 4, 5, 6, 6, 6])

    """
    return _loop_across(array,
                         pad_width,
                         _constant,
                         constant_values=constant_values)


def pad_linear_ramp(array, pad_width=1, end_values=0):
    """
    Pads with the linear ramp between end_value and the begining/end of the
    vector along each axis.

    Parameters
    ----------
    array : array_like of rank N
        Input array
    pad_width : {sequence of N sequences(int,int), sequence(int,int),
                 sequence(int,), int}, optional
        Number of values padded to each edge of each axis.
        ((before_1, after_1), ... (before_N, after_N)) unique pad widths for
        each axis.
        ((before, after),) yields same before and after pad for each axis.
        (pad,) or int is a shortcut for before = after = pad width for all
        axes.
        Default is 1.
    end_values : {sequence of N sequences(int,int), sequence(int,int),
                  sequence(int,), int}, optional
        The values used for the edge of the vector and ending value of the
        linear_ramp.
        ((before_1, after_1), ... (before_N, after_N)) unique end values
        for each axis.
        ((before, after),) yields same before and after end values for each
        axis.
        (constant,) or int is a shortcut for before = after = end value for all
        axes.
        Default is 0.

    Returns
    -------
    pad_linear_ramp : ndarray of rank N
        Padded array.

    See Also
    --------
    pad_constant
    pad_edge
    pad_maximum
    pad_mean
    pad_median
    pad_minimum
    pad_reflect
    pad_symmetric
    pad_wrap

    Notes
    -----
    For `array` with rank greater than 1, some of the padding of later axes is
    calculated from padding of previous axes.  This is easiest to think about
    with a rank 2 array where the corners of the padded array are calculated
    by using padded values from the first axes.

    Examples
    --------
    >>> a = [1, 2, 3, 4, 5]
    >>> np.lib.pad_linear_ramp(a, (2,3), (5,-4))
    array([ 5,  3,  1,  2,  3,  4,  5,  2, -1, -4])

    """
    return _loop_across(array, pad_width, _linear_ramp, end_values=end_values)


def pad_symmetric(array, pad_width=1, reflect_type='even'):
    """
    Pads with the reflection of the vector mirrored along the edge of the
    array.

    Parameters
    ----------
    array : array_like of rank N
        Input array
    pad_width : {sequence of N sequences(int,int), sequence(int,int),
                 sequence(int,), int}, optional
        Number of values padded to each edge of each axis.
        ((before_1, after_1), ... (before_N, after_N)) unique pad widths for
        each axis.
        ((before, after),) yields same before and after pad for each axis.
        (pad,) or int is a shortcut for before = after = pad width for all
        axes.
        Default is 1.
    reflect_type : str {'even', 'odd'}, optional
        The 'even' style is the default with an unaltered reflection around
        the edge value.  For the 'odd' style, the extented part of the array
        is created by subtracting the reflected values from two times the edge
        value.

    Returns
    -------
    pad_symmetric : ndarray of rank N
        Padded array.

    See Also
    --------
    pad_constant
    pad_edge
    pad_linear_ramp
    pad_maximum
    pad_mean
    pad_median
    pad_minimum
    pad_reflect
    pad_wrap

    Notes
    -----
    Very similar to pad_reflect, but includes the edge values in the
    reflection.

    For `array` with rank greater than 1, some of the padding of later axes is
    calculated from padding of previous axes.  This is easiest to think about
    with a rank 2 array where the corners of the padded array are calculated
    by using padded values from the first axes.

    Examples
    --------
    >>> a = [1, 2, 3, 4, 5]
    >>> np.lib.pad_symmetric(a, (2,3))
    array([2, 1, 1, 2, 3, 4, 5, 5, 4, 3])
    >>> np.lib.pad_symmetric(a, (2,3), reflect_type='odd')
    array([0, 1, 1, 2, 3, 4, 5, 5, 6, 7])
    """
    return _loop_across(array, pad_width, _symmetric,
                        reflect_type=reflect_type)


def pad_reflect(array, pad_width=1, reflect_type='even'):
    """
    Pads with the reflection of the vector mirrored on the first and last
    values of the vector along each axis.

    Parameters
    ----------
    array : array_like of rank N
        Input array
    pad_width : {sequence of N sequences(int,int), sequence(int,int),
                 sequence(int,), int}, optional
        Number of values padded to each edge of each axis.
        ((before_1, after_1), ... (before_N, after_N)) unique pad widths for
        each axis.
        ((before, after),) yields same before and after pad for each axis.
        (pad,) or int is a shortcut for before = after = pad width for all
        axes.
        Default is 1.
    reflect_type : str {'even', 'odd'}, optional
        The 'even' style is the default with an unaltered reflection around
        the edge value.  For the 'odd' style, the extented part of the array
        is created by subtracting the reflected values from two times the edge
        value.

    Returns
    -------
    pad_reflect : ndarray of rank N
        Padded array.

    See Also
    --------
    pad_constant
    pad_edge
    pad_linear_ramp
    pad_maximum
    pad_mean
    pad_median
    pad_minimum
    pad_symmetric
    pad_wrap

    Notes
    -----
    For `array` with rank greater than 1, some of the padding of later axes is
    calculated from padding of previous axes.  This is easiest to think about
    with a rank 2 array where the corners of the padded array are calculated
    by using padded values from the first axes.

    Examples
    --------
    >>> a = [1, 2, 3, 4, 5]
    >>> np.lib.pad_reflect(a, (2,3))
    array([3, 2, 1, 2, 3, 4, 5, 4, 3, 2])
    >>> np.lib.pad_reflect(a, (2,3), reflect_type='odd')
    array([-1,  0,  1,  2,  3,  4,  5,  6,  7,  8])

    """
    return _loop_across(array, pad_width, _reflect, reflect_type=reflect_type)


def pad_wrap(array, pad_width=1):
    """
    Pads with the wrap of the vector along the axis.  The first values are
    used to pad the end and the end values are used to pad the beginning.

    Parameters
    ----------
    array : array_like of rank N
        Input array
    pad_width : {sequence of N sequences(int,int), sequence(int,int),
                 sequence(int,), int}, optional
        Number of values padded to each edge of each axis.
        ((before_1, after_1), ... (before_N, after_N)) unique pad widths for
        each axis.
        ((before, after),) yields same before and after pad for each axis.
        (pad,) or int is a shortcut for before = after = pad width for all
        axes.
        Default is 1.

    Returns
    -------
    pad_wrap : ndarray of rank N
        Padded array.

    See Also
    --------
    pad_constant
    pad_edge
    pad_linear_ramp
    pad_maximum
    pad_mean
    pad_median
    pad_minimum
    pad_reflect
    pad_symmetric

    Notes
    -----
    For `array` with rank greater than 1, some of the padding of later axes is
    calculated from padding of previous axes.  This is easiest to think about
    with a rank 2 array where the corners of the padded array are calculated
    by using padded values from the first axes.

    Examples
    --------
    >>> a = [1, 2, 3, 4, 5]
    >>> np.lib.pad_wrap(a, (2,3))
    array([4, 5, 1, 2, 3, 4, 5, 1, 2, 3])

    """
    return _loop_across(array, pad_width, _wrap)


def pad_edge(array, pad_width=1):
    """
    Pads with the edge values of the vector along the axis.

    Parameters
    ----------
    array : array_like of rank N
        Input array
    pad_width : {sequence of N sequences(int,int), sequence(int,int),
                 sequence(int,), int}, optional
        Number of values padded to each edge of each axis.
        ((before_1, after_1), ... (before_N, after_N)) unique pad widths for
        each axis.
        ((before, after),) yields same before and after pad for each axis.
        (pad,) or int is a shortcut for before = after = pad width for all
        axes.
        Default is 1.

    Returns
    -------
    pad_edge : ndarray of rank N
        Padded array.

    See Also
    --------
    pad_constant
    pad_linear_ramp
    pad_maximum
    pad_mean
    pad_median
    pad_minimum
    pad_reflect
    pad_symmetric
    pad_wrap

    Notes
    -----
    For `array` with rank greater than 1, some of the padding of later axes is
    calculated from padding of previous axes.  This is easiest to think about
    with a rank 2 array where the corners of the padded array are calculated
    by using padded values from the first axes.

    Examples
    --------
    >>> a = [1, 2, 3, 4, 5]
    >>> np.lib.pad_edge(a, (2,3))
    array([1, 1, 1, 2, 3, 4, 5, 5, 5, 5])

    """
    return _loop_across(array, pad_width, _edge)

