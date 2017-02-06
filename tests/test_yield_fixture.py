# pylint: disable=unused-argument, unused-variable
from uuid import uuid4

import slash

from .conftest import Checkpoint
from .utils import make_runnable_tests


def test_yield_fixture(yield_fixture_decorator):
    iterations = [uuid4() for i in range(3)]
    start_checkpoints, end_checkpoints = [
        {iteration: Checkpoint() for iteration in iterations}
        for i in range(2)]
    value = uuid4()
    inner_fixture_value = uuid4()

    with slash.Session() as s:

        @s.fixture_store.add_fixture
        @slash.fixture
        def other_fixture():
            return inner_fixture_value


        @s.fixture_store.add_fixture
        @slash.parametrize('iteration', list(iterations))
        @yield_fixture_decorator
        def fixture(iteration, other_fixture):
            assert other_fixture == inner_fixture_value
            start_checkpoints[iteration]()
            yield value
            end_checkpoints[iteration]()

        def test_something(fixture):
            assert fixture == value

        s.fixture_store.resolve()

        with s.get_started_context():
            slash.runner.run_tests(make_runnable_tests(test_something))
        assert s.results.is_success(allow_skips=False)


def test_yield_fixture_with_this_argument(yield_fixture_decorator):
    iterations = [uuid4() for i in range(3)]
    value = uuid4()

    with slash.Session() as s:


        @s.fixture_store.add_fixture
        @slash.parametrize('iteration', list(iterations))
        @yield_fixture_decorator
        def fixture(this, iteration):
            yield value

        def test_something(fixture):
            assert fixture == value

        s.fixture_store.resolve()

        with s.get_started_context():
            slash.runner.run_tests(make_runnable_tests(test_something))


def test_yield_fixture_with_scope_argument(yield_fixture_decorator):
    value = str(uuid4())

    with slash.Session() as s:


        @s.fixture_store.add_fixture
        @yield_fixture_decorator(scope='session')
        def fixture():
            yield value

        def test_something(fixture):
            assert fixture == value

        s.fixture_store.resolve()

        with s.get_started_context():
            slash.runner.run_tests(make_runnable_tests(test_something))
