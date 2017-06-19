# pylint: disable=unused-variable, unused-argument
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


def test_fixture_exclusion_nested(suite, suite_test):

    fixture = suite.slashconf.add_fixture()
    param = fixture.add_parameter()
    suite_test.depend_on_fixture(fixture)

    param_value = param.values[0]

    suite_test.add_decorator('slash.exclude("{fixture_name}.{param_name}", {values})'.format(
        fixture_name=fixture.name,
        param_name=param.name,
        values=[param_value],
    ))
    suite_test.exclude_param_value(param.name, param_value)
    suite.run()
