import sys
import pytest

from slash.core.error import Error
from .utils import Unprintable


def test_exception_attributes(error):  # pylint: disable=redefined-outer-name, unused-argument
    attrs = error.exception_attributes
    assert attrs['x'] == 2
    assert isinstance(attrs['y'], str)


def test_exception_attributes_with_message():
    assert Error('x').exception_attributes is None


@pytest.fixture
def error():

    class MyException(Exception):

        def __init__(self):
            super(MyException, self).__init__()
            self.x = 2
            self.y = [str(i) for i in range(10)]
            self.d = {'some': 'dict', 'here': 'too'}
            self.unprintable = Unprintable()

    def func():
        raise MyException()

    try:
        func()
    except MyException:
        return Error(exc_info=sys.exc_info())
    else:
        assert False, 'Did not raise'
