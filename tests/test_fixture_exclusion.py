#pylint: disable=unused-variable, unused-argument
import slash

from .utils import resolve_and_run

def test_fixture_exclusion():

    with slash.Session() as s:

        @s.fixture_store.add_fixture
        @slash.parametrize('param', [1, 2])
        @slash.fixture
        def fixture(param):
            return param * 10

        @slash.exclude('fixture.param', [2])
        def test_something(fixture):
            slash.context.result.data['value'] = fixture

        results = resolve_and_run(test_something)
    assert len(results) == 2
    assert results[0].is_success()
    assert results[0].data['value'] == 10
    assert results[1].is_skip()
    assert not results[1].is_started()
