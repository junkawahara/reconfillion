from graphillion import setset, GraphSet, VertexSetSet

def _get_seq(setset_seq, s, t, search_space, model, k):
    reconf_seq = [set(t)]
    current_set = t
    for i in range(len(setset_seq) - 2, -1, -1):
        if isinstance(search_space, GraphSet):
            sz = GraphSet([current_set])
        elif isinstance(search_space, VertexSetSet):
            sz = VertexSetSet([current_set])
        else:
            sz = setset([current_set])
        if model == 'tj':
            if isinstance(search_space, GraphSet):
                next_ss = sz.remove_add_some_edges()
            elif isinstance(search_space, VertexSetSet):
                next_ss = sz.remove_add_some_vertices()
            else:
                next_ss = sz.remove_add_some_elements()
        current_set = (setset_seq[i] & next_ss).choice()
        reconf_seq.insert(0, set(current_set))
    return reconf_seq

def get_reconf_seq(s, t, search_space, model = 'tj', k = 1):
    if model != 'tj':
        raise NotImplementedError

    if s not in search_space:
        raise ValueError('s must be in search_space.')

    if t not in search_space:
        raise ValueError('t must be in search_space.')

    if s == t:
        return [s]
    
    setset_seq = []
    if isinstance(search_space, GraphSet):
        setset_seq.append(GraphSet([s]))
    elif isinstance(search_space, VertexSetSet):
        setset_seq.append(VertexSetSet([s]))
    elif isinstance(search_space, setset):
        setset_seq.append(setset([s]))
    else:
        raise TypeError

    while len(setset_seq) <= 1 or setset_seq[-2] != setset_seq[-1]:
        if model == 'tj':
            if isinstance(search_space, GraphSet):
                next_ss = setset_seq[-1].remove_add_some_edges()
            elif isinstance(search_space, VertexSetSet):
                next_ss = setset_seq[-1].remove_add_some_vertices()
            else:
                next_ss = setset_seq[-1].remove_add_some_elements()

        next_ss = next_ss & search_space

        setset_seq.append(next_ss)
        if t in next_ss:
            return _get_seq(setset_seq, s, t, search_space, model, k)
    return []
