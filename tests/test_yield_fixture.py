# pylint: disable=unused-argument, unused-variable
from uuid import uuid4
from contextlib import contextmanager
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


def test_yield_fixture_behavior():
    start_checkpoints, end_checkpoints = [[Checkpoint() for _ in range(2)] for i in range(2)]

    @contextmanager
    def errors_at_exit():
        try:
            yield
        finally:
            assert False, "success-only cleanup occurred after test-failure"

    with slash.Session() as s:


        @s.fixture_store.add_fixture
        @slash.yield_fixture
        def normal_fixture():
            start_checkpoints[0]()
            yield 0
            end_checkpoints[0]()

        @s.fixture_store.add_fixture
        @slash.yield_fixture(success_only_cleanup=True)
        def success_only_fixture():
            start_checkpoints[1]()
            with errors_at_exit():
                yield 1
            assert False, "success-only cleanup occurred after test-failure"
            end_checkpoints[1]()

        def test_something(normal_fixture, success_only_fixture):
            assert normal_fixture == 0
            assert success_only_fixture == 1
            1 / 0

        s.fixture_store.resolve()

        with s.get_started_context():
            slash.runner.run_tests(make_runnable_tests(test_something))
        assert s.results.get_num_errors() == 1
        assert all(c.called for c in start_checkpoints)
        assert end_checkpoints[0].called
        assert not end_checkpoints[1].called
