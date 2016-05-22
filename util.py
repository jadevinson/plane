def iperm(p):
    'Invert a permutation p'
    n = len(p)
    q = [-1 for i in list(range(n))]
    for i in list(range(n)):
        assert isinstance(p[i],int)
        assert p[i]>=0
        assert p[i]<n
        q[p[i]] = i
    for i in q:
        assert q[i]>=0
    return q