import warnings
from copy import deepcopy
from itertools import product
from contextlib import contextmanager

import numpy as np


# - [ ] check better ways to silence mne
@contextmanager
def silent_mne():
    import mne
    log_level = mne.set_log_level('CRITICAL', return_old_level=True)
    yield
    mne.set_log_level(log_level)


@contextmanager
def silent():
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        yield



# TODO:
# - [ ] should check type and size of the vars (check how mne-python does it)
# - [ ] detect if in notebook/qtconsole and ignore 'Out' and similar vars
# - [ ] display numpy arrays as "5 x 2 int array"
#       lists as "list of strings" etc.
def whos():
    """Print the local variables in the caller's frame.
    Copied from stack overflow:
    http://stackoverflow.com/questions/6618795/get-locals-from-calling-namespace-in-python"""
    import inspect
    frame = inspect.currentframe()
    ignore_vars = []
    ignore_starting = ['__']
    try:
        lcls = frame.f_back.f_locals
        # test if ipython
        ipy_vars = ['In', 'Out', 'get_ipython', '_oh', '_sh']
        in_ipython = all([var in lcls for var in ipy_vars])
        if in_ipython:
            ignore_vars = ipy_vars + ['_']
            ignore_starting += ['_i']
        for name, var in lcls.items():
            if name in ignore_vars:
                continue
            if any([name.startswith(s) for s in ignore_starting]):
                continue
            print(name, type(var), var)
    finally:
        del frame


# - [ ] maybe add the one_in approach from find_range
# - [ ] if np.ndarray try to format output in the right shape
def find_index(vec, vals):
    if not isinstance(vals, (list, tuple, np.ndarray)):
        vals = [vals]
    return [np.abs(vec - x).argmin() for x in vals]


def find_range(vec, ranges):
    '''
    Find specified ranges in an ordered vector and retur them as slices.

    Parameters
    ----------
    vec : numpy array
        Vector of sorted values.
    ranges: list of tuples/lists or two-element list/tuple

    Returns
    -------
    slices : slice or list of slices
        Slices representing the ranges. If one range was passed the output
        is a slice. If two or more ranges were passed the output is a list
        of slices.
    '''
    assert isinstance(ranges, (list, tuple))
    assert len(ranges) > 0
    one_in = False
    if not isinstance(ranges[0], (list, tuple)) and len(ranges) == 2:
        one_in = True
        ranges = [ranges]

    slices = list()
    for rng in ranges:
        start, stop = [np.abs(vec - x).argmin() for x in rng]
        slices.append(slice(start, stop + 1)) # including last index
    if one_in:
        slices = slices[0]
    return slices


def extend_slice(slc, val, maxval, minval=0):
    '''Extend slice `slc` by `val` in both directions but not exceeding
    `minval` or `maxval`.

    Parameters
    ----------
    slc : slice
        Slice to extend.
    val : int or float
        Value by which to extend the slice.
    maxval : int or float
        Maximum value that cannot be exceeded.

    Returns
    -------
    slc : slice
        New, extended slice.
    '''
    start, stop, step = slc.start, slc.stop, slc.step
    # start
    if not start == minval:
        start -= val
        if start < minval:
            start = minval
    # stop
    if not stop == maxval:
        stop += val
        if stop > maxval:
            stop = maxval
    return slice(start, stop, step)


# join inds
# TODO:
# - [ ] more detailed docs
# - [x] diff mode
# - [x] option to return slice
def group(vec, diff=False, return_slice=False):
    '''
    Group values in a vector into ranges of adjacent identical values.
    '''
    in_grp = False
    group_lims = list()
    if diff:
        vec = np.append(vec, np.max(vec) + 1)
        vec = np.diff(vec) > 0
    else:
        vec = np.append(vec, False)

    # group
    for ii, el in enumerate(vec):
        if in_grp and not el:
            in_grp = False
            group_lims.append([start_ind, ii-1])
        elif not in_grp and el:
            in_grp = True
            start_ind = ii
    grp = np.array(group_lims)

    # format output
    if diff:
        grp[:, 1] += 1
    if return_slice:
        slc = list()
        for start, stop in grp:
            slc.append(slice(start, stop + 1))
        return slc
    else:
        return grp


def subselect_keys(key, mapping, sep='/'):
    '''select keys with subselection by a separator.
    This code was shared by Dennis Engemann on github.

    Parameters
    ----------
    key : string | list of strings
        Keys to subselect with.
    mapping : dict
        Dictionary that is being selected.
    sep : string
        Separator to use in subselection.
    '''

    if isinstance(key, str):
        key = [key]

    mapping = deepcopy(mapping)

    if any(sep in k_i for k_i in mapping.keys()):
        if any(k_e not in mapping for k_e in key):
            # Select a given key if the requested set of
            # '/'-separated types are a subset of the types in that key

            for k in mapping.keys():
                if not all(set(k_i.split('/')).issubset(k.split('/'))
                           for k_i in key):
                    del mapping[k]

            if len(key) == 0:
                raise KeyError('Attempting selection of keys via '
                               'multiple/partial matching, but no '
                               'event matches all criteria.')
    else:
        raise ValueError('Your keys are bad formatted.')
    return mapping


# - [ ] more checks for mne type
# - [ ] maybe move to mneutils ?
def get_info(inst):
    from mne.io.meas_info import Info
    if isinstance(inst, Info):
        return inst
    else:
        return inst.info


