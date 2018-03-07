import functools
import re
import pytest
import warnings

import slash


def _warn(*args, **kwargs):
    return functools.partial(warnings.warn, *args, **kwargs)


def _catch(*args, **kwargs):
    return functools.partial(slash.ignore_warnings, *args, **kwargs)


class CustomWarning(UserWarning):
    pass


@pytest.mark.parametrize('emitter,catch,can_test_negative', [
    (_warn('hello'), _catch(message='hello'), True),
    (_warn('hello'), _catch(message=re.compile('^hello$')), True),
    (_warn('message', category=CustomWarning), _catch(category=CustomWarning), True),
    (_warn('message'), _catch(filename=__file__), False),
])
def test_ignore_warnings(request, emitter, catch, can_test_negative):

    request.addfinalizer(slash.clear_ignored_warnings)

    catch()

    with slash.Session() as session:
        emitter()
    assert list(session.warnings) == []

    if can_test_negative:
        with slash.Session() as session:
            warnings.warn('uncaught', category=DeprecationWarning)
        caught = list(session.warnings)
        assert len(caught) == 1
        assert caught[0].message == 'uncaught'
