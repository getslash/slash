import pytest
import slash
from slash import context, Session
from .utils import run_tests_assert_success
from .utils.suite_writer import Suite


def test_current_test():
    suite = Suite()

    suite.add_test(type='method').prepend_line(
        'assert slash.test == self')
    suite.add_test(type='method').prepend_line(
        'assert slash.context.test == self')
    suite.add_test(type='method').prepend_line(
        'assert slash.context.test.__slash__.id == self.__slash__.id')

    suite.run()


def test_get_current_session():
    with Session() as s:
        assert context.session is s
        assert context.session is not slash.session
        assert s == slash.session


def test_test_methodname_has_no_dot(test_globals):
    assert not test_globals['test_methodname'].startswith('.')


def test_globals_dir():
    with Session():
        assert 'x' not in dir(slash.g)
        slash.g.x = 2
        assert 'x' in dir(slash.g)


@pytest.fixture
def test_globals(is_method):
    returned = {}

    def _distill():
        returned['test_methodname'] = context.test_methodname
    if is_method:
        class test_something(slash.Test):

            def test_something(self):
                _distill()
    else:
        def test_something():
            _distill()
    run_tests_assert_success(test_something)
    return returned


@pytest.fixture(params=[True, False])
def is_method(request):
    return request.param
