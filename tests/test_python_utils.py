# pylint: disable=redefined-outer-name
import pytest

from slash.utils.python import call_all_raise_first


def test_call_all_raise_first(funcs):
    exc_type = funcs[2].raise_when_called()

    with pytest.raises(exc_type):
        call_all_raise_first(funcs)

    for index, func in enumerate(funcs):  # pylint: disable=unused-variable
        assert func.called_count == 1


@pytest.fixture
def funcs():

    class Func(object):

        called_count = 0
        exc_type = None

        def __call__(self):
            self.called_count += 1
            if self.exc_type is not None:
                raise self.exc_type()

        def raise_when_called(self):
            class CustomException(Exception):
                pass

            self.exc_type = CustomException
            return self.exc_type

    return [Func() for _ in range(10)]
