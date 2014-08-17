import itertools

import pytest
from slash.utils.iteration import iteration, PeekableIterator, iter_cartesian_dicts
from slash._compat import iteritems


def test_iteration(objects):
    for index, i in enumerate(iteration(objects)):
        assert i.last_counter0 + 1 == i.last_counter1 == i.total
        assert i.counter0 == index
        assert i.counter1 == index + 1
        if index == 0:
            assert i.first
        else:
            assert not i.first
        assert i.element is objects[index]
        assert index <= len(objects) - 1
        if index == len(objects) - 1:
            assert i.last
        else:
            assert not i.last


def test_iteration_unpacking(objects):
    for index, (i, obj) in enumerate(iteration(objects)):
        assert index == i.counter0
        assert obj is i.element
        assert obj is objects[i.counter0]


def test_iteration_unsupported_sizing():
    for i in iteration(x for x in itertools.count()):
        assert i.first
        with pytest.raises(NotImplementedError):
            i.last
        assert i.last_counter0 is None
        assert i.last_counter1 is None
        break


def test_peekable_iterator(objects):
    it = PeekableIterator(objects)
    for i, x in enumerate(it):
        assert x is objects[i]
        # no matter how many times we peek, we get the same result
        for peek_num in range(3):
            if i == len(objects) - 1:
                assert not it.has_next()
                with pytest.raises(StopIteration):
                    it.peek()
                assert it.peek_or_none() is None
            else:
                assert (it.has_next())
                assert it.peek() is objects[(i + 1)]
                assert it.peek_or_none() is objects[(i + 1)]


def test_cartesian_dict():

    params = {
        'a': [1, 2, 3],
        'b': [4, 5],
        'c': [6, 7],
    }

    assert set(frozenset(iteritems(x)) for x in iter_cartesian_dicts(params)) == \
        set(frozenset([('a', a_value), ('b', b_value), ('c', c_value)])
            for a_value, b_value, c_value in itertools.product(params['a'], params['b'], params['c']))


@pytest.fixture(params=[True, False])
def use_iterator(request):
    return request.param


@pytest.fixture
def objects(use_iterator):
    if use_iterator:
        return range(10)
    return [object() for i in range(10)]
