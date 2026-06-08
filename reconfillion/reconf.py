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
    # ``model`` is validated by the public entry points, so every branch below
    # is expected to return; the trailing ``raise`` is a defensive backstop.
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

def _forward_bfs(s, search_space, effective_space, model, stop):
    """Expand the reachable frontier from ``s`` one move at a time.

    Starting from the singleton family ``{s}``, repeatedly apply ``_one_move``
    and intersect with ``effective_space``. ``setset_seq[i]`` is the family of
    all valid states reachable from ``s`` in exactly ``i`` moves.

    The loop stops when ``stop(next_ss)`` is true (early stop, e.g. the goal
    appeared) or when a new frontier adds no state not seen before (the
    reachable component is exhausted). Returns ``(setset_seq, stopped)`` where
    ``stopped`` is ``True`` for an early stop and ``False`` for saturation.

    Saturation is detected by tracking the cumulative set of reached states.
    Comparing consecutive frontiers (``setset_seq[-2]`` vs ``setset_seq[-1]``)
    is not enough for tar: each move changes the size by +-1, so the "exactly
    i moves" frontier alternates between size parities and consecutive frontiers
    are never equal -- the loop would run forever.
    """
    setset_seq = [_singleton(s, search_space)]
    reached = setset_seq[0]
    while True:
        next_ss = _one_move(setset_seq[-1], search_space, model) & effective_space
        setset_seq.append(next_ss)
        if stop(next_ss):
            return setset_seq, True
        # Saturation: the new frontier introduces no state not already reached.
        # ``next_ss <= reached`` is equivalent to ``reached | next_ss == reached``
        # but avoids building the union when the frontier is already subsumed.
        if next_ss <= reached:
            return setset_seq, False
        reached = reached | next_ss

def _get_seq(setset_seq, s, t, search_space, model, k):
    reconf_seq = [set(t)]
    current_set = t
    for i in range(len(setset_seq) - 2, -1, -1):
        sz = _singleton(current_set, search_space)
        next_ss = _one_move(sz, search_space, model)
        current_set = (setset_seq[i] & next_ss).choice()
        reconf_seq.insert(0, set(current_set))
    return reconf_seq

def _effective_space(states, search_space, model, lower, upper):
    """Validate tar size bounds and return the effective (size-restricted) space.

    ``states`` is an iterable of ``(name, state)`` pairs to check. For the tar
    model, every state must fall within ``[lower, upper]`` (or ``ValueError`` is
    raised) and the effective search space is ``search_space`` restricted to that
    size range. For other models ``lower``/``upper`` are not meaningful and must
    be left as ``None``; the search space is returned unchanged.
    """
    if model == 'tar':
        for name, state in states:
            if lower is not None and len(state) < lower:
                raise ValueError(f'|{name}| ({len(state)}) is below lower ({lower}).')
            if upper is not None and len(state) > upper:
                raise ValueError(f'|{name}| ({len(state)}) is above upper ({upper}).')
        return _restrict_size(search_space, lower, upper)
    if lower is not None or upper is not None:
        raise ValueError(
            f"lower/upper are only supported for the 'tar' model, not '{model}'.")
    return search_space

def get_reconf_seq(s, t, search_space, model = 'tj', k = 1, lower = None, upper = None):
    """Return a shortest reconfiguration sequence from ``s`` to ``t``.

    Given a start state ``s`` and goal state ``t`` (each a subset of the
    elements/edges/vertices defining ``search_space``), find a shortest series
    of single legal moves transforming ``s`` into ``t`` while every intermediate
    state stays inside ``search_space``. The result is a list of ``set`` states
    ``[s, ..., t]`` where consecutive states differ by exactly one move; an empty
    list ``[]`` means ``t`` is unreachable from ``s``.

    ``model`` selects the move operator:

    - ``'tj'`` (token jumping): each move removes one element and adds one,
      keeping the cardinality fixed (so ``|s|`` must equal ``|t|``).
    - ``'tar'`` (token addition/removal): each move adds *or* removes one element
      (cardinality changes by +-1). ``lower``/``upper`` (either may be ``None``)
      bound every state's size; ``s`` and ``t`` must lie within ``[lower, upper]``
      but may differ in size. ``lower``/``upper`` are rejected for other models.

    The search is a breadth-first frontier expansion over ZDD set families
    (``_forward_bfs``): starting from ``{s}`` it expands one move at a time,
    intersecting with the effective (size-restricted) search space, and stops as
    soon as ``t`` appears -- so the reconstructed sequence (``_get_seq``, walking
    the frontiers backward from ``t``) is shortest. If the frontier saturates
    without reaching ``t``, ``t`` is unreachable and ``[]`` is returned.

    Raises ``ValueError`` if ``s`` or ``t`` is not in ``search_space``, or (for
    tar) falls outside ``[lower, upper]``. ``k`` is an unused placeholder.
    """
    if model not in ('tj', 'tar'):
        raise NotImplementedError

    if s not in search_space:
        raise ValueError('s must be in search_space.')

    if t not in search_space:
        raise ValueError('t must be in search_space.')

    # For the tar model, states must stay within the [lower, upper] size range.
    # The valid search space is therefore the size-restricted search_space, and
    # s/t must themselves fall inside the range.
    effective_space = _effective_space(
        (('s', s), ('t', t)), search_space, model, lower, upper)

    if s == t:
        return [set(s)]

    # Expand the frontier until t appears (reachable) or it saturates without t.
    setset_seq, found = _forward_bfs(
        s, search_space, effective_space, model, stop=lambda ss: t in ss)
    if found:
        return _get_seq(setset_seq, s, t, search_space, model, k)
    return []

def get_longest_shortest_seq(s, search_space, model = 'tj', lower = None, upper = None):
    """Return a shortest reconfiguration sequence to a farthest state from ``s``.

    Given only the start state ``s``, find a state ``t`` reachable from ``s``
    whose shortest-move distance from ``s`` is maximal (if several states tie
    for farthest, any one is chosen) and return a shortest sequence from ``s``
    to that ``t``. This realises the *eccentricity* of ``s`` in the move graph.
    If ``s`` cannot make a single legal move, ``[set(s)]`` is returned.

    Every state in the returned sequence is a ``set`` (including the trivial
    single-element case), matching ``get_reconf_seq``.

    Supports the same ``tj`` / ``tar`` models as ``get_reconf_seq`` (for tar,
    ``lower``/``upper`` bound every state's size). Unlike ``get_reconf_seq`` the
    frontier is always expanded to saturation, since the farthest state is not
    known in advance.
    """
    if model not in ('tj', 'tar'):
        raise NotImplementedError

    if s not in search_space:
        raise ValueError('s must be in search_space.')

    effective_space = _effective_space(
        (('s', s),), search_space, model, lower, upper)

    # Expand the whole reachable component (never stop early).
    setset_seq, _ = _forward_bfs(
        s, search_space, effective_space, model, stop=lambda ss: False)

    # The farthest distance is the last level at which a state appears for the
    # first time. _forward_bfs's final frontier is the saturating one (it adds
    # nothing new), and for tar earlier states reappear by parity, so scan the
    # cumulative reached set to find the last level with a genuinely new state.
    reached = setset_seq[0]
    last_level, last_new = 0, setset_seq[0]
    for i in range(1, len(setset_seq)):
        new = setset_seq[i] - reached
        if new:  # truthy iff the family is non-empty (avoids len() overflow)
            last_level, last_new = i, new
        reached = reached | setset_seq[i]

    if last_level == 0:
        return [set(s)]

    t = last_new.choice()
    return _get_seq(setset_seq[:last_level + 1], s, t, search_space, model, k=1)
