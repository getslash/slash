import pytest
from slash.utils.iteration import PeekableIterator


def test_peekable_iterator(objects):
    it = PeekableIterator(objects)
    for i, x in enumerate(it):
        assert x is objects[i]
        for peek_num in range(3): # no matter how many times we peek, we get the same result
            if i == len(objects) - 1:
                assert not it.has_next()
                with pytest.raises(StopIteration):
                    it.peek()
                assert it.peek_or_none() is None
            else:
                assert (it.has_next())
                assert it.peek() is objects[(i + 1)]
                assert it.peek_or_none() is objects[(i + 1)]

@pytest.fixture
def objects():
    return [object() for i in range(10)]
