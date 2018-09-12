import functools
import re
import os
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
    (_warn('message'), _catch(filename=re.compile('^{}$'.format(__file__))), False),
])
def test_ignore_warnings(emitter, catch, can_test_negative):
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


_WARN_MESSAGE = 'Hello World'
@pytest.mark.parametrize('catch,should_ignore', [
    (_catch(message=_WARN_MESSAGE, filename=__file__), True),
    (_catch(message=re.compile('^Hello.*$'), filename=__file__), True),
    (_catch(message=_WARN_MESSAGE, filename=re.compile('^{}'.format(os.path.dirname(__file__)))), True),
    (_catch(message=re.compile('^Hello.*$'), filename=re.compile('^{}'.format(os.path.dirname(__file__)))), True),
    # Negative  (OR relation instead of AND)
    (_catch(message=_WARN_MESSAGE, category=DeprecationWarning), False),
    (_catch(message=re.compile('^Hello.*$'), category=DeprecationWarning), False),
    (_catch(filename=__file__, category=DeprecationWarning), False),
    (_catch(filename=re.compile('^{}$'.format(__file__)), category=DeprecationWarning), False),
])
def test_ignore_warnings_with_multiple_criteria(catch, should_ignore):
    catch()

    with slash.Session() as session:
        warnings.warn(category=CustomWarning, message=_WARN_MESSAGE)
    if should_ignore:
        assert not session.warnings
    else:
        assert len(session.warnings) == 1
        [caught] = list(session.warnings)
        assert caught.message == _WARN_MESSAGE
        assert caught.category == CustomWarning


def test_ignore_warnigns_with_no_parameter():
    slash.ignore_warnings()
    with slash.Session() as session:
        warnings.warn(category=CustomWarning, message=_WARN_MESSAGE)
    assert not session.warnings


@pytest.fixture(autouse=True)
def warnings_cleanup(request):
    request.addfinalizer(slash.clear_ignored_warnings)
