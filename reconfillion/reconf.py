from graphillion import setset, GraphSet, VertexSetSet

def _singleton(state, search_space):
    """Build a singleton family ``{state}`` of the same type as search_space."""
    if isinstance(search_space, GraphSet):
        return GraphSet([state])
    elif isinstance(search_space, VertexSetSet):
        return VertexSetSet([state])
    elif isinstance(search_space, setset):
        return setset([state])
    else:
        raise TypeError

def _one_move(family, search_space, model):
    """Return the family of states reachable from ``family`` in one move.

    - ``tj`` (token jumping): remove one element and add one (size unchanged).
    - ``tar`` (token addition/removal): add one element *or* remove one
      (size changes by +-1). The caller is responsible for restricting the
      result to the valid size range by intersecting with the search space.
    """
    if isinstance(search_space, GraphSet):
        if model == 'tj':
            return family.remove_add_some_edges()
        elif model == 'tar':
            return family.add_some_edge() | family.remove_some_edge()
    elif isinstance(search_space, VertexSetSet):
        if model == 'tj':
            return family.remove_add_some_vertices()
        elif model == 'tar':
            return family.add_some_vertex() | family.remove_some_vertex()
    else:
        if model == 'tj':
            return family.remove_add_some_elements()
        elif model == 'tar':
            return family.add_some_element() | family.remove_some_element()
    raise NotImplementedError

def _restrict_size(family, lower, upper):
    """Restrict ``family`` to states whose cardinality is in ``[lower, upper]``.

    ``lower``/``upper`` of ``None`` mean no bound in that direction. ``larger``
    and ``smaller`` are available on all three graphillion family types.
    """
    if lower is not None:
        family = family.larger(lower - 1)   # keep size >= lower
    if upper is not None:
        family = family.smaller(upper + 1)  # keep size <= upper
    return family

def _get_seq(setset_seq, s, t, search_space, model, k):
    reconf_seq = [set(t)]
    current_set = t
    for i in range(len(setset_seq) - 2, -1, -1):
        sz = _singleton(current_set, search_space)
        next_ss = _one_move(sz, search_space, model)
        current_set = (setset_seq[i] & next_ss).choice()
        reconf_seq.insert(0, set(current_set))
    return reconf_seq

def get_reconf_seq(s, t, search_space, model = 'tj', k = 1, lower = None, upper = None):
    if model not in ('tj', 'tar'):
        raise NotImplementedError

    if s not in search_space:
        raise ValueError('s must be in search_space.')

    if t not in search_space:
        raise ValueError('t must be in search_space.')

    # For the tar model, states must stay within the [lower, upper] size range.
    # The valid search space is therefore the size-restricted search_space, and
    # s/t must themselves fall inside the range.
    if model == 'tar':
        for name, state in (('s', s), ('t', t)):
            if lower is not None and len(state) < lower:
                raise ValueError(f'|{name}| ({len(state)}) is below lower ({lower}).')
            if upper is not None and len(state) > upper:
                raise ValueError(f'|{name}| ({len(state)}) is above upper ({upper}).')
        effective_space = _restrict_size(search_space, lower, upper)
    else:
        effective_space = search_space

    if s == t:
        return [s]

    setset_seq = [_singleton(s, search_space)]

    # Saturation is detected by tracking the cumulative set of reached states.
    # Comparing consecutive frontiers (setset_seq[-2] vs setset_seq[-1]) is not
    # enough for tar: each move changes the size by +-1, so the "exactly i moves"
    # frontier alternates between size parities and consecutive frontiers are
    # never equal -- the loop would run forever. Once a new frontier adds no
    # state we have not seen before, the reachable component is exhausted and t
    # is unreachable.
    reached = setset_seq[0]

    while True:
        next_ss = _one_move(setset_seq[-1], search_space, model) & effective_space

        setset_seq.append(next_ss)
        if t in next_ss:
            return _get_seq(setset_seq, s, t, search_space, model, k)

        union = reached | next_ss
        if union == reached:
            return []
        reached = union
