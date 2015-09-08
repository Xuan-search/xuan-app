from elasticsearch_dsl import utils

def test_merge():
    a = {'a': {'b': 42, 'c': 47}}
    b = {'a': {'b': 123, 'd': -12}, 'e': [1, 2, 3]}

    utils.merge(a, b)

    assert a == {'a': {'b': 123, 'c': 47, 'd': -12}, 'e': [1, 2, 3]}

def test_attrdict_bool():
    d = utils.AttrDict({})

    assert not d
    d.title = 'Title'
    assert d


def test_attrlist_items_get_wrapped_during_iteration():
    al = utils.AttrList([1, object(), [1], {}])

    l = list(iter(al))

    assert isinstance(l[2], utils.AttrList)
    assert isinstance(l[3], utils.AttrDict)


def test_make_dsl_class():
    XY = utils._make_dsl_class(object, 'X', suffix='Y')

    assert XY.__name__ == 'XY'
    assert XY.__bases__ == (object, )