# TODO: add evoked (for completeness)
def mne_types():
    import mne
    types = dict()
    from mne.io.meas_info import Info
    try:
        from mne.io import _BaseRaw
        from mne.epochs import _BaseEpochs
        types['raw'] = _BaseRaw
        types['epochs'] = _BaseEpochs
    except ImportError:
        from mne.io import BaseRaw
        from mne.epochs import BaseEpochs
        types['raw'] = BaseRaw
        types['epochs'] = BaseEpochs
    types['info'] = Info
    return types


# see if there is a standard library implementation of something similar
class AtribDict(dict):
    """Just like a dictionary, except that you can access keys with obj.key.

    Copied from psychopy.data.TrialType
    """
    def __getattribute__(self, name):
        try:  # to get attr from dict in normal way (passing self)
            return dict.__getattribute__(self, name)
        except AttributeError:
            try:
                return self[name]
            except KeyError:
                msg = "TrialType has no attribute (or key) \'%s\'"
                raise AttributeError(msg % name)


# shouldn't it be in mypy.chan?
def get_chan_pos(inst):
    info = get_info(inst)
    chan_pos = [info['chs'][i]['loc'][:3] for i in range(len(info['chs']))]
    return np.array(chan_pos)


# TODO
# - [ ] more input validation
#       validate dim_names, dim_values
# - [x] infer df dtypes
# - [x] groups could be any of following
#   * dict of int -> (dict of int -> str)
#   * instead of int -> str there could be tuple -> str
#   * or str -> list mapping
# - [x] support list of lists for groups as well
def array2df(arr, dim_names=None, groups=None, value_name='value'):
    '''
    Melt array into a pandas DataFrame.

    The resulting DataFrame has one row per array value and additionally
    one column per array dimension.

    Parameters
    ----------
    arr : numpy array
        Array to be transformed to DataFrame.
    dim_names : list of str or dict of int to str mappings
        Names of consecutive array dimensions - used as column names of the
        resulting DataFrame.
    groups : list of dicts or dict of dicts
        here more datailed explanation
    value_name : ...
        ...

    Returns
    -------
    df : pandas DataFrame
        ...

    Example
    -------
    >> arr = np.arange(4).reshape((2, 2))
    >> array2df(arr)

      value dim_i dim_j
    0     0    i0    j0
    1     1    i0    j1
    2     2    i1    j0
    3     3    i1    j1

    >> arr = np.arange(12).reshape((4, 3))
    >> array2df(arr, dim_names=['first', 'second'], value_name='array_value',
    >>          groups=[{'A': [0, 2], 'B': [1, 3]},
    >>                  {(0, 2): 'abc', (1,): 'd'}])

       array_value first second
    0            0     A    abc
    1            1     A      d
    2            2     A    abc
    3            3     B    abc
    4            4     B      d
    5            5     B    abc
    6            6     A    abc
    7            7     A      d
    8            8     A    abc
    9            9     B    abc
    10          10     B      d
    11          11     B    abc
    '''
    import pandas as pd
    n_dim = arr.ndim
    shape = arr.shape

    dim_letters = list('ijklmnop')[:n_dim]
    if dim_names is None:
        dim_names = {dim: 'dim_{}'.format(l)
                     for dim, l in enumerate(dim_letters)}
    if groups is None:
        groups = {dim: {i: dim_letters[dim] + str(i)
                        for i in range(shape[dim])} for dim in range(n_dim)}
    else:
        if isinstance(groups, dict):
            groups = {dim: _check_dict(groups[dim], shape[dim])
                      for dim in groups.keys()}
        elif isinstance(groups, list):
            groups = [_check_dict(groups[dim], shape[dim])
                      for dim in range(len(groups))]

    # initialize DataFrame
    col_names = [value_name] + [dim_names[i] for i in range(n_dim)]
    df = pd.DataFrame(columns=col_names, index=np.arange(arr.size))

    # iterate through dimensions producing tuples of relevant dims...
    for idx, adr in enumerate(product(*map(range, shape))):
        df.loc[idx, value_name] = arr[adr] # this could be vectorized easily
        # add relevant values to dim columns
        for dim_idx, dim_adr in enumerate(adr):
            df.loc[idx, dim_names[dim_idx]] = groups[dim_idx][dim_adr]

    # column dtype inference
    try: # for pandas 0.22 or higher
        df = df.infer_objects()
    except: # otherwise
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            df = df.convert_objects(convert_numeric=True)
    return df


def _check_dict(dct, dim_len):
    if isinstance(dct, dict):
        str_keys = all(isinstance(k, str) for k in dct.keys())
        if not str_keys:
            tuple_keys = all(isinstance(k, tuple) for k in dct.keys())

        if str_keys:
            vals_set = set()
            new_dct = dict()
            for k in dct.keys():
                for val in dct[k]:
                    new_dct[val] = k
                    vals_set.add(val)
            assert len(vals_set) == dim_len
        elif tuple_keys:
            new_dct = dict()
            i_set = set()
            for k, val in dct.items():
                for i in k:
                    new_dct[i] = val
                    i_set.add(i)
            assert len(i_set) == dim_len
        else:
            new_dct = dct
    else:
        # validate if equal to num dims
        assert len(dct) == dim_len
        new_dct = dct
    return new_dct
